import os
import threading
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.route('/')
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    return "<h1>index.html topilmadi!</h1>"

@app.route('/generate-project', methods=['POST'])
def generate_project():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    project_type = data.get('type', 'web') # web, bot, python, fullstack
    token = data.get('token', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "Serverda GEMINI_API_KEY sozlanmagan!"}), 400

    system_instruction = f"""
    Siz dunyodagi eng kuchli AI Dasturchisisiz. Foydalanuvchi so'roviga asosan to'liq va professional loyiha yaratib bering.
    Loyiha turi: {project_type}.
    Telegram bot tokeni (agar bot bo'lsa): '{token}'.

    JAVOBINGIZNI FAQAT SHU JSON FORMATIDA QAYTARING, BOSHQA HECH NARSAYI YOZMANG:
    {{
      "files": [
        {{"name": "index.html", "content": "...html kodi..."}},
        {{"name": "style.css", "content": "...css kodi..."}},
        {{"name": "script.js", "content": "...js kodi..."}},
        {{"name": "main.py", "content": "...python kodi..."}}
      ],
      "logs": "Loyiha tayyorlandi va muvaffaqiyatli ishga tushirildi!"
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{system_instruction}\n\nFoydalanuvchi talabi: {prompt}")
        
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        import json
        result = json.loads(raw_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI Generation Error: {str(e)}"}), 500

def run_bot_in_background(code):
    try:
        exec_globals = {}
        exec(code, exec_globals)
    except Exception as e:
        print(f"Bot execution error: {e}")

@app.route('/run-python', methods=['POST'])
def run_python():
    data = request.get_json() or {}
    code = data.get('code', '')
    try:
        bot_thread = threading.Thread(target=run_bot_in_background, args=(code,), daemon=True)
        bot_thread.start()
        return jsonify({"output": "🚀 Python kodi/Bot orqa fonda 24/7 ishlamoqda!"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
