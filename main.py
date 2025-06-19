import os
import openai
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Переменные окружения
TELEGRAM_BOT_TOKEN = 7281555453:AAH4p_gW8RTfPZBT6T8pzsZ23Dck8pDN5V8
openai.api_key = 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

# Команда /start
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Ответ на сообщения
async def chat(update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    messages = [
        {"role": "system", "content": "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra."},
        {"role": "user", "content": user_input}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=messages
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
