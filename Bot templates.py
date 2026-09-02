"""
BOT SHABLONLARI
================
Bu yerda haqiqatan ishlaydigan bot "skeletonlari" bor.
AI (bot_generator.py) foydalanuvchi tavsifiga qarab shu shablonlardan birini
tanlaydi va uning ICHIDAGI MATN/TUGMA/MA'LUMOTLARINI to'ldiradi (config).

"230 ta bot" degani - shu bir nechta REAL kategoriyaning yuzlab
turli matn/mahsulot/savol kombinatsiyasi bilan sozlanishi demakdir.
Bu YOLG'ON emas, lekin halol tushuntirish shart.
"""

TEMPLATES = {
    "faq": {
        "name": "FAQ / Ma'lumot boti",
        "description": "Tez-tez so'raladigan savollarga tugmalar orqali javob beradi",
        "required_config_fields": ["welcome_text", "questions"],
        # questions: [{"question": "...", "answer": "..."}]
    },
    "shop": {
        "name": "Do'kon / Katalog boti",
        "description": "Mahsulotlarni ko'rsatadi, savatga qo'shadi, buyurtma qabul qiladi",
        "required_config_fields": ["welcome_text", "products", "order_contact"],
        # products: [{"name": "...", "price": "...", "photo_url": "..."}]
    },
    "reminder": {
        "name": "Eslatma boti",
        "description": "Foydalanuvchi belgilagan vaqtda eslatma yuboradi",
        "required_config_fields": ["welcome_text"],
    },
    "quiz": {
        "name": "Viktorina boti",
        "description": "Savol-javob o'yini, ball hisoblaydi",
        "required_config_fields": ["welcome_text", "questions"],
        # questions: [{"question": "...", "options": [...], "correct_index": 0}]
    },
    "crm": {
        "name": "Mijozlar bilan ishlash (CRM) boti",
        "description": "Mijoz murojaatlarini qabul qiladi, adminga yuboradi, holatini kuzatadi",
        "required_config_fields": ["welcome_text", "admin_chat_id", "categories"],
    },
    "booking": {
        "name": "Buyurtma/Bron qilish boti",
        "description": "Xizmat vaqtini tanlash va bron qilish (masalan, sartaroshxona, klinika)",
        "required_config_fields": ["welcome_text", "services", "available_slots"],
    },
}


def get_allowed_templates_for_plan(allowed_categories: list[str]) -> dict:
    return {k: v for k, v in TEMPLATES.items() if k in allowed_categories}
