import os
import logging
import asyncio
import pytz
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)
from datetime import datetime, timezone, timedelta, time
from handlers import (
    handlers as all_handlers,
    handle_voice,
    send_idle_reminders_compatible,
    chat
)
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)

# ⛑ Глобальный обработчик ошибок
async def error_handler(update, context):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("😵 Ой, что-то пошло не так. Я уже разбираюсь с этим.")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 👉 Сначала текст
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # 👉 Голос
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # 👉 Остальные хендлеры
    for handler in all_handlers:
        app.add_handler(handler)

    app.add_error_handler(error_handler)

    # 🔁 Idle reminder
    app.job_queue.run_repeating(
        lambda context: asyncio.create_task(send_idle_reminders_compatible(app)),
        interval=60,
        first=10
    )

    logging.info("🤖 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
