import os
import subprocess
import logging
import speech_recognition as sr
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне голосовое сообщение 👂")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    if not voice:
        await update.message.reply_text("⚠️ Голосовое сообщение не найдено")
        return

    ogg_path = "voice.ogg"
    mp3_path = "voice.mp3"

    try:
        file = await voice.get_file()
        await file.download_to_drive(ogg_path)
        logging.info("🎙️ Файл загружен")

        # Конвертация через ffmpeg
        subprocess.run([
            "ffmpeg", "-i", ogg_path, "-ar", "44100", "-ac", "2", mp3_path
        ], check=True)

        logging.info("🎧 Конвертация завершена")

        # Распознавание
        recognizer = sr.Recognizer()
        with sr.AudioFile(mp3_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        await update.message.reply_text(f"Ты сказал: {text}")

    except Exception as e:
        logging.error(f"Ошибка при обработке голосового: {e}")
        await update.message.reply_text("❌ Не удалось распознать голосовое сообщение.")

    finally:
        for path in [ogg_path, mp3_path]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logging.info("🤖 Бот запущен")
    app.run_polling()
