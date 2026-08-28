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
    return "VELTRIX Ultimate Engine Server is live and running! 🚀", 200

@app.route('/deploy-bot', methods=['POST', 'OPTIONS'])
def deploy_bot():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.json or {}
        prompt = data.get('prompt', '')
        user_email = data.get('email', 'guest@veltrix.ai')
        bot_token = data.get('token', '')
        
        if not prompt:
            return jsonify({"status": "error", "error": "Buyruq kiritilmadi!"}), 400

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"status": "error", "error": "GEMINI_API_KEY topilmadi!"}), 500

        # Bir nechta modellarni navbat bilan sinash (biri ishlamasa boshqasiga o'tadi)
        models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        ai_text = None
        last_error = None

        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        "Siz VELTRIX AI platformasisiz. "
                        "Foydalanuvchiga Telegram bot yoki veb-sayt yaratishda mukammal kod bering. "
                        f"Buyruq: {prompt}"
                    )
                }]
            }]
        }
        headers = {'Content-Type': 'application/json'}

        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                response = requests.post(url, json=payload, headers=headers, timeout=45)
                res_data = response.json()
                
                if "candidates" in res_data:
                    ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    break
                else:
                    last_error = str(res_data)
            except Exception as sub_err:
                last_error = str(sub_err)
                continue

        if not ai_text:
            ai_text = f"Barcha modellar sinaldi, lekin javob olinmadi. Xato: {last_error}"

        return jsonify({
            "status": "success",
            "message": f"VELTRIX muvaffaqiyatli yaratdi!\n\nAI Javobi:\n{ai_text}",
            "app_url": "https://veltrix.ai/preview/1"
        })

    except Exception as e:
        return jsonify({"status": "error", "error": f"Kritik xatolik: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
