# main.py
from telegram.ext import ApplicationBuilder
from handlers.commands import start, reset
from handlers.messages import chat, handle_voice
from config import TELEGRAM_BOT_TOKEN

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Хендлеры
app.add_handler(start)
app.add_handler(reset)
app.add_handler(chat)
app.add_handler(handle_voice)

print("🤖 Mindra запущен!")
app.run_polling()
