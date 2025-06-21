import os
import json
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
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
    await update.message.reply_text("🧠 История очищена! Начнём сначала?")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_input = update.message.text

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
    trimmed = trim_history(conversation_history[user_id])

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=trimmed
        )
        reply = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"OpenAI Error: {e}")
        await update.message.reply_text("Упс, я немного завис... Попробуй позже 🥺")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤖 Mindra запущен!")
    app.run_polling()
