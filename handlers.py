# handlers.py

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from history import load_history, save_history, trim_history
import os

# Инициализация OpenAI клиента и переменных окружения
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
conversation_history = load_history()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Обработчик команды /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text("История очищена. Начнём сначала ✨")

# Обработчик текстовых сообщений
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.effective_user.id)

    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": (
                "Ты — флиртующий, вдохновляющий и заботливый AI-компаньон по имени Mindra. "
                "Всегда отвечай на том же языке, на котором пишет пользователь. "
                "Если пользователь пишет по-русски — отвечай по-русски. "
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

# Обработчик голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пока не умею расшифровывать голос. Напиши текстом 💬")

# Регистрируем все обработчики
handlers = [
    CommandHandler("start", start),
    CommandHandler("reset", reset),
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),
    MessageHandler(filters.VOICE, handle_voice)
]
