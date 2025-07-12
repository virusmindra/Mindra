import os
import logging
import asyncio
import pytz
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
from datetime import datetime, timezone, timedelta, time
from handlers import (
    handlers as all_handlers,
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
from handlers import chat, handle_voice

# Инициализация приложения
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
# Добавление хендлеров
for handler in all_handlers:
    app.add_handler(handler)
    
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.job_queue.run_daily(
    send_daily_reminder,
    time=time(hour=10, minute=0, tzinfo=pytz.timezone("Europe/Kiev")),
    name="morning_reminder"
)

app.job_queue.run_repeating(
    send_idle_reminders_compatible,
    interval=timedelta(seconds=30),  # вместо минут
    first=timedelta(seconds=10),  # запуск через 10 секунд после старта
    name="idle_reminder"
)

# ⛑ Глобальный обработчик ошибок
async def error_handler(update, context):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("😵 Ой, что-то пошло не так. Я уже разбираюсь с этим.")


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

async def run_idle_reminder_loop(app):
    while True:
        try:
            await send_idle_reminders_compatible(app)
        except Exception as e:
            print(f"❌ Ошибка в idle reminder loop: {e}")
        await asyncio.sleep(180)  # каждые 3 минуты
                
async def run_idle_reminder_loop(app):
    while True:
        try:
            await send_idle_reminders_compatible(app)
        except Exception as e:
            print(f"❌ Ошибка в idle reminder loop: {e}")
        await asyncio.sleep(180)  # каждые 3 минуты

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # 👂 Обработчик голосовых
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # ✅ Все остальные хендлеры
    for handler in all_handlers:
        app.add_handler(handler)

    # 🧠 Отслеживание активности
    app.add_handler(MessageHandler(filters.ALL, track_users))

    app.add_error_handler(error_handler)

    # 🔁 Запускаем отправку напоминаний через asyncio
    asyncio.create_task(run_idle_reminder_loop(app))

    app.job_queue.run_repeating(  
        lambda context: asyncio.create_task(send_idle_reminders_compatible(app)),
        interval=60,  # 1 минута
        first=10
     )
    
    logging.info("🤖 Бот запущен!")
    await app.run_polling()
    
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    asyncio.get_event_loop().run_until_complete(main())
