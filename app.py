import os
import json
import sqlite3
import subprocess
import google.generativeai as genai
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Gemini API Key o'rnatiladi
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
    project_name = data.get('name', 'grender_app')

    if not prompt:
        return jsonify({"error": "Prompt kiritilmadi"}), 400

    system_prompt = f"""
    Siz professional Full-Stack Telegram Mini App yaratuvchi AI Agentsiz.
    Foydalanuvchi talabi: "{prompt}".

    Ushbu talab bo'yicha index.html, style.css va script.js fayllarini to'liq yozib bering.
    Faqatgina quyidagi JSON formatida javob qaytaring (hech qanday qo'shimcha matnsiz):
    {{
      "files": [
        {{"name": "index.html", "content": "...to'liq HTML kodi..."}},
        {{"name": "style.css", "content": "...to'liq CSS kodi..."}},
        {{"name": "script.js", "content": "...to'liq JS kodi..."}}
      ]
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            system_prompt,
            generation_config={"temperature": 0.2}
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.startswith("```"): raw_text = raw_text[3:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
        
        result = json.loads(raw_text.strip())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI Avto-generatsiya xatosi: {str(e)}"}), 500

@app.route('/run-terminal', methods=['POST'])
def run_terminal():
    data = request.get_json() or {}
    command = data.get('command', '')
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
        return jsonify({"output": output.decode('utf-8')})
    except Exception as e:
        return jsonify({"output": f"Error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
