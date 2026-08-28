import os
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
# CORSni barcha yo'nalishlar va metodlar uchun to'liq ochish
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
  return jsonify({"status": "VELTRIX Backend is running 24/7!"})


# 1. AI orqali bot yaratish endpointi
@app.route("/api/generate-bot", methods=["POST", "OPTIONS"])
def generate_bot():
  if request.method == "OPTIONS":
    return jsonify({"status": "ok"}), 200

  data = request.json or {}
  bot_token = data.get("token")
  user_prompt = data.get("prompt")

  if not bot_token or not user_prompt:
    return jsonify({"error": "Token va talab kiritilishi shart!"}), 400

  try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        f"Professional aiogram v3 python kodi yoz. Token: {bot_token}. Talab:"
        f" {user_prompt}. Faqat python kod qaytar."
    )
    bot_code = response.text.strip()

    if bot_code.startswith("```python"):
      bot_code = bot_code[9:]
    if bot_code.startswith("```"):
      bot_code = bot_code[3:]
    if bot_code.endswith("```"):
      bot_code = bot_code[:-3]

    return run_bot_code(bot_token, bot_code)
  except Exception as e:
    return jsonify({"error": str(e)}), 500


# 2. Shaxsiy kodni qabul qilib 24/7 ishga tushirish endpointi
@app.route("/api/run-custom-code", methods=["POST", "OPTIONS"])
def run_custom_code():
  if request.method == "OPTIONS":
    return jsonify({"status": "ok"}), 200

  data = request.json or {}
  bot_token = data.get("token")
  custom_code = data.get("code")

  if not bot_token or not custom_code:
    return jsonify({"error": "Token va python kod kiritilishi shart!"}), 400

  return run_bot_code(bot_token, custom_code)


def run_bot_code(bot_token, code_text):
  try:
    bot_id = abs(hash(bot_token))
    file_name = f"bot_{bot_id}.py"

    with open(file_name, "w", encoding="utf-8") as f:
      f.write(code_text)

    # Agar shu tokenga oldin bot ochilgan bo'lsa, uni to'xtatish
    if bot_token in active_bots:
      try:
        active_bots[bot_token].terminate()
      except Exception:
        pass

    # 24/7 fonda ishga tushirish
    process = subprocess.Popen(
        ["python", file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    active_bots[bot_token] = process

    return jsonify({
        "status": "success",
        "message": "Bot muvaffaqiyatli 24/7 rejimida ishga tushdi!",
        "pid": process.pid,
    })
  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
