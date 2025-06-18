import os
import openai
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Получение переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# /start команда
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra — твой AI-компаньон 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Чат с GPT
async def chat(update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    messages = [
        {"role": "system", "content": "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra."},
        {"role": "user", "content": user_input}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Упс, я немного завис... Попробуй позже 😢")
        print(f"❌ Ошибка OpenAI: {e}")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤖 Mindra запущен!")
    app.run_polling()
