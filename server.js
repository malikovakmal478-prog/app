const express = require('express');
const TelegramBot = require('node-telegram-bot-api');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Faol botlarni saqlash uchun xotira
const activeBots = new Map();

// --- VELTRIX DIZAYNI VA INTERFEYSI (HTML) ---
app.get('/', (req, res) => {
    res.send(`
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VELTRIX - Cloud Server</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background-color: #0e1117; color: #c9d1d9; display: flex; height: 100vh; overflow: hidden; }
            .sidebar { width: 260px; background: #161b22; border-right: 1px solid #30363d; display: flex; flex-direction: column; }
            .logo { font-size: 24px; font-weight: bold; color: #58a6ff; padding: 20px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 10px; }
            .menu { list-style: none; padding: 20px; }
            .menu li { padding: 12px 15px; margin-bottom: 8px; border-radius: 6px; cursor: pointer; background: #21262d; color: #f0f6fc; transition: 0.3s; }
            .menu li:hover { background: #30363d; color: #58a6ff; }
            .main { flex: 1; display: flex; flex-direction: column; }
            .header { padding: 15px 30px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
            .content { padding: 30px; overflow-y: auto; flex: 1; }
            .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            .card h3 { margin-bottom: 15px; color: #58a6ff; }
            input, select { width: 100%; padding: 12px; margin-bottom: 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #white; color-scheme: dark; }
            button { background: #238636; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.3s; }
            button:hover { background: #2ea043; }
            .status { display: inline-block; width: 10px; height: 10px; background: #3fb950; border-radius: 50%; margin-right: 5px; }
        .log-box { background: #0d1117; padding: 15px; border-radius: 6px; font-family: monospace; color: #3fb950; height: 150px; overflow-y: auto; border: 1px solid #30363d; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="logo">⚡ VELTRIX</div>
            <ul class="menu">
                <li>🏠 Boshqaruv Paneli</li>
                <li>🤖 Botlarni Boshqarish</li>
                <li>📱 Mini-App Yaratish</li>
                <li>📊 Server Statistikasi</li>
            </ul>
        </div>
        <div class="main">
            <div class="header">
                <h2>Xush kelibsiz, <b>VELTRIX Cloud</b> ga!</h2>
                <span><span class="status"></span> Server 24/7 Faol</span>
            </div>
            <div class="content">
                <div class="card">
                    <h3>🤖 Telegram Botni Token Orqali 24/7 Ishga Tushirish</h3>
                    <form action="/start-bot" method="POST">
                        <label>Bot Tokeningizni kiriting:</label>
                        <input type="text" name="token" placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ" required>
                        <label>Bot turi / Xabari:</label>
                        <input type="text" name="welcome" placeholder="Salom! Bot VELTRIX serverida ishlayapti." required>
                        <button type="submit">🚀 Botni Ishga Tushirish</button>
                    </form>
                </div>
                
                <div class="card">
                    <h3>💻 Server Terminali va Loglar</h3>
                    <div class="log-box" id="logs">
                        [VELTRIX System] Server muvaffaqiyatli ishga tushdi...<br>
                        [VELTRIX System] Havola: https://malikovakmal478-prog.github.io/app/<br>
                        [VELTRIX System] 24/7 rejim faol. Barcha xavfsizlik protokollari ishlayapti.
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    `);
});

// --- BOTNI TOKEN ORQALI ISHGA TUSHIRISH ENDPOINTI ---
app.post('/start-bot', (req, res) => {
    const { token, welcome } = req.body;
    
    try {
        if (activeBots.has(token)) {
            return res.send(`<script>alert('Bu bot allaqachon ishlamoqda!'); window.location='/';</script>`);
        }

        // Yangi Telegram bot yaratamiz (Polling rejimida 24/7 ishlaydi)
        const bot = new TelegramBot(token, { polling: true });

        bot.on('message', (msg) => {
            const chatId = msg.chat.id;
            const text = msg.text;

            if (text === '/start') {
                bot.sendMessage(chatId, `✨ ${welcome}\n\n📱 **VELTRIX Mini-App:** [Ochish](https://malikovakmal478-prog.github.io/app/)`, {
                    parse_mode: 'Markdown',
                    reply_markup: {
                        inline_keyboard: [
                            [{ text: '🌐 Veltrix Mini-Appni Ochish', url: 'https://malikovakmal478-prog.github.io/app/' }],
                            [{ text: '📞 Yordam', callback_data: 'help' }]
                        ]
                    }
                });
            }
        });

        activeBots.set(token, bot);
        res.send(`<script>alert('Bot muvaffaqiyatli 24/7 rejimda ishga tushdi!'); window.location='/';</script>');`);
    } catch (error) {
        res.send(`<script>alert('Xatolik: Token noto'g'ri!'); window.location='/';</script>`);
    }
});

app.listen(PORT, () => {
    console.log(`VELTRIX Server ${PORT}-portda ishga tushdi!`);
});
