import os
import logging
import asyncio
import pytz
from datetime import datetime, timezone, timedelta, time
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)
from handlers import (
    handlers as all_handlers,
    handle_voice,
    send_idle_reminders_compatible,
    chat,
    get_random_daily_task,  # ✨ импортируем функцию выбора задания
    user_last_seen,           # ✨ список активных пользователей
    send_evening_checkin,
    my_stats_command,
    send_random_support, 
    send_random_poll,
    premium_report,
    premium_challenge,
    premium_mode,
    premium_mode_callback,
    premium_stats,
    send_weekly_report,
    remind_command, 
    handle_goal_done, 
    test_mood,
    check_custom_reminders
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

    app.job_queue.run_daily(
        send_evening_checkin,
        time=time(hour=21, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        name="evening_checkin"
    )

    # ⏰ Утренние задания каждый день в 10:00 по Киеву
    app.job_queue.run_daily(
        send_daily_task,
        time=time(hour=10, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        name="daily_task_job"
    )

    # ✨ Сообщения поддержки каждые 4 часа (с 9:00 до 21:00 по Киеву)
    app.job_queue.run_repeating(
        send_random_support,
        interval=timedelta(hours=4),
        first=timedelta(minutes=5),  # начнём через 5 минут после запуска
        name="support_messages"
    )

    app.job_queue.run_repeating(
        send_random_poll,
        interval=timedelta(days=2),  # каждые 2 дня
        first=datetime.now(pytz.timezone("Europe/Kiev")).replace(hour=12, minute=0, second=0, microsecond=0).astimezone(pytz.utc)
    )

    app.job_queue.run_daily(
        send_weekly_report,
        time=time(hour=14, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        days=(6,),  # 6 = воскресенье (0 = понедельник)
        name="weekly_report"
    )

    app.job_queue.run_repeating(
        lambda context: asyncio.create_task(check_custom_reminders(app)),
        interval=60, first=10
    )

    app.job_queue.run_daily(
        send_daily_reminder,
        time=time(hour=8, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        name="daily_reminder"
    )

    logging.info("🤖 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
