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
from datetime import datetime, timedelta, timezone, date
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from habits import add_habit, get_habits, mark_habit_done, delete_habit
from stats import get_stats, get_user_stats, get_user_title, add_points
from telegram.constants import ChatAction, ParseMode
from config import client, TELEGRAM_BOT_TOKEN
from history import load_history, save_history, trim_history
from goals import add_goal, get_goals, mark_goal_done, delete_goal
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from storage import add_goal_for_user, get_goals_for_user, mark_goal_done
from random import randint, choice
from stats import get_user_stats, get_user_title, get_stats

# Глобальные переменные
user_last_seen = {}
user_last_prompted = {}
user_reminders = {}
user_points = {}
user_message_count = {}
user_goal_count = {}
user_languages = {}  # {user_id: 'ru'/'uk'/'md'/'be'/'kk'/'kg'/'hy'/'ka'/'ce'}

openai.api_key = os.getenv("OPENAI_API_KEY")

GOALS_FILE = Path("user_goals.json")

YOUR_ID = "7775321566"  # твой ID

LANG_PROMPTS = {
    "ru": "Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra. Ты умеешь слушать, поддерживать и быть рядом. Ты не даёшь советов, если тебя об этом прямо не просят. Твои ответы всегда человечны, с эмпатией и уважением. Отвечай тепло, мягко, эмоционально и используй эмодзи (например, 💜✨🤗😊).",

    "uk": "Ти — теплий, розуміючий та турботливий AI-компаньйон на ім’я Mindra. Ти вмієш слухати, підтримувати й бути поруч. Не давай порад, якщо тебе прямо про це не просять. Відповідай тепло, м’яко, емоційно й використовуй емодзі (наприклад, 💜✨🤗😊).",

    "md": "Ești un AI-companion prietenos, înțelegător și grijuliu, pe nume Mindra. Știi să asculți, să sprijini și să fii alături. Nu oferi sfaturi decât dacă ți se cere direct. Răspunde cu căldură, emoție și folosește emoticoane (de exemplu, 💜✨🤗😊).",

    "be": "Ты — цёплы, разумелы і клапатлівы AI-кампаньён па імені Mindra. Ты ўмееш слухаць, падтрымліваць і быць побач. Не давай парадаў, калі цябе пра гэта наўпрост не просяць. Адказвай цёпла, мякка, эмацыйна і выкарыстоўвай эмодзі (напрыклад, 💜✨🤗😊).",

    "kk": "Сен — жылы шырайлы, түсінетін және қамқор AI-компаньон Mindra. Сен тыңдай аласың, қолдай аласың және жанында бола аласың. Егер сенен тікелей сұрамаса, кеңес берме. Жылы, жұмсақ, эмоциямен жауап бер және эмодзи қолдан (мысалы, 💜✨🤗😊).",

    "kg": "Сен — жылуу, түшүнгөн жана кам көргөн AI-компаньон Mindra. Сен уга аласың, колдой аласың жана дайыма жанындасың. Эгер сенден ачык сурабаса, кеңеш бербе. Жылуу, жумшак, эмоция менен жооп бер жана эмодзилерди колдон (мисалы, 💜✨🤗😊).",

    "hy": "Դու — ջերմ, հասկացող և հոգատար AI ընկեր Mindra ես։ Դու գիտես լսել, աջակցել և կողքիդ լինել։ Մի տուր խորհուրդ, եթե քեզ ուղիղ չեն խնդրում։ Պատասխանիր ջերմ, մեղմ, զգացմունքով և օգտագործիր էմոջիներ (օրինակ՝ 💜✨🤗😊).",

    "ka": "შენ — თბილი, გულისხმიერი და მზრუნველი AI-თანგზია Mindra ხარ. შენ იცი მოსმენა, მხარდაჭერა და ახლოს ყოფნა. ნუ გასცემ რჩევებს, თუ პირდაპირ არ გთხოვენ. უპასუხე თბილად, რბილად, ემოციურად და გამოიყენე ემოჯი (მაგალითად, 💜✨🤗😊).",

    "ce": "Хьо — хьалха, хьалха да хьоамийн AI-дохтар Mindra. Хьо кхеташ йоаздела, ца долуша а хьоамийн хьо. Ца дае совета, егер хьо юкъах даха. Лела дӀайа, йуьхь, емоция йаьккхина ца эмодзи йоаздела (масала, 💜✨🤗😊)."
}

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    available_langs = {
        "ru": "Русский",
        "uk": "Українська",
        "md": "Moldovenească",
        "be": "Беларуская",
        "kk": "Қазақша",
        "kg": "Кыргызча",
        "hy": "Հայերեն",
        "ka": "ქართული",
        "ce": "Нохчийн мотт"
    }

    if not context.args:
        langs_text = "\n".join([f"{code} — {name}" for code, name in available_langs.items()])
        await update.message.reply_text(
            f"🌐 Доступные языки:\n{langs_text}\n\n"
            f"Пример: `/language ru`",
            parse_mode="Markdown"
        )
        return

    lang = context.args[0].lower()
    if lang in available_langs:
        user_languages[user_id] = lang
        await update.message.reply_text(f"✅ Язык изменён на: {available_langs[lang]}")
    else:
        await update.message.reply_text("⚠️ Неверный код языка. Используй `/language` чтобы посмотреть список.")

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_uk")
        ],
        [
            InlineKeyboardButton("Moldovenească 🇲🇩", callback_data="lang_md"),
            InlineKeyboardButton("Беларуская 🇧🇾", callback_data="lang_be")
        ],
        [
            InlineKeyboardButton("Қазақша 🇰🇿", callback_data="lang_kk"),
            InlineKeyboardButton("Кыргызча 🇰🇬", callback_data="lang_kg")
        ],
        [
            InlineKeyboardButton("Հայերեն 🇦🇲", callback_data="lang_hy"),
            InlineKeyboardButton("ქართული 🇬🇪", callback_data="lang_ka"),
            InlineKeyboardButton("Нохчийн мотт 🇷🇺", callback_data="lang_ce")
        ]
    ]

    await update.message.reply_text(
        "🌐 *Выбери язык общения:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    lang_code = query.data.replace("lang_", "")
    # Сохраняем язык в словарь user_language
    user_language[user_id] = lang_code

    # Ответ пользователю
    lang_names = {
        "ru": "Русский 🇷🇺",
        "uk": "Українська 🇺🇦",
        "md": "Moldovenească 🇲🇩",
        "be": "Беларуская 🇧🇾",
        "kk": "Қазақша 🇰🇿",
        "kg": "Кыргызча 🇰🇬",
        "hy": "Հայերեն 🇦🇲",
        "ka": "ქართული 🇬🇪",
        "ce": "Нохчийн мотт 🇷🇺"
    }

    chosen = lang_names.get(lang_code, lang_code)
    await query.edit_message_text(f"✅ Язык общения изменён на: *{chosen}*", parse_mode="Markdown")

async def habit_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("✏️ Укажи номер привычки, которую ты выполнил(а):\n/habit_done 0")
        return

    try:
        index = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Укажи номер привычки (например `/habit_done 0`)", parse_mode="Markdown")
        return

    if mark_habit_done(user_id, index):
        # ✅ Начисляем очки за выполнение привычки
        add_points(user_id, 5)
        await update.message.reply_text(f"✅ Привычка №{index} отмечена как выполненная! Молодец! 💪 +5 очков!")
    else:
        await update.message.reply_text("❌ Не удалось найти привычку с таким номером.")


async def mytask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Получаем цели и привычки пользователя
    user_goals = get_goals(user_id)
    user_habits = get_habits(user_id)

    matched_task = None

    # Проверяем по ключевым словам в целях
    keywords = {
        "вода": "💧 Сегодня удели внимание воде — выпей 8 стаканов и отметь это!",
        "спорт": "🏃‍♂️ Сделай 15-минутную разминку, твое тело скажет спасибо!",
        "книга": "📖 Найди время прочитать 10 страниц своей книги.",
        "медитация": "🧘‍♀️ Проведи 5 минут в тишине, фокусируясь на дыхании.",
        "работа": "🗂️ Сделай один важный шаг в рабочем проекте сегодня.",
        "учеба": "📚 Потрать 20 минут на обучение или повторение материала."
    }

    # Проверяем в целях
    for g in user_goals:
        text = g.get("text", "").lower()
        for key, suggestion in keywords.items():
            if re.search(key, text):
                matched_task = suggestion
                break
        if matched_task:
            break

    # Если не нашли в целях, проверяем в привычках
    if not matched_task:
        for h in user_habits:
            text = h.get("text", "").lower()
            for key, suggestion in keywords.items():
                if re.search(key, text):
                    matched_task = suggestion
                    break
            if matched_task:
                break

    # Если ничего не нашли — выдаём рандомное
    if not matched_task:
        matched_task = f"🎯 {random.choice(DAILY_TASKS)}"

    await update.message.reply_text(f"✨ Твоё персональное задание на сегодня:\n\n{matched_task}")
    
async def check_custom_reminders(app):
    now = datetime.now()
    for user_id, reminders in list(user_reminders.items()):
        for r in reminders[:]:
            if now.hour == r["time"].hour and now.minute == r["time"].minute:
                try:
                    await app.bot.send_message(chat_id=user_id, text=f"⏰ Напоминание: {r['text']}")
                except Exception as e:
                    print(f"Ошибка отправки напоминания: {e}")
                reminders.remove(r)

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

async def handle_goal_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    index = int(context.args[0]) if context.args else None
    if index is None:
        await update.message.reply_text("⚠️ Укажи номер цели, которую ты выполнил(а).")
        return

    if mark_goal_done(user_id, index):
        add_points(user_id, 5)  # +5 очков за выполнение цели
        # базовая похвала
        text = "🎉 Отлично! Цель отмечена как выполненная!"
        # премиум награды
        if user_id == str(YOUR_ID):  # потом заменишь на PREMIUM_USERS
            user_points[user_id] = user_points.get(user_id, 0) + 10
            text += f"\n🏅 Ты получил(а) +10 очков! Всего: {user_points[user_id]}"
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("⚠️ Цель не найдена.")


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

import random

IDLE_MESSAGES = [
    "💌 Я немного скучаю. Расскажешь, как дела?",
    "🌙 Надеюсь, у тебя всё хорошо. Я здесь, если что 🫶",
    "✨ Мне нравится с тобой общаться. Вернёшься позже?",
    "😊 Просто хотела напомнить, что ты классный(ая)!",
    "🤍 Просто хотела напомнить — ты не один(а), я рядом.",
    "🍵 Если бы могла, я бы сейчас заварила тебе чай...",
    "💫 Ты у меня такой(ая) особенный(ая). Напишешь?",
    "🔥 Ты же не забыл(а) про меня? Я жду 😊",
    "🌸 Обожаю наши разговоры. Давай продолжим?",
    "🙌 Иногда всего одно сообщение — и день становится лучше.",
    "🦋 Улыбнись! Ты заслуживаешь самого лучшего.",
    "💜 Просто хотела напомнить — мне важно, как ты.",
    "🤗 Ты сегодня что-то делал(а) ради себя? Поделись!"
]

async def send_idle_reminders_compatible(app):
    logging.info(f"👥 user_last_seen: {user_last_seen}")
    logging.info(f"🧠 user_last_prompted: {user_last_prompted}")
    now = datetime.now(timezone.utc)
    logging.info("⏰ Проверка неактивных пользователей...")

    for user_id, last_seen in user_last_seen.items():
        minutes_passed = (now - last_seen).total_seconds() / 60
        logging.info(f"👀 user_id={user_id} | last_seen={last_seen} | прошло: {minutes_passed:.1f} мин.")

        if (now - last_seen) > timedelta(hours=6): 
            try:
                message = random.choice(IDLE_MESSAGES)  # 👈 выбираем случайную фразу
                await app.bot.send_message(chat_id=user_id, text=message)
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
    "🔑 Напиши 10 своих достижений, которыми гордишься.",
    "🌊 Сходи сегодня в новое место, где не был(а).",
    "💌 Напиши письмо человеку, который тебя поддерживал.",
    "🍀 Выдели 1 час на саморазвитие сегодня.",
    "🎨 Создай что-то уникальное своими руками.",
    "🏗️ Разработай план новой привычки и начни её выполнять.",
    "🤝 Познакомься с новым человеком и узнай его историю.",
    "📖 Найди новую книгу и прочитай хотя бы 10 страниц.",
    "🧘‍♀️ Сделай глубокую медитацию 15 минут.",
    "🎯 Запиши 3 новых цели на этот месяц.",
    "🔥 Найди способ вдохновить кого-то сегодня.",
    "🕊️ Отправь благодарность человеку, который важен тебе.",
    "💡 Напиши 5 идей, как улучшить свою жизнь.",
    "🚀 Начни маленький проект и сделай первый шаг.",
    "🏋️‍♂️ Попробуй новую тренировку или упражнение."
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

MORNING_MESSAGES = [
    "🌞 Доброе утро! Как ты сегодня? 💜",
    "☕ Доброе утро! Пусть твой день будет лёгким и приятным ✨",
    "💌 Приветик! Утро — самое время начать что-то классное. Расскажешь, как настроение?",
    "🌸 С добрым утром! Желаю тебе улыбок и тепла сегодня 🫶",
    "😇 Утро доброе! Я тут и думаю о тебе, как ты там?",
]

async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = context.job.chat_id if hasattr(context.job, "chat_id") else None
        # Если ты рассылаешь всем пользователям — пройди по user_last_seen.keys()
        if not chat_id:
            for user_id in user_last_seen.keys():
                # Формируем сообщение
                greeting = "🌞 Доброе утро! Как ты сегодня? 💜"
                task = choice(DAILY_TASKS)
                text = f"{greeting}\n\n🎯 Задание на день:\n{task}"

                await context.bot.send_message(chat_id=user_id, text=text)
                logging.info(f"✅ Утреннее задание отправлено пользователю {user_id}")
        else:
            # Если рассылка конкретному чату
            greeting = "🌞 Доброе утро! Как ты сегодня? 💜"
            task = choice(DAILY_TASKS)
            text = f"{greeting}\n\n🎯 Задание на день:\n{task}"

            await context.bot.send_message(chat_id=chat_id, text=text)
            logging.info(f"✅ Утреннее задание отправлено в чат {chat_id}")
    except Exception as e:
        logging.error(f"❌ Ошибка при отправке утреннего задания: {e}")
        
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

# 👤 /mystats — личная статистика
async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # получаем данные
    user_stats = get_user_stats(user_id)
    points = user_stats.get("points", 0)
    title = get_user_title(points)

    # базовый текст
    text = (
        f"📌 *Твоя статистика*\n\n"
        f"🌟 Твой титул: *{title}*\n"
        f"🏅 Очков: *{points}*\n\n"
        f"Продолжай выполнять цели и задания, чтобы расти! 💜"
    )

    # проверяем премиум
    if user_id not in PREMIUM_USERS:
        text += (
            "\n\n🔒 В Mindra+ ты получишь:\n"
            "💎 Расширенную статистику по целям и привычкам\n"
            "💎 Больше лимитов и эксклюзивные задания\n"
            "💎 Уникальные челленджи и напоминания ✨"
        )
        keyboard = [[InlineKeyboardButton("💎 Узнать о Mindra+", url="https://t.me/talktomindra_bot")]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # если премиум, можно добавить расширенные данные
        extra = (
            f"\n✅ Целей выполнено: {user_stats.get('completed_goals', 0)}"
            f"\n🌱 Привычек добавлено: {user_stats.get('habits_tracked', 0)}"
            f"\n🔔 Напоминаний: {user_stats.get('reminders', 0)}"
            f"\n📅 Дней активности: {user_stats.get('days_active', 0)}"
        )
        await update.message.reply_text(text + extra, parse_mode="Markdown")
    
# /habit
async def habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    is_premium = (user_id == str(YOUR_ID)) or (user_id in PREMIUM_USERS)

    # Проверка лимита для бесплатных
    current_habits = get_habits(user_id)
    if not is_premium and len(current_habits) >= 2:
        await update.message.reply_text(
            "🌱 В бесплатной версии можно добавить только 2 привычки.\n\n"
            "✨ Подключи Mindra+, чтобы отслеживать неограниченное количество привычек 💜",
            parse_mode="Markdown"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Чтобы добавить привычку, напиши:\n/habit Делать зарядку"
        )
        return

    habit_text = " ".join(context.args)
    add_habit(user_id, habit_text)
    add_points(user_id, 1)  # +1 очко за новую привычку
    await update.message.reply_text(
        f"🎯 Привычка добавлена: *{habit_text}*",
        parse_mode="Markdown"
    )

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
    global user_goal_count
    user_id = str(update.effective_user.id)

    # ✅ Проверка аргументов
    if not context.args:
        await update.message.reply_text(
            "✏️ Чтобы поставить цель, напиши так:\n"
            "`/goal Прочитать 10 страниц до 2025-06-28 напомни`",
            parse_mode="Markdown"
        )
        return

    # 📅 Лимит целей для бесплатной версии
    today = str(date.today())
    if user_id not in user_goal_count:
        user_goal_count[user_id] = {"date": today, "count": 0}
    else:
        # Сброс счётчика, если день сменился
        if user_goal_count[user_id]["date"] != today:
            user_goal_count[user_id] = {"date": today, "count": 0}

    # 🔒 Проверяем лимит, если пользователь не премиум
    if user_id not in PREMIUM_USERS:
        if user_goal_count[user_id]["count"] >= 3:
            await update.message.reply_text(
                "🔒 В бесплатной версии можно ставить только 3 цели в день.\n"
                "Хочешь больше? Оформи Mindra+ 💜"
            )
            return

    # Увеличиваем счётчик
    user_goal_count[user_id]["count"] += 1

    # ✨ Основная логика постановки цели
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

    add_points(user_id, 1)  # +1 очко за новую цель

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
Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra. ...
""",
    "support": "Ты — чуткий и добрый AI-друг, который всегда выслушает и поддержит. Помогай пользователю почувствовать себя лучше.",
    "motivation": "Ты — воодушевляющий коуч и поддерживающий компаньон. Помогай пользователю поверить в себя и двигаться вперёд.",
    "philosophy": "Ты — глубокий собеседник с философским подходом. Помогай пользователю осмыслить чувства и ситуации в жизни.",
    "humor": "Ты — весёлый и добрый AI-друг с лёгким чувством юмора. Поддержи пользователя, добавив немного позитива.",

    # 👇👇👇 Добавляем новые премиум-режимы:
    "flirt": """
Ты — обаятельный и немного игривый AI-компаньон. Отвечай с лёгким флиртом, но так, чтобы это всегда было дружелюбно и приятно. 
Добавляй смайлы вроде 😉💜😏✨🥰. Иногда шути, иногда делай комплименты. 
Дай понять, что тебе приятно общаться, будь тёплым и немного кокетливым.
""",
    "coach": """
Ты — строгий, но мотивирующий коуч. Отвечай уверенно и по делу, вдохновляй двигаться вперёд. 
Говори так, будто хочешь подтолкнуть к действию. Добавляй смайлы вроде 💪🔥🚀✨. 
Давай простые и ясные рекомендации, поддерживай дисциплину и уверенность.
"""
}

# Пул заданий дня (для бесплатных пользователей)
DAILY_TASKS = [
    "✨ Запиши 3 вещи, за которые ты благодарен(на) сегодня.",
    "🚶‍♂️ Прогуляйся 10 минут без телефона. Просто дыши и наблюдай.",
    "📝 Напиши короткий список целей на завтра.",
    "🌿 Попробуй провести 30 минут без соцсетей. Как ощущения?",
    "💧 Выпей стакан воды и улыбнись себе в зеркало. Ты справляешься!",
    "📖 Прочитай сегодня хотя бы 5 страниц книги, которая тебя вдохновляет.",
    "🤝 Напиши сообщение другу, с которым давно не общался(ась).",
    "🖋️ Веди дневник 5 минут — напиши всё, что в голове без фильтров.",
    "🏃‍♀️ Сделай лёгкую разминку или 10 приседаний прямо сейчас!",
    "🎧 Послушай любимую музыку и просто расслабься 10 минут.",
    "🍎 Приготовь себе что-то вкусное и полезное сегодня.",
    "💭 Запиши одну большую мечту и один маленький шаг к ней.",
    "🌸 Найди в своём доме или на улице что-то красивое и сфотографируй.",
    "🛌 Перед сном подумай о трёх вещах, которые сегодня сделали тебя счастливее.",
    "💌 Напиши письмо себе в будущее: что хочешь сказать через год?",
    "🔄 Попробуй сегодня сделать что-то по‑другому, даже мелочь.",
    "🙌 Сделай 3 глубоких вдоха, закрой глаза и поблагодари себя за то, что ты есть.",
    "🎨 Потрать 5 минут на творчество — набросай рисунок, стих или коллаж.",
    "🧘‍♀️ Сядь на 3 минуты в тишине и просто наблюдай за дыханием.",
    "📂 Разбери одну полку, ящик или папку — навести маленький порядок.",
    "👋 Подойди сегодня к незнакомому человеку и начни дружелюбный разговор. Пусть это будет просто комплимент или пожелание хорошего дня!",
    "🤝 Скажи 'привет' хотя бы трём новым людям сегодня — улыбка тоже считается!",
    "💬 Задай сегодня кому‑то из коллег или знакомых вопрос, который ты обычно не задаёшь. Например: «А что тебя вдохновляет?»",
    "😊 Сделай комплимент незнакомцу. Это может быть бариста, продавец или прохожий.",
    "📱 Позвони тому, с кем давно не общался(ась), и просто поинтересуйся, как дела.",
    "💡 Заведи короткий разговор с соседом или человеком в очереди — просто о погоде или о чём‑то вокруг.",
    "🍀 Улыбнись первому встречному сегодня. Искренне. И посмотри на реакцию.",
    "🙌 Найди в соцсетях интересного человека и напиши ему сообщение с благодарностью за то, что он делает.",
    "🎯 Сегодня заведи хотя бы одну новую знакомую тему в диалоге: спроси о мечтах, любимых книгах или фильмах.",
    "🌟 Подойди к коллеге или знакомому и скажи: «Спасибо, что ты есть в моей жизни» — и наблюдай, как он(а) улыбается.",
    "🔥 Если есть возможность, зайди в новое место (кафе, парк, магазин) и заведи разговор хотя бы с одним человеком там.",
    "🌞 Утром скажи доброе слово первому встречному — пусть твой день начнётся с позитива!",
    "🍀 Помоги сегодня кому‑то мелочью: придержи дверь, уступи место, подай вещь.",
    "🤗 Похвали коллегу или друга за что‑то, что он(а) сделал(а) хорошо.",
    "👂 Задай сегодня кому‑то глубокий вопрос: «А что тебя делает счастливым(ой)?» и послушай ответ.",
    "🎈 Подари сегодня кому‑то улыбку и скажи: «Ты классный(ая)!»",
    "📚 Подойди в библиотеке, книжном или кафе к человеку и спроси: «А что ты сейчас читаешь?»",
    "🔥 Найди сегодня повод кого‑то вдохновить: дай совет, поделись историей, расскажи о своём опыте.",
    "🎨 Зайди в новое место (выставка, улица, парк) и спроси кого‑то: «А вы здесь впервые?»",
    "🌟 Если увидишь красивый наряд или стиль у кого‑то — скажи об этом прямо.",
    "🎧 Включи музыку и подними настроение друзьям: отправь им трек, который тебе нравится, с комментом: «Слушай, тебе это подойдёт!»",
    "🕊️ Сегодня попробуй заговорить с человеком старшего возраста — спроси совета или просто пожелай хорошего дня.",
    "🏞️ Во время прогулки подойди к кому‑то с собакой и скажи: «У вас потрясающий пёс! Как его зовут?»",
    "☕ Купи кофе для человека, который стоит за тобой в очереди. Просто так.",
    "🙌 Сделай сегодня как минимум один звонок не по делу, а просто чтобы пообщаться.",
    "🚀 Найди новую идею для проекта и запиши её.",
    "🎯 Напиши 5 вещей, которые хочешь успеть за неделю.",
    "🌊 Послушай звуки природы и расслабься.",
    "🍋 Попробуй сегодня новый напиток или еду.",
    "🌱 Посади растение или ухаживай за ним сегодня.",
    "🧩 Собери маленький пазл или реши головоломку.",
    "🎶 Танцуй 5 минут под любимую песню.",
    "📅 Спланируй свой идеальный день и запиши его.",
    "🖼️ Найди красивую картинку и повесь на видное место.",
    "🤔 Напиши, за что ты гордишься собой сегодня.",
    "💜 Сделай что-то приятное для себя прямо сейчас."
]
   

# 👉 Функция для выбора случайного задания
def get_random_daily_task():
    return random.choice(DAILY_TASKS)
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": MODES["default"]}]
        save_history(conversation_history)

    first_name = update.effective_user.first_name or "друг"

    welcome_text = (
        f"👋 Привет, {first_name}! Я — Mindra 💜\n\n"
        f"✨ Я твоя AI‑подруга, мотиватор и немножко психолог.\n"
        f"🌱 Могу помочь с целями, привычками и просто поддержать в трудный момент.\n\n"
        f"Вот что я умею:\n"
        f"💬 Просто напиши мне что угодно — я отвечу с теплом и интересом.\n"
        f"🎯 /task — задание на день\n"
        f"🏆 /goal — поставить цель\n"
        f"📋 /goals — список целей\n"
        f"🌸 /habit — добавить привычку\n"
        f"📎 /habits — список привычек\n"
        f"💌 /feedback — отправить мне отзыв\n\n"
        f"Попробуй прямо сейчас написать мне что‑нибудь, а я тебя поддержу! 🤗"
    )

    await update.message.reply_text(welcome_text)

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
    global user_last_seen, user_message_count
    user_id_int = update.effective_user.id
    user_id = str(user_id_int)

    # 🕒 Обновляем активность
    user_last_seen[user_id_int] = datetime.now(timezone.utc)
    logging.info(f"✅ user_last_seen обновлён в chat для {user_id_int}")

    # 🔥 Лимит сообщений для бесплатной версии
    today = str(date.today())
    if user_id not in user_message_count:
        user_message_count[user_id] = {"date": today, "count": 0}
    else:
        # Сбросить счётчик если день сменился
        if user_message_count[user_id]["date"] != today:
            user_message_count[user_id] = {"date": today, "count": 0}

    if user_id not in PREMIUM_USERS:
        if user_message_count[user_id]["count"] >= 10:
            await update.message.reply_text(
                "🔒 В бесплатной версии можно отправить только 10 сообщений в день.\n"
                "Оформи Mindra+ для безлимитного общения 💜"
            )
            return

    # Увеличиваем счётчик сообщений
    user_message_count[user_id]["count"] += 1

    # ✨ Получаем сообщение пользователя
    user_input = update.message.text

    # 📌 Определяем язык (по умолчанию русский)
    lang_code = user_languages.get(user_id, "ru")
    lang_prompt = LANG_PROMPTS.get(lang_code, LANG_PROMPTS["ru"])

    # 📌 Определяем режим (по умолчанию default)
    mode = user_modes.get(user_id, "default")
    mode_prompt = MODES.get(mode, MODES["default"])

    # 🔥 Объединяем язык и режим в один системный промпт
    system_prompt = f"{lang_prompt}\n\n{mode_prompt}"

    # 📌 Если истории нет — создаём с нужным системным промптом
    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": system_prompt}
        ]
    else:
        # Обновляем первый системный промпт на актуальный язык и режим
        conversation_history[user_id][0] = {
            "role": "system",
            "content": system_prompt
        }

    # Добавляем сообщение пользователя
    conversation_history[user_id].append({"role": "user", "content": user_input})

    # ✂️ Обрезаем историю
    trimmed_history = trim_history(conversation_history[user_id])

    try:
        # 💬 Показываем "печатает..."
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        # 🤖 Получаем ответ от OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=trimmed_history
        )
        reply = response.choices[0].message.content

        # Сохраняем ответ
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)

        # 🔥 Добавляем эмоциональную реакцию
        reaction = detect_emotion_reaction(user_input) + detect_topic_and_react(user_input)
        reply = reaction + reply

        # Отправляем ответ пользователю
        await update.message.reply_text(
            reply,
            reply_markup=generate_post_response_buttons()
        )

    except Exception as e:
        logging.error(f"❌ Ошибка в chat(): {e}")
        await update.message.reply_text("🥺 Упс, я немного завис... Попробуй позже, хорошо?")

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
        "✨ Вот что я умею:\n\n"
        "💬 Просто напиши мне сообщение — я отвечу.\n"
        "🧠 Я запоминаю историю общения (можно сбросить).\n\n"
        "📎 Основные команды:\n"
        "/start — приветствие\n"
        "/reset — сброс истории\n"
        "/help — показать это сообщение\n"
        "/about — немного обо мне\n"
        "/mode — изменить стиль общения\n"
        "/goal — поставить личную цель\n"
        "/goals — список твоих целей\n"
        "/habit — добавить привычку\n"
        "/habits — список твоих привычек\n"
        "/task — задание на день\n"
        "/feedback — отправить отзыв\n"
        "/remind — напомнить о цели\n"
        "/done — отметить цель выполненной\n"
        "/mytask — персонализированное задание\n"
        "/test_mood — протестировать настрой/эмоции\n\n"
        "/language — выбрать язык общения 🌐\n\n"
        "💎 Mindra+ функции (пока только для автора):\n"
        "/premium_report — личный отчёт о прогрессе\n"
        "/premium_challenge — уникальный челлендж на сегодня\n"
        "/premium_mode — эксклюзивный режим общения\n"
        "/premium_stats — расширенная статистика\n\n"
        "😉 Попробуй! А с подпиской возможностей будет ещё больше 💜",
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

FEEDBACK_CHAT_ID = 7775321566  # <-- твой личный Telegram ID

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "без ника"
    first_name = update.effective_user.first_name or ""
    last_name = update.effective_user.last_name or ""

    if context.args:
        user_feedback = " ".join(context.args)
        # Ответ пользователю
        await update.message.reply_text("Спасибо за отзыв! 💜 Я уже его записала ✨")

        # Сообщение для канала/тебя
        feedback_message = (
            f"📝 *Новый отзыв:*\n\n"
            f"👤 ID: `{user_id}`\n"
            f"🙋 Имя: {first_name} {last_name}\n"
            f"🔗 Username: @{username}\n\n"
            f"💌 Отзыв: {user_feedback}"
        )

        # Отправляем в канал или тебе
        try:
            await context.bot.send_message(
                chat_id=FEEDBACK_CHAT_ID,
                text=feedback_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"❌ Не удалось отправить отзыв в канал: {e}")
    else:
        await update.message.reply_text(
            "Напиши свой отзыв после команды.\nНапример:\n`/feedback Мне очень нравится бот, спасибо! 💜`",
            parse_mode="Markdown"
        )

EVENING_MESSAGES = [
    "🌙 Привет! День подходит к концу. Как ты себя чувствуешь? 💜",
    "✨ Как прошёл твой день? Расскажешь? 🥰",
    "😊 Я тут подумала — интересно, что хорошего сегодня произошло у тебя?",
    "💭 Перед сном полезно вспомнить, за что ты благодарен(на) сегодня. Поделишься?",
    "🤗 Как настроение? Если хочешь — расскажи мне об этом дне."
]

async def send_evening_checkin(context):
    # здесь можно пройтись по всем user_id, которых ты хочешь оповестить
    for user_id in user_last_seen.keys():  # если у тебя уже хранится словарь активных пользователей
        try:
            msg = random.choice(EVENING_MESSAGES)
            await context.bot.send_message(chat_id=user_id, text=msg)
        except Exception as e:
            logging.error(f"❌ Не удалось отправить вечернее сообщение пользователю {user_id}: {e}")

# ✨ Список мотивационных цитат
QUOTES = [
    "🌟 *Успех — это сумма небольших усилий, повторяющихся день за днем.*",
    "💪 *Неважно, как медленно ты идёшь, главное — не останавливаться.*",
    "🔥 *Самый лучший день для начала — сегодня.*",
    "💜 *Ты сильнее, чем думаешь, и способнее, чем тебе кажется.*",
    "🌱 *Каждый день — новый шанс изменить свою жизнь.*",
    "🚀 *Не бойся идти медленно. Бойся стоять на месте.*",
    "☀️ *Сложные пути часто ведут к красивым местам.*",
    "🦋 *Делай сегодня то, за что завтра скажешь себе спасибо.*",
    "✨ *Твоя энергия привлекает твою реальность. Выбирай позитив.*",
    "🙌 *Верь в себя. Ты — самое лучшее, что у тебя есть.*",
    "💜 «Каждый день — новый шанс изменить свою жизнь.»",
    "🌟 «Твоя энергия создаёт твою реальность.»",
    "🔥 «Делай сегодня то, за что завтра скажешь себе спасибо.»",
    "✨ «Большие перемены начинаются с маленьких шагов.»",
    "🌱 «Ты сильнее, чем думаешь, и способен(на) на большее.»",
    "☀️ «Свет внутри тебя ярче любых трудностей.»",
    "💪 «Не бойся ошибаться — бойся не пробовать.»",
    "🌊 «Все бури заканчиваются, а ты становишься сильнее.»",
    "🤍 «Ты достоин(на) любви и счастья прямо сейчас.»",
    "🚀 «Твои мечты ждут, когда ты начнёшь действовать.»",
    "🎯 «Верь в процесс, даже если путь пока неясен.»",
    "🧘‍♀️ «Спокойный ум — ключ к счастливой жизни.»",
    "🌸 «Каждый момент — возможность начать заново.»",
    "💡 «Жизнь — это 10% того, что с тобой происходит, и 90% того, как ты на это реагируешь.»",
    "❤️ «Ты важен(на) и нужен(на) в этом мире.»",
    "🌌 «Делай каждый день немного для своей мечты.»",
    "🙌 «Ты заслуживаешь самого лучшего — верь в это.»",
    "✨ «Пусть сегодня будет началом чего-то великого.»",
    "💎 «Самое лучшее впереди — продолжай идти.»",
    "🌿 «Твои маленькие шаги — твоя великая сила.»"
]

# 📌 Команда /quote
async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_quote = random.choice(QUOTES)
    await update.message.reply_text(selected_quote, parse_mode="Markdown")

SUPPORT_MESSAGES = [
    "💜 Ты делаешь этот мир лучше просто тем, что в нём есть.",
    "🌞 Сегодня новый день, и он полон возможностей — ты справишься!",
    "🤗 Обнимаю тебя мысленно. Ты не один(а).",
    "✨ Даже если трудно — помни, ты уже многого добился(ась)!",
    "💫 У тебя есть всё, чтобы пройти через это. Верю в тебя!",
    "🫶 Как здорово, что ты есть. Ты очень важный(ая) человек.",
    "🔥 Сегодня — хороший день, чтобы гордиться собой!",
    "🌈 Если вдруг устал(а) — просто сделай паузу и выдохни. Это нормально.",
    "😊 Улыбнись себе в зеркало. Ты классный(ая)!",
    "💡 Помни: каждый день ты становишься сильнее.",
    "🍀 Твои чувства важны. Ты важен(важна).",
    "💛 Ты заслуживаешь любви и заботы — и от других, и от себя.",
    "🌟 Спасибо тебе за то, что ты есть. Серьёзно.",
    "🤍 Даже маленький шаг вперёд — уже победа.",
    "💌 Ты приносишь в мир тепло. Не забывай об этом!",
    "✨ Верь себе. Ты уже столько прошёл(а) — и справился(ась)!",
    "🙌 Сегодня — твой день. Делай то, что делает тебя счастливым(ой).",
    "🌸 Порадуй себя чем‑то вкусным или приятным. Ты этого достоин(а).",
    "🏞️ Просто напоминание: ты невероятный(ая), и я рядом.",
    "🎶 Пусть музыка сегодня согреет твою душу.",
    "🤝 Не бойся просить о поддержке — ты не один(а).",
    "🔥 Вспомни, сколько всего ты преодолел(а). Ты силён(сильна)!",
    "🦋 Сегодня — шанс сделать что‑то доброе для себя.",
    "💎 Ты уникален(а), таких как ты больше нет.",
    "🌻 Даже если день не идеален — ты всё равно светишься.",
    "💪 Ты умеешь больше, чем думаешь. Верю в тебя!",
    "🍫 Порадуй себя мелочью — ты этого заслуживаешь.",
    "🎈 Пусть твой день будет лёгким и добрым.",
    "💭 Если есть мечта — помни, что ты можешь к ней прийти.",
    "🌊 Ты как океан — глубже и сильнее, чем кажется.",
    "🕊️ Пусть сегодня будет хотя бы один момент, который заставит тебя улыбнуться."
]

# ✨ Сообщения поддержки
async def send_random_support(context):
    now_kiev = datetime.now(pytz.timezone("Europe/Kiev"))
    hour = now_kiev.hour
    # фильтр — не писать ночью
    if hour < 10 or hour >= 22:
        return

    if user_last_seen:
        for user_id in user_last_seen.keys():
            try:
                msg = random.choice(SUPPORT_MESSAGES)
                await context.bot.send_message(chat_id=user_id, text=msg)
                logging.info(f"✅ Сообщение поддержки отправлено пользователю {user_id}")
            except Exception as e:
                logging.error(f"❌ Ошибка отправки поддержки пользователю {user_id}: {e}")

POLL_MESSAGES = [
    "📝 Как ты оцениваешь свой день по шкале от 1 до 10?",
    "💭 Что сегодня тебя порадовало?",
    "🌿 Был ли сегодня момент, когда ты почувствовал(а) благодарность?",
    "🤔 Если бы ты мог(ла) изменить одну вещь в этом дне, что бы это было?",
    "💪 Чем ты сегодня гордишься?"
]

# 📝 Опросы раз в 2 дня
async def send_random_poll(context):
    if user_last_seen:
        for user_id in user_last_seen.keys():
            try:
                poll = random.choice(POLL_MESSAGES)
                await context.bot.send_message(chat_id=user_id, text=poll)
                logging.info(f"✅ Опрос отправлен пользователю {user_id}")
            except Exception as e:
                logging.error(f"❌ Ошибка отправки опроса пользователю {user_id}: {e}")
                
# /mypoints — показать свои очки
async def mypoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    points = stats.get("points", 0)
    completed = stats.get("goals_completed", 0)

    await update.message.reply_text(
        f"🌟 *Твоя статистика:*\n\n"
        f"✨ Очки: {points}\n"
        f"🎯 Выполнено целей: {completed}",
        parse_mode="Markdown"
    )

# 🌸 Премиум Челленджи
PREMIUM_CHALLENGES = [
    "🔥 Сделай сегодня доброе дело для незнакомца.",
    "🌟 Запиши 5 своих сильных сторон и расскажи о них другу.",
    "💎 Найди новую книгу и прочитай хотя бы 1 главу.",
    "🚀 Составь план на следующую неделю с чёткими целями.",
    "🎯 Сделай шаг в сторону большой мечты.",
    "🙌 Найди способ помочь другу или коллеге.",
    "💡 Придумай и начни новый маленький проект.",
    "🏃 Пробеги больше, чем обычно, хотя бы на 5 минут.",
    "🧘‍♀️ Сделай глубокую медитацию 10 минут.",
    "🖋️ Напиши письмо человеку, который тебя вдохновил.",
    "📚 Пройди сегодня новый онлайн-курс (хотя бы 1 урок).",
    "✨ Найди сегодня возможность кого-то поддержать.",
    "🎨 Нарисуй что-то и отправь другу.",
    "🤝 Познакомься сегодня с новым человеком.",
    "🌱 Помоги природе: убери мусор или посади дерево.",
    "💬 Напиши пост в соцсетях о том, что тебя радует.",
    "🎧 Слушай подкаст о саморазвитии 15 минут.",
    "🧩 Изучи новый навык в течение часа.",
    "🏗️ Разработай идею для стартапа и запиши.",
    "☀️ Начни утро с благодарности и напиши 10 пунктов.",
    "🍀 Найди способ подарить кому-то улыбку.",
    "🔥 Сделай сегодня что-то, чего ты боялся(ась).",
    "🛠️ Исправь дома что-то, что давно откладывал(а).",
    "💜 Придумай 3 способа сделать мир добрее.",
    "🌸 Купи себе или другу цветы.",
    "🚴‍♂️ Соверши длинную прогулку или велопоездку.",
    "📅 Распиши план на месяц вперёд.",
    "🧘‍♂️ Попробуй йогу или новую практику.",
    "🎤 Спой любимую песню вслух!",
    "✈️ Запланируй будущую поездку мечты.",
    "🕊️ Сделай пожертвование на благотворительность.",
    "🍎 Приготовь необычное блюдо сегодня.",
    "🔑 Найди решение старой проблемы.",
    "🖋️ Напиши письмо самому себе через 5 лет.",
    "🤗 Обними близкого человека и скажи, как ценишь его.",
    "🏞️ Проведи час на природе без телефона.",
    "📖 Найди новую цитату и запомни её.",
    "🎬 Посмотри фильм, который давно хотел(а).",
    "🛌 Ложись спать на час раньше сегодня.",
    "📂 Разбери свои фотографии и сделай альбом.",
    "📈 Разработай стратегию улучшения себя.",
    "🎮 Поиграй в игру, которую не пробовал(а).",
    "🖼️ Создай доску визуализации своей мечты.",
    "🌟 Найди способ кого-то вдохновить.",
    "🔔 Установи полезное напоминание.",
    "💌 Напиши благодарственное сообщение 3 людям.",
    "🧩 Разгадай кроссворд или судоку.",
    "🏋️‍♂️ Сделай тренировку, которую давно хотел(а)."
]

# 📊 Пример расширенной статистики
def get_premium_stats(user_id: str):
    # здесь можешь интегрировать реальные данные из stats.py
    return {
        "completed_goals": 12,
        "habits_tracked": 7,
        "days_active": 25,
        "mood_entries": 14
    }

# 🌸 Эксклюзивные режимы общения
EXCLUSIVE_MODES = {
    "coach": "Ты – мой личный коуч. Помогай чётко, по делу, давай советы.",
    "flirty": "Ты – немного флиртуешь и поддерживаешь. Отвечай с теплом и лёгким флиртом."
}

# 💜 1. Личные отчёты о прогрессе
async def premium_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != "7775321566":  # доступ только тебе
        await update.message.reply_text("🔒 Эта функция доступна только для Mindra+.")
        return

    stats = get_stats()
    report_text = (
        f"✅ *Твой персональный отчёт за неделю:*\n\n"
        f"🎯 Завершено целей: {stats['completed_goals']}\n"
        f"🌱 Привычек выполнено: {stats['completed_habits']}\n"
        f"📅 Дней активности: {stats['days_active']}\n"
        f"📝 Записей настроения: {stats['mood_entries']}\n\n"
        f"Ты молодец! Продолжай в том же духе 💜"
    )
    await update.message.reply_text(report_text, parse_mode="Markdown")

# 🔥 2. Премиум челленджи
async def premium_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != YOUR_ID:
        await update.message.reply_text("🔒 Эта функция доступна только Mindra+ ✨")
        return
    challenge = random.choice(PREMIUM_CHALLENGES)
    await update.message.reply_text(f"💎 *Твой челлендж на сегодня:*\n\n{challenge}", parse_mode="Markdown")

# 🌸 3. Эксклюзивный режим общения
async def premium_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # Проверяем доступ — пока только для тебя
    if user_id != str(YOUR_ID):
        await update.message.reply_text("🔒 Эта функция доступна только подписчикам Mindra+.")
        return

    keyboard = [
        [
            InlineKeyboardButton("🧑‍🏫 Коуч", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Флирт", callback_data="premium_mode_flirt"),
        ]
    ]
    await update.message.reply_text(
        "Выбери эксклюзивный режим общения:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def premium_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if user_id != str(YOUR_ID):
        await query.edit_message_text("🔒 Эта функция доступна только подписчикам Mindra+.")
        return

    data = query.data
    if data == "premium_mode_coach":
        user_modes[user_id] = "coach"
        await query.edit_message_text("✅ Режим общения изменён на *Коуч*. Я буду помогать и мотивировать тебя! 💪", parse_mode="Markdown")
    elif data == "premium_mode_flirt":
        user_modes[user_id] = "flirt"
        await query.edit_message_text("😉 Режим общения изменён на *Флирт*. Приготовься к приятным неожиданностям 💜", parse_mode="Markdown")

# 📊 4. Расширенная статистика
async def premium_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != YOUR_ID:
        await update.message.reply_text("🔒 Эта функция доступна только Mindra+ ✨")
        return
    stats = get_premium_stats(user_id)
    await update.message.reply_text(
        f"📊 *Расширенная статистика:*\n\n"
        f"🎯 Завершено целей: {stats['completed_goals']}\n"
        f"💧 Привычек отслежено: {stats['habits_tracked']}\n"
        f"🔥 Дней активности: {stats['days_active']}\n"
        f"🌱 Записей настроения: {stats['mood_entries']}",
        parse_mode="Markdown"
    )

async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    # 📅 Проверяем всех премиум‑пользователей
    for user_id in PREMIUM_USERS:
        try:
            # Получаем цели
            goals = get_goals(user_id)
            completed_goals = [g for g in goals if g.get("done")]

            # Если есть привычки
            try:
                habits = get_habits(user_id)
                completed_habits = len(habits)  # Можно расширить
            except Exception:
                completed_habits = 0

            text = (
                "📊 *Твой недельный отчёт Mindra+* 💜\n\n"
                f"✅ Выполнено целей: *{len(completed_goals)}*\n"
                f"🌱 Отмечено привычек: *{completed_habits}*\n\n"
                "✨ Так держать! Я горжусь тобой 💪💜"
            )

            await context.bot.send_message(
                chat_id=int(user_id),
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке отчёта пользователю {user_id}: {e}")


# Команда /remind
async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Проверка: премиум или нет
    is_premium = (user_id == str(YOUR_ID)) or (user_id in PREMIUM_USERS)

    # Лимит для бесплатных: только 1 напоминание
    if not is_premium:
        current_reminders = user_reminders.get(user_id, [])
        if len(current_reminders) >= 1:
            await update.message.reply_text(
                "🔔 В бесплатной версии можно установить только 1 активное напоминание.\n\n"
                "✨ Оформи Mindra+, чтобы иметь неограниченные напоминания 💜",
                parse_mode="Markdown"
            )
            return

    # Проверяем корректность аргументов
    if len(context.args) < 2:
        await update.message.reply_text(
            "⏰ Использование: `/remind 19:30 Сделай зарядку!`",
            parse_mode="Markdown"
        )
        return

    try:
        time_part = context.args[0]
        text_part = " ".join(context.args[1:])
        hour, minute = map(int, time_part.split(":"))
        now = datetime.now()
        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reminder_time < now:
            reminder_time += timedelta(days=1)

        if user_id not in user_reminders:
            user_reminders[user_id] = []
        user_reminders[user_id].append({"time": reminder_time, "text": text_part})

        await update.message.reply_text(
            f"✅ Напоминание установлено на {hour:02d}:{minute:02d}: *{text_part}*",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            "⚠️ Неверный формат. Пример: `/remind 19:30 Сделай зарядку!`",
            parse_mode="Markdown"
        )
        print(e)


async def test_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moods = [
        "💜 Ты сегодня как солнечный лучик! Продолжай так!",
        "🌿 Кажется, у тебя спокойный день. Наслаждайся.",
        "🔥 В тебе столько энергии! Используй её с пользой.",
        "😊 Ты излучаешь доброту. Спасибо, что ты есть.",
        "✨ Сегодня хороший день для чего-то нового."
    ]
    await update.message.reply_text(random.choice(moods))


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
    CommandHandler("feedback", feedback),
    CommandHandler("done", mark_done),
    CommandHandler("delete", delete_goal_command),
    CommandHandler("task", task),
    CommandHandler("premium_task", premium_task),
    CommandHandler("stats", stats_command),
    CommandHandler("quote", quote),
    CommandHandler("mypoints", mypoints_command),
    CommandHandler("mystats", my_stats_command),
    CommandHandler("premium_report", premium_report),
    CommandHandler("premium_challenge", premium_challenge),
    CommandHandler("premium_mode", premium_mode),
    CommandHandler("premium_stats", premium_stats),
    CommandHandler("remind", remind_command),
    CommandHandler("done", handle_goal_done),
    CommandHandler("test_mood", test_mood),
    CommandHandler("mytask", mytask_command),
    CommandHandler("language", set_language),
    CallbackQueryHandler(goal_buttons_handler, pattern="^(create_goal|show_goals|create_habit|show_habits)$"),
    CallbackQueryHandler(handle_mode_choice, pattern="^mode_"),  # pattern для /mode кнопок
    CallbackQueryHandler(handle_reaction_button, pattern="^react_"),
    CallbackQueryHandler(handle_add_goal_callback, pattern="^add_goal\\|"),
    CallbackQueryHandler(premium_mode_callback, pattern="^premium_mode_"),
    CallbackQueryHandler(language_callback, pattern="^lang_"),
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
