import os
import json
import sqlite3
import subprocess
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
    project_name = data.get('name', 'my_app')

    # Replit Agent avtomatik yaratadigan to'liq Full-Stack Mini App strukturasi
    default_files = [
        {
            "name": "index.html",
            "content": """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Mini App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="style.css">
</head>
<body class="bg-black text-white pb-16">
    <header class="flex justify-between items-center px-4 py-3 border-b border-gray-800 sticky top-0 bg-black z-50">
        <h1 class="text-xl font-bold italic tracking-wide">Instagram</h1>
        <div class="flex space-x-4">
            <span>❤️</span>
            <span>💬</span>
        </div>
    </header>

    <div class="flex space-x-4 p-3 overflow-x-auto border-b border-gray-800">
        <div class="flex flex-col items-center">
            <div class="w-14 h-14 rounded-full border-2 border-pink-500 p-0.5">
                <img src="https://picsum.photos/100/100?random=1" class="w-full h-full rounded-full">
            </div>
            <span class="text-xs mt-1">Siz</span>
        </div>
        <div class="flex flex-col items-center">
            <div class="w-14 h-14 rounded-full border-2 border-pink-500 p-0.5">
                <img src="https://picsum.photos/100/100?random=2" class="w-full h-full rounded-full">
            </div>
            <span class="text-xs mt-1">user_1</span>
        </div>
    </div>

    <main class="p-4">
        <div class="border border-gray-800 rounded-lg overflow-hidden mb-4">
            <div class="p-3 font-semibold text-sm">user_1</div>
            <img src="https://picsum.photos/500/300?random=3" class="w-full">
            <div class="p-3 text-sm">
                <p><b>user_1</b> Replit IDE orqali ishga tushirildi! 🚀</p>
            </div>
        </div>
    </main>

    <script src="script.js"></script>
</body>
</html>"""
        },
        {
            "name": "style.css",
            "content": """/* Replit Custom Styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}"""
        },
        {
            "name": "script.js",
            "content": """// Telegram WebApp Init
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}
console.log("Replit Workspace App Loaded!");"""
        }
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO projects (name, files_json) VALUES (?, ?)", 
                   (project_name, json.dumps(default_files)))
    conn.commit()
    conn.close()

    return jsonify({"files": default_files})

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
