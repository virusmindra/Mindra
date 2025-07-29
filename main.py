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
    start,
    language_callback,
    chat,
    handle_voice,
    my_stats_command,
    mypoints_command,
    remind_command,
    handle_goal_done,
    habit_done,
    handle_habit_button,
    handle_goal_delete,
    test_mood,
    give_trial_if_needed,
    handle_referral,
    premium_report,
    premium_challenge,
    premium_mode,
    premium_mode_callback,
    premium_stats,
    send_weekly_report,
    send_idle_reminders_compatible,
    send_random_support,
    send_evening_checkin,
    send_daily_task,
    send_daily_reminder,
    send_random_poll,
    check_custom_reminders,
    all_handlers,
    get_random_daily_task,
    user_last_seen,
    user_last_prompted,
    user_reminders,
    user_points,
    user_message_count,
    user_goal_count,
    user_languages,
    user_ref_args,
    PREMIUM_USERS,
    get_goals,
    get_habits,
    save_history,
    conversation_history,
    user_modes,
    LANG_PROMPTS,
    MODES,
    WELCOME_TEXTS,
    REFERRAL_BONUS_TEXT,
    TRIAL_GRANTED_TEXT,
    TRIAL_INFO_TEXT,
    SUPPORT_MESSAGES_BY_LANG,
    EVENING_MESSAGES_BY_LANG,
    MORNING_MESSAGES_BY_LANG,
    DAILY_TASKS_BY_LANG,
    IDLE_MESSAGES,
    POLL_MESSAGES_BY_LANG,
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
