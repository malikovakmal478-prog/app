import hashlib
import secrets
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, Header, Depends

from .database import get_db
from .models import APIKey, User, PLAN_LIMITS, BotInstance, UsageLog


def generate_api_key() -> tuple[str, str, str]:
    """
    Yangi API key generatsiya qiladi.
    Qaytaradi: (foydalanuvchiga bir marta ko'rsatiladigan to'liq key, hash, prefix)
    """
    raw_key = "sk_live_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:14] + "..."  # dashboard'da ko'rsatish uchun
    return raw_key, key_hash, prefix


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def get_current_api_key(
    authorization: str = Header(None), db: Session = Depends(get_db)
) -> APIKey:
    """
    Har bir API so'rovida keyni tekshiradigan dependency.
    Foydalanish: Authorization: Bearer sk_live_xxxxx
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="API key kerak: Authorization: Bearer <key>")

    raw_key = authorization.split(" ", 1)[1]
    key_hash = hash_key(raw_key)

    key_obj = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
    if not key_obj:
        raise HTTPException(status_code=401, detail="API key noto'g'ri yoki bloklangan")

    key_obj.last_used_at = datetime.datetime.utcnow()
    db.commit()
    return key_obj


def check_bot_creation_limit(user: User, db: Session, template_category: str):
    """Tarifga qarab: bot soni limiti va shablon kategoriyasi ruxsat etilganmi tekshiradi."""
    limits = PLAN_LIMITS[user.plan]

    current_bot_count = db.query(BotInstance).filter(BotInstance.owner_id == user.id).count()
    if current_bot_count >= limits["max_bots"]:
        raise HTTPException(
            status_code=403,
            detail=f"'{user.plan.value}' tarifida maksimal {limits['max_bots']} ta bot ruxsat etilgan. "
                   f"Tarifni yangilang.",
        )

    if template_category not in limits["allowed_template_categories"]:
        raise HTTPException(
            status_code=403,
            detail=f"'{template_category}' shabloni sizning tarifingizda mavjud emas. "
                   f"Mavjud kategoriyalar: {limits['allowed_template_categories']}",
        )


def check_message_limit(bot: BotInstance, user: User, db: Session):
    """Bot uchun oylik xabar limiti tekshiriladi (UsageLog asosida)."""
    limits = PLAN_LIMITS[user.plan]
    month_start = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    count = (
        db.query(UsageLog)
        .filter(UsageLog.bot_id == bot.id, UsageLog.timestamp >= month_start)
        .count()
    )
    if count >= limits["monthly_messages_per_bot"]:
        raise HTTPException(
            status_code=429,
            detail="Bu bot uchun oylik xabar limiti tugadi. Tarifni yangilang yoki keyingi oyni kuting.",
        )
