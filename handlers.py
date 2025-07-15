import os
import json
import random
import re
import logging
import openai
import tempfile
import aiohttp
import subprocess
import ffmpeg
import traceback
import asyncio
import pytz
import shutil
from config import PREMIUM_USERS
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from habits import add_habit, get_habits, mark_habit_done, delete_habit
from stats import get_stats
from telegram.constants import ChatAction, ParseMode
from config import client, TELEGRAM_BOT_TOKEN
from history import load_history, save_history, trim_history
from goals import add_goal, get_goals, mark_goal_done, delete_goal
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from storage import add_goal_for_user, get_goals_for_user, mark_goal_done
from random import randint, choice

# Глобальные переменные
user_last_seen = {}
user_last_prompted = {}

openai.api_key = os.getenv("OPENAI_API_KEY")

GOALS_FILE = Path("user_goals.json")
    
def load_goals():
    if GOALS_FILE.exists():
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_goals(data):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_goal_for_user(user_id, goal_text):
    user_id = str(user_id)
    data = load_goals()
    if user_id not in data:
        data[user_id] = []
    if goal_text not in data[user_id]:
        data[user_id].append(goal_text)
    save_goals(data)

def get_goals_for_user(user_id):
    user_id = str(user_id)
    data = load_goals()
    return data.get(user_id, [])

# 🔍 Определение, содержит ли сообщение цель или привычку
def is_goal_like(text):
    keywords = [
        "хочу", "планирую", "мечтаю", "цель", "начну", "запишусь", "начать",
        "буду делать", "постараюсь", "нужно", "пора", "начинаю", "собираюсь",
        "решил", "решила", "буду", "привычка", "добавить"
    ]
    return any(kw in text.lower() for kw in keywords)

async def handle_add_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if "|" in query.data:
        _, goal_text = query.data.split("|", 1)
    else:
        goal_text = context.chat_data.get("goal_candidate", "Моя цель")

    add_goal_for_user(user_id, goal_text)

    await query.message.reply_text(f"✨ Готово! Я записала это как твою цель 💪\n\n👉 {goal_text}")

IDLE_MESSAGES = [
    "💌 Я немного скучаю. Расскажешь, как дела?",
    "🌙 Надеюсь, у тебя всё хорошо. Я здесь, если что 🫶",
    "✨ Мне нравится с тобой общаться. Вернёшься позже?",
    "😊 Просто хотела напомнить, что ты классный(ая)",
    "🤍 Просто хотела напомнить — ты не один(а), я рядом.",
    "🍵 Если бы могла, я бы сейчас заварила тебе чай...",
]

async def send_idle_reminders_compatible(app):
    logging.info(f"👥 user_last_seen: {user_last_seen}")
    logging.info(f"🧠 user_last_prompted: {user_last_prompted}")
    now = datetime.now(timezone.utc)
    logging.info("⏰ Проверка неактивных пользователей...")

    for user_id, last_seen in user_last_seen.items():
        logging.info(f"👀 {user_id=} | {last_seen=} | прошло: {(now - last_seen).total_seconds() / 60:.1f} мин.")

        if (now - last_seen) > timedelta(minutes=1):  # Упростим до 1 минуты для теста
            try:
                await app.bot.send_message(chat_id=user_id, text="✨ Привет, давно не болтали! Как ты?")
                user_last_seen[user_id] = now
                logging.info(f"📨 Напоминание отправлено пользователю {user_id}")
            except Exception as e:
                logging.error(f"❌ Ошибка при отправке сообщения пользователю {user_id}: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_last_seen
    user_id = update.effective_user.id
    user_last_seen[user_id] = datetime.now(timezone.utc)
    logging.info(f"✅ user_last_seen обновлён в voice для {user_id}")
    try:
        message = update.message

        # 1. Получаем файл
        file = await context.bot.get_file(message.voice.file_id)
        file_path = f"/tmp/{file.file_unique_id}.oga"
        mp3_path = f"/tmp/{file.file_unique_id}.mp3"
        await file.download_to_drive(file_path)

        # 2. Конвертируем в mp3
        subprocess.run([
            "ffmpeg", "-i", file_path, "-ar", "44100", "-ac", "2", "-b:a", "192k", mp3_path
        ], check=True)

        # 3. Распознаём голос
        with open(mp3_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )

        user_input = result.strip()
        topic = detect_topic(user_input)
        if topic:
            save_user_context(context, topic=topic)

        await message.reply_text(f"📝 Ты сказал(а): {user_input}")

        # 4. Эмпатичная реакция
        reaction = detect_emotion_reaction(user_input)

        # 5. История для ChatGPT
        system_prompt = {
            "role": "system",
            "content": (
                "Ты — эмпатичный AI-собеседник, как подруга или психолог. "
                "Ответь на голосовое сообщение пользователя с поддержкой, теплом и пониманием. "
                "Добавляй эмоджи, если уместно — 😊, 💜, 🤗, ✨ и т.п."
            )
        }

        history = [system_prompt, {"role": "user", "content": user_input}]
        history = trim_history(history)

        # 6. Ответ от ChatGPT
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=history
        )
        reply = completion.choices[0].message.content.strip()

        # 7. Добавляем отсылку к теме (если есть)
        reference = get_topic_reference(context)
        if reference:
            reply = f"{reply}\n\n{reference}"

        # 8. Добавляем follow-up вопрос
        reply = insert_followup_question(reply, user_input)

        # 9. Добавляем эмпатичную реакцию
        reply = reaction + reply

        # 10. Кнопки
        goal_text = user_input if is_goal_like(user_input) else None
        buttons = generate_post_response_buttons(goal_text=goal_text)

        await update.message.reply_text(reply, reply_markup=buttons)

    except Exception as e:
        print(f"❌ Ошибка при обработке голосового: {e}")
        await update.message.reply_text("❌ Ошибка при распознавании голоса, попробуй позже.")
        
premium_tasks = [
    "🧘 Проведи 10 минут в тишине. Просто сядь, закрой глаза и подыши. Отметь, какие мысли приходят.",
    "📓 Запиши 3 вещи, которые ты ценишь в себе. Не торопись, будь честен(на).",
    "💬 Позвони другу или родному человеку и просто скажи, что ты о нём думаешь.",
    "🧠 Напиши небольшой текст о себе из будущего — кем ты хочешь быть через 3 года?",
]

def insert_followup_question(reply, user_input):
    topic = detect_topic(user_input)
    if not topic:
        return reply

    questions_by_topic = {
        "спорт": [
            "А ты сейчас занимаешься чем-то активным?",
            "Хочешь, составим тебе лёгкий челлендж?",
            "Какая тренировка тебе приносит больше всего удовольствия?"
        ],
        "любовь": [
            "А что ты чувствуешь к этому человеку сейчас?",
            "Хочешь рассказать, что было дальше?",
            "Как ты понимаешь, что тебе важно в отношениях?"
        ],
        "работа": [
            "А чем тебе нравится (или не нравится) твоя работа?",
            "Ты хочешь что-то поменять в этом?",
            "Есть ли у тебя мечта, связанная с карьерой?"
        ],
        "деньги": [
            "Как ты сейчас чувствуешь себя в плане финансов?",
            "Что бы ты хотел улучшить?",
            "Есть ли у тебя финансовая цель?"
        ],
        "одиночество": [
            "А чего тебе сейчас больше всего не хватает?",
            "Хочешь, я просто побуду рядом?",
            "А как ты обычно проводишь время, когда тебе одиноко?"
        ],
        "мотивация": [
            "Что тебя вдохновляет прямо сейчас?",
            "Какая у тебя сейчас цель?",
            "Что ты хочешь почувствовать, когда достигнешь этого?"
        ],
        "здоровье": [
            "Как ты заботишься о себе в последнее время?",
            "Были ли у тебя моменты отдыха сегодня?",
            "Что для тебя значит быть в хорошем состоянии?"
        ],
        "тревога": [
            "Что вызывает у тебя больше всего волнения сейчас?",
            "Хочешь, я помогу тебе с этим справиться?",
            "Ты хочешь просто выговориться?"
        ],
        "друзья": [
            "С кем тебе хочется сейчас поговорить по-настоящему?",
            "Как ты обычно проводишь время с близкими?",
            "Ты хотел бы, чтобы кто-то был рядом прямо сейчас?"
        ],
        "цели": [
            "Какая цель тебе сейчас ближе всего по духу?",
            "Хочешь, я помогу тебе её распланировать?",
            "С чего ты бы хотел начать сегодня?"
        ],
    }

    questions = questions_by_topic.get(topic.lower())
    if questions:
        follow_up = random.choice(questions)
        return reply.strip() + "\n\n" + follow_up
    return reply

async def send_daily_reminder(context):
    try:
        for user_id in PREMIUM_USERS:
            await context.bot.send_message(chat_id=user_id, text="👋 Привет! Как ты сегодня? Я скучала. Расскажи, как дела?")
    except Exception as e:
        print(f"❌ Ошибка с напоминанием: {e}")

def detect_emotion_reaction(user_input: str) -> str:
    text = user_input.lower()
    if any(word in text for word in ["ура", "сделал", "сделала", "получилось", "рад", "рада", "наконец", "круто", "кайф", "горжусь"]):
        return "🥳 Вау, это звучит потрясающе! Я так рада за тебя! 💜\n\n"
    elif any(word in text for word in ["плохо", "тяжело", "устал", "устала", "раздражает", "не знаю", "выгорание", "одиноко", "грустно", "сложно"]):
        return "😔 Понимаю тебя… Я рядом, правда. Ты не один(а). 💜\n\n"
    elif any(word in text for word in ["стресс", "нервы", "не спал", "не спала", "перегруз", "паника"]):
        return "🫂 Дыши глубже. Всё пройдёт. Давай разберёмся вместе. 🤍\n\n"
    return ""
    
def detect_topic_and_react(user_input: str) -> str:
    text = user_input.lower()

    # Тема: романтика / отношения
    if re.search(r"\b(влюбил|влюблена|люблю|девушк|парн|отношен|встретил|свидани|поцелу|встреча|расстался|разошлись|флирт|переписк)\b", text):
        return "💘 Это звучит очень трогательно. Любовные чувства — это всегда волнительно. Хочешь рассказать подробнее, что происходит?"

    # Тема: одиночество
    elif re.search(r"\b(один|одна|одинок|некому|никто не|чувствую себя один)\b", text):
        return "🫂 Иногда это чувство может накрывать... Но знай: ты не один и не одна. Я рядом. 💜"

    # Тема: работа / стресс
    elif re.search(r"\b(работа|устал|босс|давлени|коллег|увольн|смена|заработ|не выношу|задолбал)\b", text):
        return "🧑‍💼 Работа может быть выматывающей. Ты не обязан(а) всё тянуть в одиночку. Я здесь, если хочешь выговориться."

    # Тема: спорт / успех
    elif re.search(r"\b(зал|спорт|бег|жим|гантел|тренир|добился|успех|100кг|тренировка|похуд)\b", text):
        return "🏆 Молодец! Это важный шаг на пути к себе. Как ты себя чувствуешь после этого достижения?"

    # Тема: семья
    elif re.search(r"\b(мама|папа|семь|родител|сестра|брат|дед|бабушк)\b", text):
        return "👨‍👩‍👧‍👦 Семья может давать и тепло, и сложности. Я готов(а) выслушать — расскажи, если хочется."

    # Тема: мотивация / цели
    elif re.search(r"\b(мотивац|цель|развитие|дух|успех|медитац|саморазвити|осознанн|рост|путь)\b", text):
        return "🌱 Это здорово, что ты стремишься к развитию. Давай обсудим, как я могу помочь тебе на этом пути."

    return ""

# Примеры
example_1 = detect_topic_and_react("Я сегодня ходил в зал и выжал 100кг от груди")
example_2 = detect_topic_and_react("Я не знаю, что делать, моя девушка странно себя ведёт")
example_1, example_2

def detect_topic(text: str) -> str:
    text = text.lower()
    if re.search(r"\b(девушк|люблю|отношен|парн|флирт|расст|поцелуй|влюб)\b", text):
        return "отношения"
    elif re.search(r"\b(работа|босс|смена|коллег|заработ|устал|стресс)\b", text):
        return "работа"
    elif re.search(r"\b(зал|спорт|тренир|бег|гантел|похуд)\b", text):
        return "спорт"
    elif re.search(r"\b(одинок|один|некому|никто не)\b", text):
        return "одиночество"
    elif re.search(r"\b(цель|развитие|мотивац|успех|саморазв)\b", text):
        return "саморазвитие"
    return ""

def get_topic_reference(context) -> str:
    topic = context.user_data.get("last_topic")
    if topic == "отношения":
        return "💘 Ты упоминал(а) недавно про отношения... Всё в порядке?"
    elif topic == "работа":
        return "💼 Как дела на работе? Я помню, тебе было тяжело."
    elif topic == "спорт":
        return "🏋️‍♂️ Как у тебя со спортом, продолжил(а)?"
    elif topic == "одиночество":
        return "🤗 Помни, что ты не один(одна), даже если так казалось."
    elif topic == "саморазвитие":
        return "🌱 Продолжаешь развиваться? Это вдохновляет!"
    return ""

def save_user_context(context, topic: str = None, emotion: str = None):
    if topic:
        topics = context.user_data.get("topics", [])
        if topic not in topics:
            topics.append(topic)
            context.user_data["topics"] = topics

    if emotion:
        context.user_data["last_emotion"] = emotion


def get_topic_reference(context) -> str:
    topics = context.user_data.get("topics", [])
    if not topics:
        return ""

    references = {
        "отношения": "Ты ведь раньше делился(ась) про чувства… Хочешь поговорить об этом подробнее? 💜",
        "одиночество": "Помню, ты чувствовал(а) себя одиноко… Я всё ещё здесь 🤗",
        "работа": "Ты рассказывал(а) про давление на работе. Как у тебя с этим сейчас?",
        "спорт": "Ты ведь начинал(а) тренироваться — продолжаешь? 🏋️",
        "семья": "Ты упоминал(а) про семью… Всё ли хорошо?",
        "мотивация": "Ты говорил(а), что хочешь развиваться. Что уже получилось? ✨"
    }

    matched_refs = []
    for topic in topics:
        for key in references:
            if key in topic.lower() and references[key] not in matched_refs:
                matched_refs.append(references[key])

    if matched_refs:
        return "\n\n".join(matched_refs[:2])  # максимум 2 отсылки
    return ""


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

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    goals = get_goals_for_user(user_id)

    if not goals:
        await update.message.reply_text("У тебя пока нет целей, которые можно отметить выполненными 😔")
        return

    buttons = [
        [InlineKeyboardButton(goal, callback_data=f"done_goal|{goal}")]
        for goal in goals
    ]

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Выбери цель, которую ты выполнил(а):", reply_markup=reply_markup)

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
    
async def show_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    goals = get_goals_for_user(user_id)  # Новая функция хранения

    if not goals:
        await update.message.reply_text("🎯 У тебя пока нет целей. Добавь первую с помощью /goal")
        return

    reply = "📋 *Твои цели:*\n\n"
    for idx, goal in enumerate(goals, 1):
        status = "✅" if goal.get("done") else "🔸"
        reply += f"{idx}. {status} {goal.get('text', '')}\n"

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

def generate_post_response_buttons(goal_text=None, include_reactions=True):
    buttons = []

    if include_reactions:
        buttons.append([
            InlineKeyboardButton("❤️ Спасибо", callback_data="react_thanks"),
        ])

    if goal_text:
        buttons.append([
            InlineKeyboardButton("📌 Добавить как цель", callback_data=f"add_goal|{goal_text}")
        ])
    if goal_text:
        buttons.append([
            InlineKeyboardButton("📋 Привычки", callback_data="show_habits"),
            InlineKeyboardButton("🎯 Цели", callback_data="show_goals")
        ])

    return InlineKeyboardMarkup(buttons)

async def handle_reaction_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "react_thanks":
        await query.message.reply_text("Всегда пожалуйста! 😊 Я рядом, если что-то захочешь обсудить 💜")

# Обработчик текстовых сообщений
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_last_seen
    user_id_int = update.effective_user.id
    user_last_seen[user_id_int] = datetime.now(timezone.utc)
    logging.info(f"✅ user_last_seen обновлён в chat для {user_id_int}")

    user_input = update.message.text
    user_id = str(update.effective_user.id)
    mode = user_modes.get(user_id, "default")

    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": MODES[mode] + " Всегда отвечай на том же языке, на котором пишет пользователь. Отвечай тепло, человечно, с эмпатией."}
        ]

    # 🔮 Эмпатичный стиль с эмоджи
    conversation_history[user_id].insert(1, {
        "role": "system",
        "content": (
            "Ты — доброжелательный и поддерживающий собеседник. "
            "Отвечай с теплотой и эмпатией. Добавляй эмоджи, если они подходят: 🤗, 💜, 😊, 😢, ✨, 🙌, ❤️. "
            "Если человек делится радостью — порадуйся вместе с ним. "
            "Если грустью — поддержи, как друг. Будь чуткой и живой."
        )
    })

    conversation_history[user_id].append({"role": "user", "content": user_input})
    trimmed_history = trim_history(conversation_history[user_id])

    try:
        # 💬 Показываем "печатает..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=trimmed_history
        )
        reply = response.choices[0].message.content
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)
        reaction = detect_emotion_reaction(user_input) + detect_topic_and_react(user_input)
        reply = reaction + reply
        await update.message.reply_text(reply, reply_markup=generate_post_response_buttons())

    except Exception as e:
        await update.message.reply_text("🥺 Упс, я немного завис... Попробуй позже, хорошо?")
        print(f"❌ Ошибка OpenAI: {e}")

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

# Список всех команд/обработчиков для экспорта
handlers = [
    CommandHandler("start", start),
    CommandHandler("help", help_command),
    CommandHandler("about", about),
    CommandHandler("mode", mode),
    CommandHandler("reset", reset),
    CommandHandler("goal", goal),
    CommandHandler("goals", show_goals),
    CommandHandler("habit", habit),
    CommandHandler("habits", habits_list),
    CommandHandler("done", mark_done),
    CommandHandler("delete", delete_goal_command),
    CommandHandler("task", task),
    CommandHandler("premium_task", premium_task),
    CommandHandler("stats", stats_command),
    CallbackQueryHandler(goal_buttons_handler, pattern="^(create_goal|show_goals|create_habit|show_habits)$"),
    CallbackQueryHandler(handle_mode_choice, pattern="^mode_"),  # pattern для /mode кнопок
    CallbackQueryHandler(handle_reaction_button, pattern="^react_"),
    CallbackQueryHandler(handle_add_goal_callback, pattern="^add_goal\\|"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.COMMAND, unknown_command),
]

__all__ = [
    "handlers",
    "goal_buttons_handler",
    "premium_task",
    "track_users",
    "error_handler",
    "handle_voice",
    "send_daily_reminder",
    "handle_add_goal_callback",
    "check_and_send_warm_messages",
    "user_last_seen",
    "user_last_prompted",
]
