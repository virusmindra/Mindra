import os
import logging
import speech_recognition as sr
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

recognizer = sr.Recognizer()

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    input_ogg = "voice.ogg"
    output_mp3 = "voice.mp3"

    await file.download_to_drive(input_ogg)

    # Конвертируем OGG → MP3
    subprocess.run(['ffmpeg', '-i', input_ogg, output_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with sr.AudioFile(output_mp3) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
            await update.message.reply_text(f"🗣️ Ты сказал: {text}")
        except sr.UnknownValueError:
            await update.message.reply_text("Не смог разобрать речь 😔")
        except sr.RequestError as e:
            await update.message.reply_text(f"Ошибка сервиса распознавания: {e}")

    os.remove(input_ogg)
    os.remove(output_mp3)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()
