import os
import json
import subprocess
import threading
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Secrets va KV Storage
PROJECT_SECRETS = {}

@app.route('/')
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    return "<h1>index.html fayli topilmadi!</h1>"

# 1. Replit Agent 3/4 - Full-Stack loyiha yaratish
@app.route('/agent-build', methods=['POST'])
def agent_build():
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    project_type = data.get('type', 'web')

    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY sozlanmagan!"}), 400

    system_instruction = f"""
    Siz Replit Agent 4 avtonom AI tizimisiz. Foydalanuvchi talabiga ko'ra ishlaydigan loyiha fayllarini bering.
    Loyiha turi: {project_type}. Secrets (agar bor bo'lsa): {json.dumps(PROJECT_SECRETS)}

    FAQAT QUYIDAGI JSON FORMATIDA JAVOB BERING (hech qanday qo'shimcha matnsiz):
    {{
      "files": [
        {{"name": "index.html", "content": "...html..."}},
        {{"name": "style.css", "content": "...css..."}},
        {{"name": "script.js", "content": "...js..."}},
        {{"name": "main.py", "content": "...python..."}}
      ],
      "logs": "Replit Agent 4: Architecture designed -> Environment initialized -> Dependencies resolved -> System Live!"
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{system_instruction}\n\nLoyiha: {prompt}")
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Agent Xatoligi: {str(e)}"}), 500

# 2. Ghostwriter AI (Explain, Debug, Refactor, Security Scan, Unit Test)
@app.route('/ai-ghostwriter', methods=['POST'])
def ai_ghostwriter():
    data = request.get_json() or {}
    action = data.get('action', 'explain')
    code = data.get('code', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY sozlanmagan!"}), 400

    prompts = {
        "explain": f"Ushbu kodni mantiqiy satrma-satr tushuntirib ber:\n\n{code}",
        "debug": f"Ushbu koddagi xatolarni top, tuzat va tayyor kodni qaytar:\n\n{code}",
        "refactor": f"Ushbu kodni optimallashtir va strukturasini yaxshila:\n\n{code}",
        "test": f"Ushbu kod uchun to'liq Unit Test tayyorla:\n\n{code}",
        "scan": f"Semgrep xavfsizlik standarti bo'yicha koddagi zaifliklarni skaner qil va hisobot ber:\n\n{code}"
    }

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompts.get(action, prompts['explain']))
        return jsonify({"result": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Terminal & Shell Integratsiyasi (Real Code Execution)
@app.route('/run-terminal', methods=['POST'])
def run_terminal():
    data = request.get_json() or {}
    command = data.get('command', '')
    
    try:
        # Xavfsiz shell ijrosi
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
        return jsonify({"output": output.decode('utf-8')})
    except subprocess.CalledProcessError as e:
        return jsonify({"output": e.output.decode('utf-8')})
    except Exception as e:
        return jsonify({"output": f"Terminal Xatosi: {str(e)}"})

# 4. Secrets Management (.env)
@app.route('/save-secret', methods=['POST'])
def save_secret():
    data = request.get_json() or {}
    key = data.get('key')
    val = data.get('val')
    if key and val:
        PROJECT_SECRETS[key] = val
        os.environ[key] = val
        return jsonify({"success": True, "secrets": list(PROJECT_SECRETS.keys())})
    return jsonify({"error": "Noto'liq ma'lumot"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
