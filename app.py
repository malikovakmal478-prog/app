import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)

# CORS sozlamasini barcha manbalar va metodlar uchun to'liq ochish
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": "*"}})

# Gemini API Klienti
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Server ishlamoqda"}), 200

@app.route('/agent-build', methods=['POST', 'OPTIONS'])
def agent_build():
    if request.method == 'OPTIONS':
        return jsonify({"status": "OK"}), 200

    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'error': 'Prompt kiritilmadi'}), 400

        system_prompt = f"""
        Siz professional Telegram Mini App va Web dasturchisisiz.
        Foydalanuvchi talabi: "{prompt}"

        MUHIM KO'RSATMALAR:
        1. Standart "Salom Mini Ilova" degan qisqa shablon BERMANG.
        2. Foydalanuvchi so'rovi bo'yicha to'liq, interaktiv va vizual boy loyiha yarating (TailwindCSS va Telegram WebApp SDK ishlatilsin).

        Natijani FAQAT valid JSON formatida qaytaring:
        {{
            "files": [
                {{
                    "name": "index.html",
                    "content": "...to'liq HTML va JS kodi bu yerda..."
                }}
            ]
        }}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        text_response = response.text.strip()

        if text_response.startswith("```"):
            text_response = re.sub(r"^```[a-z]*\n?", "", text_response)
            text_response = re.sub(r"\n?```$", "", text_response)

        try:
            result_json = json.loads(text_response)
        except json.JSONDecodeError:
            cleaned_text = text_response.replace('\\', '\\\\')
            result_json = json.loads(cleaned_text)

        return jsonify(result_json)

    except Exception as e:
        return jsonify({'error': f"AI Avto-generatsiya xatosi: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
