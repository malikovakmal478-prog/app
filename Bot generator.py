import os
import json
import anthropic

from .bot_templates import TEMPLATES

# API kalitni environment variable orqali bering: export ANTHROPIC_API_KEY=...
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def generate_bot_config(user_description: str, template_category: str) -> dict:
    """
    Foydalanuvchining oddiy tavsifidan (masalan: "kiyim do'koni uchun bot kerak")
    tanlangan shablon uchun to'liq config (matnlar, tugmalar, mahsulotlar) generatsiya qiladi.
    """
    template = TEMPLATES[template_category]
    required_fields = template["required_config_fields"]

    system_prompt = f"""Sen professional Telegram bot config generatoriisan.
Foydalanuvchi tavsifiga asoslanib "{template['name']}" turidagi bot uchun
JSON config yarat. Config quyidagi maydonlarni o'z ichiga olishi SHART: {required_fields}.
FAQAT JSON qaytar, boshqa hech qanday matn, izoh yoki markdown belgisi bo'lmasin."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_description}],
    )

    raw_text = response.content[0].text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        config = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError(f"AI noto'g'ri formatda javob qaytardi: {raw_text[:200]}")

    for field in required_fields:
        if field not in config:
            raise ValueError(f"AI generatsiyasida '{field}' maydoni yetishmayapti")

    return config
