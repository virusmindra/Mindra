import os
import json
import tempfile
import openai
import logging
import asyncio
import aiohttp
import subprocess

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

HISTORY_FILE = "dialogues.json"
logging.basicConfig(level=logging.INFO)

# Загрузка истории
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Готов поддержать, вдохновить и пофлиртовать 😉")

# Текстовые сообщения
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.effective_user.id)

    if user_id not in conversation_history:
        conversation_history[user_id] = [{
            "role": "system",
            "content": (
                "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra. "
                "Всегда отвечай на том же языке, на котором пишет пользователь. "
                "Отвечай тепло, человечно, с лёгким флиртом и эмпатией."
            )
        }]

    conversation_history[user_id].append({"role": "user", "content": user_input})
    trimmed = trim_history(conversation_history[user_id])

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=trimmed
        )
        reply = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Упс, что-то пошло не так... Попробуй ещё раз.")

# Голосовые сообщения
async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    voice_file = await update.message.voice.get_file()

    ogg_path = tempfile.mktemp(suffix=".ogg")
    mp3_path = tempfile.mktemp(suffix=".mp3")

    await voice_file.download_to_drive(ogg_path)

    try:
        # Конвертация через ffmpeg
        subprocess.run([
            "ffmpeg", "-i", ogg_path, "-ar", "44100", "-ac", "2", "-f", "mp3", mp3_path
        ], check=True)

        with open(mp3_path, "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", file=f)

        update.message.text = transcript["text"]
        await chat(update, context)

    except Exception as e:
        print(f"Ошибка при обработке голоса: {e}")
        await update.message.reply_text("Не удалось распознать голос 😢")

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(MessageHandler(filters.VOICE, voice))
    print("🤖 Mindra готов слушать и говорить!")
    app.run_polling()
