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
from datetime import datetime, timezone, timedelta
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

# Инициализация приложения
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
# Добавление хендлеров
for handler in all_handlers:
    app.add_handler(handler)
    
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

async def run_idle_reminder_loop(app):
    while True:
        try:
            await send_idle_reminders_compatible(app)
        except Exception as e:
            print(f"❌ Ошибка в idle reminder loop: {e}")
        await asyncio.sleep(180)  # каждые 3 минуты

# 🕐 Отправка сообщений после короткой неактивности (для теста)
async def send_idle_reminders_compatible(app):
    now = datetime.now(timezone.utc)
    logging.info("⏰ Проверка неактивных пользователей...")

    for user_id, last_seen in user_last_seen.items():
        if (now - last_seen) > timedelta(seconds=15):  # временно для теста
            try:
                await app.bot.send_message(chat_id=user_id, text="✨ Привет, давно не болтали! Как ты?")
                user_last_seen[user_id] = now
                logging.info(f"📨 Напоминание отправлено пользователю {user_id}")
            except Exception as e:
                logging.error(f"❌ Ошибка при отправке сообщения пользователю {user_id}: {e}")
                
async def run_idle_reminder_loop(app):
    while True:
        try:
            await send_idle_reminders_compatible(app)
        except Exception as e:
            print(f"❌ Ошибка в idle reminder loop: {e}")
        await asyncio.sleep(180)  # каждые 3 минуты

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

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
