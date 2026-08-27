import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

chat_histories = {}
user_stats = {"total_requests": 0, "active_users": set(), "created_apps": 0}

@app.route('/')
def home():
    return "VELTRIX Super AI Server is live and running! 🚀", 200

@app.route('/deploy-bot', methods=['POST'])
def deploy_bot():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        user_email = data.get('email', 'guest@veltrix.ai')
        
        if not prompt:
            return jsonify({"status": "error", "error": "Buyruq kiritilmadi!"}), 400

        user_stats["total_requests"] += 1
        user_stats["active_users"].add(user_email)
        user_stats["created_apps"] += 1

        # 18+ va taqiqlangan kontentni qat'iy cheklaydigan hamda eng kuchli javob beruvchi tizim ko'rsatmasi
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Siz dunyodagi eng kuchli AI platformasi — VELTRIX'ning asosiy miyasiz. "
                    "Foydalanuvchilarga istalgan Telegram bot, Mini App yoki veb-sayt yaratishda mukammal kod va ko'rsatmalar berasiz. "
                    "Qat'iy qoida: Har qanday 18+ (kattalar uchun), zo'ravonlik, noqonuniy yoki zararli kontent so'ralsa, uni mutlaqo rad etasiz. "
                    "Javoblaringiz har doim aniq, professional va to'liq ishlaydigan bo'lsin."
                ),
                temperature=0.7
            )
        )

        app_url = f"https://veltrix.ai/preview/{user_stats['created_apps']}"

        return jsonify({
            "status": "success",
            "message": f"VELTRIX muvaffaqiyatli yaratdi va umrbod Serverga ulab qo'ydi!\n\nAI Javobi:\n{response.text}",
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
