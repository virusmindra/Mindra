import os
import logging
import asyncio
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from telegram.error import TelegramError
from pytz import timezone

# 👇 Импорты из твоих модулей
from handlers import (
    handlers as all_handlers,
    track_user,
    goal_buttons_handler,
    premium_task,
    handle_voice,
    send_daily_reminder,
    start_idle_scheduler,
    user_last_seen,
    check_and_send_warm_messages,
    user_last_prompted,
)
from goals import get_goals
from config import TELEGRAM_BOT_TOKEN

# 📋 Настройка логов
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.DEBUG)

# ⛑ Глобальный обработчик ошибок
async def error_handler(update, context):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("😵 Ой, что-то пошло не так. Я уже разбираюсь с этим.")

# 👥 Трекинг пользователей
async def track_users(update, context):
    user_id = str(update.effective_user.id)
    context.application.bot_data.setdefault("user_ids", set()).add(user_id)

# 🔔 Планировщик напоминаний
async def send_reminders(app):
    for user_id in app.bot_data.get("user_ids", []):
        goals = get_goals(user_id)
        for goal in goals:
            if goal.get("remind") and not goal["done"] and goal.get("deadline"):
                try:
                    deadline = datetime.strptime(goal["deadline"], "%Y-%m-%d")
                    if datetime.now().date() >= deadline.date():
                        await app.bot.send_message(
                            chat_id=int(user_id),
                            text=f"🔔 Напоминание: не забудь про цель:\n\n*{goal['text']}*",
                            parse_mode="Markdown"
                        )
                except Exception as e:
                    print(f"❌ Ошибка с напоминанием: {e}")

# 🚀 Планировщик запускается здесь
def start_scheduler(app):
    scheduler = BackgroundScheduler()

    scheduler.add_job(send_idle_reminders_compatible, trigger="interval", minutes=30, args=[application])

    scheduler.start()

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 🔁 Автоматические тёплые сообщения
    from handlers import check_and_send_warm_messages
    app.job_queue.run_repeating(check_and_send_warm_messages, interval=3600, first=600)

    # 👂 Обработчик голосовых
    print("🧪 Зарегистрирован handler VOICE:", handle_voice)
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # ✅ Обработчики из списка
    for handler in all_handlers:
        app.add_handler(handler)

    # 👥 Отслеживание пользователей
    app.add_handler(MessageHandler(filters.ALL, track_users))

    # ⛑ Обработка ошибок
    app.add_error_handler(error_handler)

    # ⏰ Планировщики
    start_scheduler(app)
    start_idle_scheduler(application)
    
    logging.info("🤖 Бот запущен в режиме polling!")
    app.run_polling()
