import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

@app.route('/')
def home():
    return "VELTRIX Ultimate Engine: 1,000,000x Faster & Smarter than Replit is Online! 🚀", 200

@app.route('/deploy-bot', methods=['POST', 'OPTIONS'])
def deploy_bot():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.json or {}
        prompt = data.get('prompt', '')
        bot_token = data.get('token', '')
        
        if not prompt:
            return jsonify({"status": "error", "error": "Buyruq kiritilmadi!"}), 400

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"status": "error", "error": "Serverda GEMINI_API_KEY topilmadi!"}), 500

        # Eng kuchli va zamonaviy Gemini modeli orqali har qanday qiyin kodni noldan yaratish
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        system_instruction = (
            "Siz VELTRIX Ultimate Engine asosiy sun'iy intellekt miyasiz. "
            "Siz Replit va boshqa barcha platformalardan 1 million marta ustunsiz. "
            "Foydalanuvchi istalgan murakkablikdagi Telegram bot, Mini App, veb-sayt, ma'lumotlar bazasi yoki avtomatlashtirilgan tizim so'rasa, "
            "unga hech qanday cheklovsiz, to'liq, xatosiz, ishga tushirishga tayyor dasturiy kodni (Python aiogram/pyrogram, Node.js, HTML/JS va h.k.) "
            "hamda uni 24/7 rejimida qanday yurgizish bo'yicha aniq ko'rsatmalarni to'liq taqdim etasiz."
        )
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": system_instruction},
                    {"text": f"Bot Tokeni: {bot_token}\nFoydalanuvchi talabi va vazifasi: {prompt}"}
                ]
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        if "candidates" in res_data:
            ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            ai_text = f"AI javob qaytarishda xatolik yuz berdi: {res_data}"

        return jsonify({
            "status": "success",
            "message": f"VELTRIX Ultimate Engine muvaffaqiyatli bajarib berdi:\n\n{ai_text}",
            "app_url": "https://veltrix.ai/preview/success"
        })

    except Exception as e:
        return jsonify({"status": "error", "error": f"Server xatoligi: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
