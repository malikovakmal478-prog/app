from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db, engine, Base
from .models import User, APIKey, BotInstance, PlanTier, PLAN_LIMITS
from .schemas import RegisterRequest, LoginRequest, CreateBotRequest, UpgradePlanRequest
from .auth import hash_password, verify_password, create_access_token, get_current_user
from .api_key_utils import generate_api_key, get_current_api_key, check_bot_creation_limit
from .bot_templates import TEMPLATES, get_allowed_templates_for_plan
from .bot_generator import generate_bot_config
from .telegram_manager import validate_bot_token, set_webhook, handle_incoming_update

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BotFactory API", version="1.0")


# ---------- FOYDALANUVCHI RO'YXATDAN O'TISHI / LOGIN ----------

@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Bu email allaqachon ro'yxatdan o'tgan")

    user = User(email=data.email, hashed_password=hash_password(data.password), plan=PlanTier.starter)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return {"access_token": token, "user_id": user.id, "plan": user.plan.value}


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Email yoki parol noto'g'ri")

    token = create_access_token(user.id)
    return {"access_token": token, "user_id": user.id, "plan": user.plan.value}


# ---------- API KEY BOSHQARUVI (dashboard, login token bilan) ----------

@app.post("/dashboard/api-keys")
def create_api_key(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    raw_key, key_hash, prefix = generate_api_key()
    key_obj = APIKey(key_hash=key_hash, key_prefix=prefix, owner_id=user.id)
    db.add(key_obj)
    db.commit()
    return {
        "api_key": raw_key,  # FAQAT SHU YERDA to'liq ko'rsatiladi - keyin qayta ko'rinmaydi
        "warning": "Bu keyni xavfsiz joyda saqlang, qayta ko'rsatilmaydi!",
    }


@app.get("/dashboard/api-keys")
def list_api_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    keys = db.query(APIKey).filter(APIKey.owner_id == user.id).all()
    return [{"id": k.id, "prefix": k.key_prefix, "active": k.is_active, "last_used": k.last_used_at} for k in keys]


@app.delete("/dashboard/api-keys/{key_id}")
def revoke_api_key(key_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    key_obj = db.query(APIKey).filter(APIKey.id == key_id, APIKey.owner_id == user.id).first()
    if not key_obj:
        raise HTTPException(404, "Key topilmadi")
    key_obj.is_active = False
    db.commit()
    return {"status": "bloklandi"}


@app.post("/dashboard/upgrade-plan")
def upgrade_plan(data: UpgradePlanRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.plan not in [p.value for p in PlanTier]:
        raise HTTPException(400, "Noto'g'ri tarif nomi")
    # ESLATMA: bu yerga real to'lov tekshiruvi (Payme/Click webhook) ulanishi SHART.
    # Hozircha to'lov qabul qilingan deb faraz qilinmoqda.
    user.plan = PlanTier(data.plan)
    db.commit()
    return {"status": "yangilandi", "new_plan": user.plan.value, "limits": PLAN_LIMITS[user.plan]}


@app.get("/dashboard/available-templates")
def available_templates(user: User = Depends(get_current_user)):
    allowed = PLAN_LIMITS[user.plan]["allowed_template_categories"]
    return get_allowed_templates_for_plan(allowed)


# ---------- BOT YARATISH (REST API - tashqi dasturchilar API KEY bilan chaqiradi) ----------

@app.post("/api/v1/bots/create")
async def create_bot(
    data: CreateBotRequest,
    api_key: APIKey = Depends(get_current_api_key),
    db: Session = Depends(get_db),
):
    user = api_key.owner

    if data.template_category not in TEMPLATES:
        raise HTTPException(400, f"Noma'lum shablon. Mavjudlar: {list(TEMPLATES.keys())}")

    check_bot_creation_limit(user, db, data.template_category)

    # 1) Telegram tokenini tekshirish
    try:
        bot_info = await validate_bot_token(data.telegram_token)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # 2) AI orqali config generatsiya qilish (matnlar, mahsulotlar, savollar...)
    try:
        config = generate_bot_config(data.description, data.template_category)
    except ValueError as e:
        raise HTTPException(500, f"Bot config generatsiyasida xato: {e}")

    # 3) Bazaga saqlash
    bot = BotInstance(
        owner_id=user.id,
        telegram_token=data.telegram_token,
        telegram_username=bot_info.get("username"),
        template_category=data.template_category,
        config=config,
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)

    # 4) Webhookni o'rnatish - shu paytdan bot HAQIQIY ishlay boshlaydi
    webhook_url = await set_webhook(data.telegram_token, bot.id)
    bot.webhook_url = webhook_url
    db.commit()

    return {
        "bot_id": bot.id,
        "telegram_username": bot.telegram_username,
        "status": "faol",
        "config_preview": config,
    }


@app.get("/api/v1/bots")
def list_my_bots(api_key: APIKey = Depends(get_current_api_key), db: Session = Depends(get_db)):
    bots = db.query(BotInstance).filter(BotInstance.owner_id == api_key.owner_id).all()
    return [
        {"id": b.id, "username": b.telegram_username, "category": b.template_category, "active": b.is_active}
        for b in bots
    ]


@app.get("/api/v1/usage")
def usage_stats(api_key: APIKey = Depends(get_current_api_key), db: Session = Depends(get_db)):
    """Foydalanuvchi qolgan limitlarini ko'radi."""
    user = api_key.owner
    limits = PLAN_LIMITS[user.plan]
    bot_count = db.query(BotInstance).filter(BotInstance.owner_id == user.id).count()
    return {
        "plan": user.plan.value,
        "bots_used": bot_count,
        "bots_limit": limits["max_bots"],
        "messages_limit_per_bot_monthly": limits["monthly_messages_per_bot"],
    }


# ---------- TELEGRAM WEBHOOK QABULLOVCHISI ----------

@app.post("/webhook/{bot_id}")
async def telegram_webhook(bot_id: int, request: Request, db: Session = Depends(get_db)):
    """Telegram har bir yangi xabarni shu manzilga yuboradi."""
    bot = db.query(BotInstance).filter(BotInstance.id == bot_id, BotInstance.is_active == True).first()
    if not bot:
        raise HTTPException(404, "Bot topilmadi")

    update = await request.json()
    await handle_incoming_update(bot, update, db)
    return {"ok": True}
