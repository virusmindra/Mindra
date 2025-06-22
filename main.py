# main.py

import os
from telegram.ext import ApplicationBuilder
from handlers import handlers

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем все обработчики
    for handler in handlers:
        app.add_handler(handler)

    print("🤖 Mindra запущен!")
    app.run_polling()
