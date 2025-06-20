import os
import json
import subprocess
from openai import OpenAI
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# История
HISTORY_FILE = "dialogues.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

conversation_history = load_history()

def trim_history(history, max_messages=10):
    system_prompt = history[0]
    trimmed = history[-max_messages:] if len(history) > max_messages else history[1:]
    return [system_prompt] + trimmed

# Команда /start
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Команда /reset
async def reset(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text("История очищена. Начнём сначала ✨")

# Ответ на текст
async def chat(update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.message.from_user.id)

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

# Ответ на голосовое сообщение
async def handle_voice(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    ogg_path = f"voice_{user_id}.ogg"
    mp3_path = f"voice_{user_id}.mp3"

    await file.download_to_drive(ogg_path)
    subprocess.run(["ffmpeg", "-i", ogg_path, mp3_path])

    try:
        with open(mp3_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        update.message.text = transcription
        await chat(update, context)

    except Exception as e:
        await update.message.reply_text("Не удалось распознать голосовое сообщение 🥲")
        print(f"❌ Ошибка распознавания: {e}")

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤖 Mindra запущен!")
    app.run_polling()
