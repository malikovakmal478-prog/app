import os
import subprocess
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    return "<h1>index.html topilmadi!</h1>"

@app.route('/agent-build', methods=['POST'])
def agent_build():
    data = request.get_json() or {}
    name = data.get('name', 'my_app')
    
    # 100% barqaror, bir soniyada yuklanadigan Instagram Mini App shabloni
    template_code = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Mini App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="bg-black text-white pb-16">
    <div class="flex justify-between items-center px-4 py-3 border-b border-gray-800 sticky top-0 bg-black z-50">
        <h1 class="text-xl font-bold italic font-serif tracking-wide">Instagram</h1>
        <div class="flex space-x-5 text-xl">
            <i class="far fa-heart cursor-pointer"></i>
            <i class="fab fa-facebook-messenger cursor-pointer"></i>
        </div>
    </div>
    <div class="flex space-x-4 p-3 overflow-x-auto no-scrollbar border-b border-gray-800">
        <div class="flex flex-col items-center space-y-1 min-w-[65px]">
            <div class="w-16 h-16 rounded-full p-[2px] bg-gradient-to-tr from-yellow-500 to-fuchsia-600">
                <img src="https://picsum.photos/100/100?random=1" class="w-full h-full rounded-full border-2 border-black object-cover">
            </div>
            <span class="text-xs truncate w-14 text-center">Mening Story</span>
        </div>
        <div class="flex flex-col items-center space-y-1 min-w-[65px]">
            <div class="w-16 h-16 rounded-full p-[2px] bg-gradient-to-tr from-yellow-500 to-fuchsia-600">
                <img src="https://picsum.photos/100/100?random=2" class="w-full h-full rounded-full border-2 border-black object-cover">
            </div>
            <span class="text-xs truncate w-14 text-center">user_1</span>
        </div>
    </div>
    <div class="space-y-4 my-2">
        <div class="border-b border-gray-900 pb-3">
            <div class="flex items-center justify-between p-3">
                <div class="flex items-center space-x-3">
                    <img src="https://picsum.photos/100/100?random=2" class="w-8 h-8 rounded-full object-cover">
                    <span class="font-semibold text-sm">user_1</span>
                </div>
                <i class="fas fa-ellipsis-h text-gray-400"></i>
            </div>
            <img src="https://picsum.photos/600/600?random=10" class="w-full object-cover max-h-[400px]">
            <div class="p-3 space-y-2">
                <div class="flex justify-between text-xl">
                    <div class="flex space-x-4">
                        <i class="far fa-heart cursor-pointer hover:text-red-500" onclick="toggleLike(this)"></i>
                        <i class="far fa-comment cursor-pointer"></i>
                        <i class="far fa-paper-plane cursor-pointer"></i>
                    </div>
                    <i class="far fa-bookmark cursor-pointer"></i>
                </div>
                <p class="font-semibold text-sm">1,240 likes</p>
                <p class="text-sm"><span class="font-semibold">user_1</span> Telegram Mini App 100% tayyor! 🚀</p>
            </div>
        </div>
    </div>
    <div class="fixed bottom-0 left-0 right-0 bg-black border-t border-gray-800 flex justify-around py-3 text-xl z-50">
        <i class="fas fa-home"></i>
        <i class="fas fa-search text-gray-400"></i>
        <i class="far fa-plus-square text-gray-400"></i>
        <i class="fas fa-film text-gray-400"></i>
        <i class="far fa-user-circle text-gray-400"></i>
    </div>
    <script>
        function toggleLike(elm) {
            elm.classList.toggle('fas');
            elm.classList.toggle('far');
            elm.classList.toggle('text-red-500');
        }
    </script>
</body>
</html>"""
    return jsonify({
        "files": [
            {"name": "index.html", "content": template_code}
        ]
    })

@app.route('/auto-fix', methods=['POST'])
def auto_fix():
    data = request.get_json() or {}
    return jsonify({"fixed_code": data.get('code', '')})

@app.route('/run-terminal', methods=['POST'])
def run_terminal():
    data = request.get_json() or {}
    command = data.get('command', '')
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
        return jsonify({"output": output.decode('utf-8')})
    except Exception as e:
        return jsonify({"output": f"Terminal xatoligi: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
