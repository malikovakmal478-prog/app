import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

chat_histories = {}
user_stats = {"total_requests": 0, "active_users": set(), "created_apps": 0}

@app.route('/')
def home():
    return "VELTRIX Ultimate Engine Server is live and running! 🚀", 200

@app.route('/deploy-bot', methods=['POST'])
def deploy_bot():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        user_email = data.get('email', 'guest@veltrix.ai')
        bot_token = data.get('token', '')
        
        if not prompt:
            return jsonify({"status": "error", "error": "Buyruq kiritilmadi!"}), 400

        user_stats["total_requests"] += 1
        user_stats["active_users"].add(user_email)
        user_stats["created_apps"] += 1

        if user_email not in chat_histories:
            chat_histories[user_email] = []
        chat_histories[user_email].append({"prompt": prompt, "token": bot_token})

        api_key = os.environ.get("GEMINI_API_KEY")
        # Universal va o'zgarmas model manzili
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        "Siz dunyodagi eng kuchli AI platformasi — VELTRIX'ning asosiy miyasiz. "
                        "Foydalanuvchilarga istalgan Telegram bot, Mini App yoki veb-sayt yaratishda mukammal kod va ko'rsatmalar berasiz. "
                        "18+, zo'ravonlik yoki noqonuniy kontent so'ralsa mutlaqo rad etasiz. "
                        f"Buyruq: {prompt}"
                    )
                }]
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        res_data = response.json()
        
        if "candidates" in res_data:
            ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            ai_text = f"Javob olishda xatolik: {res_data}"

        app_url = f"https://veltrix.ai/preview/{user_stats['created_apps']}"

        return jsonify({
            "status": "success",
            "message": f"VELTRIX muvaffaqiyatli yaratdi va serverga ulab qo'ydi!\n\nAI Javobi:\n{ai_text}",
            "app_url": app_url
        })

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({
        "total_requests": user_stats["total_requests"],
        "active_users_count": len(user_stats["active_users"]),
        "created_apps": user_stats["created_apps"]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
