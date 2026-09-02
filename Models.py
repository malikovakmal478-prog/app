import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


class PlanTier(str, enum.Enum):
    starter = "starter"    # $5  -> 25 ta shablon kombinatsiyasi
    pro = "pro"            # $30 -> 65 ta
    business = "business"  # $49 -> 230+ ta


# Har bir tarifning haqiqiy texnik cheklovlari (marketing raqami emas!)
PLAN_LIMITS = {
    PlanTier.starter: {
        "price_usd": 5,
        "max_bots": 3,
        "monthly_messages_per_bot": 1000,
        "allowed_template_categories": ["shop", "faq", "reminder"],
        "ai_customization_level": "basic",   # faqat matn/tugma o'zgartirish
    },
    PlanTier.pro: {
        "price_usd": 30,
        "max_bots": 10,
        "monthly_messages_per_bot": 10000,
        "allowed_template_categories": ["shop", "faq", "reminder", "quiz", "crm", "booking"],
        "ai_customization_level": "advanced",  # logika, tashqi API ulash
    },
    PlanTier.business: {
        "price_usd": 49,
        "max_bots": 999,
        "monthly_messages_per_bot": 100000,
        "allowed_template_categories": ["shop", "faq", "reminder", "quiz", "crm",
                                         "booking", "payments", "multistep", "database"],
        "ai_customization_level": "full",  # ko'p bosqichli, DB bilan ishlash
    },
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan = Column(Enum(PlanTier), default=PlanTier.starter)
    plan_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    api_keys = relationship("APIKey", back_populates="owner")
    bots = relationship("BotInstance", back_populates="owner")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    key_prefix = Column(String, nullable=False)  # UI da ko'rsatish uchun (sk_live_ab12...)
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="api_keys")


class BotInstance(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    telegram_token = Column(String, nullable=False)   # BotFather'dan olingan token
    telegram_username = Column(String, nullable=True)
    template_category = Column(String, nullable=False)   # shop, faq, quiz, ...
    config = Column(JSON, nullable=False)   # AI generatsiya qilgan sozlamalar (matnlar, tugmalar, logika)
    webhook_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="bots")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=True)
    endpoint = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
