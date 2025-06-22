# handlers.py

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_BOT_TOKEN, client
from history import load_history, save_history, trim_history

# Загрузка истории
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

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вот что я умею:\n\n"
        "💬 Просто напиши мне сообщение — я отвечу.\n"
        "🧠 Я запоминаю твои предыдущие реплики (историю можно сбросить).\n"
        "📎 Команды:\n"
        "/start — приветствие\n"
        "/reset — сброс истории\n"
        "/help — показать это сообщение\n"
        "/about — кто такая Mindra\n"
        "/mode [режим] — изменить стиль общения (default, support, motivation, philosophy, humor)\n"
        "\nСкоро научусь и другим фишкам 😉"
    )

# Обработчик команды /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💜 *Привет! Я — Mindra.*\n\n"
        "Я здесь, чтобы быть рядом, когда тебе нужно выговориться, найти мотивацию или просто почувствовать поддержку.\n"
        "Можем пообщаться тепло, по-доброму, с заботой — без осуждения и давления 🦋\n\n"
        "🔮 *Что я умею:*\n"
        "• Поддержать, когда тяжело\n"
        "• Напомнить, что ты — не один(а)\n"
        "• Помочь найти фокус и вдохновение\n"
        "• И иногда просто поговорить по душам 😊\n\n"
        "_Я не ставлю диагнозы и не заменяю психолога, но стараюсь быть рядом в нужный момент._\n\n"
        "✨ *Mindra — это пространство для тебя.*"
    )
    await update.message.reply_markdown(text)

# Обработчик команды /mode
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args

    available_modes = {
        "default": "Ты — тёплый, заботливый и вдохновляющий AI-компаньон по имени Mindra.",
        "support": "Ты — заботливый и понимающий собеседник, как психолог. Слушаешь внимательно, поддерживаешь мягко и с эмпатией.",
        "motivation": "Ты — энергичный коуч, который вдохновляет, заряжает и помогает двигаться вперёд.",
        "philosophy": "Ты — философ, который помогает взглянуть на вещи глубже, задаёт вопросы и делится мудрыми размышлениями.",
        "humor": "Ты — весёлый, дружелюбный собеседник с лёгким чувством юмора. Можешь пошутить, поднять настроение, но остаёшься добрым."
    }

    if not args:
        await update.message.reply_text("Укажи режим после команды. Например: /mode support\nДоступные режимы: default, support, motivation, philosophy, humor")
        return

    selected_mode = args[0].lower()
    if selected_mode not in available_modes:
        await update.message.reply_text("Такого режима нет. Используй: default, support, motivation, philosophy, humor")
        return

    conversation_history[user_id] = [
        {"role": "system", "content": (
            available_modes[selected_mode] +
            " Всегда отвечай на том же языке, на котором пишет пользователь. Отвечай тепло, человечно и с пониманием."
        )}
    ]
    save_history(conversation_history)
    await update.message.reply_text(f"Режим общения переключён на *{selected_mode}* ✨", parse_mode="Markdown")

# Обработчик текстовых сообщений
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.effective_user.id)

    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": (
                "Ты — тёплый, заботливый и вдохновляющий AI-компаньон по имени Mindra."
                " Всегда отвечай на том же языке, на котором пишет пользователь. Отвечай тепло, человечно и с пониманием."
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

# Обработка неизвестных команд
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Я не знаю такой команды. Напиши /help, чтобы увидеть, что я умею.")

# Регистрируем все обработчики
handlers = [
    CommandHandler("start", start),
    CommandHandler("reset", reset),
    CommandHandler("help", help_command),
    CommandHandler("about", about),
    CommandHandler("mode", mode),
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.COMMAND, unknown_command),
]
