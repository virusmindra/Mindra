# handlers.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import TELEGRAM_BOT_TOKEN, client
from history import load_history, save_history, trim_history

# Загрузка истории и режимов
conversation_history = load_history()
user_modes = {}

MODES = {
    "default": "Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra.",
    "support": "Ты — чуткий и добрый AI-друг, который всегда выслушает и поддержит. Помогай пользователю почувствовать себя лучше.",
    "motivation": "Ты — воодушевляющий коуч и поддерживающий компаньон. Помогай пользователю поверить в себя и двигаться вперёд.",
    "philosophy": "Ты — глубокий собеседник с философским подходом. Помогай пользователю осмыслить чувства и ситуации в жизни.",
    "humor": "Ты — весёлый и добрый AI-друг с лёгким чувством юмора. Поддержи пользователя, добавив немного позитива."
}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    mode = user_modes.get(user_id, "default")
    prompt = MODES.get(mode, MODES["default"])
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")
    await update.message.reply_text(f"🌈 Сейчас включён режим общения: *{mode}*\n_({prompt})_", parse_mode="Markdown")

# Команда /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text("История очищена. Начнём сначала ✨")

# Команда /mode (текстовая)
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎧 Поддержка", callback_data="mode_support")],
        [InlineKeyboardButton("🌸 Мотивация", callback_data="mode_motivation")],
        [InlineKeyboardButton("🧘 Психолог", callback_data="mode_philosophy")],
        [InlineKeyboardButton("🎭 Юмор", callback_data="mode_humor")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери стиль общения Mindra ✨", reply_markup=reply_markup)

# Обработка выбора режима (по кнопке)
async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = query.data  # "mode_humor"
    mode_key = data.replace("mode_", "")

    if mode_key in MODES:
        user_modes[user_id] = mode_key
        conversation_history[user_id] = [
            {"role": "system", "content": MODES[mode_key] + " Всегда отвечай на том же языке, на котором пишет пользователь. Отвечай тепло, человечно, с эмпатией."}
        ]
        save_history(conversation_history)

        await query.edit_message_text(f"✅ Режим общения изменён на *{mode_key}*!", parse_mode="Markdown")

# Ответы на текст
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.effective_user.id)
    mode = user_modes.get(user_id, "default")

    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": MODES[mode] + " Всегда отвечай на том же языке, на котором пишет пользователь. Отвечай тепло, человечно, с эмпатией."}
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

# Голосовые
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пока не умею расшифровывать голос. Напиши текстом 💬")

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вот что я умею:\n\n" 
        "💬 Просто напиши мне сообщение — я отвечу.\n"
        "🧠 Я запоминаю твои предыдущие реплики (историю можно сбросить).\n"
        "📎 Команды:\n"
        "/start — приветствие\n"
        "/reset — сброс истории\n"
        "/help — показать это сообщение\n"
        "/about — немного обо мне\n"
        "/mode — изменить стиль общения\n"
        "Скоро научусь и другим фишкам 😉"
    )

# /about
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

# Неизвестные команды
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Я не знаю такой команды. Напиши /help, чтобы увидеть, что я умею.")

# Регистрация обработчиков
handlers = [
    CommandHandler("start", start),
    CommandHandler("reset", reset),
    CommandHandler("help", help_command),
    CommandHandler("about", about),
    CommandHandler("mode", mode),
    CallbackQueryHandler(mode_callback),
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.COMMAND, unknown_command),
]
