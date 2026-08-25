import os
import json
import sqlite3
import subprocess
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

DB_PATH = "replit_projects.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            files_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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
    project_name = data.get('name', 'default_project')
    
    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY sozlanmagan!"}), 400

    system_prompt = f"""
    Siz Replit Agent-siz. Telegram Mini App uchun to'liq HTML, CSS, JS kodlarini tayyorlang.
    Loyiha nomi: {project_name}

    FAQAT quyidagi JSON formatida javob bering (hech qanday ortiqcha matnsiz):
    {{
      "files": [
        {{"name": "index.html", "content": "..."}},
        {{"name": "style.css", "content": "..."}},
        {{"name": "script.js", "content": "..."}}
      ]
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{system_prompt}\n\nTalab: {prompt}")
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        result = json.loads(raw_text)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO projects (name, files_json) VALUES (?, ?)", 
                       (project_name, json.dumps(result.get('files', []))))
        conn.commit()
        conn.close()

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Agent Xatosi: {str(e)}"}), 500

@app.route('/auto-fix', methods=['POST'])
def auto_fix():
    data = request.get_json() or {}
    error_msg = data.get('error', '')
    current_code = data.get('code', '')

    if not GEMINI_API_KEY:
        return jsonify({"error": "API Key yo'q!"}), 400

    prompt = f"Ushbu koddagi xatolikni avtomatik tuzat va FAQAT to'g'rilangan kodni qaytar:\n\nXato: {error_msg}\n\nKod:\n{current_code}"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        res = model.generate_content(prompt)
        fixed_code = res.text.replace("```javascript", "").replace("```python", "").replace("```html", "").replace("```", "").strip()
        return jsonify({"fixed_code": fixed_code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/run-terminal', methods=['POST'])
def run_terminal():
    data = request.get_json() or {}
    command = data.get('command', '')
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
        return jsonify({"output": output.decode('utf-8')})
    except subprocess.CalledProcessError as e:
        return jsonify({"output": e.output.decode('utf-8')})
    except Exception as e:
        return jsonify({"output": f"Terminal Xato: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
