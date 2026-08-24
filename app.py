from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess, sys, uuid, os

app = Flask(__name__)
CORS(app)
processes = {}

@app.route('/run-bot', methods=['POST'])
def run_bot():
    data = request.json or {}
    code = data.get('code', '')
    if not code:
        return jsonify({'status': 'error', 'message': 'Kod yo\'q'}), 400

    bot_id = str(uuid.uuid4())[:8]
    filename = f"bot_{bot_id}.py"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    proc = subprocess.Popen([sys.executable, filename])
    processes[bot_id] = proc
    return jsonify({'status': 'success', 'message': f'Bot 24/7 ishga tushdi! ID: {bot_id}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
