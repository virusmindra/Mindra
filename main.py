# main.py

import os
import logging
from telegram.ext import ApplicationBuilder
from telegram.error import TelegramError
from handlers import handlers

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Глобальный обработчик ошибок
async def error_handler(update, context):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("😵 Ой, что-то пошло не так. Я уже разбираюсь с этим.")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем все обработчики
    for handler in handlers:
        app.add_handler(handler)

    # Регистрируем глобальный обработчик ошибок
    app.add_error_handler(error_handler)

    print("🤖 Mindra запущен!")
    app.run_polling()
