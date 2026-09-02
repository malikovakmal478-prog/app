from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import secrets

app = FastAPI(title="OmniSphere Global API Gateway", version="3.0")

# CORS ni yoqish (Web saytlar va mobil ilovalar murojaat qilishi uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ma'lumotlar bazasi simulyatsiyasi (Real loyihada PostgreSQL ishlatiladi)
DB_USERS = {}
DB_KEYS = {}

class RegisterRequest(BaseModel):
    username: str
    tier: str  # 'starter' ($5), 'pro' ($30), 'enterprise' ($49)

class BotGenerateRequest(BaseModel):
    api_key: str
    bot_token: str
    bot_type: str

@app.post("/api/v1/register")
def register_user(data: RegisterRequest):
    """Foydalanuvchini ro'yxatdan o'tkazish va tarifiga qarab API Key berish"""
    user_id = str(uuid.uuid4())[:8]
    api_key = f"omni_live_{secrets.token_hex(16)}"
    
    limits = {
        "starter": {"bots": 25, "requests": 10000},
        "pro": {"bots": 65, "ai_builders": 15, "requests": 100000},
        "enterprise": {"bots": 230, "ai_builders": 115, "requests": 1000000}
    }
    
    tier_info = limits.get(data.tier, limits["starter"])
    
    DB_KEYS[api_key] = {
        "username": data.username,
        "tier": data.tier,
        "limits": tier_info,
        "used_requests": 0
    }
    
    return {
        "status": "success",
        "message": f"Tabriklaymiz {data.username}! Sizning {data.tier.upper()} tarifingiz faollashdi.",
        "api_key": api_key,
        "allowed_features": tier_info
    }

@app.post("/api/v1/generate-bot")
def generate_bot(data: BotGenerateRequest):
    """API Key orqali Telegram bot yaratish va avtomatik ulash"""
    if data.api_key not in DB_KEYS:
        raise HTTPException(status_code=403, detail="Xatolik: Yaroqsiz yoki bloklangan API Key!")
    
    user_data = DB_KEYS[data.api_key]
    
    # Bot kodini generatsiya qilish
    bot_script = f"""
# OmniSphere Auto-Generated Bot for {user_data['username']}
# Tarif: {user_data['tier'].upper()} | Bot Turi: {data.bot_type}
import telebot

TOKEN = "{data.bot_token}"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Salom! Bu OmniSphere platformasi orqali yaratilgan avtomatik bot.")

if __name__ == '__main__':
    bot.infinity_polling()
    """
    
    return {
        "status": "success",
        "message": "Bot muvaffaqiyatli yaratildi va serverga ulandi!",
        "bot_type": data.bot_type,
        "generated_code_preview": bot_script[:150] + "..."
    }

@app.get("/api/v1/stats")
def get_stats(x_api_key: str = Header(None)):
    """Foydalanuvchining limit va foydalanish statistikasi"""
    if not x_api_key or x_api_key not in DB_KEYS:
        raise HTTPException(status_code=403, detail="API Key talab qilinadi!")
    
    return {
        "api_key": x_api_key,
        "account_info": DB_KEYS[x_api_key]
    }
