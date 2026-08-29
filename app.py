import os
import subprocess
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
  genai.configure(api_key=api_key)

active_bots = {}


@app.route("/", methods=["GET"])
def home():
  return jsonify({"status": "VELTRIX Backend 24/7 is active!"})


@app.route("/api/run-custom-code", methods=["POST", "OPTIONS"])
def run_custom_code():
  if request.method == "OPTIONS":
    return jsonify({"status": "ok"}), 200

  data = request.json or {}
  bot_token = data.get("token")
  custom_code = data.get("code")

  if not bot_token or not custom_code:
    return jsonify({"error": "Token va python kod kiritilishi shart!"}), 400

  try:
    bot_id = abs(hash(bot_token))
    file_name = f"bot_{bot_id}.py"

    with open(file_name, "w", encoding="utf-8") as f:
      f.write(custom_code)

    if bot_token in active_bots:
      try:
        active_bots[bot_token].terminate()
      except Exception:
        pass

    # Xatoliklarni ushlash uchun log fayliga yo'naltiramiz
    log_file = open(f"log_{bot_id}.txt", "w")
    process = subprocess.Popen(
        [sys.executable, file_name],
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    active_bots[bot_token] = process

    return jsonify({
        "status": "success",
        "message": "Bot muvaffaqiyatli ishga tushirildi!",
        "pid": process.pid,
    })
  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
