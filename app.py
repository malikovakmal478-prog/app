import os
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
  genai.configure(api_key=api_key)

active_bots = {}


@app.route("/api/generate-bot", methods=["POST", "OPTIONS"])
def generate_bot():
  if request.method == "OPTIONS":
    return jsonify({"status": "ok"}), 200

  data = request.json
  if not data:
    return jsonify({"error": "Ma'lumot topilmadi!"}), 400

  bot_token = data.get("token")
  user_prompt = data.get("prompt")

  if not bot_token or not user_prompt:
    return (
        jsonify({"error": "Telegram bot tokeni va talab kiritilishi shart!"}),
        400,
    )

  safety_system_instruction = """
    Sen professional Telegram bot dasturchisan. 
    Faqat 'telebot' yoki 'aiogram' kutubxonasi yordamida ishlaydigan Python kod yoz.
    Bot tokenini kodga quyidagicha kirit: TOKEN = '<BOT_TOKEN>'
    Faqat toza Python kodining o'zini qaytar (markdown formatlash belgilarisiz, ```python ... ``` ishlatmasdan).
    """

  generation_prompt = (
      f"{safety_system_instruction}\n\nTalab: {user_prompt}\nToken:"
      f" {bot_token}"
  )

  try:
    # Eski va barqaror ishlaydigan 'gemini-pro' modeliga o'tkazamiz
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(generation_prompt)
    bot_code = response.text.strip()

    if bot_code.startswith("```python"):
      bot_code = bot_code[9:]
    if bot_code.startswith("```"):
      bot_code = bot_code[3:]
    if bot_code.endswith("```"):
      bot_code = bot_code[:-3]

    bot_id = abs(hash(bot_token))
    file_name = f"bot_{bot_id}.py"

    with open(file_name, "w", encoding="utf-8") as f:
      f.write(bot_code)

    if bot_token in active_bots:
      try:
        active_bots[bot_token].terminate()
      except Exception:
        pass

    process = subprocess.Popen(
        ["python", file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    active_bots[bot_token] = process

    return jsonify({
        "status": "success",
        "message": "Bot muvaffaqiyatli yaratildi va ishga tushirildi!",
        "pid": process.pid,
    })

  except Exception as e:
    print("XATOLIK:", str(e))  # Render loglarida ko'rinishi uchun
    return jsonify({"error": f"AI xatoligi: {str(e)}"}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
