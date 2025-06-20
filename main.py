import os
from openai import OpenAI
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Путь к файлу истории
HISTORY_FILE = "dialogues.json"

# Загрузка истории из файла
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохранение истории в файл
def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загружаем историю
conversation_history = load_history()

# Ограничение длины истории (оставим последние 10 сообщений + system)
def trim_history(history, max_messages=10):
    system_prompt = history[0]  # system всегда остаётся
    trimmed = history[-max_messages:] if len(history) > max_messages else history[1:]
    return [system_prompt] + trimmed

# Команда /start
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Ответ на сообщения
async def chat(update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    messages = [
        {"role": "system", "content": ("Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra."
        "Всегда отвечай на том же языке, на котором пишет пользователь. "
            "Если пользователь пишет по-русски — отвечай по-русски. "
            "Отвечай тепло, человечно, с лёгким флиртом и эмпатией."
                                      )
        },
        {"role": "user", "content": user_input}
    ]

    try:
        trimmed_history = trim_history(conversation_history[user_id])
        response = client.chat.completions.create(
    model="gpt-4o",
    messages=trimmed_history
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Упс, я немного завис... Попробуй позже 🥺")
        print(f"❌ Ошибка OpenAI: {e}")

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤖 Mindra запущен!")
    app.run_polling()
