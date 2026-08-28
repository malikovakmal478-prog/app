import os
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
# CORS orqali barcha manbalardan keladigan so'rovlarga ruxsat berish
CORS(app, resources={r"/*": {"origins": "*"}})

# Gemini API kalitini sozlash (Render muhit o'zgaruvchisidan olinadi)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Ishlayotgan bot jarayonlarini saqlash uchun lug'at (PID lar)
active_bots = {}


@app.route("/deploy-bot", methods=["POST", "OPTIONS"])
def deploy_bot():
  # CORS preflight so'rovlari uchun
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

  # Xavfsizlik va axloqiy qoidalar uchun qattiq cheklovlar
  safety_system_instruction = """
    Sen professional va xavfsiz Telegram bot dasturchisan. 
    MUHIM QOIDALAR:
    1. Faqat 'telebot' yoki 'aiogram' kutubxonasi yordamida to'liq ishlaydigan Python kod yoz.
    2. Bot tokenini kodga quyidagicha kirit: TOKEN = '<BOT_TOKEN>'
    3. Agar foydalanuvchi talabi uyatsiz, zo'ravonlikni targ'ib qiluvchi, firibgarlik, noqonuniy harakatlar yoki 18+ kontent bilan bog'liq bo'lsa, uni BAJARMA va faqat quyidagi JSON formatda xato qaytar: {"error": "Taqiqlangan kontent!"}
    4. Faqat toza Python kodining o'zini qaytar (markdown formatlash belgilarisiz, ```python ... ``` ishlatmasdan).
    """

  full_prompt = (
      f"{safety_system_instruction}\n\nFoydalanuvchi talabi: {user_prompt}\nBot"
      f" tokeni: {bot_token}"
  )

  try:
    # Gemini modelini chaqirish
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(full_prompt)
    bot_code = response.text.strip()

    # Agar taqiqlangan kontent aniqlansa
    if "Taqiqlangan kontent!" in bot_code or len(bot_code) < 20:
      return (
          jsonify({
              "error": (
                  "Kechirasiz, bu talab xavfsizlik qoidalariga zid yoki"
                  " uyatsiz/taqiqlangan bot yaratishga urinish deb topildi."
              )
          }),
          400,
      )

    # Kodni tozalash (markdown belgilaridan xoli qilish)
    if bot_code.startswith("```python"):
      bot_code = bot_code[9:]
    if bot_code.startswith("```"):
      bot_code = bot_code[3:]
    if bot_code.endswith("```"):
      bot_code = bot_code[:-3]

    # Har bir bot uchun unikal fayl nomi yaratish
    bot_id = abs(hash(bot_token))
    file_name = f"bot_{bot_id}.py"

    with open(file_name, "w", encoding="utf-8") as f:
      f.write(bot_code)

    # Avval shu tokenga tegishli eski bot ishlayotgan bo'lsa, uni to'xtatish
    if bot_token in active_bots:
      try:
        old_process = active_bots[bot_token]
        old_process.terminate()
      except Exception:
        pass

    # Subprocess yordamida fonda ishga tushirish
    process = subprocess.Popen(
        ["python", file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    active_bots[bot_token] = process

    return jsonify({
        "status": "success",
        "message": "VELTRIX botingiz muvaffaqiyatli yaratildi va ishga tushdi!",
        "pid": process.pid,
    })

  except Exception as e:
    return jsonify({"error": f"Xatolik yuz berdi: {str(e)}"}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
