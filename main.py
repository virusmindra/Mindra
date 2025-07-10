import os
import logging
import asyncio
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram import Update
from telegram.error import TelegramError
from datetime import datetime, timezone, timedelta

# 👇 Импорты из твоих модулей
from handlers import (
    handlers as all_handlers,
    track_user,
    goal_buttons_handler,
    premium_task,
    handle_voice,
    send_daily_reminder,
    user_last_seen,
    user_last_prompted,
    send_idle_reminders_compatible,
)
from goals import get_goals
from config import TELEGRAM_BOT_TOKEN

# Глобальные переменные
user_last_seen = {}
user_last_prompted = {}

user_last_seen[7775321566] = datetime.now(timezone.utc) - timedelta(hours=3)
# 📋 Настройка логов
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.DEBUG)

# ⛑ Глобальный обработчик ошибок
async def error_handler(update, context):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("😵 Ой, что-то пошло не так. Я уже разбираюсь с этим.")


# 📬 Обработчик всех сообщений
async def track_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_last_seen[user_id] = datetime.now(timezone.utc)
    logging.info(f"👀 Обновлено время активности для {user_id}")
    
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

# 🚀 Запуск планировщика
def start_scheduler(app):
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(send_idle_reminders_compatible, "interval", minutes=3, args=[app])
    scheduler.start()
    
    if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 🧪 Тестовая подстановка времени последней активности
    from datetime import datetime, timedelta
    import pytz
    user_last_seen[7775321566] = datetime.now(timezone.utc) - timedelta(hours=3)
    
    # ⏰ Планировщики
    start_scheduler(app)

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

    logging.info("🤖 Бот запущен в режиме polling!")
    app.run_polling()
