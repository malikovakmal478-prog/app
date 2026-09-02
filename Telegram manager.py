import httpx
from sqlalchemy.orm import Session

from .models import BotInstance, UsageLog

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

# O'z domeningizga o'zgartiring (HTTPS bo'lishi SHART - Telegram talabi)
BASE_WEBHOOK_URL = "https://your-domain.com/webhook"


async def validate_bot_token(token: str) -> dict:
    """Token haqiqiy BotFather tokeni ekanini tekshiradi."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(TELEGRAM_API.format(token=token, method="getMe"))
        data = resp.json()
        if not data.get("ok"):
            raise ValueError("Bu Telegram bot token yaroqsiz. BotFather'dan olingan tokenni tekshiring.")
        return data["result"]  # {"id":..., "username":..., ...}


async def set_webhook(token: str, bot_id: int) -> str:
    """Bot uchun webhook o'rnatadi - Telegram shu manzilga xabar yuboradi."""
    webhook_url = f"{BASE_WEBHOOK_URL}/{bot_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            TELEGRAM_API.format(token=token, method="setWebhook"),
            params={"url": webhook_url},
        )
        data = resp.json()
        if not data.get("ok"):
            raise ValueError(f"Webhook o'rnatilmadi: {data}")
    return webhook_url


async def send_message(token: str, chat_id: int, text: str, reply_markup: dict = None):
    async with httpx.AsyncClient() as client:
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        await client.post(TELEGRAM_API.format(token=token, method="sendMessage"), json=payload)


def build_inline_keyboard(buttons: list[dict]) -> dict:
    """buttons: [{"text": "...", "callback_data": "..."}]"""
    return {"inline_keyboard": [[{"text": b["text"], "callback_data": b["callback_data"]}] for b in buttons]}


async def handle_incoming_update(bot: BotInstance, update: dict, db: Session):
    """
    Telegramdan kelgan har bir xabarni shablon turiga qarab qayta ishlaydi.
    Bu funksiya HAQIQIY logikani bajaradi - shunchaki demo emas.
    """
    config = bot.config
    token = bot.telegram_token

    message = update.get("message")
    callback = update.get("callback_query")

    # Foydalanish statistikasini yozib boramiz (limit tekshirish uchun)
    db.add(UsageLog(bot_id=bot.id, endpoint="telegram_update"))
    db.commit()

    if message:
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text == "/start":
            welcome = config.get("welcome_text", "Salom!")
            if bot.template_category == "faq":
                buttons = [
                    {"text": q["question"], "callback_data": f"faq_{i}"}
                    for i, q in enumerate(config.get("questions", []))
                ]
                await send_message(token, chat_id, welcome, build_inline_keyboard(buttons))
            elif bot.template_category == "shop":
                buttons = [
                    {"text": f"{p['name']} - {p['price']}", "callback_data": f"prod_{i}"}
                    for i, p in enumerate(config.get("products", []))
                ]
                await send_message(token, chat_id, welcome, build_inline_keyboard(buttons))
            else:
                await send_message(token, chat_id, welcome)
            return

        # Boshqa har qanday matn - keyingi bosqichda kengaytiriladi (FSM, holat saqlash va h.k.)
        await send_message(token, chat_id, "Buyruqni tushunmadim. /start ni bosing.")

    elif callback:
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]

        if bot.template_category == "faq" and data.startswith("faq_"):
            idx = int(data.split("_")[1])
            answer = config["questions"][idx]["answer"]
            await send_message(token, chat_id, answer)

        elif bot.template_category == "shop" and data.startswith("prod_"):
            idx = int(data.split("_")[1])
            product = config["products"][idx]
            text = f"{product['name']}\nNarxi: {product['price']}\n\nBuyurtma berish uchun: {config.get('order_contact', '')}"
            await send_message(token, chat_id, text)
