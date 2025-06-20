import os
import json
from openai import OpenAI
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Клиент OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Путь к истории
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

# История общения
conversation_history = load_history()

# Ограничение длины истории
def trim_history(history, max_messages=10):
    system_prompt = history[0]
    trimmed = history[-max_messages:] if len(history) > max_messages else history[1:]
    return [system_prompt] + trimmed

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Команда /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    conversation_history[user_id] = [
        {"role": "system", "content": (
            "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra. "
            "Всегда отвечай на том же языке, на котором пишет пользователь. "
            "Отвечай тепло, человечно, с лёгким флиртом и эмпатией."
        )}
    ]
    save_history(conversation_history)
    await update.message.reply_text("История сброшена ✨")

# Обработка текста
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.message.from_user.id)

    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": (
                "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra. "
                "Всегда отвечай на том же языке, на котором пишет пользователь. "
                "Отвечай тепло, человечно, с лёгким флиртом и эмпатией."
            )}
        ]

    conversation_history[user_id].append({"role": "user", "content": user_input})
    trimmed_history = trim_history(conversation_history[user_id])

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=trimmed_history
        )
        reply = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Упс, я немного завис... Попробуй позже 🥺")
        print(f"❌ Ошибка OpenAI: {e}")

# Обработка голосовых
async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = await update.message.voice.get_file()
        file_path = "voice.ogg"
        await file.download_to_drive(file_path)

        with open(file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )

        update.message.text = transcript  # подставим как будто это текстовое сообщение
        await chat(update, context)

    except Exception as e:
        await update.message.reply_text("Не удалось распознать голосовое сообщение 🥲")
        print(f"Ошибка при обработке голосового: {e}")

# Запуск приложения
if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(MessageHandler(filters.VOICE, voice))
    print("🤖 Mindra запущен!")
    app.run_polling()
