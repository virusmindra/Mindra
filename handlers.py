# handlers.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import TELEGRAM_BOT_TOKEN, client
from history import load_history, save_history, trim_history
import random
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from goals import add_goal
from goals import get_goals

PREMIUM_USERS = {"7775321566"}  # замени на свой Telegram ID

premium_tasks = [
    "🧘 Проведи 10 минут в тишине. Просто сядь, закрой глаза и подыши. Отметь, какие мысли приходят.",
    "📓 Запиши 3 вещи, которые ты ценишь в себе. Не торопись, будь честен(на).",
    "💬 Позвони другу или родному человеку и просто скажи, что ты о нём думаешь.",
    "🧠 Напиши небольшой текст о себе из будущего — кем ты хочешь быть через 3 года?",
]

async def premium_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id in PREMIUM_USERS:
        task = random.choice(premium_tasks)
        await update.message.reply_text(f"✨ *Твоё премиум-задание на сегодня:*\n\n{task}", parse_mode="Markdown")
    else:
        keyboard = [
            [InlineKeyboardButton("💎 Узнать о подписке", url="https://t.me/твойботилилендинг")]
        ]
        await update.message.reply_text(
            "🔒 Эта функция доступна только подписчикам Mindra+.\n"
            "Подписка открывает доступ к уникальным заданиям и функциям ✨",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
# Обработчик команды /goal
async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("✏️ Чтобы поставить цель, напиши так:\n/goal Прочитать 10 страниц книги")
        return

    goal_text = " ".join(context.args)
    add_goal(user_id, goal_text)
    await update.message.reply_text(f"🎯 Цель добавлена: *{goal_text}*", parse_mode="Markdown")
    
# /goals — показать список целей
async def show_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    goals = get_goals(user_id)

    if not goals:
        await update.message.reply_text("🎯 У тебя пока нет целей. Добавь первую с помощью /goal")
        return

    reply = "📋 *Твои цели:*\n\n"
    for idx, goal in enumerate(goals, 1):
        status = "✅" if goal["done"] else "🔸"
        reply += f"{idx}. {status} {goal['text']}\n"

    await update.message.reply_markdown(reply)

# Загрузка истории и режимов
conversation_history = load_history()
user_modes = {}

# Режимы общения
MODES = {
    "default": "Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra.",
    "support": "Ты — чуткий и добрый AI-друг, который всегда выслушает и поддержит. Помогай пользователю почувствовать себя лучше.",
    "motivation": "Ты — воодушевляющий коуч и поддерживающий компаньон. Помогай пользователю поверить в себя и двигаться вперёд.",
    "philosophy": "Ты — глубокий собеседник с философским подходом. Помогай пользователю осмыслить чувства и ситуации в жизни.",
    "humor": "Ты — весёлый и добрый AI-друг с лёгким чувством юмора. Поддержи пользователя, добавив немного позитива."
}

# Пул заданий дня (для бесплатных пользователей)
DAILY_TASKS = [
    "✨ Запиши 3 вещи, за которые ты благодарен(на) сегодня.",
    "🚶‍♂️ Прогуляйся 10 минут без телефона. Просто дыши и наблюдай.",
    "📝 Напиши короткий список целей на завтра.",
    "🌿 Попробуй провести 30 минут без соцсетей. Как ощущения?",
    "💧 Выпей стакан воды и улыбнись себе в зеркало. Ты справляешься!"
]

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": MODES["default"]}]
        save_history(conversation_history)
    await update.message.reply_text("Привет, я Mindra 💜 Поддержка, мотивация и немного психолог. Готов поговорить!")

# Обработчик команды /reset
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text("История очищена. Начнём сначала ✨")

# Обработчик команды /mode (с кнопками)
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎧 Поддержка", callback_data="mode_support")],
        [InlineKeyboardButton("🌸 Мотивация", callback_data="mode_motivation")],
        [InlineKeyboardButton("🧘 Психолог", callback_data="mode_philosophy")],
        [InlineKeyboardButton("🎭 Юмор", callback_data="mode_humor")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери стиль общения Mindra ✨", reply_markup=reply_markup)

# Обработка выбора режима по кнопке
async def handle_mode_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    mode_key = query.data.replace("mode_", "")

    if mode_key in MODES:
        user_modes[user_id] = mode_key
        conversation_history[user_id] = [{"role": "system", "content": MODES[mode_key]}]
        save_history(conversation_history)
        await query.answer()
        await query.edit_message_text(f"✅ Режим общения изменён на *{mode_key}*!", parse_mode="Markdown")

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
        "/task — задание на день\n"
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

# /task — задание на день
async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = random.choice(DAILY_TASKS)
    await update.message.reply_text(f"🎯 Задание на день:\n{task}")

# Неизвестные команды
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Я не знаю такой команды. Напиши /help, чтобы увидеть, что я умею.")

# Обработчики
handlers = [
    CommandHandler("start", start),
    CommandHandler("reset", reset),
    CommandHandler("help", help_command),
    CommandHandler("about", about),
    CommandHandler("mode", mode),
    CommandHandler("task", task),
    CommandHandler("premium_task", premium_task),
    CommandHandler("goal", goal),
    CommandHandler("goals", show_goals),
    CallbackQueryHandler(handle_mode_choice),
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.COMMAND, unknown_command)
]
