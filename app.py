import os
import io
import sys
import threading
import contextlib
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)

# AI Modelini sozlash
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Botlarni orqa fonda yuritish uchun lug'at
running_bots = {}

@app.route('/')
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Pro AI IDE Server Active!</h1>"

@app.route('/generate-bot', methods=['POST'])
def generate_bot():
    data = request.get_json()
    prompt = data.get('prompt', '')
    token = data.get('token', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "Serverda GEMINI_API_KEY sozlanmagan!"}), 400

    system_instruction = f"""
    Siz professional Python Telegram Bot dasturchisisiz. 
    Foydalanuvchi so'ragan botni `pyTelegramBotAPI` (telebot) kutubxonasidan foydalanib yozing.
    Bot Tokeni: '{token}' bo'lsin.
    Faqatgina toza Python kodini qaytaring. Kod ichida tushuntirishlar yozmang, faqat kod bo'lsin.
    Kodingiz oxirida albatta `bot.infinity_polling()` bo'lsin.
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{system_instruction}\n\nFoydalanuvchi talabi: {prompt}")
        
        generated_code = response.text.replace("```python", "").replace("```", "").strip()
        
        return jsonify({
            "code": generated_code,
            "filename": "main.py"
        })
    except Exception as e:
        return jsonify({"error": f"AI Xatoligi: {str(e)}"}), 500

def execute_code_in_background(code):
    try:
        exec_globals = {}
        exec(code, exec_globals)
    except Exception as e:
        print(f"Bot background error: {e}")

@app.route('/run-python', methods=['POST'])
def run_python():
    data = request.get_json()
    code = data.get('code', '')

    try:
        # Botni orqa fonda (Thread) ishga tushiramiz, shunda HTTP timeout bo'lmaydi
        bot_thread = threading.Thread(target=execute_code_in_background, args=(code,), daemon=True)
        bot_thread.start()

        return jsonify({
            "output": "🚀 Bot orqa fonda 24/7 rejimda muvaffaqiyatli ishga tushirildi!",
            "error": None
        })
    except Exception as e:
        return jsonify({
            "output": "",
            "error": f"Ishga tushirishda xatolik: {str(e)}"
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
