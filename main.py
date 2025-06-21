import os
import json
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Путь к файлу истории
HISTORY_FILE = "dialogues.json"

# Загрузка истории
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохранение истории
def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# История
conversation_history = load_history()

# Ограничение истории
def trim_history(history, max_messages=10):
    system_prompt = history[0]
    trimmed = history[-max_messages:] if len(history) > max_messages else history[1:]
    return [system_prompt] + trimmed

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Команда /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    conversation_history[user_id] = [{
        "role": "system",
        "content": (
            "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra. "
            "Всегда отвечай на том же языке, на котором пишет пользователь. "
            "Если пользователь пишет по-русски — отвечай по-русски. "
            "Отвечай тепло, человечно, с лёгким флиртом и эмпатией."
        )
    }]
    save_history(conversation_history)
    await update.message.reply_text("История очищена 🧠🔄")

# Обработка текста
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.effective_user.id)

    if user_id not in conversation_history:
        conversation_history[user_id] = [{
            "role": "system",
            "content": (
                "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra. "
                "Всегда отвечай на том же языке, на котором пишет пользователь. "
                "Если пользователь пишет по-русски — отвечай по-русски. "
                "Отвечай тепло, человечно, с лёгким флиртом и эмпатией."
            )
        }]

    conversation_history[user_id].append({"role": "user", "content": user_input})
    messages = trim_history(conversation_history[user_id])

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Упс, я немного завис... Попробуй позже 🥺")
        print(f"❌ Ошибка OpenAI: {e}")

# Обработка голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пока не умею расшифровывать голос. Напиши текстом 💬")

# Запуск бота
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))  # если нужно

    application.run_polling()

