# main.py

from telegram.ext import ApplicationBuilder
from handlers import handlers
from config import TELEGRAM_BOT_TOKEN

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    for handler in handlers:
        app.add_handler(handler)

    print("🤖 Mindra запущен!")
    app.run_polling()
