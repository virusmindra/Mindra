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
from telegram.request import HTTPXRequest
from stats import (
    ensure_premium_db,
    ensure_premium_challenges,
    migrate_premium_from_stats,
    ensure_remind_db,
    load_stats,
    PREMIUM_DB_PATH,
)
from handlers import (
    start,
    language_callback,
    chat,
    restore_reminder_jobs,
    voice_mode_cmd,
    handle_voice,
    my_stats_command,
    mypoints_command,
    remind_command,
    habit_done,
    handle_habit_button,
    handle_done_goal_callback,
    parse_goal_index,
    test_mood,
    give_trial_if_needed,
    handle_referral,
    premium_report_cmd,
    premium_challenge_cmd,
    premium_mode_cmd,
    premium_challenge_callback,
    premium_stats_cmd,
    send_weekly_report,
    send_idle_reminders_compatible,
    send_random_support,
    send_evening_checkin,
    send_daily_task,
    send_daily_reminder,
    send_random_poll,
    check_custom_reminders,
    handlers,
    get_random_daily_task,
    user_last_seen,
    user_last_prompted,
    user_reminders,
    user_points,
    user_message_count,
    user_goal_count,
    user_languages,
    user_ref_args,
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
    ensure_remind_db, 
    ensure_premium_db,
    restore_reminder_jobs
)
from config import TELEGRAM_BOT_TOKEN

CUSTOM_JOB_NAME = "custom_rem_check"

def _ensure_single_job(job_queue, name: str):
    try:
        for j in job_queue.get_jobs_by_name(name):
            j.schedule_removal()
    except Exception:
        pass

def schedule_custom_reminders(job_queue, app):
    _ensure_single_job(job_queue, CUSTOM_JOB_NAME)
    job_queue.run_repeating(
        lambda context: asyncio.create_task(check_custom_reminders(app)),
        interval=60, first=5, name=CUSTOM_JOB_NAME
    )

def schedule_idle_reminders(job_queue, app):
    _ensure_single_job(job_queue, "idle_reminders")
    job_queue.run_repeating(
        lambda context: asyncio.create_task(send_idle_reminders_compatible(app)),
        interval=60, first=10, name="idle_reminders"
    )

def schedule_evening_checkin(job_queue):
    _ensure_single_job(job_queue, "evening_checkin")
    job_queue.run_daily(
        send_evening_checkin,
        time=time(hour=21, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        name="evening_checkin"
    )

def schedule_daily_task(job_queue):
    _ensure_single_job(job_queue, "daily_task_job")
    job_queue.run_daily(
        send_daily_task,
        time=time(hour=10, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        name="daily_task_job"
    )

def schedule_support_messages(job_queue):
    _ensure_single_job(job_queue, "support_messages")
    job_queue.run_repeating(
        send_random_support,
        interval=timedelta(hours=4),
        first=timedelta(minutes=5),
        name="support_messages"
    )

def schedule_random_poll(job_queue):
    _ensure_single_job(job_queue, "random_poll")
    job_queue.run_repeating(
        send_random_poll,
        interval=timedelta(days=2),
        first=datetime.now(pytz.timezone("Europe/Kiev")).replace(
            hour=12, minute=0, second=0, microsecond=0
        ).astimezone(pytz.utc),
        name="random_poll"
    )

def schedule_weekly_report(job_queue):
    _ensure_single_job(job_queue, "weekly_report")
    job_queue.run_daily(
        send_weekly_report,
        time=time(hour=14, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        days=(6,),  # воскресенье
        name="weekly_report"
    )

def schedule_daily_reminder(job_queue):
    _ensure_single_job(job_queue, "daily_reminder")
    job_queue.run_daily(
        send_daily_reminder,
        time=time(hour=8, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
        name="daily_reminder"
    )
# ---------------------------------------------------------------------------


async def error_handler(update, context):
    err = context.error

    # мягко игнорируем типичные сетевые обрывы long-poll
    if isinstance(err, (NetworkError, TimedOut)):
        msg = str(err) or ""
        if "httpx.ReadError" in msg or "Timed out" in msg:
            # тихий лог на уровне info
            logging.info(f"Network glitch during getUpdates: {msg}")
            return

    # остальное логируем как ошибку и уведомляем пользователя (если уместно)
    logging.error("Exception while handling an update:", exc_info=err)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("😵 Ой, что-то пошло не так. Я уже разбираюсь с этим.")
    except Exception:
        pass

async def main():
    # Клиент с расширенными таймаутами
    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=60,
    )
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request).build()

    # Базы/миграции ДО старта
    ensure_remind_db()
    ensure_premium_db()
    ensure_premium_challenges()
    migrate_premium_from_stats(load_stats)

    # Хендлеры
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    for handler in handlers:
        app.add_handler(handler)
    app.add_error_handler(error_handler)

    # === Ручной жизненный цикл без run_polling ===
    await app.initialize()
    await app.start()

    # Планирование джоб (после start)
    schedule_idle_reminders(app.job_queue, app)
    schedule_custom_reminders(app.job_queue, app)
    schedule_evening_checkin(app.job_queue)
    schedule_daily_task(app.job_queue)
    schedule_support_messages(app.job_queue)
    schedule_random_poll(app.job_queue)
    schedule_weekly_report(app.job_queue)
    schedule_daily_reminder(app.job_queue)

    # Восстановить все запланированные напоминания
    await restore_reminder_jobs(app.job_queue)

    # Запуск long-polling
    await app.updater.start_polling()
    logging.info("🤖 Бот запущен!")

    # Блокируемся до сигнала остановки
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()   # будет отменено SIGTERM/SIGINT средой деплоя
    finally:
        # Корректная остановка
        try:
            await app.updater.stop()
        except Exception:
            pass
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
