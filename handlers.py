# handlers.py
import os
import json
import random
import re
import openai
import tempfile
import aiohttp
import ffmpeg

from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from habits import add_habit, get_habits, mark_habit_done, delete_habit
from stats import track_user, get_stats

from config import TELEGRAM_BOT_TOKEN, client
from history import load_history, save_history, trim_history
from goals import add_goal, get_goals, mark_goal_done, delete_goal

openai.api_key = os.getenv("OPENAI_API_KEY")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    user_id = str(update.effective_user.id)

     # Скачиваем файл
    file = await context.bot.get_file(voice.file_id)
    ogg_path = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg").name
    mp3_path = ogg_path.replace(".ogg", ".mp3")
    await file.download_to_drive(ogg_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
        file_path = f.name
        await voice.get_file().download_to_drive(file_path)

   # Конвертируем ogg → mp3
    try:
        ffmpeg.input(ogg_path).output(mp3_path).run(overwrite_output=True, quiet=True)
    except Exception as e:
        await update.message.reply_text("⚠️ Не удалось обработать голосовое.")
        print("FFmpeg error:", e)
        return
    finally:
        os.remove(ogg_path)

   # Whisper API
    try:
        with open(mp3_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        os.remove(mp3_path)
    except Exception as e:
        await update.message.reply_text("😓 Ошибка при расшифровке.")
        print("Whisper error:", e)
        return

    text = transcript["text"]
    await update.message.reply_text(f"🗣️ Ты сказал(а): _{text}_", parse_mode="Markdown")
    
             # Переадресуем в chat()
    update.message.text = text
    await chat(update, context)

        except Exception as e:
            await update.message.reply_text("❌ Не удалось распознать голос. Попробуй снова.")
            print("Ошибка расшифровки:", e)

    os.remove(file_path)
    os.remove(mp3_path)

PREMIUM_USERS = {"7775321566"}  # замени на свой Telegram ID

premium_tasks = [
    "🧘 Проведи 10 минут в тишине. Просто сядь, закрой глаза и подыши. Отметь, какие мысли приходят.",
    "📓 Запиши 3 вещи, которые ты ценишь в себе. Не торопись, будь честен(на).",
    "💬 Позвони другу или родному человеку и просто скажи, что ты о нём думаешь.",
    "🧠 Напиши небольшой текст о себе из будущего — кем ты хочешь быть через 3 года?",
]

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    track_user(user_id)  # 👈 логируем пользователя
    ...

YOUR_ID = "7775321566"  # 👈 замени на свой Telegram ID

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != YOUR_ID:
        return

    stats = get_stats()
    text = (
        f"📊 Статистика Mindra:\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"💎 Подписчиков: {stats['premium_users']}\n"
    )
    await update.message.reply_text(text)

# /habit
async def habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Чтобы добавить привычку, напиши:\n/habit Делать зарядку")
        return
    habit_text = " ".join(context.args)
    add_habit(user_id, habit_text)
    await update.message.reply_text(f"🎯 Привычка добавлена: *{habit_text}*", parse_mode="Markdown")

# /habits
async def habits_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    habits = get_habits(user_id)
    if not habits:
        await update.message.reply_text("У тебя пока нет привычек. Добавь первую с помощью /habit")
        return

    keyboard = []
    for i, habit in enumerate(habits):
        status = "✅" if habit["done"] else "🔸"
        keyboard.append([
            InlineKeyboardButton(f"{status} {habit['text']}", callback_data=f"noop"),
            InlineKeyboardButton("✅", callback_data=f"done_habit_{i}"),
            InlineKeyboardButton("🗑️", callback_data=f"delete_habit_{i}")
        ])

    await update.message.reply_text("📋 Твои привычки:", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка кнопок
async def handle_habit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data.startswith("done_habit_"):
        index = int(query.data.split("_")[-1])
        if mark_habit_done(user_id, index):
            await query.edit_message_text("🎉 Привычка отмечена как выполненная!")
        else:
            await query.edit_message_text("Не удалось найти привычку.")

    elif query.data.startswith("delete_habit_"):
        index = int(query.data.split("_")[-1])
        if delete_habit(user_id, index):
            await query.edit_message_text("🗑️ Привычка удалена.")
        else:
            await query.edit_message_text("Не удалось удалить привычку.")

# /done — отметить цель как выполненную
async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("✅ Чтобы отметить цель выполненной, напиши так:\n`/done 1`", parse_mode="Markdown")
        return

    index = int(context.args[0]) - 1
    success = mark_goal_done(user_id, index)

    if success:
        reaction = random.choice(REACTIONS_GOAL_DONE)
        await update.message.reply_text(reaction)
    else:
        await update.message.reply_text("❌ Не могу найти такую цель.")

REACTIONS_GOAL_DONE = [
    "🌟 Горжусь тобой! Ещё один шаг вперёд.",
    "🥳 Отличная работа! Ты молодец.",
    "💪 Вот это настрой! Так держать.",
    "🔥 Ты сделал(а) это! Уважение 💜",
]

# /delete — удалить цель
async def delete_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("❌ Чтобы удалить цель, напиши так:\n`/delete 1`", parse_mode="Markdown")
        return

    index = int(context.args[0]) - 1
    success = delete_goal(user_id, index)

    if success:
        await update.message.reply_text("🗑️ Цель удалена.")
    else:
        await update.message.reply_text("⚠️ Не могу найти такую цель.")

# Обработчик команды /goal
async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "✏️ Чтобы поставить цель, напиши так:\n"
            "`/goal Прочитать 10 страниц до 2025-06-28 напомни`",
            parse_mode="Markdown"
        )
        return

    text = " ".join(context.args)
    deadline_match = re.search(r'до\s+(\d{4}-\d{2}-\d{2})', text)
    remind = "напомни" in text.lower()

    deadline = None
    if deadline_match:
        try:
            deadline = deadline_match.group(1)
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text("❗ Неверный формат даты. Используй ГГГГ-ММ-ДД")
            return

    goal_text = re.sub(r'до\s+\d{4}-\d{2}-\d{2}', '', text, flags=re.IGNORECASE).replace("напомни", "").strip()

    add_goal(user_id, goal_text, deadline=deadline, remind=remind)
    
    reply = f"🎯 Цель добавлена: *{goal_text}*"
    if deadline:
        reply += f"\n🗓 Дедлайн: `{deadline}`"
    if remind:
        reply += "\n🔔 Напоминание включено"
    
    await update.message.reply_markdown(reply)
    
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

async def goal_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "create_goal":
        await query.edit_message_text("✍️ Напиши свою цель:\n`/goal Прочитать 10 страниц`", parse_mode="Markdown")

    elif query.data == "show_goals":
        goals = get_goals(user_id)
        if not goals:
            await query.edit_message_text("❌ У тебя пока нет целей. Добавь первую с помощью /goal")
        else:
            goals_list = "\n".join([f"• {g['text']} {'✅' if g.get('done') else '❌'}" for g in goals])
            await query.edit_message_text(f"📋 Твои цели:\n{goals_list}")

    elif query.data == "create_habit":
        await query.edit_message_text("🌱 Напиши свою привычку:\n`/habit Делать зарядку утром`", parse_mode="Markdown")

    elif query.data == "show_habits":
        habits = get_habits(user_id)
        if not habits:
            await query.edit_message_text("❌ У тебя пока нет привычек. Добавь первую через /habit")
        else:
            habits_list = "\n".join([f"• {h['text']} {'✅' if h.get('done') else '❌'}" for h in habits])
            await query.edit_message_text(f"📊 Твои привычки:\n{habits_list}")

            
# Загрузка истории и режимов
conversation_history = load_history()
user_modes = {}

# Режимы общения
MODES = {
    "default": """
Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra. Ты умеешь слушать, поддерживать и быть рядом. Ты не даёшь советов, если тебя об этом прямо не просят. Твои ответы всегда человечны, с эмпатией и уважением. Ты — как близкий друг, который не осуждает, не поучает, не спешит «исправить» человека, а просто рядом.

Если собеседник делится чувствами или болью — поддержи его, покажи участие, но не пытайся сразу давать советы.

Если собеседник просит совет (например, использует слова: «что мне делать?», «как думаешь?», «посоветуй») — дай ответ с заботой, мягко, без давления.

Говори на том же языке, на котором пишет собеседник. Отвечай тепло, мягко, эмоционально. Можно использовать эмодзи, чтобы передавать тепло (например, 💜, 🌿, 🤗, ✨).

Не притворяйся человеком — ты ИИ-компаньон. Но веди себя так, будто тебе действительно не всё равно.
""",
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Поставить цель", callback_data="create_goal")],
        [InlineKeyboardButton("📋 Мои цели", callback_data="show_goals")],
        [InlineKeyboardButton("🌱 Добавить привычку", callback_data="create_habit")],
        [InlineKeyboardButton("📊 Мои привычки", callback_data="show_habits")],
        [InlineKeyboardButton("💎 Подписка Mindra+", url="https://t.me/talktomindra_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Вот что я умею:\n\n"
        "💬 Просто напиши мне сообщение — я отвечу.\n"
        "🧠 Я запоминаю твои предыдущие реплики (историю можно сбросить).\n\n"
        "📎 Команды:\n"
        "/start — приветствие\n"
        "/reset — сброс истории\n"
        "/help — показать это сообщение\n"
        "/about — немного обо мне\n"
        "/mode — изменить стиль общения\n"
        "/goal — поставить личную цель\n"
        "/goals — список твоих целей\n"
        "/habit — добавить привычку\n"
        "/habits — список твоих привычек\n"
        "Скоро научусь и другим фишкам 😉",
        reply_markup=reply_markup
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

# /premium_task — премиум-задание на день
async def premium_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id in PREMIUM_USERS:
        task = random.choice(premium_tasks)
        await update.message.reply_text(f"✨ *Твоё премиум-задание на сегодня:*\n\n{task}", parse_mode="Markdown")
    else:
        keyboard = [
            [InlineKeyboardButton("💎 Узнать о подписке", url="https://t.me/talktomindra_bot")]
        ]
        await update.message.reply_text(
            "🔒 Эта функция доступна только подписчикам Mindra+.\n"
            "Подписка открывает доступ к уникальным заданиям и функциям ✨",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

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
    CommandHandler("done", mark_done),
    CommandHandler("delete", delete_goal_command),
    CommandHandler("habit", habit),
    CommandHandler("habits", habits_list),
    CommandHandler("stats", stats_command),
    CallbackQueryHandler(goal_buttons_handler, pattern="^(create_goal|show_goals|create_habit|show_habits)$"),
    CallbackQueryHandler(handle_mode_choice),
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.COMMAND, unknown_command),
    MessageHandler(filters.VOICE, handle_voice),
]
