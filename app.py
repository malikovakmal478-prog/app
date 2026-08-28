import os
import subprocess
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Gemini API ni sozlash (Render muhit o'zgaruvchisidan olinadi)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Ishlayotgan bot jarayonlarini saqlash uchun lug'at
running_bots = {}

# Taqiqlangan mavzularni tekshirish uchun oddiy filtr
FORBIDDEN_KEYWORDS = ["porn", "sex", "nsfw", "betting", "casino", "gambling", "scam", "hack", "malware", "suicide"]

def is_content_safe(prompt_text):
    text_lower = prompt_text.lower()
    for word in FORBIDDEN_KEYWORDS:
        if word in text_lower:
            return False
    return True

@app.route('/api/generate-bot', methods=['POST'])
def generate_bot():
    data = request.json
    bot_token = data.get('token')
    user_prompt = data.get('prompt')
    
    if not bot_token or not user_prompt:
        return jsonify({"error": "Token va bot talabi kiritilishi shart!"}), 400

    # Xavfsizlik tekshiruvi
    if not is_content_safe(user_prompt):
        return jsonify({"error": "Kechirasiz, bu turdagi (uyatsiz, buzg'unchi yoki noqonuniy) botlarni yaratish taqiqlangan!"}), 400

    try:
        # Gemini orqali Python bot kodini generatsiya qilish
        generation_prompt = f"""
        Siz professional Telegram bot yaratuvchisiz (aiogram v3 kutubxonasidan foydalaning).
        Foydalanuvchi talabi: {user_prompt}
        Bot tokeni: {bot_token}
        
        Talablar:
        1. Faqat ishga tushishga tayyor, to'liq Python kodini qaytaring.
        2. Kodni ```python ... ``` bloklari ichiga yozing.
        3. Agar foydalanuvchi Telegram Mini App so'ragan bo'lsa, WebAppInfo tugmalarini qo'shing.
        4. Agar oddiy tugmali (Inline/Reply) so'ragan bo'lsa, mos tugmalarni yarating.
        5. Kod hech qanday qo'shimcha tushuntirishlarsiz, faqat Python kodi bo'lsin.
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(generation_prompt)
        raw_code = response.text

        # Markdown bloklaridan kodni ajratib olish
        if "```python" in raw_code:
            code = raw_code.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_code:
            code = raw_code.split("```")[1].split("```")[0].strip()
        else:
            code = raw_code.strip()

        # Bot uchun alohida fayl yaratish
        bot_filename = f"bot_{abs(hash(bot_token))}.py"
        with open(bot_filename, "w", encoding="utf-8") as f:
            f.write(code)

        # Botni fonda subprocess orqali ishga tushirish
        process = subprocess.Popen(["python", bot_filename])
        running_bots[bot_token] = {"process": process, "file": bot_filename}

        return jsonify({"success": True, "message": "Bot muvaffaqiyatli yaratildi va 24/7 rejimida ishga tushirildi!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/run-custom-code', methods=['POST'])
def run_custom_code():
    data = request.json
    bot_token = data.get('token')
    custom_code = data.get('code')
    
    if not bot_token or not custom_code:
        return jsonify({"error": "Token va kod kiritilishi shart!"}), 400

    try:
        # Foydalanuvchi o'zi yozgan kodni saqlash va ishga tushirish
        bot_filename = f"custom_bot_{abs(hash(bot_token))}.py"
        with open(bot_filename, "w", encoding="utf-8") as f:
            f.write(custom_code)

        process = subprocess.Popen(["python", bot_filename])
        running_bots[bot_token] = {"process": process, "file": bot_filename}

        return jsonify({"success": True, "message": "Sizning kodingiz bo'yicha bot ishga tushirildi!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
