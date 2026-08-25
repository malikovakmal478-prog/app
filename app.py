import os
import sys
import io
import contextlib
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)

@app.route('/')
def index():
    # GitHub Pages yoki Render orqali index.html faylini ko'rsatish
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Mini Replit Server Active!</h1>"

@app.route('/run-python', methods=['POST'])
def run_python():
    data = request.get_json()
    code = data.get('code', '')

    # Python kod natijasini va xatolarini ushlab olish
    output_buffer = io.StringIO()
    error_message = None

    try:
        with contextlib.redirect_stdout(output_buffer):
            # Kodni bajarish
            exec_globals = {}
            exec(code, exec_globals)
        result = output_buffer.getvalue()
    except Exception as e:
        result = output_buffer.getvalue()
        error_message = f"{type(e).__name__}: {str(e)}"

    return jsonify({
        "output": result,
        "error": error_message
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
