import os
import logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from telegram.error import TelegramError
from handlers import handlers as all_handlers, goal_buttons_handler
from handlers import habit, habits_list, handle_habit_button
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
from goals import get_goals
from datetime import datetime, timedelta
import asyncio

# Функция напоминания
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
                    print(f"Ошибка с напоминанием: {e}")

# Получаем токен бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Глобальный обработчик ошибок
async def error_handler(update, context):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("😵 Ой, что-то пошло не так. Я уже разбираюсь с этим.")

 # Сохраняем ID пользователей
def track_users(update, context):
    user_id = str(update.effective_user.id)
    app.bot_data.setdefault("user_ids", set()).add(user_id)

app.add_handler(MessageHandler(filters.ALL, track_users))

# Запускаем планировщик напоминаний
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(send_reminders(app)), 'interval', hours=24)
scheduler.start()

 # Добавляем отдельно кнопку целей
    app.add_handler(CallbackQueryHandler(goal_buttons_handler, pattern="^(create_goal|show_goals)$"))

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем все обработчики из handlers.py
    for handler in all_handlers:
        app.add_handler(handler)

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    print("🤖 Mindra запущен!")
    app.run_polling()
