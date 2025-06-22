# handlers.py

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_BOT_TOKEN, client
from history import load_history, save_history, trim_history
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup

# Список режимов
MODES = {
    "🎧 Поддержка": "Ты — добрый и поддерживающий AI-компаньон, который помогает справиться с трудными моментами. Ты очень чуткий, тёплый и спокойный.",
    "🌸 Мотивация": "Ты — вдохновляющий и заряжающий AI-компаньон. Помогаешь поверить в себя, мотивируешь и поддерживаешь уверенность.",
    "🧘 Психолог": "Ты — внимательный, рассудительный и очень деликатный AI, похожий на хорошего психолога. Ты задаёшь вопросы и помогаешь разобраться в себе.",
    "🎭 Разговор по душам": "Ты — как близкий друг, с которым можно поговорить по душам. Общение лёгкое, но глубокое и искреннее."
}

# Команда /mode — выбор режима
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[mode] for mode in MODES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выбери стиль общения Mindra ✨", reply_markup=reply_markup)

# Обработка выбора режима
async def handle_mode_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    mode_text = update.message.text.strip()

    if mode_text in MODES:
        system_prompt = MODES[mode_text]

        # Сохраняем новый system prompt и очищаем историю
        conversation_history[user_id] = [
            {"role": "system", "content": system_prompt}
        ]
        save_history(conversation_history)

        await update.message.reply_text(f"✅ Режим *{mode_text}* выбран!", parse_mode="Markdown")
    else:
        await chat(update, context)  # если не режим — отправляем как обычное сообщение


# Загрузка истории
conversation_history = load_history()

# Настройки режимов
MODES = {
    "default": "Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra.",
    "support": "Ты — чуткий и добрый AI-друг, который всегда выслушает и поддержит. Помогай пользователю почувствовать себя лучше.",
    "motivation": "Ты — воодушевляющий коуч и поддерживающий компаньон. Помогай пользователю поверить в себя и двигаться вперёд.",
    "philosophy": "Ты — глубокий собеседник с философским подходом. Помогай пользователю осмыслить чувства и ситуации в жизни.",
    "humor": "Ты — весёлый и добрый AI-друг с лёгким чувством юмора. Поддержи пользователя, добавив немного позитива."
}

user_modes = {}

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    mode = user_modes.get(user_id, "default")
    prompt = MODES.get(mode, MODES["default"])
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")
    await update.message.reply_text(f"🌈 Сейчас включён режим общения: *{mode}*\n_({prompt})_", parse_mode="Markdown")

# Обработчик команды /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text("История очищена. Начнём сначала ✨")

# Обработчик команды /mode
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if context.args:
        selected = context.args[0].lower()
        if selected in MODES:
            user_modes[user_id] = selected
            await update.message.reply_text(f"✅ Режим общения изменён на *{selected}*", parse_mode="Markdown")
            return
    await update.message.reply_text("❗ Укажи режим: /mode [default|support|motivation|philosophy|humor]")

# Обработчик текстовых сообщений
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

# Обработчик голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пока не умею расшифровывать голос. Напиши текстом 💬")

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

# Обработка неизвестных команд
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Я не знаю такой команды. Напиши /help, чтобы увидеть, что я умею.")

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

# Регистрируем все обработчики
handlers = [
    CommandHandler("start", start),
    CommandHandler("reset", reset),
    CommandHandler("help", help_command),
    CommandHandler("about", about),
    CommandHandler("mode", mode),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mode_choice),  # заменили на обработку и выбора режима и чата
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.COMMAND, unknown_command),
]
