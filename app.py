import os
import io
import json
import threading
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Ma'lumotlar bazasi va kalitlar uchun simulyatsiya (KV Store & Secrets)
PROJECT_SECRETS = {}
PROJECT_DB = {}

@app.route('/')
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    return "<h1>index.html topilmadi!</h1>"

@app.route('/generate-all', methods=['POST'])
def generate_all():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    project_type = data.get('type', 'web')
    token = data.get('token', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "Serverda GEMINI_API_KEY sozlanmagan!"}), 400

    system_instruction = f"""
    Siz Replit Agent va AI Full-Stack Dasturchisisiz. Foydalanuvchi talabiga asosan professional loyiha yaratib bering.
    Loyiha turi: {project_type}. Token: '{token}'.
    
    JAVOBINGIZNI FAQAT QUYIDAGI JSON FORMATIDA QAYTARING, BOSHQA HECH NARSAYI YOZMANG:
    {{
      "files": [
        {{"name": "index.html", "content": "...html kodi..."}},
        {{"name": "style.css", "content": "...css kodi..."}},
        {{"name": "script.js", "content": "...js kodi..."}},
        {{"name": "main.py", "content": "...python kodi..."}}
      ],
      "logs": "Loyiha muvaffaqiyatli generatsiya qilindi va ishga tushirildi!"
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{system_instruction}\n\nFoydalanuvchi so'rovi: {prompt}")
        
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI Xatoligi: {str(e)}"}), 500

@app.route('/ai-assistant', methods=['POST'])
def ai_assistant():
    data = request.get_json() or {}
    task = data.get('task', 'explain') # explain, test, refactor, debug
    code = data.get('code', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY yo'q"}), 400

    prompts = {
        "explain": f"Ushbu kodni har bir satrini sodda o'zbek tilida tushuntirib ber:\n\n{code}",
        "test": f"Ushbu kod uchun to'liq Unit Test yozib ber:\n\n{code}",
        "refactor": f"Ushbu kodni optimallashtir va eng zamonaviy standartlarga o'tkaz:\n\n{code}",
        "debug": f"Ushbu koddagi xatolarni top va tuzatilgan varianti taqdim et:\n\n{code}"
    }

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompts.get(task, prompts['explain']))
        return jsonify({"result": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_bot_in_background(code):
    try:
        exec_globals = {}
        exec(code, exec_globals)
    except Exception as e:
        print(f"Background process error: {e}")

@app.route('/run-python', methods=['POST'])
def run_python():
    data = request.get_json() or {}
    code = data.get('code', '')
    try:
        thread = threading.Thread(target=run_bot_in_background, args=(code,), daemon=True)
        thread.start()
        return jsonify({"output": "🚀 Background Server & Bot 24/7 Always-On rejimida ishlamoqda!"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
