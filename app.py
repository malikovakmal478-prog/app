import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# Gemini API kalitini sozlash (Render muhitidagi GEMINI_API_KEY olinadi)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Xotira va statistika uchun bazaviy o'zgaruvchilar
chat_histories = {}
user_stats = {"total_requests": 0, "active_users": set(), "created_apps": 0}

@app.route('/')
def home():
    return "VELTRIX AI Server is running live! 🚀", 200

@app.route('/deploy-bot', methods=['POST'])
def deploy_bot():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        user_email = data.get('email', 'guest@veltrix.ai')
        
        if not prompt:
            return jsonify({"status": "error", "error": "Buyruq kiritilmadi!"}), 400

        # Statistikani yangilash
        user_stats["total_requests"] += 1
        user_stats["active_users"].add(user_email)
        user_stats["created_apps"] += 1

        # Gemini AI orqali kuchli javob yaratish (18+ kontentni cheklash uchun system instruction)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Siz VELTRIX AI professional dasturchisiz. Foydalanuvchiga Telegram bot yoki Mini App yaratishda yordam berasiz. Har qanday 18+, zo'ravonlik yoki taqiqlangan kontentni qat'iy rad etasiz va xavfsiz javob qaytarasiz.",
                temperature=0.7
            )
        )

        app_url = f"https://veltrix.ai/preview/{user_stats['created_apps']}"

        return jsonify({
            "status": "success",
            "message": f"VELTRIX AI muvaffaqiyatli yaratdi! Javob: {response.text[:150]}...",
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
