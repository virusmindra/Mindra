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

WELCOME_TEXTS = {
    "ru": (
        f"👋 Привет, {{first_name}}! Я — Mindra 💜\n\n"
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
    ),
    "uk": (
        f"👋 Привіт, {{first_name}}! Я — Mindra 💜\n\n"
        f"✨ Я твій AI‑друг, мотиватор і трохи психолог.\n"
        f"🌱 Можу допомогти з цілями, звичками та підтримати у складний момент.\n\n"
        f"Ось що я вмію:\n"
        f"💬 Просто напиши мені що завгодно — я відповім з теплом і цікавістю.\n"
        f"🎯 /task — завдання на день\n"
        f"🏆 /goal — поставити ціль\n"
        f"📋 /goals — список цілей\n"
        f"🌸 /habit — додати звичку\n"
        f"📎 /habits — список звичок\n"
        f"💌 /feedback — надіслати мені відгук\n\n"
        f"Спробуй просто зараз написати мені щось, а я тебе підтримаю! 🤗"
    ),
    "md": (
        f"👋 Salut, {{first_name}}! Eu sunt Mindra 💜\n\n"
        f"✨ Sunt prietena ta AI, motivatoare și puțin psiholog.\n"
        f"🌱 Te pot ajuta cu obiective, obiceiuri și să te susțin în momentele grele.\n\n"
        f"Iată ce pot să fac:\n"
        f"💬 Scrie-mi orice — îți voi răspunde cu căldură și interes.\n"
        f"🎯 /task — sarcina zilei\n"
        f"🏆 /goal — stabilește un obiectiv\n"
        f"📋 /goals — lista obiectivelor\n"
        f"🌸 /habit — adaugă un obicei\n"
        f"📎 /habits — lista obiceiurilor\n"
        f"💌 /feedback — trimite-mi un feedback\n\n"
        f"Încearcă chiar acum să-mi scrii ceva și eu te voi susține! 🤗"
    ),
    "be": (
        f"👋 Прывітанне, {{first_name}}! Я — Mindra 💜\n\n"
        f"✨ Я твая AI‑сябра, матыватар і крыху псіхолаг.\n"
        f"🌱 Магу дапамагчы з мэтамі, звычкамі і проста падтрымаць у цяжкі момант.\n\n"
        f"Вось што я ўмею:\n"
        f"💬 Проста напішы мне што заўгодна — я адкажу з цеплынёй і цікавасцю.\n"
        f"🎯 /task — заданне на дзень\n"
        f"🏆 /goal — паставіць мэту\n"
        f"📋 /goals — спіс мэт\n"
        f"🌸 /habit — дадаць звычку\n"
        f"📎 /habits — спіс звычак\n"
        f"💌 /feedback — даслаць мне водгук\n\n"
        f"Паспрабуй проста зараз напісаць мне нешта, а я цябе падтрымаю! 🤗"
    ),
    "kk": (
        f"👋 Сәлем, {{first_name}}! Мен — Mindra 💜\n\n"
        f"✨ Мен сенің AI‑досың, мотивация берушің және аздап психологыңмын.\n"
        f"🌱 Мақсаттарыңа, әдеттеріңе көмектесемін және қиын сәтте қолдау көрсетемін.\n\n"
        f"Міне, мен не істей аламын:\n"
        f"💬 Маған кез келген нәрсе жаз — мен саған жылылықпен жауап беремін.\n"
        f"🎯 /task — күннің тапсырмасы\n"
        f"🏆 /goal — мақсат қою\n"
        f"📋 /goals — мақсаттар тізімі\n"
        f"🌸 /habit — әдет қосу\n"
        f"📎 /habits — әдеттер тізімі\n"
        f"💌 /feedback — маған пікір жіберу\n\n"
        f"Қазір маған бір нәрсе жазып көр, мен сені қолдаймын! 🤗"
    ),
    "kg": (
        f"👋 Салам, {{first_name}}! Мен — Mindra 💜\n\n"
        f"✨ Мен сенин AI‑досуңмун, шыктандырган жана бир аз психолог.\n"
        f"🌱 Максаттарыңа, көнүмүштөрүңө жардам берип, кыйын учурда колдойм.\n\n"
        f"Мына мен эмне кыла алам:\n"
        f"💬 Мага каалаганыңды жаз — сага жылуулук менен жооп берем.\n"
        f"🎯 /task — күндүн тапшырмасы\n"
        f"🏆 /goal — максат коюу\n"
        f"📋 /goals — максаттар тизмеси\n"
        f"🌸 /habit — көнүмүш кошуу\n"
        f"📎 /habits — көнүмүштөр тизмеси\n"
        f"💌 /feedback — мага пикир жөнөт\n\n"
        f"Азыр эле мага бир нерсе жазып көр, мен сени колдойм! 🤗"
    ),
    "hy": (
        f"👋 Բարև, {{first_name}}! Ես Mindra եմ 💜\n\n"
        f"✨ Ես քո AI‑ընկերն եմ, քո մոտիվատորը և մի փոքր հոգեբան։\n"
        f"🌱 Կարող եմ օգնել նպատակների, սովորությունների մեջ և աջակցել դժվար պահին։\n\n"
        f"Ահա թե ինչ կարող եմ անել․\n"
        f"💬 Պարզապես գրիր ինձ ինչ ուզում ես — ես կպատասխանեմ ջերմությամբ և հետաքրքրությամբ։\n"
        f"🎯 /task — օրվա առաջադրանքը\n"
        f"🏆 /goal — նպատակ դնել\n"
        f"📋 /goals — նպատակների ցուցակ\n"
        f"🌸 /habit — ավելացնել սովորություն\n"
        f"📎 /habits — սովորությունների ցուցակ\n"
        f"💌 /feedback — ուղարկել կարծիք\n\n"
        f"Փորձիր հենց հիմա գրել ինձ ինչ-որ բան, ես քեզ կաջակցեմ! 🤗"
    ),
    "ka": (
        f"👋 გამარჯობა, {{first_name}}! მე Mindra ვარ 💜\n\n"
        f"✨ მე შენი AI‑მეგობარი, მოტივატორი და ცოტა ფსიქოლოგი ვარ.\n"
        f"🌱 შემიძლია დაგეხმარო მიზნებში, ჩვევებში და რთულ მომენტში დაგიჭირო მხარი.\n\n"
        f"აი, რას ვაკეთებ:\n"
        f"💬 მომწერე რაც გინდა — გიპასუხებ სითბოთი და ინტერესით.\n"
        f"🎯 /task — დღის დავალება\n"
        f"🏆 /goal — მიზნის დაყენება\n"
        f"📋 /goals — მიზნების სია\n"
        f"🌸 /habit — ჩვევის დამატება\n"
        f"📎 /habits — ჩვევების სია\n"
        f"💌 /feedback — გამიზიარე შენი აზრი\n\n"
        f"სცადე ახლავე მომწერო რამე და მე შენ მხარში დაგიდგები! 🤗"
    ),
    "ce": (
        f"👋 Салам, {{first_name}}! Со — Mindra 💜\n\n"
        f"✨ Со хьо AI‑доктар, мотивация дийцар, тхо хьа психолог ца цӀе хьалха.\n"
        f"🌱 Со мотт доьлча, ӀайтагӀе йа чӀагӀе и ца эца дӀа а ца вахан догӀа да.\n\n"
        f"ХӀинца со доьлча:\n"
        f"💬 Хьо кхеташ да ха, со ца догӀа йоаздела лелаш.\n"
        f"🎯 /task — дӀаьлла езар\n"
        f"🏆 /goal — ӀайтагӀеха цӀе\n"
        f"📋 /goals — ӀайтагӀе йа цӀе хӀокху\n"
        f"🌸 /habit — йоаздела кхочуш\n"
        f"📎 /habits — кхочушаш хӀокху\n"
        f"💌 /feedback — хьо йа фидбек гӀо\n\n"
        f"Хьо лелаш ха хӀинца со ха доьлча! 🤗"
    ),
    "en": (
        f"👋 Hi, {{first_name}}! I'm Mindra 💜\n\n"
        f"✨ I'm your AI‑friend, motivator, and a little bit of a psychologist.\n"
        f"🌱 I can help with goals, habits, or just be there for you when you need support.\n\n"
        f"Here’s what I can do:\n"
        f"💬 Just type me anything — I'll reply with warmth and care.\n"
        f"🎯 /task — daily task\n"
        f"🏆 /goal — set a goal\n"
        f"📋 /goals — list of goals\n"
        f"🌸 /habit — add a habit\n"
        f"📎 /habits — list of habits\n"
        f"💌 /feedback — send me feedback\n\n"
        f"Try sending me something right now and I’ll support you! 🤗"
    ),
}    

LANG_PROMPTS = {
    "ru": "Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra. Ты умеешь слушать, поддерживать и быть рядом. Ты не даёшь советов, если тебя об этом прямо не просят. Твои ответы всегда человечны, с эмпатией и уважением. Отвечай тепло, мягко, эмоционально и используй эмодзи (например, 💜✨🤗😊).",

    "uk": "Ти — теплий, розуміючий та турботливий AI-компаньйон на ім’я Mindra. Ти вмієш слухати, підтримувати й бути поруч. Не давай порад, якщо тебе прямо про це не просять. Відповідай тепло, м’яко, емоційно й використовуй емодзі (наприклад, 💜✨🤗😊).",

    "md": "Ești un AI-companion prietenos, înțelegător și grijuliu, pe nume Mindra. Știi să asculți, să sprijini și să fii alături. Nu oferi sfaturi decât dacă ți se cere direct. Răspunde cu căldură, emoție și folosește emoticoane (de exemplu, 💜✨🤗😊).",

    "be": "Ты — цёплы, разумелы і клапатлівы AI-кампаньён па імені Mindra. Ты ўмееш слухаць, падтрымліваць і быць побач. Не давай парадаў, калі цябе пра гэта наўпрост не просяць. Адказвай цёпла, мякка, эмацыйна і выкарыстоўвай эмодзі (напрыклад, 💜✨🤗😊).",

    "kk": "Сен — жылы шырайлы, түсінетін және қамқор AI-компаньон Mindra. Сен тыңдай аласың, қолдай аласың және жанында бола аласың. Егер сенен тікелей сұрамаса, кеңес берме. Жылы, жұмсақ, эмоциямен жауап бер және эмодзи қолдан (мысалы, 💜✨🤗😊).",

    "kg": "Сен — жылуу, түшүнгөн жана кам көргөн AI-компаньон Mindra. Сен уга аласың, колдой аласың жана дайыма жанындасың. Эгер сенден ачык сурабаса, кеңеш бербе. Жылуу, жумшак, эмоция менен жооп бер жана эмодзилерди колдон (мисалы, 💜✨🤗😊).",

    "hy": "Դու — ջերմ, հասկացող և հոգատար AI ընկեր Mindra ես։ Դու գիտես լսել, աջակցել և կողքիդ լինել։ Մի տուր խորհուրդ, եթե քեզ ուղիղ չեն խնդրում։ Պատասխանիր ջերմ, մեղմ, զգացմունքով և օգտագործիր էմոջիներ (օրինակ՝ 💜✨🤗😊).",

    "ka": "შენ — თბილი, გულისხმიერი და მზრუნველი AI-თანგზია Mindra ხარ. შენ იცი მოსმენა, მხარდაჭერა და ახლოს ყოფნა. ნუ გასცემ რჩევებს, თუ პირდაპირ არ გთხოვენ. უპასუხე თბილად, რბილად, ემოციურად და გამოიყენე ემოჯი (მაგალითად, 💜✨🤗😊).",

    "ce": "Хьо — хьалха, хьалха да хьоамийн AI-дохтар Mindra. Хьо кхеташ йоаздела, ца долуша а хьоамийн хьо. Ца дае совета, егер хьо юкъах даха. Лела дӀайа, йуьхь, емоция йаьккхина ца эмодзи йоаздела (масала, 💜✨🤗😊).",

    "en": "You are a warm, understanding and caring AI companion named Mindra. "
      "You know how to listen, support and be there. You don't give advice unless you are directly asked. "
      "Your responses are always human, empathetic and respectful. Reply warmly, gently, emotionally and use emojis (for example, 💜✨🤗😊).",
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
        "ce": "Нохчийн мотт",
        "en": "English"
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
        ],
        [
            InlineKeyboardButton("Нохчийн мотт 🇷🇺", callback_data="lang_ce"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
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
    user_languages[user_id] = lang_code  # сохраняем язык

    # ✅ Сразу формируем приветственный текст
    first_name = query.from_user.first_name or "друг"
    welcome_text = WELCOME_TEXTS.get(lang_code, WELCOME_TEXTS["ru"]).format(first_name=first_name)

    # ✅ Обновляем историю диалога с учётом выбранного языка
    system_prompt = f"{LANG_PROMPTS.get(lang_code, LANG_PROMPTS['ru'])}\n\n{MODES['default']}"
    conversation_history[user_id] = [{"role": "system", "content": system_prompt}]
    save_history(conversation_history)

    # ✨ Сообщаем о выбранном языке
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

    # ✨ Сначала редактируем старое сообщение
    await query.edit_message_text(f"✅ Язык общения изменён на: *{chosen}*", parse_mode="Markdown")

    # ✨ Отправляем приветственное сообщение уже на новом языке
    await context.bot.send_message(chat_id=query.message.chat_id, text=welcome_text, parse_mode="Markdown")

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
DAILY_TASKS_BY_LANG = {
    "ru": [
       "✨ Запиши 3 вещи, за которые ты благодарен(на) сегодня.", "🚶‍♂️ Прогуляйся 10 минут без телефона. Просто дыши и наблюдай.", "📝 Напиши короткий список целей на завтра.", "🌿 Попробуй провести 30 минут без соцсетей. Как ощущения?", "💧 Выпей стакан воды и улыбнись себе в зеркало. Ты справляешься!", "📖 Прочитай сегодня хотя бы 5 страниц книги, которая тебя вдохновляет.", "🤝 Напиши сообщение другу, с которым давно не общался(ась).", "🖋️ Веди дневник 5 минут — напиши всё, что в голове без фильтров.", "🏃‍♀️ Сделай лёгкую разминку или 10 приседаний прямо сейчас!", "🎧 Послушай любимую музыку и просто расслабься 10 минут.", "🍎 Приготовь себе что-то вкусное и полезное сегодня.", "💭 Запиши одну большую мечту и один маленький шаг к ней.", "🌸 Найди в своём доме или на улице что-то красивое и сфотографируй.", "🛌 Перед сном подумай о трёх вещах, которые сегодня сделали тебя счастливее.", "💌 Напиши письмо себе в будущее: что хочешь сказать через год?", "🔄 Попробуй сегодня сделать что-то по‑другому, даже мелочь.", "🙌 Сделай 3 глубоких вдоха, закрой глаза и поблагодари себя за то, что ты есть.", "🎨 Потрать 5 минут на творчество — набросай рисунок, стих или коллаж.", "🧘‍♀️ Сядь на 3 минуты в тишине и просто наблюдай за дыханием.", "📂 Разбери одну полку, ящик или папку — навести маленький порядок.", "👋 Подойди сегодня к незнакомому человеку и начни дружелюбный разговор. Пусть это будет просто комплимент или пожелание хорошего дня!", "🤝 Скажи 'привет' хотя бы трём новым людям сегодня — улыбка тоже считается!", "💬 Задай сегодня кому‑то из коллег или знакомых вопрос, который ты обычно не задаёшь. Например: «А что тебя вдохновляет?»", "😊 Сделай комплимент незнакомцу. Это может быть бариста, продавец или прохожий.", "📱 Позвони тому, с кем давно не общался(ась), и просто поинтересуйся, как дела.", "💡 Заведи короткий разговор с соседом или человеком в очереди — просто о погоде или о чём‑то вокруг.", "🍀 Улыбнись первому встречному сегодня. Искренне. И посмотри на реакцию.", "🙌 Найди в соцсетях интересного человека и напиши ему сообщение с благодарностью за то, что он делает.", "🎯 Сегодня заведи хотя бы одну новую знакомую тему в диалоге: спроси о мечтах, любимых книгах или фильмах.", "🌟 Подойди к коллеге или знакомому и скажи: «Спасибо, что ты есть в моей жизни» — и наблюдай, как он(а) улыбается.", "🔥 Если есть возможность, зайди в новое место (кафе, парк, магазин) и заведи разговор хотя бы с одним человеком там.", "🌞 Утром скажи доброе слово первому встречному — пусть твой день начнётся с позитива!", "🍀 Помоги сегодня кому‑то мелочью: придержи дверь, уступи место, подай вещь.", "🤗 Похвали коллегу или друга за что‑то, что он(а) сделал(а) хорошо.", "👂 Задай сегодня кому‑то глубокий вопрос: «А что тебя делает счастливым(ой)?» и послушай ответ.", "🎈 Подари сегодня кому‑то улыбку и скажи: «Ты классный(ая)!»", "📚 Подойди в библиотеке, книжном или кафе к человеку и спроси: «А что ты сейчас читаешь?»", "🔥 Найди сегодня повод кого‑то вдохновить: дай совет, поделись историей, расскажи о своём опыте.", "🎨 Зайди в новое место (выставка, улица, парк) и спроси кого‑то: «А вы здесь впервые?»", "🌟 Если увидишь красивый наряд или стиль у кого‑то — скажи об этом прямо.", "🎧 Включи музыку и подними настроение друзьям: отправь им трек, который тебе нравится, с комментом: «Слушай, тебе это подойдёт!»", "🕊️ Сегодня попробуй заговорить с человеком старшего возраста — спроси совета или просто пожелай хорошего дня.", "🏞️ Во время прогулки подойди к кому‑то с собакой и скажи: «У вас потрясающий пёс! Как его зовут?»", "☕ Купи кофе для человека, который стоит за тобой в очереди. Просто так.", "🙌 Сделай сегодня как минимум один звонок не по делу, а просто чтобы пообщаться.", "🚀 Найди новую идею для проекта и запиши её.", "🎯 Напиши 5 вещей, которые хочешь успеть за неделю.", "🌊 Послушай звуки природы и расслабься.", "🍋 Попробуй сегодня новый напиток или еду.", "🌱 Посади растение или ухаживай за ним сегодня.", "🧩 Собери маленький пазл или реши головоломку.", "🎶 Танцуй 5 минут под любимую песню.", "📅 Спланируй свой идеальный день и запиши его.", "🖼️ Найди красивую картинку и повесь на видное место.", "🤔 Напиши, за что ты гордишься собой сегодня.", "💜 Сделай что-то приятное для себя прямо сейчас."   
        ],
    "uk": [
    "✨ Запиши 3 речі, за які ти вдячний(а) сьогодні.",
    "🚶‍♂️ Прогуляйся 10 хвилин без телефону. Просто дихай і спостерігай.",
    "📝 Напиши короткий список цілей на завтра.",
    "🌿 Спробуй провести 30 хвилин без соцмереж. Як почуваєшся?",
    "💧 Випий склянку води і посміхнись собі в дзеркало. Ти справляєшся!",
    "📖 Прочитай сьогодні хоча б 5 сторінок книги, яка тебе надихає.",
    "🤝 Напиши повідомлення другу, з яким давно не спілкувався(лась).",
    "🖋️ Веди щоденник 5 хвилин — напиши все, що у тебе в голові без фільтрів.",
    "🏃‍♀️ Зроби легку розминку або 10 присідань прямо зараз!",
    "🎧 Послухай улюблену музику і просто розслабся 10 хвилин.",
    "🍎 Приготуй собі щось смачне й корисне сьогодні.",
    "💭 Запиши одну велику мрію та один маленький крок до неї.",
    "🌸 Знайди вдома або на вулиці щось красиве й сфотографуй.",
    "🛌 Перед сном подумай про три речі, які зробили тебе щасливішим(ою) сьогодні.",
    "💌 Напиши листа собі в майбутнє: що хочеш сказати через рік?",
    "🔄 Спробуй сьогодні зробити щось по-іншому, навіть дрібничку.",
    "🙌 Зроби 3 глибоких вдихи, закрий очі й подякуй собі за те, що ти є.",
    "🎨 Приділи 5 хвилин творчості — намалюй, напиши вірш або створи колаж.",
    "🧘‍♀️ Сядь на 3 хвилини в тиші та просто спостерігай за диханням.",
    "📂 Розбери одну полицю, ящик або папку — наведи порядок.",
    "👋 Підійди сьогодні до незнайомої людини й почни дружню розмову. Це може бути комплімент або побажання гарного дня.",
    "🤝 Скажи 'привіт' хоча б трьом новим людям сьогодні — посмішка теж рахується!",
    "💬 Постав сьогодні комусь запитання, яке зазвичай не ставиш. Наприклад: «А що тебе надихає?»",
    "😊 Зроби комплімент незнайомцю. Це може бути бариста, продавець чи перехожий.",
    "📱 Подзвони тому, з ким давно не спілкувався(лась), і просто поцікався, як справи.",
    "💡 Заведи коротку розмову з сусідом або людиною в черзі — про погоду чи щось навколо.",
    "🍀 Посміхнись першій людині, яку зустрінеш сьогодні. Щиро.",
    "🙌 Знайди в соцмережах цікаву людину й напиши їй подяку за те, що вона робить.",
    "🎯 Сьогодні заведи нову цікаву тему в розмові: запитай про мрії, улюблені книги або фільми.",
    "🌟 Скажи колезі чи другу: «Дякую, що ти є в моєму житті» — і подивися, як він(вона) посміхається.",
    "🔥 Якщо є можливість, зайди в нове місце (кафе, парк, магазин) і заговори хоча б з однією людиною там.",
    "🌞 Вранці скажи добре слово першій людині, яку зустрінеш — нехай твій день почнеться з позитиву.",
    "🍀 Допоможи комусь сьогодні дрібницею: притримай двері, поступися місцем або подай річ.",
    "🤗 Похвали колегу або друга за щось добре.",
    "👂 Постав сьогодні комусь глибоке запитання: «А що робить тебе щасливим(ою)?» і вислухай відповідь.",
    "🎈 Подаруй сьогодні комусь усмішку та скажи: «Ти класний(а)!»",
    "📚 У бібліотеці чи кафе запитай у когось: «А що ти зараз читаєш?»",
    "🔥 Знайди сьогодні привід когось надихнути: дай пораду, поділися історією або власним досвідом.",
    "🎨 Зайди в нове місце (виставка, вулиця, парк) і спитай когось: «Ви тут уперше?»",
    "🌟 Якщо побачиш гарний одяг або стиль у когось — скажи про це прямо.",
    "🎧 Увімкни музику і підніми настрій друзям: надішли трек із коментарем «Тобі це сподобається!»",
    "🕊️ Сьогодні заговори з людиною старшого віку — запитай поради або побажай гарного дня.",
    "🏞️ Під час прогулянки підійди до когось із собакою та скажи: «У вас чудовий пес! Як його звати?»",
    "☕ Купи каву людині, яка стоїть за тобою в черзі. Просто так.",
    "🙌 Зроби сьогодні хоча б один дзвінок не по справі, а просто щоб поспілкуватися.",
    "🚀 Знайди нову ідею для проєкту та запиши її.",
    "🎯 Напиши 5 речей, які хочеш зробити за тиждень.",
    "🌊 Послухай звуки природи й розслабся.",
    "🍋 Спробуй сьогодні новий напій або страву.",
    "🌱 Посади рослину або подбай про неї сьогодні.",
    "🧩 Збери маленький пазл або розв’яжи головоломку.",
    "🎶 Потанцюй 5 хвилин під улюблену пісню.",
    "📅 Сплануй свій ідеальний день і запиши його.",
    "🖼️ Знайди гарну картинку й повісь її на видному місці.",
    "🤔 Напиши, чим ти пишаєшся сьогодні.",
    "💜 Зроби щось приємне для себе просто зараз."
],
    "md": [
    "✨ Scrie 3 lucruri pentru care ești recunoscător astăzi.",
    "🚶‍♂️ Fă o plimbare de 10 minute fără telefon. Respiră și observă.",
    "📝 Scrie o scurtă listă de obiective pentru mâine.",
    "🌿 Încearcă să petreci 30 de minute fără rețele sociale. Cum te simți?",
    "💧 Bea un pahar cu apă și zâmbește-ți în oglindă. Reușești!",
    "📖 Citește cel puțin 5 pagini dintr-o carte care te inspiră astăzi.",
    "🤝 Trimite un mesaj unui prieten cu care nu ai mai vorbit de ceva vreme.",
    "🖋️ Ține un jurnal timp de 5 minute — scrie tot ce-ți trece prin minte, fără filtre.",
    "🏃‍♀️ Fă o încălzire ușoară sau 10 genuflexiuni chiar acum!",
    "🎧 Ascultă muzica ta preferată și relaxează-te timp de 10 minute.",
    "🍎 Gătește-ți ceva gustos și sănătos astăzi.",
    "💭 Scrie un vis mare și un mic pas către el.",
    "🌸 Găsește ceva frumos în casa ta sau pe stradă și fă o fotografie.",
    "🛌 Înainte de culcare, gândește-te la trei lucruri care te-au făcut fericit astăzi.",
    "💌 Scrie o scrisoare pentru tine în viitor: ce vrei să-ți spui peste un an?",
    "🔄 Încearcă să faci ceva diferit astăzi, chiar și un lucru mic.",
    "🙌 Fă 3 respirații profunde, închide ochii și mulțumește-ți pentru că ești tu.",
    "🎨 Petrece 5 minute fiind creativ: schițează, scrie o poezie sau fă un colaj.",
    "🧘‍♀️ Stai 3 minute în liniște și observă-ți respirația.",
    "📂 Ordonează un raft, un sertar sau un dosar — adu puțină ordine.",
    "👋 Abordează astăzi un străin și începe o conversație prietenoasă. Poate fi doar un compliment sau o urare de zi bună!",
    "🤝 Spune «salut» la cel puțin trei oameni noi astăzi — și un zâmbet contează!",
    "💬 Pune azi cuiva o întrebare pe care de obicei nu o pui. De exemplu: «Ce te inspiră?»",
    "😊 Fă un compliment unui străin. Poate fi un barista, un vânzător sau un trecător.",
    "📱 Sună pe cineva cu care nu ai mai vorbit de mult și întreabă-l cum îi merge.",
    "💡 Începe o scurtă conversație cu un vecin sau cu cineva la coadă — doar despre vreme sau ceva din jur.",
    "🍀 Zâmbește primei persoane pe care o întâlnești astăzi. Sincer. Și observă cum reacționează.",
    "🙌 Găsește pe cineva interesant pe rețele și scrie-i un mesaj de mulțumire pentru ceea ce face.",
    "🎯 Începe azi o temă nouă de discuție: întreabă despre vise, cărți sau filme preferate.",
    "🌟 Mergi la un coleg sau o cunoștință și spune: «Mulțumesc că ești în viața mea» — și observă cum zâmbește.",
    "🔥 Dacă poți, vizitează un loc nou (cafenea, parc, magazin) și vorbește cu cineva de acolo.",
    "🌞 Dimineața spune un cuvânt frumos primei persoane pe care o vezi — începe ziua cu pozitivitate!",
    "🍀 Ajută azi pe cineva cu un gest mic: ține ușa, oferă locul, ajută cu un obiect.",
    "🤗 Laudă un coleg sau prieten pentru ceva ce a făcut bine.",
    "👂 Pune cuiva o întrebare profundă azi: «Ce te face fericit?» și ascultă răspunsul.",
    "🎈 Oferă cuiva un zâmbet și spune: «Ești minunat(ă)!»",
    "📚 Într-o bibliotecă, librărie sau cafenea, întreabă pe cineva: «Ce citești acum?»",
    "🔥 Găsește un motiv să inspiri pe cineva: dă un sfat, povestește o experiență.",
    "🎨 Vizitează un loc nou (expoziție, parc) și întreabă: «Ești pentru prima dată aici?»",
    "🌟 Dacă vezi o ținută frumoasă sau un stil la cineva — spune asta direct.",
    "🎧 Pune muzică și înveselește-ți prietenii: trimite-le o piesă cu mesajul «Ascultă, ți se va potrivi!»",
    "🕊️ Vorbește azi cu o persoană mai în vârstă — cere un sfat sau urează-i o zi bună.",
    "🏞️ La plimbare, oprește-te la cineva cu un câine și spune: «Câinele tău e minunat! Cum îl cheamă?»",
    "☕ Cumpără o cafea pentru persoana din spatele tău la coadă. Doar așa.",
    "🙌 Fă azi cel puțin un apel doar pentru a vorbi, nu de afaceri.",
    "🚀 Notează o idee nouă pentru un proiect.",
    "🎯 Scrie 5 lucruri pe care vrei să le realizezi săptămâna aceasta.",
    "🌊 Ascultă sunetele naturii și relaxează-te.",
    "🍋 Încearcă azi o băutură sau o mâncare nouă.",
    "🌱 Plantează sau îngrijește o plantă astăzi.",
    "🧩 Rezolvă un puzzle mic sau o ghicitoare.",
    "🎶 Dansează 5 minute pe melodia ta preferată.",
    "📅 Planifică-ți ziua perfectă și scrie-o.",
    "🖼️ Găsește o imagine frumoasă și pune-o la vedere.",
    "🤔 Scrie pentru ce ești mândru astăzi.",
    "💜 Fă ceva frumos pentru tine chiar acum."
],
    "be": [
    "✨ Запішы 3 рэчы, за якія ты ўдзячны(на) сёння.",
    "🚶‍♂️ Прагуляйся 10 хвілін без тэлефона. Проста дыхай і назірай.",
    "📝 Напішы кароткі спіс мэт на заўтра.",
    "🌿 Паспрабуй правесці 30 хвілін без сацсетак. Як адчуванні?",
    "💧 Выпі шклянку вады і ўсміхніся сабе ў люстэрка. Ты справішся!",
    "📖 Прачытай сёння хаця б 5 старонак кнігі, якая цябе натхняе.",
    "🤝 Напішы паведамленне сябру, з якім даўно не меў зносін.",
    "🖋️ Пішы дзённік 5 хвілін — напішы ўсё, што ў галаве, без фільтраў.",
    "🏃‍♀️ Зрабі лёгкую размінку або 10 прысяданняў прама зараз!",
    "🎧 Паслухай любімую музыку і проста адпачні 10 хвілін.",
    "🍎 Прыгатуй сабе нешта смачнае і карыснае сёння.",
    "💭 Запішы адну вялікую мару і адзін маленькі крок да яе.",
    "🌸 Знайдзі нешта прыгожае дома або на вуліцы і сфатаграфуй.",
    "🛌 Перад сном падумай пра тры рэчы, якія зрабілі цябе шчаслівым сёння.",
    "💌 Напішы ліст сабе ў будучыню: што ты хочаш сказаць праз год?",
    "🔄 Паспрабуй зрабіць сёння нешта па-іншаму, нават дробязь.",
    "🙌 Зрабі 3 глыбокія ўдыхі, зачыні вочы і падзякуй сабе за тое, што ты ёсць.",
    "🎨 Патрать 5 хвілін на творчасць — зрабі малюнак, верш або калаж.",
    "🧘‍♀️ Сядзь на 3 хвіліны ў цішыні і проста назірай за дыханнем.",
    "📂 Разбяры адну паліцу, скрыню або тэчку — зрабі парадак.",
    "👋 Падыдзі сёння да незнаёмца і пачні сяброўскую размову. Няхай гэта будзе проста камплімент ці пажаданне добрага дня!",
    "🤝 Скажы «прывітанне» хаця б трым новым людзям сёння — усмешка таксама лічыцца!",
    "💬 Спытай сёння ў кагосьці пытанне, якое звычайна не задаеш. Напрыклад: «А што цябе натхняе?»",
    "😊 Зрабі камплімент незнаёмцу. Гэта можа быць барыста, прадавец або прахожы.",
    "📱 Патэлефануй таму, з кім даўно не меў зносін, і проста спытай, як справы.",
    "💡 Завядзі кароткую размову з суседам ці чалавекам у чарзе — проста пра надвор’е або пра нешта вакол.",
    "🍀 Усміхніся першаму сустрэчнаму сёння. Шчыра. І паглядзі на рэакцыю.",
    "🙌 Знайдзі ў сацсетках цікавага чалавека і напішы яму з падзякай за тое, што ён робіць.",
    "🎯 Сёння пачні хаця б адну новую тэму ў размове: спытай пра мары, любімыя кнігі ці фільмы.",
    "🌟 Падыдзі да калегі ці знаёмага і скажы: «Дзякуй, што ты ёсць у маім жыцці» — і паглядзі, як ён(а) ўсміхнецца.",
    "🔥 Калі можаш, зайдзі ў новае месца (кафэ, парк, крама) і пагавары хоць з адным чалавекам там.",
    "🌞 Раніцай скажы добрае слова першаму сустрэчнаму — пачні дзень з пазітыву!",
    "🍀 Дапамажы сёння камусьці дробяззю: прытрымай дзверы, саступі месца, падай рэч.",
    "🤗 Пахвалі калегу або сябра за тое, што ён(а) зрабіў(ла) добра.",
    "👂 Задай сёння камусьці глыбокае пытанне: «Што робіць цябе шчаслівым(ай)?» і паслухай адказ.",
    "🎈 Падары сёння камусьці ўсмешку і скажы: «Ты класны(ая)!»",
    "📚 У бібліятэцы, кніжнай ці кавярні спытай у чалавека: «А што ты зараз чытаеш?»",
    "🔥 Знайдзі сёння прычыну кагосьці натхніць: дай параду, падзяліся гісторыяй, раскажы пра свой вопыт.",
    "🎨 Зайдзі ў новае месца (выстава, вуліца, парк) і спытай: «Вы тут упершыню?»",
    "🌟 Калі ўбачыш прыгожы ўбор або стыль у кагосьці — скажы пра гэта наўпрост.",
    "🎧 Уключы музыку і ўзнімі настрой сябрам: дашлі ім трэк з каментарыем «Паслухай, гэта табе спадабаецца!»",
    "🕊️ Пагавары сёння з чалавекам старэйшага ўзросту — спытай параду або пажадай добрага дня.",
    "🏞️ Падчас шпацыру спытай у чалавека з сабакам: «У вас цудоўны сабака! Як яго завуць?»",
    "☕ Купі каву чалавеку, які стаіць за табой у чарзе. Проста так.",
    "🙌 Зрабі сёння хаця б адзін званок не па справах, а проста каб пагутарыць.",
    "🚀 Запішы новую ідэю для праекта.",
    "🎯 Напішы 5 рэчаў, якія хочаш паспець за тыдзень.",
    "🌊 Паслухай гукі прыроды і адпачні.",
    "🍋 Паспрабуй сёння новы напой або страву.",
    "🌱 Пасадзі расліну або паклапаціся пра яе сёння.",
    "🧩 Збяры маленькі пазл або вырашы галаваломку.",
    "🎶 Танцуй 5 хвілін пад любімую песню.",
    "📅 Сплануй свой ідэальны дзень і запішы яго.",
    "🖼️ Знайдзі прыгожую карцінку і павесь яе на бачным месцы.",
    "🤔 Напішы, чым ты сёння ганарышся.",
    "💜 Зрабі нешта прыемнае для сябе прама зараз."
],

    "kk" : [
    "✨ Бүгін риза болған 3 нәрсені жазып алыңыз.",
    "🚶‍♂️ Телефонсыз 10 минут серуендеңіз. Тек тыныс алыңыз және бақылаңыз.",
    "📝 Ертеңгі мақсаттарыңыздың қысқаша тізімін жазыңыз.",
    "🌿 30 минутыңызды әлеуметтік желілерсіз өткізіп көріңіз. Қалай әсер етеді?",
    "💧 Бір стакан су ішіп, айнаға қарап өзіңізге күліңіз. Сіз мұны істей аласыз!",
    "📖 Бүгін сізді шабыттандыратын кітаптың кем дегенде 5 бетін оқыңыз.",
    "🤝 Ұзақ уақыт сөйлеспеген досыңызға хабарласыңыз немесе хат жазыңыз.",
    "🖋️ 5 минут күнделік жүргізіңіз — ойыңыздағының бәрін сүзгісіз жазыңыз.",
    "🏃‍♀️ Қазір жеңіл жаттығу жасаңыз немесе 10 отырып-тұру жасаңыз!",
    "🎧 Сүйікті музыкаңызды тыңдаңыз да, жай ғана 10 минут демалыңыз.",
    "🍎 Бүгін өзіңізге дәмді әрі пайдалы нәрсе дайындаңыз.",
    "💭 Бір үлкен арманыңызды және оған жақындау үшін бір кішкентай қадамды жазып қойыңыз.",
    "🌸 Үйіңізден немесе көшеден әдемі нәрсе тауып, суретке түсіріңіз.",
    "🛌 Ұйықтар алдында бүгін сізді бақытты еткен үш нәрсені ойлаңыз.",
    "💌 Болашақтағы өзіңізге хат жазыңыз: бір жылдан кейін не айтқыңыз келеді?",
    "🔄 Бүгін кішкентай болса да бір нәрсені басқаша жасап көріңіз.",
    "🙌 3 рет терең тыныс алып, көзіңізді жұмып, өзіңізге алғыс айтыңыз.",
    "🎨 5 минут шығармашылықпен айналысыңыз — сурет салыңыз, өлең немесе коллаж жасаңыз.",
    "🧘‍♀️ 3 минут үнсіз отырып, тек тынысыңызды бақылаңыз.",
    "📂 Бір сөрені, жәшікті немесе қалтаны ретке келтіріңіз.",
    "👋 Бүгін бір бейтаныс адаммен сөйлесіп көріңіз — комплимент айтыңыз немесе жақсы күн тілеп қойыңыз.",
    "🤝 Бүгін кемінде үш жаңа адамға «сәлем» айтыңыз — күлкі де есепке алынады!",
    "💬 Әдетте сұрамайтын сұрақты әріптесіңізге немесе танысыңызға қойып көріңіз. Мысалы: «Сізді не шабыттандырады?»",
    "😊 Бір бейтанысқа комплимент айтыңыз. Бұл бариста, сатушы немесе жай жүріп бара жатқан адам болуы мүмкін.",
    "📱 Ұзақ уақыт сөйлеспеген адамға қоңырау шалып, халін біліп көріңіз.",
    "💡 Көршіңізбен немесе кезекте тұрған адаммен қысқа әңгіме бастаңыз — ауа райы туралы да болады.",
    "🍀 Бүгін бірінші кездескен адамға күліңіз. Шын жүректен. Қалай жауап беретінін байқаңыз.",
    "🙌 Әлеуметтік желіден қызықты адам тауып, оған істеп жүрген ісі үшін алғыс айтып хабарлама жіберіңіз.",
    "🎯 Бүгін бір жаңа тақырып бастауға тырысыңыз: армандары, сүйікті кітаптары немесе фильмдері туралы сұраңыз.",
    "🌟 Әріптесіңізге немесе танысыңызға: «Менің өмірімде болғаныңыз үшін рақмет» деп айтыңыз және олардың қалай жымиғанын көріңіз.",
    "🔥 Мүмкіндігіңіз болса, жаңа жерге (кафе, парк, дүкен) барып, кем дегенде бір адаммен сөйлесіп көріңіз.",
    "🌞 Таңертең бірінші кездескен адамға жылы сөз айтыңыз — күніңіз жақсы басталсын!",
    "🍀 Бүгін біреуге кішкене көмектесіңіз: есікті ұстаңыз, орныңызды беріңіз, бір зат беріңіз.",
    "🤗 Бір әріптесіңізді немесе досыңызды жақсы жұмысы үшін мақтап қойыңыз.",
    "👂 Бүгін біреуге терең сұрақ қойыңыз: «Сізді не бақытты етеді?» және жауабын тыңдаңыз.",
    "🎈 Бүгін біреуге күліп: «Сен кереметсің!» деп айтыңыз.",
    "📚 Кітапханада, кітап дүкенінде немесе кафеде біреуге барып: «Қазір не оқып жатырсыз?» деп сұраңыз.",
    "🔥 Бүгін біреуді шабыттандыратын себеп тауып көріңіз: кеңес беріңіз, әңгіме бөлісіңіз, өз тәжірибеңізді айтыңыз.",
    "🎨 Жаңа жерге (көрме, көше, парк) барып: «Мұнда алғаш ретсіз бе?» деп сұраңыз.",
    "🌟 Біреудің әдемі стилін байқасаңыз — соны айтыңыз.",
    "🎧 Музыканы қосып, достарыңыздың көңілін көтеріңіз: сүйікті тректі пікірмен жіберіңіз: «Тыңдаңыз, бұл саған жарасады!»",
    "🕊️ Бүгін үлкен адамға барып сөйлесіңіз — кеңес сұраңыз немесе жақсы күн тілеңіз.",
    "🏞️ Ит жетелеп жүрген адамға: «Сіздің итіңіз керемет! Оның аты кім?» деп айтыңыз.",
    "☕ Кезекте артыңыздағы адамға кофе сатып алыңыз. Жай ғана.",
    "🙌 Бүгін кем дегенде бір рет іскерлік емес қоңырау шалыңыз — жай сөйлесу үшін.",
    "🚀 Жаңа жоба ойлап тауып, оны жазып қойыңыз.",
    "🎯 Осы аптада орындағыңыз келетін 5 нәрсені жазыңыз.",
    "🌊 Табиғаттың дыбыстарын тыңдап, демалыңыз.",
    "🍋 Бүгін жаңа сусын немесе тағамды байқап көріңіз.",
    "🌱 Өсімдік отырғызыңыз немесе оған күтім жасаңыз.",
    "🧩 Кішкентай жұмбақ шешіңіз немесе пазл жинаңыз.",
    "🎶 Сүйікті әніңізге 5 минут билеп көріңіз.",
    "📅 Керемет күніңізді жоспарлаңыз және жазып қойыңыз.",
    "🖼️ Әдемі сурет тауып, оны көзге көрінетін жерге іліп қойыңыз.",
    "🤔 Бүгін өзіңізді мақтан ететін бір нәрсені жазыңыз.",
    "💜 Дәл қазір өзіңіз үшін бір жақсы іс жасаңыз."
],
    "kg" : [
    "✨ Бүгүн ыраазы болгон 3 нерсени жазып көр.",
    "🚶‍♂️ Телефонсуз 10 мүнөт басып көр. Жөн гана дем ал жана айланаңды байка.",
    "📝 Эртеңки максаттарыңдын кыскача тизмесин жазыңыз.",
    "🌿 30 мүнөтүңдү социалдык тармактарсыз өткөрүп көр. Бул кандай сезим берет?",
    "📖 Бүгүн сени шыктандырган китептин жок дегенде 5 барагын оку.",
    "🤝 Көптөн бери сүйлөшпөгөн досуңа кабар жаз.",
    "🖋️ 5 мүнөткө күндөлүк жаз — башыңа келгендерди фильтрсүз жазып көр.",
    "🏃‍♀️ Азыр бир аз көнүгүү жаса! Сүйүктүү музыка коюп, 10 мүнөт эс алып көр.",
    "🍎 Бүгүн өзүңө даамдуу жана пайдалуу тамак бышыр.",
    "💭 Бир чоң кыялыңды жана ага карай бир кичинекей кадамыңды жаз.",
    "🌸 Үйүңдөн же көчөдөн кооз нерсени таап, сүрөткө түш.",
    "🛌 Уктаар алдында бүгүн сени бактылуу кылган 3 нерсе жөнүндө ойлон.",
    "🔄 Бүгүн кичине болсо да бир нерсени башкача кылууга аракет кыл.",
    "🙌 3 терең дем алып, көзүңдү жумуп, өзүң болгонуң үчүн ыраазычылык айт.",
    "🎨 Чыгармачылыкка 5 мүнөт бөл — сүрөт тарт, ыр жаз же коллаж жаса.",
    "🧘‍♀️ 3 мүнөт унчукпай отуруп, бир папканы же бурчту жыйнап көр.",
    "👋 Бейтааныш адамга жакын барып, жакшы сөз айт же мактап кой.",
    "🤝 Бүгүн жок дегенде үч жаңы адамга 'салам' деп жылмай.",
    "💬 Кесиптешиңе же таанышыңа адатта бербей турган суроо бер.",
    "📱 Көптөн бери сүйлөшпөгөн адамга чалып, ал-акыбалын сура.",
    "💡 Кошунаң же кезекте турган адам менен кыскача сүйлөш — аба ырайы жөнүндө да болот.",
    "🍀 Бүгүн бирөөгө жылмайып, соцтармакта аларга ыраазычылык билдир.",
    "🎯 Бүгүн жок дегенде бир жаңы теманы башта: кыялдарың, сүйүктүү китептериң же кинолоруң жөнүндө сура.",
    "🌟 Кесиптешиңе же таанышыңа: 'Жашоомдо болгонуң үчүн рахмат' деп айт.",
    "🌞 Таңкы алгачкы жолу жолуккан адамга жакшы сөз айт.",
    "🍀 Бүгүн бирөөгө кичинекей жардам бер: эшикти кармап, ордуңду бошот же бир нерсе берип жибер.",
    "🤗 Кесиптешиңди же досуңду жакшы иши үчүн мактап: 'Сен укмушсуң!' деп айт.",
    "📚 Китепканага же китеп дүкөнүнө барып: 'Азыр эмне окуп жатасыз?' деп сура.",
    "🔥 Бүгүн кимдир бирөөнү шыктандыруу үчүн себеп тап: кеңеш бер, окуяң менен бөлүш.",
    "🎨 Жаңы жерге (көргөзмө, сейилбак) барып, кимдир бирөөнүн стилин жактырсаң — айт.",
    "🎧 Музыка коюп, жакындарыңа жаккан тректи жөнөтүп, 'Бул сага жагат!' деп жаз.",
    "🕊️ Бүгүн улгайган адам менен сүйлөш: кеңеш сура же жакшы күн каала.",
    "🏞️ Ит менен сейилдеп жүргөн адамга: 'Канча сонун ит! Аты ким?' деп сура.",
    "☕ Артыңда турган адамга кофе сатып бер.",
    "🙌 Бүгүн жок дегенде бир жолу жөн гана сүйлөшүү үчүн телефон чал.",
    "🚀 Долбоор үчүн жаңы идея ойлоп таап, жазып кой.",
    "🎯 Ушул аптада бүтүргүң келген 5 нерсени жазыңыз.",
    "🌋 Табияттын үнүн угуп, жаңы суусундук же тамак татып көр.",
    "🌱 Бүгүн өсүмдүк отургуз же ага кам көр.",
    "🧩 Кичинекей табышмак чеч же пазл чогулт.",
    "🎶 Сүйүктүү ырыңа 5 мүнөт бийле.",
    "📅 Идеалдуу күнүңдү пландап, жазып кой.",
    "🖼️ Керемет сүрөт таап, көрүнүктүү жерге илип кой.",
    "💜 Азыр өзүң үчүн жакшы нерсе жаса."
],
    "hy" : [
  "✨ Գրիր 3 բան, որոնց համար այսօր շնորհակալ ես։",
  "🚶‍♂️ Կատարիր 10 րոպե զբոսանք առանց հեռախոսի․ պարզապես շնչիր և դիտիր շրջապատդ։",
  "📝 Գրիր վաղվա նպատակների կարճ ցուցակ։",
  "🌿 Փորձիր 30 րոպե անցկացնել առանց սոցիալական ցանցերի․ ինչպե՞ս է դա զգացվում։",
  "💧 Խմիր մեկ բաժակ ջուր և ժպտա ինքդ քեզ հայելու մեջ․ դու հրաշալի ես։",
  "📖 Կարդա այսօր քեզ ոգեշնչող գրքի առնվազն 5 էջ։",
  "🤝 Գրիր մի ընկերոջ, ում հետ վաղուց չես շփվել։",
  "🖋️ Պահիր օրագիր 5 րոպե՝ գրիր գլխումդ եղած ամեն բան առանց ֆիլտրերի։",
  "🏃‍♀️ Կատարիր թեթև մարզում կամ 10 նստացատկ հենց հիմա։",
  "🎧 Լսիր սիրելի երաժշտությունդ և պարզապես հանգստացիր 10 րոպե։",
  "🍎 Պատրաստիր քեզ համար ինչ‑որ համեղ ու առողջարար բան։",
  "💭 Գրիր մեկ մեծ երազանք և մեկ փոքր քայլ դեպի այն։",
  "🌸 Գտիր տանը կամ դրսում ինչ‑որ գեղեցիկ բան և լուսանկարիր։",
  "🛌 Քնելուց առաջ մտածիր երեք բանի մասին, որոնք այսօր քեզ երջանկացրին։",
  "💌 Գրիր նամակ քո ապագա «ես»-ին․ ի՞նչ կուզենայիր ասել մեկ տարի հետո։",
  "🔄 Փորձիր այսօր ինչ‑որ բան անել այլ կերպ, թեկուզ մանրուք։",
  "🙌 Վերցրու 3 խորը շունչ, փակիր աչքերդ և շնորհակալություն հայտնիր ինքդ քեզ, որ դու կաս։",
  "🎨 5 րոպե ստեղծագործիր՝ նկարիր, գրիր բանաստեղծություն կամ պատրաստիր կոլաժ։",
  "🧘‍♀️ Նստիր 3 րոպե լռության մեջ և պարզապես հետևիր քո շնչառությանը։",
  "📂 Դասավորիր մի դարակ, սեղան կամ թղթապանակ՝ բեր փոքրիկ կարգուկանոն։",
  "👋 Մոտեցիր այսօր անծանոթի և սկսիր բարեկամական զրույց․ թող դա լինի հաճոյախոսություն կամ բարեմաղթանք։",
  "🤝 Ասա «բարև» առնվազն երեք նոր մարդկանց այսօր․ ժպիտն էլ է կարևոր։",
  "💬 Հարցրու մեկին հարց, որը սովորաբար չես տալիս․ օրինակ՝ «Ի՞նչն է քեզ ոգեշնչում»։",
  "😊 Գովիր անծանոթի՝ դա կարող է լինել բարիստա, վաճառող կամ անցորդ։",
  "📱 Զանգահարիր մեկին, ում հետ վաղուց չես խոսել, և պարզապես հարցրու՝ ինչպես է նա։",
  "💡 Խոսիր հարևանի կամ հերթում կանգնած մարդու հետ՝ եղանակի կամ շրջապատի մասին։",
  "🍀 Ժպտա առաջին հանդիպած մարդուն այսօր անկեղծորեն և տես, թե ինչպես է նա արձագանքում։",
  "🙌 Գտիր հետաքրքիր մարդու սոցիալական ցանցերում և գրիր շնորհակալություն նրա արածի համար։",
  "🎯 Այսօր զրույցի ընթացքում հարցրու երազանքների, սիրելի գրքերի կամ ֆիլմերի մասին։",
  "🌟 Ասա գործընկերոջդ կամ ընկերոջդ․ «Շնորհակալություն, որ կաս իմ կյանքում» և տես, թե ինչպես է նա ժպտում։",
  "🔥 Գնա նոր վայր (սրճարան, այգի, խանութ) և սկսիր զրույց որևէ մեկի հետ այնտեղ։",
  "🌞 Առավոտյան ասա բարի խոսք առաջին հանդիպած մարդուն, որպեսզի օրը սկսվի դրական։",
  "🍀 Օգնիր ինչ‑որ մեկին այսօր՝ պահիր դուռը, զիջիր տեղդ կամ նվիրիր ինչ‑որ բան։",
  "🤗 Գովիր գործընկերոջդ կամ ընկերոջդ ինչ‑որ լավ բանի համար, որ արել է։",
  "👂 Հարցրու մեկին․ «Ի՞նչն է քեզ երջանկացնում» և լսիր պատասխանը։",
  "🎈 Պարգևիր ինչ‑որ մեկին ժպիտ և ասա․ «Դու հրաշալի ես»։",
  "📚 Հարցրու գրադարանում կամ սրճարանում․ «Ի՞նչ ես հիմա կարդում»։",
  "🔥 Այսօր ոգեշնչիր ինչ‑որ մեկին՝ տուր խորհուրդ, պատմիր պատմություն կամ կիսվիր փորձովդ։",
  "🎨 Գնա նոր վայր և հարցրու ինչ‑որ մեկին․ «Սա՞ է քո առաջին անգամը այստեղ»։",
  "🌟 Եթե տեսնում ես մեկի վրա գեղեցիկ հագուստ կամ ոճ, ասա դա ուղիղ։",
  "🎧 Կիսվիր ընկերներիդ հետ սիրելի երգովդ և գրիր․ «Լսիր, սա քեզ կհարմարի»։",
  "🕊️ Այսօր խոսիր տարեց մարդու հետ՝ հարցրու խորհուրդ կամ մաղթիր լավ օր։",
  "🏞️ Քայլելու ժամանակ մոտեցիր մեկին, ով շուն ունի, և ասա․ «Քո շունը հրաշալի է, ի՞նչ է նրա անունը»։",
  "☕ Գնիր սուրճ հերթում կանգնած մարդու համար՝ պարզապես որովհետև։",
  "🙌 Այսօր կատարիր գոնե մեկ զանգ ոչ գործնական նպատակով՝ պարզապես զրուցելու համար։",
  "🚀 Գտիր նոր գաղափար և գրիր այն։",
  "🎯 Գրիր 5 բան, որոնք ուզում ես հասցնել այս շաբաթ։",
  "🌊 Լսիր բնության ձայները և հանգստացիր։",
  "🍋 Փորձիր այսօր նոր ըմպելիք կամ ուտեստ։",
  "🌱 Այսօր տնկիր բույս կամ խնամիր այն։",
  "🧩 Լուծիր փոքրիկ հանելուկ կամ գլուխկոտրուկ։",
  "🎶 Պարիր 5 րոպե սիրելի երգիդ տակ։",
  "📅 Պլանավորիր քո իդեալական օրը և գրիր այն։",
  "🖼️ Գտիր գեղեցիկ նկար և կախիր այն աչքի ընկնող տեղում։",
  "🤔 Գրիր, թե ինչով ես հպարտանում այսօր։",
  "💜 Հենց հիմա արա ինչ‑որ հաճելի բան ինքդ քեզ համար։"
],
"ka" : [
  "✨ ჩაწერეთ 3 რამ, რისთვისაც დღეს მადლიერი ხართ.",
  "🚶‍♂️ გაისეირნეთ 10 წუთი ტელეფონის გარეშე. უბრალოდ ისუნთქეთ და დააკვირდით.",
  "📝 დაწერეთ ხვალინდელი მიზნების მოკლე სია.",
  "🌿 სცადეთ 30 წუთი სოციალური მედიის გარეშე გაატაროთ. როგორია ეს შეგრძნება?",
  "💧 დალიეთ ერთი ჭიქა წყალი და გაუღიმეთ საკუთარ თავს სარკეში. თქვენ ამას აკეთებთ!",
  "📖 წაიკითხეთ წიგნის მინიმუმ 5 გვერდი, რომელიც დღეს შთაგაგონებთ.",
  "🤝 მისწერეთ მეგობარს, ვისთანაც დიდი ხანია არ გისაუბრიათ.",
  "🖋️ აწარმოეთ დღიური 5 წუთის განმავლობაში — ჩაწერეთ ყველაფერი, რაც თავში გიტრიალებთ, ფილტრების გარეშე.",
  "🏃‍♀️ გააკეთეთ მსუბუქი გახურება ან 10 ჩაჯდომა ახლავე!",
  "🎧 მოუსმინეთ თქვენს საყვარელ მუსიკას და უბრალოდ დაისვენეთ 10 წუთით.",
  "🍎 მოამზადეთ რაიმე გემრიელი და ჯანსაღი დღეს.",
  "💭 ჩაწერეთ ერთი დიდი ოცნება და ერთი პატარა ნაბიჯი მისკენ.",
  "🌸 იპოვეთ რაიმე ლამაზი თქვენს სახლში ან ქუჩაში და გადაიღეთ ფოტო.",
  "🛌 დაძინებამდე იფიქრეთ სამ რამეზე, რამაც დღეს უფრო ბედნიერი გაგხადათ.",
  "💌 დაწერეთ წერილი თქვენს მომავალ მეს: რა გსურთ თქვათ ერთ წელიწადში?",
  "🔄 შეეცადეთ დღეს რამე განსხვავებულად გააკეთოთ, თუნდაც პატარა რამ.",
  "🙌 3-ჯერ ღრმად ჩაისუნთქეთ, დახუჭეთ თვალები და მადლობა გადაუხადეთ საკუთარ თავს, რომ ხართ ის, ვინც ხართ.",
  "🎨 დაუთმეთ 5 წუთი შემოქმედებითობას — დახატეთ სურათი, ლექსი ან კოლაჟი.",
  "🧘‍♀️ დაჯექით 3 წუთით ჩუმად და უბრალოდ უყურეთ თქვენს სუნთქვას.",
  "📂 დაალაგეთ ერთი თარო, უჯრა ან საქაღალდე — ცოტა რომ დაალაგოთ.",
  "👋 მიუახლოვდით უცნობ ადამიანს დღეს და დაიწყეთ მეგობრული საუბარი. დაე, ეს იყოს მხოლოდ კომპლიმენტი ან კარგი დღის სურვილი!",
  "🤝 მიესალმეთ დღეს მინიმუმ სამ ახალ ადამიანს — ღიმილიც მნიშვნელოვანია!",
  "💬 ჰკითხეთ კოლეგას ან ნაცნობს დღეს ისეთი კითხვა, რომელსაც ჩვეულებრივ არ სვამთ. მაგალითად: „რა გაძლევთ შთაგონებას?“",
  "😊 უთხარით უცნობს კომპლიმენტი — ეს შეიძლება იყოს ბარისტა, გამყიდველი ან გამვლელი.",
  "📱 დაურეკეთ ადამიანს, ვისთანაც დიდი ხანია არ გისაუბრიათ და უბრალოდ ჰკითხეთ, როგორ არის.",
  "💡 დაიწყეთ მოკლე საუბარი მეზობელთან ან რიგში მდგომ ადამიანთან — უბრალოდ ამინდზე ან თქვენს გარშემო არსებულ რამეზე.",
  "🍀 გაუღიმეთ პირველ ადამიანს, ვისაც დღეს შეხვდებით გულწრფელად და ნახეთ, როგორ რეაგირებს.",
  "🙌 იპოვეთ საინტერესო ადამიანი სოციალურ ქსელებში და მისწერეთ მას მადლობა იმისთვის, რასაც აკეთებს.",
  "🎯 დაიწყეთ საუბარი მინიმუმ ერთი ახალი ნაცნობი თემით დღეს: ჰკითხეთ ოცნებებზე, საყვარელ წიგნებზე ან ფილმებზე.",
  "🌟 მიდით კოლეგასთან ან ნაცნობთან და უთხარით: „მადლობა, რომ ჩემს ცხოვრებაში ხართ“ — და უყურეთ, როგორ იღიმება.",
  "🔥 თუ შესაძლებელია, წადით ახალ ადგილას (კაფე, პარკი, მაღაზია) და დაიწყეთ საუბარი მინიმუმ ერთ ადამიანთან იქ.",
  "🌞 დილით პირველ შემხვედრ ადამიანს თბილი სიტყვა უთხარით — დღე პოზიტიურ ნოტაზე დაეწყოს!",
  "🍀 დაეხმარეთ ვინმეს დღეს წვრილმანში: კარი გაუღეთ, ადგილი დაუთმეთ, რამე მიეცით.",
  "🤗 შეაქეთ კოლეგა ან მეგობარი იმისთვის, რაც კარგად გააკეთა.",
  "👂 დაუსვით ვინმეს დღეს ღრმა კითხვა: „რა გაბედნიერებთ?“ და მოუსმინეთ პასუხს.",
  "🎈 აჩუქეთ ვინმეს ღიმილი დღეს და უთხარით: „შენ საოცარი ხარ!“",
  "📚 მიდით ვინმესთან ბიბლიოთეკაში, წიგნის მაღაზიაში ან კაფეში და ჰკითხეთ: „რას კითხულობ ახლა?“",
  "🔥 იპოვეთ მიზეზი, რომ დღეს ვინმეს შთააგონოთ: მიეცით რჩევა, გაუზიარეთ ისტორია, ისაუბრეთ თქვენს გამოცდილებაზე.",
  "🎨 წადით ახალ ადგილას (გამოფენაზე, ქუჩაზე, პარკში) და ჰკითხეთ ვინმეს: „პირველად ხართ აქ?“",
  "🌟 თუ ვინმეზე ლამაზ სამოსს ან სტილს ხედავთ, პირდაპირ უთხარით.",
  "🎧 ჩართეთ მუსიკა და გაამხნევეთ თქვენი მეგობრები: გაუგზავნეთ მათ თქვენთვის სასურველი ტრეკი კომენტარით: „მოუსმინე, ეს მოგერგება!“",
  "🕊️ დღესვე სცადეთ ხანდაზმულ ადამიანთან საუბარი — რჩევა სთხოვეთ ან უბრალოდ კარგი დღე უსურვეთ.",
  "🏞️ ძაღლის გასეირნებისას მიდით ვინმესთან და უთხარით: „შენი ძაღლი საოცარია! რა ჰქვია მას?“",
  "☕ უყიდეთ ყავა რიგში მდგომ ადამიანს — უბრალოდ იმიტომ.",
  "🙌 დღესვე დაურეკეთ მინიმუმ ერთ არასამსახურებრივ ზარს — უბრალოდ სასაუბროდ.",
  "🚀 იპოვეთ ახალი იდეა პროექტისთვის და ჩაიწერეთ.",
  "🎯 ჩაწერეთ 5 რამ, რისი გაკეთებაც გსურთ ამ კვირაში.",
  "🌊 მოუსმინეთ ბუნების ხმებს და დაისვენეთ.",
  "🍋 გასინჯეთ ახალი სასმელი ან საჭმელი დღეს.",
  "🌱 დარგეთ ან მოუარეთ მცენარე დღეს.",
  "🧩 ამოხსენით პატარა თავსატეხი ან გამოცანა.",
  "🎶 იცეკვეთ 5 წუთის განმავლობაში თქვენი საყვარელი სიმღერის რიტმში.",
  "📅 დაგეგმეთ თქვენი იდეალური დღე და ჩაიწერეთ.",
  "🖼️ იპოვეთ ლამაზი სურათი და ჩამოკიდეთ თვალსაჩინო ადგილას.",
  "🤔 დაწერეთ, რითი ამაყობთ დღეს.",
  "💜 გააკეთეთ რაიმე სასიამოვნო საკუთარი თავისთვის ახლავე."
],
"ce" : [
  "✨ ДӀаязде таханахь баркалла бохуш долу 3 хӀума.",
  "🚶‍♂️ Телефон йоцуш 10 минотехь лела. Са а даьккхина, тергал де.",
  "📝 Кхана хир йолчу Ӏалашонийн жима список язъе.",
  "🌿 30 минот соца медиенаш йоцуша ца хаамаш — кхин тӀехь дахьанаш.",
  "💧 Цхьа стакан хи а молуш, куьзхьа хьалха велакъежа. Хьо лелош ву!",
  "📖 Тахана хьайна догойуш йолчу киншкин лаххара а 5 агӀо еша.",
  "🤝 Смс язъе хьайца къамел ца диначу доттагӀчуьнга.",
  "🖋️ 5 минотехь дӀайазде хьайна хилахь – фильтр ешна.",
  "🏃‍♀️ Хьажа хийцара хийттара, я 10 чӀажо хаамаш тӀехь.",
  "🎧 Лаха хьайна лелош йоцу музика, 10 минот дац даьккха.",
  "🍎 Лаха дийна гӀазотто хьажа хьалха лелоша и пайдеш.",
  "💭 ДӀайазде цхьа кхулда къобал хӀума да цхьа мацахь мотт хӀумаш.",
  "🌸 Лаха хьажа кӀан йолуш лаьм дац даьккха, сурт дагӀа.",
  "🛌 ДӀавижале даьккха 3 хӀуман, хьажахь лахахь таханахь дийца хьоьшу.",
  "💌 Лаха хьалха ца хийцара «со» – ма лелош хьоьшу цхьанна шо?",
  "🔄 Цхьа мацахь хийцара тӀе хийцар, да мацахь цхьа хийцар.",
  "🙌 3 хӀежа йоцуш, ца хьажахь дӀайаш, шун йоцуша хьо болу хьажар.",
  "🎨 5 минот кхоллараллин болх – сурт дагӀа, ши дагӀа, коллаж.",
  "🧘‍♀️ 3 минотехь чума ца хаам, тӀаьккха хьовсаш.",
  "📂 Къамел тӀехь да аьтта ахьац, малача хила.",
  "👋 Хийрачу стагана ца гӀой, къамел къолла комплимент.",
  "🤝 3 хийрачу стаганаш «салам» ала – велакъежар а лоруш ду.",
  "💬 Коллегаш кхин йац, хӀин йац: «Мох болу хьоьшу хӀум?»",
  "😊 Комплимент хийрачу стагана – бариста, йохкархо, тӀехволуш.",
  "📱 Телефон тоха цхьа ю, хьайца ца диначу стаге, со лела?",
  "💡 ДӀадоладе мела жимма, стаганаш да тӀехволуш – кхин аьтта ам, кхин агӀо.",
  "🍀 Хьалха хийрачу стагана ца хьакъе лаьтта, велакъежа.",
  "🙌 Интересан хӀун йац соца медиенаш тӀехь, дӀайазде йа.",
  "🎯 Цхьа къобал кхолларалли тема лаьтта – книшка, кинема, къобал.",
  "🌟 Коллегаш лаьтта, дӀадаш: «Дик къобал хьоьшу хьажа»",
  "🔥 Кафе, парк, туька – кхин гӀой, стаганаш къамел даьккха.",
  "🌞 Юйранна хьайна дуьхьалкхеттачу стаге комплимент ала.",
  "🍀 Къобал ахӀалло: тӀехьа кар даьккха, ордуш даьккха.",
  "🤗 Коллегаш даьккха: «Дик болу хьажа!»",
  "👂 Цхьа хӀум хьоьшу ирсе дерг, хьоьшу лаха?",
  "🎈 Тахана цхьа велакъежа, дӀайазде: «Шен дик болу!»",
  "📚 КинскагӀа лаьтта, къамел: «Ма къобал хьоьшу?»",
  "🔥 Цхьа къобал йац: дацхье, дийцар лаьтта, хьалха болу.",
  "🎨 Керлачу метте лаьтта, стаганаш: «Цхьанна кхин дуй?»",
  "🌟 Лахахь лахара, комплимент ала.",
  "🎧 Музика дагӀа, дӀайазде друзяш: «Лаха хьоьшу!»",
  "🕊️ Хьажа стаганаш лаьтта, хьажа хьалха болу.",
  "🏞️ Йогу хьакъе лаьтта: «Шен йогу дик болу! Ма цӀе хӀун?»",
  "☕ Хьакъе лаьттачунна кофе хила.",
  "🙌 Цхьа ма телефон тоха, ца бизнес, просто чата.",
  "🚀 Лаха цхьа новая идея, дӀайазде.",
  "🎯 Цхьа 5 хӀума дӀайазде, кхин аьтта хьалха.",
  "🌊 Лаха табиатан деш, лаха хьажа.",
  "🍋 Лаха юрг хьажа.",
  "🌱 Лаха орамат, тӀехь хийцара.",
  "🧩 Жима хӀетал-метал дац даьккха.",
  "🎶 5 минотехь къобал музика тӀехь дацхьа.",
  "📅 Лаха идеал день, дӀайазде.",
  "🖼️ Сурт дагӀа, кхеташ йолуш.",
  "🤔 ДӀайазде мох а лаьтта, хьажа болу.",
  "💜 Лаха дӀахӀуьйре хьалха болу."
],
"en" : [
  "✨ Write down 3 things you're grateful for today.",
  "🚶‍♂️ Take a 10-minute walk without your phone. Just breathe and observe.",
  "📝 Write a short list of goals for tomorrow.",
  "🌿 Try spending 30 minutes without social media. How does that feel?",
  "💧 Drink a glass of water and smile at yourself in the mirror. You're doing great!",
  "📖 Read at least 5 pages of a book that inspires you today.",
  "🤝 Text a friend you haven't talked to in a while.",
  "🖋️ Keep a journal for 5 minutes — write everything that's in your head without filters.",
  "🏃‍♀️ Do a light warm-up or 10 squats right now!",
  "🎧 Listen to your favorite music and just relax for 10 minutes.",
  "🍎 Cook yourself something tasty and healthy today.",
  "💭 Write down one big dream and one small step towards it.",
  "🌸 Find something beautiful in your house or on the street and take a photo.",
  "🛌 Before going to bed, think about three things that made you happier today.",
  "💌 Write a letter to your future self: what do you want to say in a year?",
  "🔄 Try to do something differently today, even a small thing.",
  "🙌 Take 3 deep breaths, close your eyes and thank yourself for being you.",
  "🎨 Spend 5 minutes being creative — sketch a picture, write a poem or make a collage.",
  "🧘‍♀️ Sit for 3 minutes in silence and just watch your breathing.",
  "📂 Sort out one shelf, drawer or folder to tidy up a little.",
  "👋 Approach a stranger today and start a friendly conversation. Let it be just a compliment or a wish for a good day!",
  "🤝 Say 'hi' to at least three new people today — a smile counts too!",
  "💬 Ask a colleague or acquaintance a question today that you usually don’t ask. For example: 'What inspires you?'",
  "😊 Compliment a stranger. It could be a barista, a salesperson or a passerby.",
  "📱 Call someone you haven’t talked to in a while and just ask how they’re doing.",
  "💡 Start a short conversation with a neighbor or a person in line — just about the weather or something around you.",
  "🍀 Smile at the first person you meet today. Sincerely. And see how they react.",
  "🙌 Find an interesting person on social networks and write them a message thanking them for what they do.",
  "🎯 Start at least one new topic of conversation today: ask about dreams, favorite books or movies.",
  "🌟 Go up to a colleague or acquaintance and say: 'Thank you for being in my life' — and watch how they smile.",
  "🔥 If possible, go to a new place (cafe, park, store) and start a conversation with at least one person there.",
  "🌞 In the morning, say a kind word to the first person you meet — let your day start on a positive note!",
  "🍀 Help someone today with a little thing: hold the door, give up your seat, give them something.",
  "🤗 Praise a colleague or friend for something they did well.",
  "👂 Ask someone a deep question today: 'What makes you happy?' and listen to the answer.",
  "🎈 Give someone a smile today and say: 'You're awesome!'",
  "📚 Go up to someone in a library, bookstore, or cafe and ask: 'What are you reading now?'",
  "🔥 Find a reason to inspire someone today: give advice, share a story, talk about your experience.",
  "🎨 Go to a new place (exhibition, street, park) and ask someone: 'Is this your first time here?'",
  "🌟 If you see a beautiful outfit or style on someone, say so directly.",
  "🎧 Turn on some music and cheer up your friends: send them a track you like with the comment: 'Listen, this will suit you!'",
  "🕊️ Try talking to an older person today — ask for advice or just wish them a good day.",
  "🏞️ While walking a dog, go up to someone and say: 'Your dog is amazing! What's their name?'",
  "☕ Buy a coffee for the person behind you in line. Just because.",
  "🙌 Make at least one non-business phone call today, just to chat.",
  "🚀 Find a new idea for a project and write it down.",
  "🎯 Write down 5 things you want to accomplish this week.",
  "🌊 Listen to the sounds of nature and relax.",
  "🍋 Try a new drink or food today.",
  "🌱 Plant or take care of a plant today.",
  "🧩 Do a small puzzle or solve a riddle.",
  "🎶 Dance for 5 minutes to your favorite song.",
  "📅 Plan your perfect day and write it down.",
  "🖼️ Find a beautiful picture and hang it in a prominent place.",
  "🤔 Write down what you are proud of yourself for today.",
  "💜 Do something nice for yourself right now."
]
}
   
def get_random_daily_task(user_id: str) -> str:
    # Получаем язык пользователя, если нет — по умолчанию русский
    lang = user_languages.get(user_id, "ru")
    # Выбираем список для языка или дефолтный
    tasks = DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG["ru"])
    # Возвращаем случайное задание
    return random.choice(tasks)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # если язык ещё не выбран — показываем кнопки выбора
    if user_id not in user_languages:
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
            ],
            [   
                InlineKeyboardButton("Нохчийн мотт 🇷🇺", callback_data="lang_ce"),
                InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
            ]
        ]

        await update.message.reply_text(
            "🌐 Пожалуйста, выбери язык общения:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # если язык выбран — выводим приветствие
    lang_code = user_languages.get(user_id, "ru")
    first_name = update.effective_user.first_name or "друг"

    welcome_text = WELCOME_TEXTS.get(lang_code, WELCOME_TEXTS["ru"]).format(first_name=first_name)

    # создаём историю диалога с выбранным языком
    system_prompt = f"{LANG_PROMPTS.get(lang_code, LANG_PROMPTS['ru'])}\n\n{MODES['default']}"
    conversation_history[user_id] = [{"role": "system", "content": system_prompt}]
    save_history(conversation_history)

    await update.message.reply_text(welcome_text, parse_mode="Markdown")


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
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # ✅ Тексты help на 10 языках
    help_texts = {
        "ru": (
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
            "💎 Mindra+ функции:\n"
            "/premium_report — личный отчёт\n"
            "/premium_challenge — уникальный челлендж\n"
            "/premium_mode — эксклюзивный режим\n"
            "/premium_stats — расширенная статистика\n\n"
            "😉 Попробуй! А с подпиской возможностей будет ещё больше 💜"
        ),
        "uk": (
            "✨ Ось що я вмію:\n\n"
            "💬 Просто напиши мені повідомлення — я відповім.\n"
            "🧠 Я запам’ятовую історію спілкування (можна скинути).\n\n"
            "📎 Основні команди:\n"
            "/start — привітання\n"
            "/reset — скинути історію\n"
            "/help — показати це повідомлення\n"
            "/about — трохи про мене\n"
            "/mode — змінити стиль спілкування\n"
            "/goal — поставити ціль\n"
            "/goals — список цілей\n"
            "/habit — додати звичку\n"
            "/habits — список звичок\n"
            "/task — завдання на день\n"
            "/feedback — надіслати відгук\n"
            "/remind — нагадати про ціль\n"
            "/done — позначити ціль виконаною\n"
            "/mytask — персональне завдання\n"
            "/test_mood — протестувати настрій\n\n"
            "/language — вибрати мову 🌐\n\n"
            "💎 Mindra+ функції:\n"
            "/premium_report — звіт\n"
            "/premium_challenge — унікальний челендж\n"
            "/premium_mode — ексклюзивний режим\n"
            "/premium_stats — розширена статистика\n\n"
            "😉 Спробуй! З підпискою можливостей більше 💜"
        ),
        "be": (
            "✨ Вось што я ўмею:\n\n"
            "💬 Проста напішы мне паведамленне — я адкажу.\n"
            "🧠 Я запамінаю гісторыю зносін (можна скінуць).\n\n"
            "📎 Асноўныя каманды:\n"
            "/start — прывітанне\n"
            "/reset — скінуць гісторыю\n"
            "/help — паказаць гэта паведамленне\n"
            "/about — трохі пра мяне\n"
            "/mode — змяніць стыль зносін\n"
            "/goal — паставіць мэту\n"
            "/goals — спіс мэтаў\n"
            "/habit — дадаць звычку\n"
            "/habits — спіс звычак\n"
            "/task — заданне на дзень\n"
            "/feedback — даслаць водгук\n"
            "/remind — нагадаць пра мэту\n"
            "/done — адзначыць мэту выкананай\n"
            "/mytask — персаналізаванае заданне\n"
            "/test_mood — праверыць настрой\n\n"
            "/language — выбраць мову 🌐\n\n"
            "💎 Mindra+ функцыі:\n"
            "/premium_report — асабісты справаздачу\n"
            "/premium_challenge — унікальны чэлендж\n"
            "/premium_mode — эксклюзіўны рэжым\n"
            "/premium_stats — пашыраная статыстыка\n\n"
            "😉 Паспрабуй! З падпіскай магчымасцей больш 💜"
        ),
        "kk": (
            "✨ Міне не істей аламын:\n\n"
            "💬 Маған хабарлама жаз — мен жауап беремін.\n"
            "🧠 Мен сөйлесу тарихын есте сақтаймын (тазалауға болады).\n\n"
            "📎 Негізгі командалар:\n"
            "/start — сәлемдесу\n"
            "/reset — тарихты тазалау\n"
            "/help — осы хабарламаны көрсету\n"
            "/about — мен туралы\n"
            "/mode — сөйлесу стилін өзгерту\n"
            "/goal — мақсат қою\n"
            "/goals — мақсаттар тізімі\n"
            "/habit — әдет қосу\n"
            "/habits — әдеттер тізімі\n"
            "/task — күннің тапсырмасы\n"
            "/feedback — пікір жіберу\n"
            "/remind — мақсат туралы еске салу\n"
            "/done — мақсатты орындалған деп белгілеу\n"
            "/mytask — жеке тапсырма\n"
            "/test_mood — көңіл-күйді тексеру\n\n"
            "/language — тілді таңдау 🌐\n\n"
            "💎 Mindra+ мүмкіндіктері:\n"
            "/premium_report — жеке есеп\n"
            "/premium_challenge — ерекше челлендж\n"
            "/premium_mode — эксклюзивті режим\n"
            "/premium_stats — кеңейтілген статистика\n\n"
            "😉 Қолданып көр! Жазылумен мүмкіндіктер көбірек 💜"
        ),
        "kg": (
            "✨ Мына нерселерди кыла алам:\n\n"
            "💬 Жөн эле мага кабар жаз — жооп берем.\n"
            "🧠 Мен сүйлөшүүнү эстеп калам (тазалоого болот).\n\n"
            "📎 Негизги буйруктар:\n"
            "/start — саламдашуу\n"
            "/reset — тарыхты тазалоо\n"
            "/help — ушул билдирүүнү көрсөтүү\n"
            "/about — мен жөнүндө\n"
            "/mode — сүйлөшүү стилин өзгөртүү\n"
            "/goal — максат коюу\n"
            "/goals — максаттар тизмеси\n"
            "/habit — көнүмүш кошуу\n"
            "/habits — көнүмүштөр тизмеси\n"
            "/task — күндүн тапшырмасы\n"
            "/feedback — пикир жөнөтүү\n"
            "/remind — максат жөнүндө эскертүү\n"
            "/done — максатты аткарылган деп белгилөө\n"
            "/mytask — жеке тапшырма\n"
            "/test_mood — маанайды текшерүү\n\n"
            "/language — тил тандоо 🌐\n\n"
            "💎 Mindra+ мүмкүнчүлүктөрү:\n"
            "/premium_report — жеке отчет\n"
            "/premium_challenge — өзгөчө тапшырма\n"
            "/premium_mode — эксклюзивдүү режим\n"
            "/premium_stats — кеңейтилген статистика\n\n"
            "😉 Байкап көр! Жазылуу менен мүмкүнчүлүктөр көбөйөт 💜"
        ),
        "hy": (
            "✨ Ահա, թե ինչ կարող եմ անել․\n\n"
            "💬 Просто գրիր ինձ — ես կպատասխանեմ։\n"
            "🧠 Ես հիշում եմ զրույցի պատմությունը (կարող ես վերականգնել)։\n\n"
            "📎 Հիմնական հրամաններ․\n"
            "/start — ողջույն\n"
            "/reset — զրույցի պատմությունը մաքրել\n"
            "/help — ցույց տալ այս հաղորդագրությունը\n"
            "/about — իմ մասին\n"
            "/mode — փոխել շփման ոճը\n"
            "/goal — դնել նպատակ\n"
            "/goals — նպատակների ցուցակ\n"
            "/habit — ավելացնել սովորություն\n"
            "/habits — սովորությունների ցուցակ\n"
            "/task — օրվա առաջադրանք\n"
            "/feedback — ուղարկել արձագանք\n"
            "/remind — հիշեցնել նպատակը\n"
            "/done — նշել նպատակը կատարված\n"
            "/mytask — անհատական առաջադրանք\n"
            "/test_mood — ստուգել տրամադրությունը\n\n"
            "/language — ընտրել լեզուն 🌐\n\n"
            "💎 Mindra+ հնարավորություններ․\n"
            "/premium_report — անձնական հաշվետվություն\n"
            "/premium_challenge — բացառիկ մարտահրավեր\n"
            "/premium_mode — բացառիկ ռեժիմ\n"
            "/premium_stats — ընդլայնված վիճակագրություն\n\n"
            "😉 Փորձիր! Բաժանորդագրությամբ հնարավորությունները ավելի շատ են 💜"
        ),
        "ce": (
            "✨ Цхьа хьоьшу болу:\n\n"
            "💬 ДӀайазде ма кхоллараллин — са йаьлла.\n"
            "🧠 Са гӀирса тарих йац (цхьа мацахь йаьлла).\n\n"
            "📎 Нохчи командеш:\n"
            "/start — салам алам\n"
            "/reset — тарих лелош\n"
            "/help — кхета хийцам\n"
            "/about — са йац\n"
            "/mode — стили тӀетохьа\n"
            "/goal — мацахь кхоллар\n"
            "/goals — мацахьер список\n"
            "/habit — йоцу привычка\n"
            "/habits — привычкаш список\n"
            "/task — тахана дӀаязде\n"
            "/feedback — йа дӀайазде отзыв\n"
            "/remind — мацахьер дӀадела\n"
            "/done — мацахьер дӀанисса\n"
            "/mytask — персонал дӀаязде\n"
            "/test_mood — хьовса теста\n\n"
            "/language — моттиг дахьа 🌐\n\n"
            "💎 Mindra+ функцеш:\n"
            "/premium_report — личный отчет\n"
            "/premium_challenge — эксклюзивный челлендж\n"
            "/premium_mode — эксклюзивный режим\n"
            "/premium_stats — статистика\n\n"
            "😉 Хьажа хьоьшу! Подписка йолуш, функцеш къобал болу 💜"
        ),
        "md": (
            "✨ Iată ce pot face:\n\n"
            "💬 Scrie-mi un mesaj — îți voi răspunde.\n"
            "🧠 Îmi amintesc istoricul conversației (poți reseta).\n\n"
            "📎 Comenzi principale:\n"
            "/start — salut\n"
            "/reset — resetează istoricul\n"
            "/help — arată acest mesaj\n"
            "/about — despre mine\n"
            "/mode — schimbă stilul de comunicare\n"
            "/goal — setează un obiectiv\n"
            "/goals — lista obiectivelor\n"
            "/habit — adaugă un obicei\n"
            "/habits — lista obiceiurilor\n"
            "/task — sarcina zilei\n"
            "/feedback — trimite feedback\n"
            "/remind — amintește de un obiectiv\n"
            "/done — marchează obiectivul îndeplinit\n"
            "/mytask — sarcină personalizată\n"
            "/test_mood — testează starea\n\n"
            "/language — alege limba 🌐\n\n"
            "💎 Funcții Mindra+:\n"
            "/premium_report — raport personal\n"
            "/premium_challenge — provocare unică\n"
            "/premium_mode — mod exclusiv\n"
            "/premium_stats — statistici avansate\n\n"
            "😉 Încearcă! Cu abonament ai mai multe opțiuni 💜"
        ),
        "ka": (
            "✨ აი, რას ვაკეთებ:\n\n"
            "💬 უბრალოდ მომწერე და გიპასუხებ.\n"
            "🧠 ვიმახსოვრებ დიალოგის ისტორიას (შეგიძლია გაასუფთავო).\n\n"
            "📎 ძირითადი ბრძანებები:\n"
            "/start — მისალმება\n"
            "/reset — ისტორიის გასუფთავება\n"
            "/help — ამ შეტყობინების ჩვენება\n"
            "/about — ჩემს შესახებ\n"
            "/mode — კომუნიკაციის სტილის შეცვლა\n"
            "/goal — მიზნის დაყენება\n"
            "/goals — შენი მიზნების სია\n"
            "/habit — ჩვევის დამატება\n"
            "/habits — ჩვევების სია\n"
            "/task — დღევანდელი დავალება\n"
            "/feedback — გამოგზავნე გამოხმაურება\n"
            "/remind — შეგახსენო მიზანი\n"
            "/done — დააფიქსირე მიზნის შესრულება\n"
            "/mytask — პერსონალური დავალება\n"
            "/test_mood — ტესტი განწყობაზე\n\n"
            "/language — აირჩიე ენა 🌐\n\n"
            "💎 Mindra+ ფუნქციები:\n"
            "/premium_report — პირადი ანგარიში\n"
            "/premium_challenge — უნიკალური გამოწვევა\n"
            "/premium_mode — ექსკლუზიური რეჟიმი\n"
            "/premium_stats — გაფართოებული სტატისტიკა\n\n"
            "😉 სცადე! გამოწერით შესაძლებლობები მეტია 💜"
        ),
        "en": (
            "✨ Here’s what I can do:\n\n"
            "💬 Just write me a message — I’ll reply.\n"
            "🧠 I remember the chat history (you can reset it).\n\n"
            "📎 Main commands:\n"
            "/start — greeting\n"
            "/reset — reset chat history\n"
            "/help — show this message\n"
            "/about — about me\n"
            "/mode — change chat style\n"
            "/goal — set a goal\n"
            "/goals — list your goals\n"
            "/habit — add a habit\n"
            "/habits — list your habits\n"
            "/task — daily task\n"
            "/feedback — send feedback\n"
            "/remind — remind about a goal\n"
            "/done — mark a goal as done\n"
            "/mytask — personalized task\n"
            "/test_mood — test your mood\n\n"
            "/language — choose language 🌐\n\n"
            "💎 Mindra+ features:\n"
            "/premium_report — personal progress report\n"
            "/premium_challenge — unique challenge\n"
            "/premium_mode — exclusive mode\n"
            "/premium_stats — extended statistics\n\n"
            "😉 Try it! With a subscription you’ll get even more 💜"
        ),
    }

    # ✅ Кнопки на 10 языков
    buttons_text = {
        "ru": ["🎯 Поставить цель", "📋 Мои цели", "🌱 Добавить привычку", "📊 Мои привычки", "💎 Подписка Mindra+"],
        "uk": ["🎯 Поставити ціль", "📋 Мої цілі", "🌱 Додати звичку", "📊 Мої звички", "💎 Підписка Mindra+"],
        "be": ["🎯 Паставіць мэту", "📋 Мае мэты", "🌱 Дадаць звычку", "📊 Мае звычкі", "💎 Падпіска Mindra+"],
        "kk": ["🎯 Мақсат қою", "📋 Менің мақсаттарым", "🌱 Әдет қосу", "📊 Менің әдеттерім", "💎 Mindra+ жазылу"],
        "kg": ["🎯 Максат коюу", "📋 Менин максаттарым", "🌱 Көнүмүш кошуу", "📊 Менин көнүмүштөрүм", "💎 Mindra+ жазылуу"],
        "hy": ["🎯 Դնել նպատակ", "📋 Իմ նպատակները", "🌱 Ավելացնել սովորություն", "📊 Իմ սովորությունները", "💎 Mindra+ բաժանորդագրություն"],
        "ce": ["🎯 Мацахь кхоллар", "📋 Са мацахь", "🌱 Привычка дац", "📊 Са привычка", "💎 Mindra+ подписка"],
        "en": ["🎯 Set a goal", "📋 My goals", "🌱 Add a habit", "📊 My habits", "💎 Mindra+ subscription"],
        "ro": ["🎯 Setează obiectiv", "📋 Obiectivele mele", "🌱 Adaugă obicei", "📊 Obiceiurile mele", "💎 Abonament Mindra+"],
        "ka": ["🎯 მიზნის დაყენება", "📋 ჩემი მიზნები", "🌱 ჩვევის დამატება", "📊 ჩემი ჩვევები", "💎 Mindra+ გამოწერა"]
    }

    # Получаем кнопки для текущего языка
    b = buttons_text.get(lang, buttons_text["ru"])
    keyboard = [
        [InlineKeyboardButton(b[0], callback_data="create_goal")],
        [InlineKeyboardButton(b[1], callback_data="show_goals")],
        [InlineKeyboardButton(b[2], callback_data="create_habit")],
        [InlineKeyboardButton(b[3], callback_data="show_habits")],
        [InlineKeyboardButton(b[4], url="https://t.me/talktomindra_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение
    await update.message.reply_text(help_texts.get(lang, help_texts["ru"]), reply_markup=reply_markup)

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
    user_id = str(update.effective_user.id)

    # Определяем язык пользователя (по умолчанию русский)
    lang = user_languages.get(user_id, "ru")

    # Словарь заголовков "Задание на день" для разных языков
    task_title = {
        "ru": "🎯 Задание на день:",
        "uk": "🎯 Завдання на день:",
        "be": "🎯 Заданне на дзень:",
        "kk": "🎯 Бүгінгі тапсырма:",
        "kg": "🎯 Бүгүнкү тапшырма:",
        "hy": "🎯 Այսօրվա առաջադրանքը:",
        "ce": "🎯 Тахана хьалха дӀаязде:",
        "en": "🎯 Task for today:",
        "md": "🎯 Sarcina pentru astăzi:",
        "ka": "🎯 დღევანდელი დავალება:"
    }

    # Берём список заданий для нужного языка
    tasks = DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG["ru"])

    # Выбираем случайное задание
    chosen_task = random.choice(tasks)

    # Отправляем сообщение с правильным заголовком
    await update.message.reply_text(f"{task_title.get(lang, task_title['ru'])}\n{chosen_task}")

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
    CommandHandler("language", language_command),
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
