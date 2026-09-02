from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CreateBotRequest(BaseModel):
    telegram_token: str          # BotFather'dan olingan token
    template_category: str       # "faq", "shop", "quiz", ...
    description: str             # "Kiyim do'koni uchun bot kerak, erkaklar va ayollar bo'limi bilan"


class UpgradePlanRequest(BaseModel):
    plan: str   # "starter" | "pro" | "business"
