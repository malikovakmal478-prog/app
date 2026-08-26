import os
import json
import re
import sqlite3
import threading
from flask import Flask, request, jsonify, send_from_html
from flask_cors import CORS
from google import genai
from google.genai import types
import telebot

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": "*"}})

# Gemini API
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Ma'lumotlar bazasini sozlash (SQLite)
DB_FILE = "platform_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            bot_token TEXT UNIQUE,
            bot_type TEXT,
            html_content TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

ACTIVE_BOTS = {}

def start_telegram_bot(token, bot_type, app_url=""):
    try:
        bot = telebot.TeleBot(token)

        @bot.message_handler(commands=['start'])
        def send_welcome(message):
            if bot_type == "miniapp":
                keyboard = telebot.types.InlineKeyboardMarkup()
                web_app = telebot.types.WebAppInfo(url=app_url)
                button = telebot.types.InlineKeyboardButton(text="📱 Mini App-ni ochish", web_app=web_app)
                keyboard.add(button)
                bot.reply_to(message, "Salom! Shaxsiy Mini App-ingizni ochish uchun quyidagi tugmani bosing:", reply_markup=keyboard)
            else:
                keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add("ℹ️ Biz haqimizda", "📞 Bog'lanish")
                keyboard.add("🛍️ Xizmatlar")
                bot.reply_to(message, "Salom! AI tomonidan yaratilgan botga xush kelibsiz!", reply_markup=keyboard)

        @bot.message_handler(func=lambda message: True)
        def echo_all(message):
            bot.reply_to(message, f"Siz yozdingiz: {message.text}")

        ACTIVE_BOTS[token] = bot
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Bot xatosi: {e}")

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Mukammal AI Platform Engine ishlamoqda"}), 200

# Dinamik Mini App sahifasini uzatish (Har bir bot uchun alohida)
@app.route('/app/<int:bot_id>', methods=['GET'])
def get_mini_app(bot_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT html_content FROM bots WHERE id = ?", (bot_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return row[0], 200, {'Content-Type': 'text/html; charset=utf-8'}
    return "Mini App topilmadi!", 404

@app.route('/deploy-bot', methods=['POST', 'OPTIONS'])
def deploy_bot():
    if request.method == 'OPTIONS':
        return jsonify({"status": "OK"}), 200

    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        prompt = data.get('prompt', '').strip()
        user_email = data.get('email', 'anonymous')

        if not token or not prompt:
            return jsonify({'error': 'Bot Token va Prompt kiritilishi shart!'}), 400

        system_prompt = f"""
        Siz Telegram Bot va Mini App bo'yicha mutaxassissiz.
        Foydalanuvchi so'rovi: "{prompt}"

        Agar so'rov Mini App bo'lsa, HTML (TailwindCSS va Telegram SDK bilan) kodini yarating.
        Natijani FAQAT valid JSON formatida qaytaring:
        {{
            "type": "miniapp",
            "html": "...to'liq HTML kodi..."
        }}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )

        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = re.sub(r"^```[a-z]*\n?", "", text_response)
            text_response = re.sub(r"\n?```$", "", text_response)

        result_json = json.loads(text_response)
        bot_type = result_json.get("type", "buttons")
        html_content = result_json.get("html", "")

        # Bazaga saqlash
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bots (user_email, bot_token, bot_type, html_content)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(bot_token) DO UPDATE SET bot_type=excluded.bot_type, html_content=excluded.html_content
        ''', (user_email, token, bot_type, html_content))
        
        bot_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Har bir bot uchun unikal Mini App havolasi shakllantiriladi
        server_domain = request.host_url.rstrip('/')
        mini_app_url = f"{server_domain}/app/{bot_id}"

        # Botni fonda ishga tushirish
        bot_thread = threading.Thread(
            target=start_telegram_bot, 
            args=(token, bot_type, mini_app_url)
        )
        bot_thread.daemon = True
        bot_thread.start()

        return jsonify({
            "status": "success",
            "message": "Bot yaratildi, bazaga saqlandi va ishga tushirildi!",
            "app_url": mini_app_url
        })

    except Exception as e:
        return jsonify({'error': f"Tizim xatosi: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
