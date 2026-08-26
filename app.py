import os
import json
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__, template_folder=".")
CORS(app)

# Gemini API sozlamasi
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config={"response_mime_type": "application/json"}
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agent-build', methods=['POST'])
def agent_build():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'error': 'Prompt kiritilmadi'}), 400

        system_prompt = f"""
        Siz professional Web va Telegram Mini App dasturchisisiz.
        Foydalanuvchi so'rovi: "{prompt}"

        Ushbu so'rov bo'yicha to'liq ishlaydigan HTML/CSS/JS loyihasini yarating.
        Natijani FAQAT valid JSON formatida qaytaring:
        {{
            "files": [
                {{
                    "name": "index.html",
                    "content": "To'liq HTML kodi bu yerda"
                }}
            ]
        }}
        """

        response = model.generate_content(system_prompt)
        text_response = response.text.strip()

        # Markdown belgilari o'chirib tashlanadi
        if text_response.startswith("```"):
            text_response = re.sub(r"^```[a-z]*\n?", "", text_response)
            text_response = re.sub(r"\n?```$", "", text_response)

        # JSON escape xatoliklarini avtomatik to'g'rilash
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
