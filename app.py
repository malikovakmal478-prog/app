import os
import json
import re
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types
import telebot

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": "*"}})

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
                bot.reply_to(message, "Salom! Mini App-dan foydalanish uchun quyidagi tugmani bosing:", reply_markup=keyboard)
            else:
                keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add("ℹ️ Biz haqimizda", "📞 Bog'lanish")
                keyboard.add("🛍️ Xizmatlar / Mahsulotlar")
                bot.reply_to(message, "Salom! AI tomonidan yaratilgan botga xush kelibsiz!", reply_markup=keyboard)

        @bot.message_handler(func=lambda message: True)
        def echo_all(message):
            if message.text == "ℹ️ Biz haqimizda":
                bot.reply_to(message, "Bu AI Bot Constructor platformasi orqali yaratilgan bot.")
            elif message.text == "📞 Bog'lanish":
                bot.reply_to(message, "Administrator bilan bog'lanish uchun xabar qoldiring.")
            else:
                bot.reply_to(message, f"Siz yozdingiz: {message.text}")

        ACTIVE_BOTS[token] = bot
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Bot xatosi: {e}")

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "AI Platform Engine ishlamoqda"}), 200

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

        Agar so'rov Mini App bo'lsa, HTML va Telegram WebApp SDK kodini yarating.
        Natijani FAQAT valid JSON formatida qaytaring:
        {{
            "type": "miniapp",
            "files": [
                {{
                    "name": "index.html",
                    "content": "...HTML kodi..."
                }}
            ]
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

        # Botni fonda yurgazish
        bot_thread = threading.Thread(target=start_telegram_bot, args=(token, bot_type, "[https://malikovakmal478-prog.github.io/mini-replit/](https://malikovakmal478-prog.github.io/mini-replit/)"))
        bot_thread.daemon = True
        bot_thread.start()

        return jsonify({
            "status": "success",
            "message": "Bot yaratildi va ishga tushirildi!"
        })

    except Exception as e:
        return jsonify({'error': f"Tizim xatosi: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
