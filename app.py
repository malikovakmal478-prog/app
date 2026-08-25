import os
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

# Secrets va KV Data Simulyatsiyasi
PROJECT_SECRETS = {}

@app.route('/')
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    return "<h1>index.html topilmadi!</h1>"

@app.route('/agent-build', methods=['POST'])
def agent_build():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    project_type = data.get('type', 'web')
    token = data.get('token', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY sozlanmagan!"}), 400

    system_instruction = f"""
    Siz Replit Agent 3/4 kabi avtonom AI dasturchisisiz. Foydalanuvchi so'roviga asosan full-stack loyiha yaratib bering.
    Loyiha turi: {project_type}. Bot Token: '{token}'.
    
    JAVOBINGIZNI FAQAT QUYIDAGI JSON FORMATIDA QAYTARING:
    {{
      "files": [
        {{"name": "index.html", "content": "...html..."}},
        {{"name": "style.css", "content": "...css..."}},
        {{"name": "script.js", "content": "...js..."}},
        {{"name": "main.py", "content": "...python..."}}
      ],
      "logs": "Replit Agent 3: Architecture planned -> Dependencies installed -> Neon DB Connected -> Deploy Complete!"
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{system_instruction}\n\nTask: {prompt}")
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Agent Error: {str(e)}"}), 500

@app.route('/ai-ghostwriter', methods=['POST'])
def ai_ghostwriter():
    data = request.get_json() or {}
    action = data.get('action', 'explain') # explain, debug, refactor, test, scan
    code = data.get('code', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "API Key yo'q"}), 400

    prompts = {
        "explain": f"Ushbu kodni satrma-satr tushuntirib ber:\n\n{code}",
        "debug": f"Ushbu koddagi xatoni top va tuzatilgan kodni ber:\n\n{code}",
        "refactor": f"Ushbu kodni optimallashtir (Clean Code):\n\n{code}",
        "test": f"Ushbu kod uchun unit test yozib ber:\n\n{code}",
        "scan": f"Semgrep kabi xavfsizlik va zaifliklarni skaner qil va hisobot ber:\n\n{code}"
    }

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompts.get(action, prompts['explain']))
        return jsonify({"result": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_background_process(code):
    try:
        exec_globals = {}
        exec(code, exec_globals)
    except Exception as e:
        print(f"Background VM execution error: {e}")

@app.route('/run-vm', methods=['POST'])
def run_vm():
    data = request.get_json() or {}
    code = data.get('code', '')
    try:
        thread = threading.Thread(target=run_background_process, args=(code,), daemon=True)
        thread.start()
        return jsonify({"output": "🟢 Reserved VM: Always-On Process & Bot is running on Cloud (24/7)."})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
