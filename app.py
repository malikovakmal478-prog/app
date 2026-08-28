import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Gemini API ni sozlash
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Ishlayotgan bot jarayonlarini saqlash uchun
running_bots = {}

# Taqiqlangan mavzularni tekshirish uchun filtr
FORBIDDEN_KEYWORDS = [
    "porn", "sex", "nsfw", "betting", "casino", "gambling", 
    "scam", "hack", "malware", "suicide", "porno", "qimor", 
    "seks", "aldash", "feyk"
]

def is_content_safe(prompt_text):
    text_lower = prompt_text.lower()
    for word in FORBIDDEN_KEYWORDS:
        if word in text_lower:
            return False
    return True

@app.route('/')
def home():
    return "VELTRIX Backend Server ishlayapti! 🚀"

@app.route('/api/generate-bot', methods=['POST'])
def generate_bot():
    data = request.json
    bot_token = data.get('token')
    user_prompt = data.get('prompt')
    
    if not bot_token or not user_prompt:
        return jsonify({"error": "Token va bot talabi kiritilishi shart!"}), 400

    if not is_content_safe(user_prompt):
        return jsonify({"error": "Kechirasiz, bu turdagi (uyatsiz, buzg'unchi yoki noqonuniy) botlarni yaratish taqiqlangan!"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "Serverda GEMINI_API_KEY sozlanmagan!"}), 500

    try:
        generation_prompt = f"""
        Siz professional Telegram bot yaratuvchisiz. aiogram v3 kutubxonasidan foydalanib to'liq ishlaydigan Python kodi yozing.
        Foydalanuvchi talabi: {user_prompt}
        Bot tokeni: {bot_token}
        
        Talablar:
        1. Faqat ishga tushishga tayyor, to'liq va xatosiz Python kodini qaytaring.
        2. Kodni ```python ... ``` bloklari ichiga yozing.
        3. Agar foydalanuvchi Telegram Mini App so'ragan bo'lsa, WebAppInfo va mos inline tugmalarni qo'shing.
        4. Agar oddiy tugmali (Inline/Reply) so'ragan bo'lsa, mos tugmalarni yarating.
        5. Kod oxirida botni ishga tushirish uchun asyncio.run(dp.start_polling(bot)) yoki shunga o'xshash aiogram v3 ishga tushirish qismi bo'lsin. Tokenni kodga to'g'ridan-to'g'ri matn ko'rinishida yozing.
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

        # Eski jarayon ishlayotgan bo'lsa, uni to'xtatish
        if bot_token in running_bots:
            try:
                running_bots[bot_token]["process"].terminate()
            except Exception:
                pass

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
        bot_filename = f"custom_bot_{abs(hash(bot_token))}.py"
        with open(bot_filename, "w", encoding="utf-8") as f:
            f.write(custom_code)

        if bot_token in running_bots:
            try:
                running_bots[bot_token]["process"].terminate()
            except Exception:
                pass

        process = subprocess.Popen(["python", bot_filename])
        running_bots[bot_token] = {"process": process, "file": bot_filename}

        return jsonify({"success": True, "message": "Sizning kodingiz asosida bot ishga tushirildi!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
