import os
import subprocess
import sqlite3
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

active_bots = {}

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

def init_db():
    try:
        conn = sqlite3.connect('veltrix_ultimate.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            token TEXT,
                            prompt TEXT,
                            status TEXT
                        )''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

@app.route('/', methods=['GET'])
def home():
    return "VELTRIX Ultimate Bot Engine is 100% Online! 🚀", 200

@app.route('/deploy-bot', methods=['OPTIONS'])
def deploy_bot_options():
    return jsonify({}), 200

@app.route('/deploy-bot', methods=['POST'])
def deploy_bot():
    try:
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt', '')
        bot_token = data.get('token', '')
        
        if not prompt or not bot_token:
            return jsonify({"status": "error", "error": "Bot tokeni yoki talab kiritilmadi!"}), 400

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"status": "error", "error": "Serverda GEMINI_API_KEY topilmadi!"}), 500

        # Ishlaydigan Gemini modeli
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        system_instruction = (
            "Siz professional dasturchisiz. Foydalanuvchi bergan token va talab asosida "
            "faqatgina ishga tushirishga tayyor, bitta faylga sig'adigan to'liq Python (telebot yoki aiogram) kodini yozib berasiz. "
            "Javobda faqat Python kodini ```python va ``` teglari orasiga yozing, ortiqcha gap yozmang."
        )
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": system_instruction},
                    {"text": f"Bot Tokeni: {bot_token}\nTalab: {prompt}"}
                ]
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        if "candidates" in res_data:
            ai_raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            
            if "```python" in ai_raw_text:
                bot_code = ai_raw_text.split("```python")[1].split("```")[0].strip()
            elif "```" in ai_raw_text:
                bot_code = ai_raw_text.split("```")[1].split("```")[0].strip()
            else:
                bot_code = ai_raw_text
                
            if bot_token not in bot_code:
                bot_code = f"TOKEN = '{bot_token}'\n" + bot_code

            bot_file_name = f"bot_{bot_token[:10]}.py"
            with open(bot_file_name, "w", encoding="utf-8") as f:
                f.write(bot_code)

            if bot_token in active_bots:
                try:
                    active_bots[bot_token].terminate()
                except:
                    pass

            # Botni fonda 24/7 rejimida ishga tushirish
            process = subprocess.Popen(["python", bot_file_name])
            active_bots[bot_token] = process

            return jsonify({
                "status": "success",
                "message": "Bot muvaffaqiyatli yaratildi va serverda 24/7 rejimida ishga tushirildi! 🚀",
                "code": bot_code
            })
        else:
            return jsonify({"status": "error", "error": f"AI xatolik qaytardi: {res_data}"}), 500

    except Exception as e:
        return jsonify({"status": "error", "error": f"Server xatoligi: {str(e)}"}), 500

@app.route('/system/stats', methods=['GET'])
def system_stats():
    return jsonify({
        "status": "Active",
        "running_bots_count": len(active_bots)
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
