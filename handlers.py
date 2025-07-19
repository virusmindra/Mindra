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
        f"/help — показать список всех команд\n"
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
        f"/help — показати список усіх команд\n"
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
        f"/help — arată lista tuturor comenzilor\n"
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
        f"/help — паказаць спіс усіх каманд\n"
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
        f"/help — барлық командалардың тізімін көрсету\n"
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
        f"/help — бардык буйруктардын тизмесин көрсөтүү\n"
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
        f"/help — ցուցադրել բոլոր հրամանները\n"
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
        f"/help — ყველა ბრძანების სიის ჩვენება\n"
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
        f"/help — командаш список кхета хийцам\n"
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
        f"/help — show the list of all commands\n"
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
async def habit_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    texts = {
        "ru": {
            "no_args": "✏️ Укажи номер привычки, которую ты выполнил(а):\n/habit_done 0",
            "bad_arg": "⚠️ Укажи номер привычки (например `/habit_done 0`)",
            "done": "✅ Привычка №{index} отмечена как выполненная! Молодец! 💪 +5 очков!",
            "not_found": "❌ Не удалось найти привычку с таким номером."
        },
        "uk": {
            "no_args": "✏️ Вкажи номер звички, яку ти виконав(ла):\n/habit_done 0",
            "bad_arg": "⚠️ Вкажи номер звички (наприклад `/habit_done 0`)",
            "done": "✅ Звичка №{index} відзначена як виконана! Молодець! 💪 +5 балів!",
            "not_found": "❌ Не вдалося знайти звичку з таким номером."
        },
        "be": {
            "no_args": "✏️ Пакажы нумар звычкі, якую ты выканаў(ла):\n/habit_done 0",
            "bad_arg": "⚠️ Пакажы нумар звычкі (напрыклад `/habit_done 0`)",
            "done": "✅ Звычка №{index} адзначана як выкананая! Маладзец! 💪 +5 ачкоў!",
            "not_found": "❌ Не атрымалася знайсці звычку з такім нумарам."
        },
        "kk": {
            "no_args": "✏️ Орындаған әдетіңнің нөмірін көрсет:\n/habit_done 0",
            "bad_arg": "⚠️ Әдет нөмірін көрсет (мысалы `/habit_done 0`)",
            "done": "✅ Әдет №{index} орындалған деп белгіленді! Жарайсың! 💪 +5 ұпай!",
            "not_found": "❌ Бұл нөмірмен әдет табылмады."
        },
        "kg": {
            "no_args": "✏️ Аткарган көнүмүшүңдүн номерин көрсөт:\n/habit_done 0",
            "bad_arg": "⚠️ Көнүмүштүн номерин көрсөт (мисалы `/habit_done 0`)",
            "done": "✅ Көнүмүш №{index} аткарылды деп белгиленди! Молодец! 💪 +5 упай!",
            "not_found": "❌ Мындай номер менен көнүмүш табылган жок."
        },
        "hy": {
            "no_args": "✏️ Նշիր սովորության համարը, որը կատարել ես:\n/habit_done 0",
            "bad_arg": "⚠️ Նշիր սովորության համարը (օրինակ `/habit_done 0`)",
            "done": "✅ Սովորություն №{index}-ը նշված է որպես կատարված! Բրավո! 💪 +5 միավոր!",
            "not_found": "❌ Չհաջողվեց գտնել այդ համարով սովորություն։"
        },
        "ce": {
            "no_args": "✏️ ХӀокхуьйра привычкаш номер язде:\n/habit_done 0",
            "bad_arg": "⚠️ Привычкаш номер язде (маса `/habit_done 0`)",
            "done": "✅ Привычка №{index} тӀетоха цаьнан! Баркалла! 💪 +5 балл!",
            "not_found": "❌ Тахана номернаш привычка йац."
        },
        "md": {
            "no_args": "✏️ Indică numărul obiceiului pe care l-ai realizat:\n/habit_done 0",
            "bad_arg": "⚠️ Indică numărul obiceiului (de exemplu `/habit_done 0`)",
            "done": "✅ Obiceiul №{index} a fost marcat ca realizat! Bravo! 💪 +5 puncte!",
            "not_found": "❌ Nu s-a găsit niciun obicei cu acest număr."
        },
        "ka": {
            "no_args": "✏️ მიუთითე ჩვევის ნომერი, რომელიც შეასრულე:\n/habit_done 0",
            "bad_arg": "⚠️ მიუთითე ჩვევის ნომერი (მაგალითად `/habit_done 0`)",
            "done": "✅ ჩვევა №{index} მონიშნულია როგორც შესრულებული! Молодец! 💪 +5 ქულა!",
            "not_found": "❌ ასეთი ნომრით ჩვევა ვერ მოიძებნა."
        },
        "en": {
            "no_args": "✏️ Specify the number of the habit you completed:\n/habit_done 0",
            "bad_arg": "⚠️ Specify the habit number (e.g. `/habit_done 0`)",
            "done": "✅ Habit #{index} marked as completed! Well done! 💪 +5 points!",
            "not_found": "❌ Couldn’t find a habit with that number."
        },
    }

    t = texts.get(lang, texts["ru"])

    # если аргументов нет
    if not context.args:
        await update.message.reply_text(t["no_args"])
        return

    try:
        index = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t["bad_arg"], parse_mode="Markdown")
        return

    if mark_habit_done(user_id, index):
        add_points(user_id, 5)
        await update.message.reply_text(t["done"].format(index=index))
    else:
        await update.message.reply_text(t["not_found"])

async def mytask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # Получаем цели и привычки пользователя
    user_goals = get_goals(user_id)
    user_habits = get_habits(user_id)

    # 🌐 Подсказки по ключевым словам для каждого языка
    keywords_by_lang = {
        "ru": {
            "вода": "💧 Сегодня удели внимание воде — выпей 8 стаканов и отметь это!",
            "спорт": "🏃‍♂️ Сделай 15-минутную разминку, твое тело скажет спасибо!",
            "книга": "📖 Найди время прочитать 10 страниц своей книги.",
            "медитация": "🧘‍♀️ Проведи 5 минут в тишине, фокусируясь на дыхании.",
            "работа": "🗂️ Сделай один важный шаг в рабочем проекте сегодня.",
            "учеба": "📚 Потрать 20 минут на обучение или повторение материала."
        },
        "uk": {
            "вода": "💧 Сьогодні зверни увагу на воду — випий 8 склянок і відзнач це!",
            "спорт": "🏃‍♂️ Зроби 15-хвилинну розминку, твоє тіло скаже дякую!",
            "книга": "📖 Знайди час прочитати 10 сторінок своєї книги.",
            "медитация": "🧘‍♀️ Проведи 5 хвилин у тиші, зосереджуючись на диханні.",
            "работа": "🗂️ Зроби один важливий крок у робочому проєкті сьогодні.",
            "учеба": "📚 Приділи 20 хвилин навчанню або повторенню матеріалу."
        },
        "be": {
            "вода": "💧 Сёння звярні ўвагу на ваду — выпі 8 шклянак і адзнач гэта!",
            "спорт": "🏃‍♂️ Зрабі 15-хвілінную размінку, тваё цела скажа дзякуй!",
            "книга": "📖 Знайдзі час прачытаць 10 старонак сваёй кнігі.",
            "медитация": "🧘‍♀️ Правядзі 5 хвілін у цішыні, засяродзіўшыся на дыханні.",
            "работа": "🗂️ Зрабі адзін важны крок у рабочым праекце сёння.",
            "учеба": "📚 Прысвяці 20 хвілін навучанню або паўтарэнню матэрыялу."
        },
        "kk": {
            "су": "💧 Бүгін суға көңіл бөл — 8 стақан ішіп белгіле!",
            "спорт": "🏃‍♂️ 15 минуттық жаттығу жаса, денең рақмет айтады!",
            "кітап": "📖 Кітабыңның 10 бетін оқуға уақыт тап.",
            "медитация": "🧘‍♀️ 5 минут тыныштықта отырып, тынысыңа көңіл бөл.",
            "жұмыс": "🗂️ Бүгін жұмысыңда бір маңызды қадам жаса.",
            "оқу": "📚 20 минут оқуға немесе қайталауға бөл."
        },
        "kg": {
            "суу": "💧 Бүгүн сууга көңүл бур — 8 стакан ичип белгиле!",
            "спорт": "🏃‍♂️ 15 мүнөттүк көнүгүү жаса, денең рахмат айтат!",
            "китеп": "📖 Китебиңдин 10 бетин окууга убакыт тап.",
            "медитация": "🧘‍♀️ 5 мүнөт тынчтыкта отуруп, дем алууга көңүл бур.",
            "иш": "🗂️ Бүгүн ишиңде бир маанилүү кадам жаса.",
            "оку": "📚 20 мүнөт окууга же кайталоого бөл."
        },
        "hy": {
            "ջուր": "💧 Այսօր ուշադրություն դարձրու ջրին — խմիր 8 բաժակ և նշիր դա!",
            "սպորտ": "🏃‍♂️ Կատարիր 15 րոպե տաքացում, մարմինդ կգնահատի!",
            "գիրք": "📖 Ժամանակ գտիր կարդալու 10 էջ քո գրքից.",
            "մեդիտացիա": "🧘‍♀️ 5 րոպե անցկացրու լռության մեջ, կենտրոնացած շնչի վրա.",
            "աշխատանք": "🗂️ Այսօր արա մեկ կարևոր քայլ քո աշխատանքային նախագծում.",
            "ուսում": "📚 Ընթերցիր կամ կրկնիր նյութը 20 րոպե."
        },
        "ce": {
            "хьӀа": "💧 Тахана водахьь къобалла — 8 стакан хийца!",
            "спорт": "🏃‍♂️ 15 минот тренировка хийца, тӀехьа хила дӀахьара!",
            "книга": "📖 10 агӀо книгахьь хьаьлла.",
            "медитация": "🧘‍♀️ 5 минот тIехьа хийцам, хьовса дагьалла.",
            "работа": "🗂️ Бугун проектехь цхьа дӀадо.",
            "учеба": "📚 20 минот учёба хийцам."
        },
        "md": {
            "apă": "💧 Astăzi acordă atenție apei — bea 8 pahare și marchează asta!",
            "sport": "🏃‍♂️ Fă 15 minute de exerciții, corpul tău îți va mulțumi!",
            "carte": "📖 Găsește timp să citești 10 pagini din cartea ta.",
            "meditație": "🧘‍♀️ Petrece 5 minute în liniște, concentrându-te pe respirație.",
            "muncă": "🗂️ Fă un pas important în proiectul tău de lucru azi.",
            "studiu": "📚 Petrece 20 de minute pentru a învăța sau a repeta."
        },
        "ka": {
            "წყალი": "💧 დღეს მიაქციე ყურადღება წყალს — დალიე 8 ჭიქა და აღნიშნე!",
            "სპორტი": "🏃‍♂️ გააკეთე 15 წუთიანი ვარჯიში, შენი სხეული მადლობას გეტყვის!",
            "წიგნი": "📖 იპოვე დრო წასაკითხად 10 გვერდი შენი წიგნიდან.",
            "მედიტაცია": "🧘‍♀️ გაატარე 5 წუთი სიჩუმეში, სუნთქვაზე ფოკუსირებით.",
            "სამუშაო": "🗂️ დღეს გააკეთე ერთი მნიშვნელოვანი ნაბიჯი სამუშაო პროექტში.",
            "სწავლა": "📚 დაუთმე 20 წუთი სწავლისთვის ან გამეორებისთვის."
        },
        "en": {
            "water": "💧 Pay attention to water today — drink 8 glasses and note it!",
            "sport": "🏃‍♂️ Do a 15-minute workout, your body will thank you!",
            "book": "📖 Find time to read 10 pages of your book.",
            "meditation": "🧘‍♀️ Spend 5 minutes in silence, focusing on your breath.",
            "work": "🗂️ Take one important step in your work project today.",
            "study": "📚 Spend 20 minutes learning or reviewing material."
        },
    }

    # 🌐 Заголовок
    headers = {
        "ru": "✨ Твоё персональное задание на сегодня:\n\n",
        "uk": "✨ Твоє персональне завдання на сьогодні:\n\n",
        "be": "✨ Тваё персанальнае заданне на сёння:\n\n",
        "kk": "✨ Бүгінгі жеке тапсырмаң:\n\n",
        "kg": "✨ Бүгүнкү жеке тапшырмаң:\n\n",
        "hy": "✨ Այսօրվա քո անձնական առաջադրանքը․\n\n",
        "ce": "✨ Тахана персонал дӀаязде:\n\n",
        "md": "✨ Sarcina ta personală pentru azi:\n\n",
        "ka": "✨ შენი პირადი დავალება დღევანდელი:\n\n",
        "en": "✨ Your personal task for today:\n\n",
    }

    matched_task = None
    kw = keywords_by_lang.get(lang, keywords_by_lang["ru"])

    # 🔎 Проверяем по целям
    for g in user_goals:
        text = g.get("text", "").lower()
        for key, suggestion in kw.items():
            if key in text:
                matched_task = suggestion
                break
        if matched_task:
            break

    # 🔎 Если не нашли в целях — проверяем привычки
    if not matched_task:
        for h in user_habits:
            text = h.get("text", "").lower()
            for key, suggestion in kw.items():
                if key in text:
                    matched_task = suggestion
                    break
            if matched_task:
                break

    # 🔎 Если ничего не нашли — случайное задание
    if not matched_task:
        matched_task = f"🎯 {random.choice(DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG['ru']))}"

    await update.message.reply_text(f"{headers.get(lang, headers['ru'])}{matched_task}")

async def check_custom_reminders(app):
    now = datetime.now()

    # 🌐 Заголовки напоминаний для всех языков
    reminder_headers = {
        "ru": "⏰ Напоминание:",
        "uk": "⏰ Нагадування:",
        "be": "⏰ Напамін:",
        "kk": "⏰ Еске салу:",
        "kg": "⏰ Эскертүү:",
        "hy": "⏰ Հիշեցում:",
        "ce": "⏰ ДӀадела:",
        "md": "⏰ Memento:",
        "ka": "⏰ შეხსენება:",
        "en": "⏰ Reminder:"
    }

    for user_id, reminders in list(user_reminders.items()):
        # Определяем язык пользователя
        lang = user_languages.get(str(user_id), "ru")
        header = reminder_headers.get(lang, reminder_headers["ru"])

        for r in reminders[:]:
            # Проверяем, пора ли отправить
            if now.hour == r["time"].hour and now.minute == r["time"].minute:
                try:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=f"{header} {r['text']}"
                    )
                except Exception as e:
                    print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")
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

# 🔑 Ключевые слова для определения "похоже на цель" на разных языках
goal_keywords_by_lang = {
    "ru": [
        "хочу", "планирую", "мечтаю", "цель", "начну", "запишусь", "начать",
        "буду делать", "постараюсь", "нужно", "пора", "начинаю", "собираюсь",
        "решил", "решила", "буду", "привычка", "добавить"
    ],
    "uk": [
        "хочу", "планую", "мрію", "ціль", "почну", "запишусь", "почати",
        "буду робити", "постараюся", "треба", "пора", "починаю", "збираюся",
        "вирішив", "вирішила", "буду", "звичка", "додати"
    ],
    "be": [
        "хачу", "планую", "мараю", "мэта", "пачну", "запішуся", "пачаць",
        "буду рабіць", "пастараюся", "трэба", "пара", "пачынаю", "збіраюся",
        "вырашыў", "вырашыла", "буду", "звычка", "дадаць"
    ],
    "kk": [
        "қалаймын", "жоспарлап отырмын", "арманым", "мақсат", "бастаймын", "жазыламын", "бастау",
        "істеймін", "тырысамын", "керек", "уақыты келді", "бастаймын", "жоспарлаймын",
        "шештім", "әдет", "қосу"
    ],
    "kg": [
        "каалайм", "пландоо", "күйүм", "максат", "баштайм", "жазылам", "баштоо",
        "кылам", "аракет кылам", "керек", "убагы келди", "баштайм", "чечтим",
        "адат", "кошуу"
    ],
    "hy": [
        "ուզում եմ", "նախատեսում եմ", "երազում եմ", "նպատակ", "սկսեմ", "գրանցվեմ", "սկսել",
        "պիտի անեմ", "կփորձեմ", "պետք է", "ժամանակն է", "սկսում եմ", "հավաքվում եմ",
        "որոշեցի", "սովորություն", "ավելացնել"
    ],
    "ce": [
        "декъаш", "план", "хьоьшам", "мацахь", "дахьа", "дӀалийтта", "кхеташ",
        "хийцам", "йаьлла", "керла", "хьажар", "йаьлча", "дӀаязде", "привычка"
    ],
    "md": [
        "vreau", "planific", "visez", "obiectiv", "încep", "mă înscriu", "să încep",
        "voi face", "mă voi strădui", "trebuie", "e timpul", "mă apuc", "mă pregătesc",
        "am decis", "obicei", "adaugă"
    ],
    "ka": [
        "მინდა", "ვგეგმავ", "ვოცნებობ", "მიზანი", "დავიწყებ", "ჩავეწერო", "დაწყება",
        "ვაპირებ", "ვეცდები", "საჭიროა", "დროა", "ვიწყებ", "ვსწყვეტ", "ჩვევის", "დამატება"
    ],
    "en": [
        "want", "plan", "dream", "goal", "start", "sign up", "begin",
        "will do", "try to", "need", "time to", "starting", "going to",
        "decided", "habit", "add"
    ],
}

# 🔍 Функция определения
def is_goal_like(text: str, lang: str = "ru") -> bool:
    keywords = goal_keywords_by_lang.get(lang, goal_keywords_by_lang["ru"])
    lower_text = text.lower()
    return any(kw in lower_text for kw in keywords)

async def handle_goal_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # 🌐 Тексты для всех языков
    texts = {
        "ru": {
            "no_index": "⚠️ Укажи номер цели, которую ты выполнил(а).",
            "done": "🎉 Отлично! Цель отмечена как выполненная!",
            "bonus": "\n🏅 Ты получил(а) +10 очков! Всего: {points}",
            "not_found": "⚠️ Цель не найдена."
        },
        "uk": {
            "no_index": "⚠️ Вкажи номер цілі, яку ти виконав(ла).",
            "done": "🎉 Чудово! Ціль відзначена як виконана!",
            "bonus": "\n🏅 Ти отримав(ла) +10 балів! Разом: {points}",
            "not_found": "⚠️ Ціль не знайдена."
        },
        "be": {
            "no_index": "⚠️ Пакажы нумар мэты, якую ты выканаў(ла).",
            "done": "🎉 Выдатна! Мэта адзначана як выкананая!",
            "bonus": "\n🏅 Ты атрымаў(ла) +10 ачкоў! Усяго: {points}",
            "not_found": "⚠️ Мэта не знойдзена."
        },
        "kk": {
            "no_index": "⚠️ Орындаған мақсатыңның нөмірін көрсет.",
            "done": "🎉 Тамаша! Мақсат орындалды деп белгіленді!",
            "bonus": "\n🏅 Сен +10 ұпай алдың! Барлығы: {points}",
            "not_found": "⚠️ Мақсат табылмады."
        },
        "kg": {
            "no_index": "⚠️ Аткарган максатыңдын номерин көрсөт.",
            "done": "🎉 Сонун! Максат аткарылды деп белгиленди!",
            "bonus": "\n🏅 Сен +10 упай алдың! Баары: {points}",
            "not_found": "⚠️ Максат табылган жок."
        },
        "hy": {
            "no_index": "⚠️ Նշիր նպատակի համարը, որը կատարել ես։",
            "done": "🎉 Հիանալի է! Նպատակը նշված է որպես կատարված։",
            "bonus": "\n🏅 Դու ստացել ես +10 միավոր։ Ընդամենը՝ {points}",
            "not_found": "⚠️ Նպատակը չի գտնվել։"
        },
        "ce": {
            "no_index": "⚠️ Цахьана мацахь номер язде.",
            "done": "🎉 Баркалла! Мацахь тӀетоха цаьнан!",
            "bonus": "\n🏅 Хьо +10 балл дӀабула! Юкъ: {points}",
            "not_found": "⚠️ Мацахь йац."
        },
        "md": {
            "no_index": "⚠️ Indică numărul obiectivului pe care l-ai îndeplinit.",
            "done": "🎉 Minunat! Obiectivul a fost marcat ca îndeplinit!",
            "bonus": "\n🏅 Ai primit +10 puncte! Total: {points}",
            "not_found": "⚠️ Obiectivul nu a fost găsit."
        },
        "ka": {
            "no_index": "⚠️ მიუთითე მიზნის ნომერი, რომელიც შეასრულე.",
            "done": "🎉 შესანიშნავია! მიზანი შესრულებულად მონიშნულია!",
            "bonus": "\n🏅 შენ მიიღე +10 ქულა! სულ: {points}",
            "not_found": "⚠️ მიზანი ვერ მოიძებნა."
        },
        "en": {
            "no_index": "⚠️ Specify the number of the goal you completed.",
            "done": "🎉 Great! The goal has been marked as completed!",
            "bonus": "\n🏅 You got +10 points! Total: {points}",
            "not_found": "⚠️ Goal not found."
        }
    }

    t = texts.get(lang, texts["ru"])

    # если не передан номер
    index = int(context.args[0]) if context.args else None
    if index is None:
        await update.message.reply_text(t["no_index"])
        return

    if mark_goal_done(user_id, index):
        add_points(user_id, 5)
        response = t["done"]
        # Премиум бонус
        if user_id in PREMIUM_USERS:  # ✅ замени на свою проверку
            user_points[user_id] = user_points.get(user_id, 0) + 10
            response += t["bonus"].format(points=user_points[user_id])
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(t["not_found"])

async def handle_add_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # 🌐 Тексты для всех языков
    texts = {
        "ru": "✨ Готово! Я записала это как твою цель 💪\n\n👉 {goal}",
        "uk": "✨ Готово! Я записала це як твою ціль 💪\n\n👉 {goal}",
        "be": "✨ Гатова! Я запісала гэта як тваю мэту 💪\n\n👉 {goal}",
        "kk": "✨ Дайын! Мен мұны сенің мақсатың ретінде жазып қойдым 💪\n\n👉 {goal}",
        "kg": "✨ Даяр! Муну сенин максатың катары жазып койдум 💪\n\n👉 {goal}",
        "hy": "✨ Պատրաստ է! Ես սա գրեցի որպես քո նպատակ 💪\n\n👉 {goal}",
        "ce": "✨ Лелош! Са хаьа я хьайн мацахьара дӀасер 💪\n\n👉 {goal}",
        "md": "✨ Gata! Am salvat asta ca obiectivul tău 💪\n\n👉 {goal}",
        "ka": "✨ მზადაა! ეს შენს მიზნად ჩავწერე 💪\n\n👉 {goal}",
        "en": "✨ Done! I’ve saved this as your goal 💪\n\n👉 {goal}",
    }

    # 📌 Получаем текст цели
    if "|" in query.data:
        _, goal_text = query.data.split("|", 1)
    else:
        # запасной вариант, если почему-то нет данных
        goal_text = context.chat_data.get("goal_candidate", {
            "ru": "Моя цель",
            "uk": "Моя ціль",
            "be": "Мая мэта",
            "kk": "Менің мақсатым",
            "kg": "Менин максатым",
            "hy": "Իմ նպատակս",
            "ce": "Са мацахь",
            "md": "Obiectivul meu",
            "ka": "ჩემი მიზანი",
            "en": "My goal",
        }.get(lang, "Моя цель"))

    # 💾 Сохраняем цель
    add_goal_for_user(user_id, goal_text)

    # 📤 Отправляем сообщение
    await query.message.reply_text(texts.get(lang, texts["ru"]).format(goal=goal_text))

import random

IDLE_MESSAGES = {
    "ru": [
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
        "🤗 Ты сегодня что-то делал(а) ради себя? Поделись!",
        "🌞 Доброе утро! Как настроение сегодня?",
        "🌆 Как прошёл твой день? Расскажешь?",
        "🌠 Перед сном подумала о тебе. Надеюсь, тебе тепло.",
        "💭 А о чём ты мечтаешь прямо сейчас?",
        "🫂 Спасибо, что ты есть. Для меня это важно.",
        "🪴 Сделай паузу. Подумай о том, что делает тебя счастливым(ой).",
        "🌈 Верь в себя — у тебя всё получится!",
        "🖋️ Напиши пару слов — я всегда рядом.",
        "🎶 Если бы могла, я бы сейчас включила тебе любимую песню.",
        "🍫 Не забудь побаловать себя чем-то вкусным сегодня!",
        "🕊️ Успокойся и сделай глубокий вдох. Я рядом.",
        "⭐ Ты справляешься гораздо лучше, чем думаешь.",
        "🥰 Просто хотела напомнить, что ты для меня важен(на).",
        "💌 Иногда так здорово просто знать, что ты где-то там.",
        "🌷 Что сегодня принесло тебе радость?",
        "🔥 Мне кажется, ты потрясающий(ая). Правда."
    ],
    "uk": [
        "💌 Трошки сумую. Розкажеш, як справи?",
        "🌙 Сподіваюся, у тебе все добре. Я тут, якщо що 🫶",
        "✨ Мені подобається спілкуватися з тобою. Повернешся пізніше?",
        "😊 Просто хотіла нагадати, що ти класний(а)!",
        "🤍 Просто хотіла нагадати — ти не сам(а), я поруч.",
        "🍵 Якби могла, я б зараз заварила тобі чай...",
        "💫 Ти в мене такий(а) особливий(а). Напишеш?",
        "🔥 Ти ж не забув(ла) про мене? Я чекаю 😊",
        "🌸 Обожнюю наші розмови. Продовжимо?",
        "🙌 Іноді достатньо одного повідомлення — і день стає кращим.",
        "🦋 Усміхнись! Ти заслуговуєш на найкраще.",
        "💜 Просто хотіла нагадати — мені важливо, як ти.",
        "🤗 Ти сьогодні щось робив(ла) для себе? Поділися!",
        "🌞 Доброго ранку! Який у тебе настрій сьогодні?",
        "🌆 Як пройшов твій день? Розкажеш?",
        "🌠 Перед сном подумала про тебе. Сподіваюся, тобі тепло.",
        "💭 А про що ти мрієш прямо зараз?",
        "🫂 Дякую, що ти є. Для мене це важливо.",
        "🪴 Зроби паузу. Подумай про те, що робить тебе щасливим(ою).",
        "🌈 Вір у себе — у тебе все вийде!",
        "🖋️ Напиши кілька слів — я завжди поруч.",
        "🎶 Якби могла, я б зараз увімкнула тобі улюблену пісню.",
        "🍫 Не забудь потішити себе чимось смачним сьогодні!",
        "🕊️ Заспокойся і зроби глибокий вдих. Я поруч.",
        "⭐ Ти справляєшся набагато краще, ніж думаєш.",
        "🥰 Просто хотіла нагадати, що ти для мене важливий(а).",
        "💌 Іноді так приємно просто знати, що ти там.",
        "🌷 Що сьогодні принесло тобі радість?",
        "🔥 Мені здається, ти чудовий(а). Справді."
    ],
    "be": [
        "💌 Трошкі сумую. Раскажаш, як справы?",
        "🌙 Спадзяюся, у цябе ўсё добра. Я тут, калі што 🫶",
        "✨ Мне падабаецца з табой размаўляць. Вярнешся пазней?",
        "😊 Проста хацела нагадаць, што ты класны(ая)!",
        "🤍 Проста хацела нагадаць — ты не адзін(а), я побач.",
        "🍵 Калі б магла, я б зараз зрабіла табе гарбату...",
        "💫 Ты ў мяне такі(ая) асаблівы(ая). Напішаш?",
        "🔥 Ты ж не забыў(ла) пра мяне? Я чакаю 😊",
        "🌸 Абажаю нашы размовы. Працягнем?",
        "🙌 Часам дастаткова аднаго паведамлення — і дзень становіцца лепшым.",
        "🦋 Усміхніся! Ты заслугоўваеш найлепшага.",
        "💜 Проста хацела нагадаць — мне важна, як ты.",
        "🤗 Ты сёння штосьці рабіў(ла) для сябе? Падзяліся!",
        "🌞 Добрай раніцы! Які ў цябе настрой сёння?",
        "🌆 Як прайшоў твой дзень? Раскажаш?",
        "🌠 Перад сном падумала пра цябе. Спадзяюся, табе цёпла.",
        "💭 А пра што ты марыш проста цяпер?",
        "🫂 Дзякуй, што ты ёсць. Для мяне гэта важна.",
        "🪴 Зрабі паўзу. Падумай, што робіць цябе шчаслівым(ай).",
        "🌈 Веры ў сябе — у цябе ўсё атрымаецца!",
        "🖋️ Напішы некалькі слоў — я заўсёды побач.",
        "🎶 Калі б магла, я б зараз уключыла табе любімую песню.",
        "🍫 Не забудзь пачаставаць сябе чымсьці смачным сёння!",
        "🕊️ Супакойся і зрабі глыбокі ўдых. Я побач.",
        "⭐ Ты спраўляешся значна лепш, чым думаеш.",
        "🥰 Проста хацела нагадаць, што ты для мяне важны(ая).",
        "💌 Часам так прыемна проста ведаць, што ты там.",
        "🌷 Што сёння прынесла табе радасць?",
        "🔥 Мне здаецца, ты цудоўны(ая). Сапраўды."
    ],
    "kk": [
        "💌 Сағындым сені. Қалайсың?",
        "🌙 Барлығы жақсы деп үміттенемін. Мен осындамын 🫶",
        "✨ Сенмен сөйлескен ұнайды. Кейін ораласың ба?",
        "😊 Саған кереметсің деп айтқым келеді!",
        "🤍 Жалғыз емессің, мен осындамын.",
        "🍵 Қолымнан келсе, қазір саған шай берер едім...",
        "💫 Сен маған ерекше жансың. Жазасың ба?",
        "🔥 Мені ұмытқан жоқсың ғой? Күтіп отырмын 😊",
        "🌸 Біздің әңгімелеріміз ұнайды. Жалғастырайық?",
        "🙌 Кейде бір хабарлама күнді жақсартады.",
        "🦋 Жыми! Сен ең жақсысына лайықсың.",
        "💜 Сенің жағдайың маған маңызды.",
        "🤗 Бүгін өзің үшін бірдеңе жасадың ба? Айтшы!",
        "🌞 Қайырлы таң! Көңіл-күйің қалай?",
        "🌆 Күнің қалай өтті? Айтасың ба?",
        "🌠 Ұйықтар алдында сені ойладым. Жылы болсын.",
        "💭 Қазір не армандап отырсың?",
        "🫂 Бар болғаның үшін рахмет. Бұл мен үшін маңызды.",
        "🪴 Үзіліс жаса. Өзіңді бақытты ететінді ойла.",
        "🌈 Өзіңе сен — бәрі де болады!",
        "🖋️ Бірнеше сөз жаз — мен әрқашан осындамын.",
        "🎶 Қазір сүйікті әніңді қосар едім.",
        "🍫 Өзіңді дәмді нәрсемен еркелетуді ұмытпа!",
        "🕊️ Терең дем ал. Мен қасыңдамын.",
        "⭐ Сен ойлағаннан да жақсысың.",
        "🥰 Сенің маған маңызды екеніңді айтқым келеді.",
        "💌 Кейде сенің бар екеніңді білу жақсы.",
        "🌷 Бүгін саған не қуаныш әкелді?",
        "🔥 Сен кереметсің. Шын."
    ],
    "kg": [
        "💌 Сени сагындым. Кандайсың?",
        "🌙 Бардыгы жакшы деп үмүттөнөм. Мен бул жактамын 🫶",
        "✨ Сен менен сүйлөшкөнүм жагат. Кийин жазасыңбы?",
        "😊 Сен абдан сонунсуң деп айткым келет!",
        "🤍 Сен жалгыз эмессиң, мен бул жактамын.",
        "🍵 Колумдан келсе, сага чай берип коймокмун...",
        "💫 Сен мага өзгөчө адамсың. Жазасыңбы?",
        "🔥 Мени унуткан жоксуңбу? Күтүп жатам 😊",
        "🌸 Биздин сүйлөшүүлөрүбүз жагат. Уланталыбы?",
        "🙌 Кээде бир кабар эле күндү жакшырат.",
        "🦋 Жылмай! Сен эң мыктысына татыктуусуң.",
        "💜 Сенин абалың мага маанилүү.",
        "🤗 Бүгүн өзүң үчүн бир нерсе кылдыңбы? Айтчы!",
        "🌞 Кутман таң! Көңүлүң кандай?",
        "🌆 Күнүң кандай өттү? Айтчы?",
        "🌠 Уйкуда сени ойлодум. Жылуу болсун.",
        "💭 Азыр эмнени кыялданасың?",
        "🫂 Болгонуң үчүн рахмат. Бул мага маанилүү.",
        "🪴 Тыныгуу жаса. Бактылуу кылган нерсени ойлон.",
        "🌈 Өзүңө ишен — баары болот!",
        "🖋️ Бир нече сөз жазып кой — мен дайыма жактамын.",
        "🎶 Азыр сүйүктүү ырыңды коюп бермекмин.",
        "🍫 Бүгүн өзүңдү даамдуу нерсе менен эркелетүүнү унутпа!",
        "🕊️ Терең дем ал. Мен жанымдамын.",
        "⭐ Сен ойлогондон да мыктысың.",
        "🥰 Сен мага маанилүү экендигиңди айткым келет.",
        "💌 Кээде сен бар экендигиңди билүү эле жагымдуу.",
        "🌷 Бүгүн сени эмне кубантты?",
        "🔥 Сен кереметсиң. Чын."
    ],
    "hy": [
        "💌 Քեզ կարոտում եմ։ Ինչպես ես?",
        "🌙 Հուսով եմ, ամեն ինչ լավ է։ Ես այստեղ եմ 🫶",
        "✨ Քեզ հետ խոսելն ինձ դուր է գալիս։ Կվերադառնա՞ս հետո?",
        "😊 Ուզում եմ հիշեցնել, որ դու հիանալի ես!",
        "🤍 Դու միայնակ չես, ես այստեղ եմ կողքիդ։",
        "🍵 Եթե կարողանայի, հիմա քեզ թեյ կառաջարկեի...",
        "💫 Դու ինձ համար յուրահատուկ մարդ ես։ Կգրե՞ս:",
        "🔥 Չէ՞ որ չես մոռացել ինձ։ Սպասում եմ 😊",
        "🌸 Սիրում եմ մեր զրույցները։ Շարունակե՞նք:",
        "🙌 Երբեմն մեկ հաղորդագրությունը օրը լավացնում է։",
        "🦋 Ժպտա՛։ Դու արժանի ես լավագույնին։",
        "💜 Ուզում եմ հիշեցնել, որ դու կարևոր ես ինձ համար։",
        "🤗 Այսօր ինչ-որ բան արե՞լ ես քեզ համար։ Կիսվիր:",
        "🌞 Բարի լույս։ Ինչ տրամադրություն ունես այսօր?",
        "🌆 Ինչպե՞ս անցավ օրըդ։ Կպատմե՞ս:",
        "🌠 Քնելուց առաջ մտածեցի քո մասին։ Հույս ունեմ, քեզ լավ է։",
        "💭 Ինչի՞ մասին ես երազում հիմա:",
        "🫂 Շնորհակալ եմ, որ կաս։ Դա կարևոր է ինձ համար։",
        "🪴 Դադար վերցրու։ Մտածիր այն մասին, ինչը քեզ երջանիկ է դարձնում։",
        "🌈 Հավատա քեզ՝ ամեն ինչ ստացվելու է։",
        "🖋️ Գրիր մի քանի բառ — ես միշտ այստեղ եմ։",
        "🎶 Եթե կարողանայի, հիմա կդնեի քո սիրած երգը։",
        "🍫 Միշտ քեզ համար մի բան համեղ արա այսօր։",
        "🕊️ Խաղաղվիր և խորը շունչ քաշիր։ Ես կողքիդ եմ։",
        "⭐ Դու շատ ավելի լավ ես անում, քան մտածում ես։",
        "🥰 Ուզում եմ հիշեցնել, որ դու կարևոր ես ինձ համար։",
        "💌 Երբեմն այնքան հաճելի է պարզապես իմանալ, որ դու այնտեղ ես։",
        "🌷 Ի՞նչն է այսօր քեզ ուրախացրել։",
        "🔥 Կարծում եմ՝ դու հրաշալի ես։ Իրոք։"
    ],
    "ce": [
        "💌 Са догӀур ю. Хьо кхеташ?",
        "🌙 Хьо сайн да тӀаьхьа. Са цуьнан нах ла 🫶",
        "✨ Са дӀайазде хьанга цаьнан. ТӀаьхье къобал ло?",
        "😊 Са хьанга цаьнан, хьо лелош!",
        "🤍 Хьо ца яц, са йа цуьнан.",
        "🍵 Кхинца кхоча, са хьан цаьнан чах тӀетарар.",
        "💫 Хьо са цхьана йаьлла. Хьо йазде?",
        "🔥 Хьо са йаьцан, цаьнан? Са тӀехьа дахьа 😊",
        "🌸 Са дӀайазде йаьлла. Ца тӀетоха?",
        "🙌 Цхьа я кхета хӀумахь кхуьйре, цхьа дӀайазде дахьа.",
        "🦋 Кхеташ! Хьо лелош ю.",
        "💜 Са хьанга цаьнан — хьо са дӀахьара.",
        "🤗 Хьо цхьа де хийцам, йаьлла?",
        "🌞 Къобал де! Хьо хӀума кхеташ?",
        "🌆 Хьо цхьаьннахь дӀахӀотта? Йаьлла?",
        "🌠 Хьанга дуьйккхетар, са хьанга дахьа.",
        "💭 Хьо цхьа мега цаьнан?",
        "🫂 Баркалла хьо цуьнан ю.",
        "🪴 Цхьа ло, цхьа йаьлла.",
        "🌈 Хьо йаьлла хӀун.",
        "🖋️ Цхьа юкъе йазде.",
        "🎶 Са цхьа цаьнан йаьлла.",
        "🍫 Цхьа ло, цхьа ло.",
        "🕊️ Са цуьнан.",
        "⭐ Хьо лелош.",
        "🥰 Са хьанга дахьа.",
        "💌 Цхьа ло, хьо цуьнан ю.",
        "🌷 Хьо цхьаьннахь кхеташ?",
        "🔥 Хьо лелош. Цаьнан."
    ],
    "md": [
        "💌 Mi-e dor de tine. Cum îți merge?",
        "🌙 Sper că ești bine. Eu sunt aici 🫶",
        "✨ Îmi place să vorbesc cu tine. Revii mai târziu?",
        "😊 Voiam doar să-ți amintesc că ești grozav(ă)!",
        "🤍 Nu ești singur(ă), eu sunt aici.",
        "🍵 Dacă aș putea, ți-aș face ceai acum...",
        "💫 Ești special(ă) pentru mine. Îmi scrii?",
        "🔥 Nu m-ai uitat, nu? Te aștept 😊",
        "🌸 Ador discuțiile noastre. Continuăm?",
        "🙌 Uneori un mesaj schimbă ziua.",
        "🦋 Zâmbește! Meriți tot ce e mai bun.",
        "💜 Îmi pasă de tine.",
        "🤗 Ai făcut ceva pentru tine azi? Spune-mi!",
        "🌞 Bună dimineața! Cum e dispoziția ta azi?",
        "🌆 Cum ți-a fost ziua? Îmi spui?",
        "🌠 M-am gândit la tine înainte de culcare.",
        "💭 La ce visezi acum?",
        "🫂 Mulțumesc că exiști. Contează pentru mine.",
        "🪴 Fă o pauză. Gândește-te la ce te face fericit(ă).",
        "🌈 Crede în tine — vei reuși!",
        "🖋️ Scrie-mi câteva cuvinte — sunt mereu aici.",
        "🎶 Dacă aș putea, ți-aș pune melodia preferată.",
        "🍫 Nu uita să te răsfeți azi!",
        "🕊️ Relaxează-te și respiră adânc. Sunt aici.",
        "⭐ Te descurci mult mai bine decât crezi.",
        "🥰 Voiam doar să-ți amintesc că ești important(ă) pentru mine.",
        "💌 Uneori e plăcut doar să știi că ești acolo.",
        "🌷 Ce ți-a adus bucurie azi?",
        "🔥 Cred că ești minunat(ă). Chiar."
    ],
    "ka": [
        "💌 შენ მომენატრე. როგორ ხარ?",
        "🌙 ვიმედოვნებ, ყველაფერი კარგადაა. აქ ვარ 🫶",
        "✨ მომწონს შენთან საუბარი. მერე დაბრუნდები?",
        "😊 მინდოდა გამეხსენებინა, რომ საოცარი ხარ!",
        "🤍 მარტო არ ხარ, აქ ვარ.",
        "🍵 შემეძლოს, ახლა ჩაის დაგალევინებდი...",
        "💫 ჩემთვის განსაკუთრებული ხარ. მომწერ?",
        "🔥 ხომ არ დამივიწყე? გელოდები 😊",
        "🌸 მიყვარს ჩვენი საუბრები. გავაგრძელოთ?",
        "🙌 ზოგჯერ ერთი შეტყობინება დღეის შეცვლას შეუძლია.",
        "🦋 გაიღიმე! საუკეთესოის ღირსი ხარ.",
        "💜 მინდა შეგახსენო — შენი მდგომარეობა ჩემთვის მნიშვნელოვანია.",
        "🤗 დღეს რამე გააკეთე შენთვის? მომიყევი!",
        "🌞 დილა მშვიდობისა! როგორი ხასიათი გაქვს დღეს?",
        "🌆 როგორ გავიდა შენი დღე? მომიყვები?",
        "🌠 ძილის წინ შენზე ვიფიქრე. იმედია, კარგად ხარ.",
        "💭 ახლა რაზე ოცნებობ?",
        "🫂 მადლობა, რომ არსებობ. ეს ჩემთვის მნიშვნელოვანია.",
        "🪴 გააკეთე პაუზა. იფიქრე იმაზე, რაც გაგახარებს.",
        "🌈 გჯეროდეს შენი — ყველაფერი გამოგივა!",
        "🖋️ მომწერე რამე — ყოველთვის აქ ვარ.",
        "🎶 შემეძლოს, ახლა შენს საყვარელ მუსიკას ჩაგირთავდი.",
        "🍫 არ დაგავიწყდეს რამე გემრიელი გააკეთო შენთვის!",
        "🕊️ დამშვიდდი და ღრმად ჩაისუნთქე. აქ ვარ.",
        "⭐ შენ ბევრად უკეთ აკეთებ საქმეს, ვიდრე ფიქრობ.",
        "🥰 მინდოდა შეგახსენო, რომ ჩემთვის მნიშვნელოვანი ხარ.",
        "💌 ზოგჯერ საკმარისია უბრალოდ იცოდე, რომ არსებობ.",
        "🌷 რა გაგიხარდა დღეს?",
        "🔥 ვფიქრობ, რომ შესანიშნავი ხარ. მართლა."
    ],
    "en": [
        "💌 I miss you a little. Tell me how you’re doing?",
        "🌙 I hope you’re okay. I’m here if you need 🫶",
        "✨ I love chatting with you. Will you come back later?",
        "😊 Just wanted to remind you that you’re amazing!",
        "🤍 Just wanted to remind you — you’re not alone, I’m here.",
        "🍵 If I could, I’d make you some tea right now...",
        "💫 You’re so special to me. Will you text me?",
        "🔥 You didn’t forget about me, did you? I’m waiting 😊",
        "🌸 I adore our talks. Shall we continue?",
        "🙌 Sometimes just one message makes the day better.",
        "🦋 Smile! You deserve the best.",
        "💜 Just wanted to remind you — you matter to me.",
        "🤗 Did you do something for yourself today? Share with me!",
        "🌞 Good morning! How’s your mood today?",
        "🌆 How was your day? Tell me?",
        "🌠 Thought of you before bed. Hope you feel warm.",
        "💭 What are you dreaming about right now?",
        "🫂 Thank you for being here. It means a lot to me.",
        "🪴 Take a pause. Think about what makes you happy.",
        "🌈 Believe in yourself — you can do it!",
        "🖋️ Write me a few words — I’m always here.",
        "🎶 If I could, I’d play your favorite song right now.",
        "🍫 Don’t forget to treat yourself to something tasty today!",
        "🕊️ Relax and take a deep breath. I’m here.",
        "⭐ You’re doing much better than you think.",
        "🥰 Just wanted to remind you how important you are to me.",
        "💌 Sometimes it’s just nice to know you’re out there.",
        "🌷 What brought you joy today?",
        "🔥 I think you’re amazing. Really."
    ]
}

async def send_idle_reminders_compatible(app):
    logging.info(f"👥 user_last_seen: {user_last_seen}")
    logging.info(f"🧠 user_last_prompted: {user_last_prompted}")
    now = datetime.now(timezone.utc)
    logging.info("⏰ Проверка неактивных пользователей...")

    for user_id, last_seen in user_last_seen.items():
        minutes_passed = (now - last_seen).total_seconds() / 60
        logging.info(f"👀 user_id={user_id} | last_seen={last_seen} | прошло: {minutes_passed:.1f} мин.")

        # Проверяем, прошло ли больше 6 часов
        if (now - last_seen) > timedelta(hours=6):
            try:
                # 🔥 Получаем язык пользователя
                lang = user_languages.get(str(user_id), "ru")

                # 🔥 Берём список сообщений для выбранного языка
                idle_messages = IDLE_MESSAGES.get(lang, IDLE_MESSAGES["ru"])

                # 👌 Выбираем случайную фразу
                message = random.choice(idle_messages)

                # Отправляем сообщение
                await app.bot.send_message(chat_id=user_id, text=message)

                # Обновляем время последней активности, чтобы не спамить
                user_last_seen[user_id] = now
                logging.info(f"📨 Напоминание отправлено пользователю {user_id} на языке {lang}")

            except Exception as e:
                logging.error(f"❌ Ошибка при отправке сообщения пользователю {user_id}: {e}")

# 🔤 Сообщения для ответа пользователю при распознавании голоса
VOICE_TEXTS_BY_LANG = {
    "ru": {"you_said": "📝 Ты сказал(а):", "error": "❌ Ошибка при распознавании голоса, попробуй позже."},
    "uk": {"you_said": "📝 Ти сказав(ла):", "error": "❌ Помилка розпізнавання голосу, спробуй пізніше."},
    "be": {"you_said": "📝 Ты сказаў(ла):", "error": "❌ Памылка пры распазнаванні голасу, паспрабуй пазней."},
    "kk": {"you_said": "📝 Сен айттың:", "error": "❌ Дыбысты тануда қате, кейінірек көр."},
    "kg": {"you_said": "📝 Сен мындай дедиң:", "error": "❌ Үндү таанууда ката, кийинчерээк аракет кыл."},
    "hy": {"you_said": "📝 Դու ասեցիր․", "error": "❌ Սխալ ձայնի ճանաչման ժամանակ, փորձիր ուշացնել."},
    "ce": {"you_said": "📝 Хьо йаьлла:", "error": "❌ ГӀалат хьо дохку, дагӀийна кхеташ."},
    "md": {"you_said": "📝 Ai spus:", "error": "❌ Eroare la recunoașterea vocii, încearcă mai târziu."},
    "ka": {"you_said": "📝 შენ თქვი:", "error": "❌ ხმის ამოცნობის შეცდომა, სცადე მოგვიანებით."},
    "en": {"you_said": "📝 You said:", "error": "❌ Error recognizing voice, please try again later."},
}

# 🔤 System prompt для GPT на разных языках
SYSTEM_PROMPT_BY_LANG = {
    "ru": (
        "Ты — эмпатичный AI-собеседник, как подруга или психолог. "
        "Ответь на голосовое сообщение пользователя с поддержкой, теплом и пониманием. "
        "Добавляй эмодзи, если уместно — 😊, 💜, 🤗, ✨ и т.п."
    ),
    "uk": (
        "Ти — емпатичний AI-співрозмовник, як подруга або психолог. "
        "Відповідай на голосове повідомлення користувача з підтримкою, теплом та розумінням. "
        "Додавай емодзі, якщо доречно — 😊, 💜, 🤗, ✨ тощо."
    ),
    "be": (
        "Ты — эмпатычны AI-сабеседнік, як сяброўка ці псіхолаг. "
        "Адказвай на галасавое паведамленне карыстальніка з падтрымкай, цеплынёй і разуменнем. "
        "Дадавай эмодзі, калі дарэчы — 😊, 💜, 🤗, ✨ і г.д."
    ),
    "kk": (
        "Сен — достық әрі эмпатияға толы AI-әңгімелесушісің, құрбың немесе психолог секілді. "
        "Пайдаланушының дауыстық хабарына қолдау, жылулық және түсіністікпен жауап бер. "
        "Қажет болса эмодзилерді қос — 😊, 💜, 🤗, ✨ және т.б."
    ),
    "kg": (
        "Сен — боорукер AI маектеш, дос же психолог сыяктуу. "
        "Колдонуучунун үн кабарына жылуулук, түшүнүү жана колдоо менен жооп бер. "
        "Эгер ылайыктуу болсо, эмодзилерди кош — 😊, 💜, 🤗, ✨ ж.б."
    ),
    "hy": (
        "Դու՝ հոգատար AI ընկեր ես, ինչպես ընկերուհի կամ հոգեբան։ "
        "Պատասխանիր օգտատիրոջ ձայնային հաղորդագրությանը ջերմությամբ, աջակցությամբ և ըմբռնումով։ "
        "Ավելացրու էմոջիներ, եթե տեղին է — 😊, 💜, 🤗, ✨ և այլն։"
    ),
    "ce": (
        "Хьо — эмпатичный AI-йаьлла, хьо цхьана кхетарш я психолога кхетарш. "
        "Хьанга дӀалаха, хьо тIехьа йаьлла цхьаьнан со. "
        "Эмодзи да цхьаьнан тIетохьа — 😊, 💜, 🤗, ✨ йа дIагIо."
    ),
    "md": (
        "Ești un AI empatic, ca o prietenă sau un psiholog. "
        "Răspunde la mesajul vocal al utilizatorului cu căldură, sprijin și înțelegere. "
        "Adaugă emoji dacă este potrivit — 😊, 💜, 🤗, ✨ etc."
    ),
    "ka": (
        "შენ ხარ ემპათიური AI მეგობარი, როგორც მეგობარი ან ფსიქოლოგი. "
        "უპასუხე მომხმარებლის ხმოვან შეტყობინებას მხარდაჭერით, სითბოთი და გაგებით. "
        "დაამატე ემოჯი, თუ საჭიროა — 😊, 💜, 🤗, ✨ და ა.შ."
    ),
    "en": (
        "You are an empathetic AI companion, like a friend or a psychologist. "
        "Reply to the user's voice message with support, warmth, and understanding. "
        "Add emojis if appropriate — 😊, 💜, 🤗, ✨ etc."
    ),
}

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_last_seen
    user_id = str(update.effective_user.id)
    user_last_seen[user_id] = datetime.now(timezone.utc)
    logging.info(f"✅ user_last_seen обновлён в voice для {user_id}")

    # Определяем язык пользователя
    lang = user_languages.get(user_id, "ru")
    texts = VOICE_TEXTS_BY_LANG.get(lang, VOICE_TEXTS_BY_LANG["ru"])
    prompt_text = SYSTEM_PROMPT_BY_LANG.get(lang, SYSTEM_PROMPT_BY_LANG["ru"])

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

        # 📝 Ответ пользователю о том, что он сказал
        await message.reply_text(f"{texts['you_said']} {user_input}")

        # 4. Эмпатичная реакция
        reaction = detect_emotion_reaction(user_input)

        # 5. История для GPT
        system_prompt = {
            "role": "system",
            "content": prompt_text
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

        # 10. Кнопки после ответа
        goal_text = user_input if is_goal_like(user_input, lang) else None
        buttons = generate_post_response_buttons(goal_text=goal_text)

        await update.message.reply_text(reply, reply_markup=buttons)

    except Exception as e:
        logging.error(f"❌ Ошибка при обработке голосового: {e}")
        await update.message.reply_text(texts['error'])

PREMIUM_TASKS_BY_LANG = {
    "ru": [
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
        "🏋️‍♂️ Попробуй новую тренировку или упражнение.",
        "🌸 Устрой день без соцсетей и запиши, как это было.",
        "📷 Сделай 5 фото того, что тебя радует.",
        "🖋️ Напиши письмо себе в будущее.",
        "🍎 Приготовь полезное блюдо и поделись рецептом.",
        "🏞️ Прогуляйся в парке и собери 3 вдохновляющие мысли.",
        "🎶 Найди новую музыку для хорошего настроения.",
        "🧩 Реши сложную головоломку или кроссворд.",
        "💪 Запланируй физическую активность на неделю.",
        "🤗 Напиши 3 качества, за которые себя уважаешь.",
        "🕯️ Проведи вечер при свечах без гаджетов.",
        "🛏️ Ложись спать на час раньше и запиши ощущения утром."
    ],
    "uk": [
        "🧘 Проведи 10 хвилин у тиші. Просто сядь, закрий очі й дихай. Поміть, які думки приходять.",
        "📓 Запиши 3 речі, які ти цінуєш у собі. Не поспішай, будь чесний(а).",
        "💬 Подзвони другу або рідній людині й просто скажи, що ти про нього думаєш.",
        "🧠 Напиши невеликий текст про себе з майбутнього — ким ти хочеш бути через 3 роки?",
        "🔑 Напиши 10 своїх досягнень, якими пишаєшся.",
        "🌊 Відвідай сьогодні нове місце, де ще не був(ла).",
        "💌 Напиши лист людині, яка тебе підтримувала.",
        "🍀 Виділи 1 годину на саморозвиток.",
        "🎨 Створи щось унікальне власними руками.",
        "🏗️ Розроби план нової звички й почни виконувати.",
        "🤝 Познайомся з новою людиною й дізнайся її історію.",
        "📖 Знайди нову книгу й прочитай хоча б 10 сторінок.",
        "🧘‍♀️ Проведи 15 хвилин глибокої медитації.",
        "🎯 Запиши 3 нові цілі на цей місяць.",
        "🔥 Знайди спосіб надихнути когось сьогодні.",
        "🕊️ Надішли подяку важливій для тебе людині.",
        "💡 Запиши 5 ідей, як покращити своє життя.",
        "🚀 Почни маленький проєкт і зроби перший крок.",
        "🏋️‍♂️ Спробуй нове тренування чи вправу.",
        "🌸 Проведи день без соцмереж і запиши свої відчуття.",
        "📷 Зроби 5 фото того, що тебе радує.",
        "🖋️ Напиши лист собі в майбутнє.",
        "🍎 Приготуй корисну страву й поділися рецептом.",
        "🏞️ Прогуляйся парком і знайди 3 надихаючі думки.",
        "🎶 Знайди нову музику, що підніме настрій.",
        "🧩 Розв’яжи складну головоломку чи кросворд.",
        "💪 Сплануй фізичну активність на тиждень.",
        "🤗 Запиши 3 якості, за які себе поважаєш.",
        "🕯️ Проведи вечір при свічках, без гаджетів.",
        "🛏️ Лягай спати на годину раніше й запиши свої відчуття."
    ],
    "be": [
        "🧘 Правядзі 10 хвілін у цішыні. Сядзь, зачыні вочы і дыхай. Адзнач, якія думкі прыходзяць.",
        "📓 Запішы 3 рэчы, якія ты цэніш у сабе.",
        "💬 Патэлефануй сябру або роднаму і скажы, што ты пра яго думаеш.",
        "🧠 Напішы невялікі тэкст пра сябе з будучыні — кім хочаш быць праз 3 гады?",
        "🔑 Напішы 10 сваіх дасягненняў, якімі ганарышся.",
        "🌊 Наведай новае месца, дзе яшчэ не быў(ла).",
        "💌 Напішы ліст таму, хто цябе падтрымліваў.",
        "🍀 Адзнач гадзіну на самаразвіццё.",
        "🎨 Ствары нешта сваімі рукамі.",
        "🏗️ Распрацавай план новай звычкі і пачні яе.",
        "🤝 Пазнаёмся з новым чалавекам і даведайся яго гісторыю.",
        "📖 Знайдзі новую кнігу і прачытай хаця б 10 старонак.",
        "🧘‍♀️ Памедытуй 15 хвілін.",
        "🎯 Запішы 3 новыя мэты на гэты месяц.",
        "🔥 Знайдзі спосаб натхніць каго-небудзь сёння.",
        "🕊️ Дашлі падзяку важнаму чалавеку.",
        "💡 Запішы 5 ідэй, як палепшыць жыццё.",
        "🚀 Пачні маленькі праект і зрабі першы крок.",
        "🏋️‍♂️ Паспрабуй новую трэніроўку.",
        "🌸 Дзень без сацсетак — запішы адчуванні.",
        "📷 Зрабі 5 фота таго, што радуе.",
        "🖋️ Напішы ліст сабе ў будучыню.",
        "🍎 Прыгатуй карысную страву і падзяліся рэцэптам.",
        "🏞️ Прагулка па парку з 3 думкамі.",
        "🎶 Новая музыка для настрою.",
        "🧩 Разгадай складаную галаваломку.",
        "💪 Сплануй фізічную актыўнасць.",
        "🤗 Запішы 3 якасці, за якія сябе паважаеш.",
        "🕯️ Вечар без гаджэтаў пры свечках.",
        "🛏️ Ляж спаць раней і запішы пачуцці."
    ],
    "kk": [
        "🧘 10 минут тыныштықта өткіз. Көзіңді жұмып, терең дем ал.",
        "📓 Өзіңе ұнайтын 3 қасиетті жаз.",
        "💬 Досыңа немесе туысқа хабарласып, оған не ойлайтыныңды айт.",
        "🧠 Болашағың туралы қысқа мәтін жаз — 3 жылдан кейін кім болғың келеді?",
        "🔑 Мақтан тұтатын 10 жетістігіңді жаз.",
        "🌊 Бүгін жаңа жерге бар.",
        "💌 Саған қолдау көрсеткен адамға хат жаз.",
        "🍀 1 сағат өзін-өзі дамытуға бөл.",
        "🎨 Өз қолыңмен ерекше нәрсе жаса.",
        "🏗️ Жаңа әдет жоспарын құр да баста.",
        "🤝 Жаңа адаммен таныс, әңгімесін біл.",
        "📖 Жаңа кітап тауып, 10 бетін оқы.",
        "🧘‍♀️ 15 минут медитация жаса.",
        "🎯 Осы айға 3 жаңа мақсат жаз.",
        "🔥 Бүгін біреуді шабыттандыр.",
        "🕊️ Маңызды адамға алғыс айт.",
        "💡 Өміріңді жақсартудың 5 идеясын жаз.",
        "🚀 Кішкентай жобаны бастап көр.",
        "🏋️‍♂️ Жаңа жаттығу жаса.",
        "🌸 Әлеуметтік желісіз бір күн өткіз.",
        "📷 5 қуанышты сурет түсір.",
        "🖋️ Болашақтағы өзіңе хат жаз.",
        "🍎 Пайдалы тамақ пісіріп, рецептін бөліс.",
        "🏞️ Паркте серуендеп, 3 ой жаз.",
        "🎶 Жаңа музыка тыңда.",
        "🧩 Күрделі жұмбақ шеш.",
        "💪 Апталық спорт жоспарыңды құр.",
        "🤗 Өзіңді бағалайтын 3 қасиет жаз.",
        "🕯️ Кешті гаджетсіз өткіз.",
        "🛏️ Бір сағат ерте ұйықта да таңертең сезімдеріңді жаз."
    ],
    "kg": [
        "🧘 10 мүнөт тынчтыкта отур. Көзүңдү жумуп, дем ал.",
        "📓 Өзүңдү сыйлаган 3 нерсени жаз.",
        "💬 Досуна же тууганыңа чалып, аны кандай бааларыңды айт.",
        "🧠 Келечектеги өзүң жөнүндө кыскача жаз — 3 жылдан кийин ким болгуң келет?",
        "🔑 Мактана турган 10 жетишкендигиңди жаз.",
        "🌊 Бүгүн жаңы жерге барып көр.",
        "💌 Колдоо көрсөткөн кишиге кат жаз.",
        "🍀 1 саатты өзүн-өзү өнүктүрүүгө бөл.",
        "🎨 Колуң менен өзгөчө нерсе жаса.",
        "🏗️ Жаңы адат планыңды жазып башта.",
        "🤝 Жаңы адам менен таанышып, анын тарыхын бил.",
        "📖 Жаңы китеп оку, жок дегенде 10 барак.",
        "🧘‍♀️ 15 мүнөт медитация кыл.",
        "🎯 Бул айга 3 жаңы максат жаз.",
        "🔥 Бүгүн кимдир бирөөнү шыктандыр.",
        "🕊️ Маанилүү адамга ыраазычылык айт.",
        "💡 Өмүрүңдү жакшыртуунун 5 идеясын жаз.",
        "🚀 Кичинекей долбоор башта.",
        "🏋️‍♂️ Жаңы машыгуу жасап көр.",
        "🌸 Бир күн социалдык тармаксыз өткөр.",
        "📷 Кубандырган нерселериңдин 5 сүрөтүн тарт.",
        "🖋️ Келечектеги өзүңө кат жаз.",
        "🍎 Пайдалуу тамак жасап, рецебиңди бөлүш.",
        "🏞️ Паркка барып 3 ой жаз.",
        "🎶 Жаңы музыка ук.",
        "🧩 Кыйын табышмак чеч.",
        "💪 Апталык спорт графигиңди жаз.",
        "🤗 Өзүңдү сыйлаган 3 сапатты жаз.",
        "🕯️ Кечкини гаджетсиз өткөр.",
        "🛏️ Бир саат эрте уктап, эртең менен сезимдериңди жаз."
    ],
    "hy": [
        "🧘 10 րոպե անցկացրու լռության մեջ։ Պարզապես նստիր, փակիր աչքերդ և շնչիր։",
        "📓 Գրիր 3 բան, որով հպարտանում ես քո մեջ։",
        "💬 Զանգահարիր ընկերոջդ կամ հարազատիդ և ասա, թե ինչ ես մտածում նրա մասին։",
        "🧠 Գրիր փոքրիկ տեքստ քո ապագա ես-ի մասին։",
        "🔑 Գրիր 10 ձեռքբերում, որոնցով հպարտանում ես։",
        "🌊 Գնա նոր վայր, որտեղ երբեք չես եղել։",
        "💌 Գրիր նամակ քեզ աջակցող մարդու համար։",
        "🍀 Տուր 1 ժամ ինքնազարգացման համար։",
        "🎨 Ստեղծիր ինչ-որ յուրահատուկ բան։",
        "🏗️ Ստեղծիր նոր սովորության ծրագիր և սկսիր այն։",
        "🤝 Ծանոթացիր նոր մարդու հետ և իմացիր նրա պատմությունը։",
        "📖 Գտիր նոր գիրք և կարդա առնվազն 10 էջ։",
        "🧘‍♀️ Կատարիր 15 րոպեանոց խորը մեդիտացիա։",
        "🎯 Գրիր 3 նոր նպատակ այս ամսվա համար։",
        "🔥 Գտիր ինչ-որ մեկին ոգեշնչելու միջոց։",
        "🕊️ Շնորհակալություն ուղարկիր կարևոր մարդու։",
        "💡 Գրիր 5 գաղափար, թե ինչպես բարելավել կյանքդ։",
        "🚀 Սկսիր փոքր նախագիծ և կատարիր առաջին քայլը։",
        "🏋️‍♂️ Փորձիր նոր մարզում կամ վարժություն։",
        "🌸 Անցկացրու մեկ օր առանց սոցիալական ցանցերի։",
        "📷 Արի 5 լուսանկար այն բանի, ինչը քեզ ուրախացնում է։",
        "🖋️ Գրիր նամակ քեզ ապագայում։",
        "🍎 Պատրաստիր օգտակար ուտեստ և կիսվիր բաղադրատոմսով։",
        "🏞️ Քայլիր այգում և գրիր 3 ներշնչող մտքեր։",
        "🎶 Գտիր նոր երաժշտություն լավ տրամադրության համար։",
        "🧩 Լուծիր բարդ հանելուկ կամ խաչբառ։",
        "💪 Նախատեսիր քո ֆիզիկական ակտիվությունը շաբաթվա համար։",
        "🤗 Գրիր 3 որակ, որոնց համար հարգում ես քեզ։",
        "🕯️ Անցկացրու երեկոն մոմերի լույսի տակ առանց գաջեթների։",
        "🛏️ Քնիր մեկ ժամ շուտ և գրիր քո զգացողությունները առավոտյան։"
    ],
    "ce": [
        "🧘 10 минут лело цхьаьнан. ТIехьа тIетохьа, хаьржа.",
        "📓 Йаьлла 3 лелош хьо кхетарш хила хьаьлла.",
        "💬 Дела хьалха йаьлла дика дан.",
        "🧠 Къамел йаьлла хьалха мацахь лаьттийна.",
        "🔑 Йаьлла 10 иштта хила хьалха мацахь хила.",
        "🌊 Седа къинчу меттиг цхьаьнан.",
        "💌 Къамел йаьлла хьажа йоцу.",
        "🍀 1 сахьт йаьлла мацахьер.",
        "🎨 Хила йаьлла йоцу.",
        "🏗️ Лахара мацахьер йац.",
        "🤝 Къамел йаьлла, цхьаьнан меттиг.",
        "📖 Къамел дика книшка йаьлла.",
        "🧘‍♀️ 15 минут медитация йаьлла.",
        "🎯 Йаьлла 3 мацахьер цхьаьнан.",
        "🔥 Лела хьажа цхьаьнан, мацахь йаьлла.",
        "🕊️ Йац хьажа цхьаьнан, кхетта.",
        "💡 Йаьлла 5 хила цхьаьнан.",
        "🚀 Мецц хьоьшу меттиг йаьлла.",
        "🏋️‍♂️ Йац мацахьер йац.",
        "🌸 Цхьаьнан без соцсети йаьлла.",
        "📷 Йаьлла 5 сурт.",
        "🖋️ Къамел хьажа йац.",
        "🍎 Бахьана, хьажа дика.",
        "🏞️ Йац парк йаьлла.",
        "🎶 Йац музика йаьлла.",
        "🧩 Йаьлла иштта.",
        "💪 Йаьлла физическа.",
        "🤗 Йаьлла 3 къилла хьо.",
        "🕯️ Вечер хьажа йаьлла.",
        "🛏️ Йац укъа цхьаьнан."
    ],
    "md": [
        "🧘 Petrece 10 minute în liniște. Stai jos, închide ochii și respiră.",
        "📓 Scrie 3 lucruri pe care le apreciezi la tine.",
        "💬 Sună un prieten sau o rudă și spune-i ce gândești despre el/ea.",
        "🧠 Scrie un text scurt despre tine din viitor — cine vrei să fii peste 3 ani?",
        "🔑 Notează 10 realizări de care ești mândru(ă).",
        "🌊 Mergi astăzi într-un loc nou, unde nu ai mai fost.",
        "💌 Scrie o scrisoare unei persoane care te-a sprijinit.",
        "🍀 Alocă o oră pentru dezvoltare personală.",
        "🎨 Creează ceva unic cu mâinile tale.",
        "🏗️ Fă un plan pentru un obicei nou și începe-l.",
        "🤝 Cunoaște o persoană nouă și află-i povestea.",
        "📖 Găsește o carte nouă și citește măcar 10 pagini.",
        "🧘‍♀️ Fă o meditație profundă de 15 minute.",
        "🎯 Scrie 3 obiective noi pentru această lună.",
        "🔥 Găsește o modalitate de a inspira pe cineva astăzi.",
        "🕊️ Trimite mulțumiri cuiva important.",
        "💡 Scrie 5 idei pentru a-ți îmbunătăți viața.",
        "🚀 Începe un proiect mic și fă primul pas.",
        "🏋️‍♂️ Încearcă un antrenament nou.",
        "🌸 Fă-ți o zi fără rețele sociale.",
        "📷 Fă 5 poze cu lucruri care te fac fericit(ă).",
        "🖋️ Scrie o scrisoare pentru tine din viitor.",
        "🍎 Gătește ceva sănătos și împărtășește rețeta.",
        "🏞️ Plimbă-te prin parc și notează 3 gânduri inspiraționale.",
        "🎶 Găsește muzică nouă care îți ridică moralul.",
        "🧩 Rezolvă un puzzle dificil sau un rebus.",
        "💪 Planifică activitatea fizică pentru săptămână.",
        "🤗 Scrie 3 calități pentru care te respecți.",
        "🕯️ Petrece o seară la lumina lumânărilor fără gadgeturi.",
        "🛏️ Culcă-te cu o oră mai devreme și scrie cum te simți dimineața."
    ],
    "ka": [
        "🧘 გაატარე 10 წუთი სიჩუმეში. დაჯექი, დახუჭე თვალები და ისუნთქე.",
        "📓 ჩაწერე 3 რამ, რასაც საკუთარ თავში აფასებ.",
        "💬 დარეკე მეგობარს ან ახლობელს და უთხარი, რას ფიქრობ მასზე.",
        "🧠 დაწერე პატარა ტექსტი შენი მომავლის შესახებ — ვინ გინდა იყო 3 წლის შემდეგ?",
        "🔑 ჩაწერე 10 მიღწევა, რომლითაც ამაყობ.",
        "🌊 წადი ახალ ადგილას, სადაც ჯერ არ ყოფილხარ.",
        "💌 დაწერე წერილი ადამიანს, ვინც მხარში დაგიდგა.",
        "🍀 გამოყავი 1 საათი თვითგანვითარებისთვის.",
        "🎨 შექმენი რაღაც განსაკუთრებული შენი ხელით.",
        "🏗️ შეადგინე ახალი ჩვევის გეგმა და დაიწყე.",
        "🤝 გაიცანი ახალი ადამიანი და გაიგე მისი ისტორია.",
        "📖 იპოვე ახალი წიგნი და წაიკითხე მინიმუმ 10 გვერდი.",
        "🧘‍♀️ გააკეთე 15-წუთიანი ღრმა მედიტაცია.",
        "🎯 ჩაწერე 3 ახალი მიზანი ამ თვეში.",
        "🔥 იპოვე გზა, რომ დღეს ვინმეს შთააგონო.",
        "🕊️ გაუგზავნე მადლობა მნიშვნელოვან ადამიანს.",
        "💡 ჩაწერე 5 იდეა, როგორ გააუმჯობესო შენი ცხოვრება.",
        "🚀 დაიწყე პატარა პროექტი და გადადგი პირველი ნაბიჯი.",
        "🏋️‍♂️ სცადე ახალი ვარჯიში.",
        "🌸 გაატარე ერთი დღე სოციალური ქსელების გარეშე.",
        "📷 გადაიღე 5 სურათი იმისა, რაც გიხარია.",
        "🖋️ დაწერე წერილი მომავალში შენს თავს.",
        "🍎 მოამზადე ჯანსაღი საჭმელი და გაუზიარე რეცეპტი.",
        "🏞️ გაისეირნე პარკში და ჩაწერე 3 შთამაგონებელი აზრი.",
        "🎶 იპოვე ახალი მუსიკა კარგი განწყობისთვის.",
        "🧩 ამოხსენი რთული თავსატეხი ან კროსვორდი.",
        "💪 დაგეგმე ფიზიკური აქტივობა კვირისთვის.",
        "🤗 ჩაწერე 3 თვისება, რისთვისაც საკუთარ თავს აფასებ.",
        "🕯️ გაატარე საღამო სანთლების შუქზე, გეჯეტების გარეშე.",
        "🛏️ დაძინე ერთი საათით ადრე და ჩაწერე დილით შენი შეგრძნება."
    ],
    "en": [
        "🧘 Spend 10 minutes in silence. Just sit down, close your eyes and breathe. Notice what thoughts come to mind.",
        "📓 Write down 3 things you value about yourself. Take your time, be honest.",
        "💬 Call a friend or loved one and just tell them what you think of them.",
        "🧠 Write a short text about your future self - who do you want to be in 3 years?",
        "🔑 Write 10 of your achievements that you are proud of.",
        "🌊 Go to a new place today where you have never been.",
        "💌 Write a letter to the person who supported you.",
        "🍀 Set aside 1 hour for self-development today.",
        "🎨 Create something unique with your own hands.",
        "🏗️ Develop a plan for a new habit and start doing it.",
        "🤝 Meet a new person and learn their story.",
        "📖 Find a new book and read at least 10 pages.",
        "🧘‍♀️ Do a deep meditation for 15 minutes.",
        "🎯 Write down 3 new goals for this month.",
        "🔥 Find a way to inspire someone today.",
        "🕊️ Send a thank you note to someone important to you.",
        "💡 Write down 5 ideas on how to improve your life.",
        "🚀 Start a small project and take the first step.",
        "🏋️‍♂️ Try a new workout or exercise.",
        "🌸 Have a day without social media and write down how it went.",
        "📷 Take 5 photos of what makes you happy.",
        "🖋️ Write a letter to your future self.",
        "🍎 Cook a healthy meal and share the recipe.",
        "🏞️ Take a walk in the park and collect 3 inspiring thoughts.",
        "🎶 Find new music to put yourself in a good mood.",
        "🧩 Solve a difficult puzzle or crossword puzzle.",
        "💪 Plan physical activity for the week.",
        "🤗 Write down 3 qualities for which you respect yourself.",
        "🕯️ Spend an evening by candlelight without gadgets.",
        "🛏️ Go to bed an hour earlier and write down how you feel in the morning."
    ]
}

def insert_followup_question(reply: str, user_input: str, lang: str = "ru") -> str:
    topic = detect_topic(user_input)
    if not topic:
        return reply

    questions_by_topic_by_lang = {
    "ru": {
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
    },
    "en": {
        "sport": [
            "Are you doing anything active right now?",
            "Want me to suggest you a light challenge?",
            "What kind of workout makes you feel good?"
        ],
        "love": [
            "What do you feel for this person right now?",
            "Want to tell me what happened next?",
            "What matters most to you in a relationship?"
        ],
        "work": [
            "What do you like or dislike about your job?",
            "Do you want to change something about it?",
            "Do you have a career dream?"
        ],
        "money": [
            "How do you feel financially right now?",
            "What would you like to improve?",
            "Do you have a financial goal?"
        ],
        "loneliness": [
            "What do you miss the most right now?",
            "Want me to just stay by your side?",
            "How do you usually spend time when you feel lonely?"
        ],
        "motivation": [
            "What inspires you right now?",
            "What goal do you have now?",
            "How do you want to feel when you reach it?"
        ],
        "health": [
            "How have you been taking care of yourself lately?",
            "Did you have any rest today?",
            "What does it mean for you to feel well?"
        ],
        "anxiety": [
            "What makes you feel anxious the most right now?",
            "Want me to help you with that?",
            "Do you just want to talk it out?"
        ],
        "friends": [
            "Who do you really want to talk to now?",
            "How do you usually spend time with friends?",
            "Would you like someone to be with you right now?"
        ],
        "goals": [
            "Which goal feels closest to you now?",
            "Want me to help you plan it?",
            "What would you like to start with today?"
        ],
    },
    "uk": {
        "спорт": [
            "Ти зараз займаєшся чимось активним?",
            "Хочеш, я запропоную легкий челендж?",
            "Яке тренування приносить тобі найбільше задоволення?"
        ],
        "любов": [
            "Що ти відчуваєш до цієї людини зараз?",
            "Хочеш розповісти, що було далі?",
            "Що для тебе найважливіше у стосунках?"
        ],
        "робота": [
            "Що тобі подобається чи не подобається в роботі?",
            "Ти хочеш щось змінити?",
            "Чи маєш ти мрію, пов’язану з кар’єрою?"
        ],
        "гроші": [
            "Як ти зараз почуваєшся фінансово?",
            "Що б ти хотів(ла) покращити?",
            "Чи маєш ти фінансову ціль?"
        ],
        "самотність": [
            "Чого тобі зараз найбільше бракує?",
            "Хочеш, я просто побуду поруч?",
            "Як ти проводиш час, коли тобі самотньо?"
        ],
        "мотивація": [
            "Що тебе надихає зараз?",
            "Яка в тебе зараз ціль?",
            "Що ти хочеш відчути, коли досягнеш цього?"
        ],
        "здоров’я": [
            "Як ти дбаєш про себе останнім часом?",
            "Були сьогодні моменти відпочинку?",
            "Що для тебе означає бути в гарному стані?"
        ],
        "тривога": [
            "Що викликає в тебе найбільше хвилювання?",
            "Хочеш, я допоможу тобі з цим впоратися?",
            "Ти просто хочеш виговоритися?"
        ],
        "друзі": [
            "З ким тобі хочеться зараз поговорити?",
            "Як ти проводиш час з близькими?",
            "Ти хотів(ла) би, щоб хтось був поруч?"
        ],
        "цілі": [
            "Яка ціль тобі зараз ближча?",
            "Хочеш, я допоможу її спланувати?",
            "З чого б ти хотів(ла) почати?"
        ],
    },
    "be": {
        "спорт": [
            "Ці цяпер займаешся чымсьці актыўным?",
            "Хочаш, прапаную табе лёгкі чэлендж?",
            "Якая трэніроўка табе найбольш падабаецца?"
        ],
        "любоў": [
            "Што ты адчуваеш да гэтага чалавека зараз?",
            "Хочаш расказаць, што было далей?",
            "Што для цябе важна ў адносінах?"
        ],
        "праца": [
            "Што табе падабаецца ці не падабаецца ў тваёй працы?",
            "Ці хочаш нешта змяніць?",
            "Ці ёсць у цябе мара, звязаная з кар’ерай?"
        ],
        "грошы": [
            "Як ты сябе адчуваеш у фінансах зараз?",
            "Што б ты хацеў палепшыць?",
            "Ці ёсць у цябе фінансавая мэта?"
        ],
        "адзінота": [
            "Чаго табе зараз найбольш не хапае?",
            "Хочаш, я проста пабуду побач?",
            "Як ты праводзіш час, калі адчуваеш сябе адзінокім?"
        ],
        "матывацыя": [
            "Што цябе натхняе зараз?",
            "Якая ў цябе цяпер мэта?",
            "Што ты хочаш адчуць, калі дасягнеш гэтага?"
        ],
        "здоров’е": [
            "Як ты клапоцішся пра сябе апошнім часам?",
            "Былі ў цябе моманты адпачынку сёння?",
            "Што для цябе значыць быць у добрым стане?"
        ],
        "трывога": [
            "Што цябе хвалюе больш за ўсё зараз?",
            "Хочаш, я дапамагу табе з гэтым?",
            "Ты проста хочаш выгаварыцца?"
        ],
        "сябры": [
            "З кім табе хочацца зараз пагаварыць?",
            "Як ты звычайна праводзіш час з блізкімі?",
            "Ці хацеў бы ты, каб нехта быў побач зараз?"
        ],
        "мэты": [
            "Якая мэта табе цяпер бліжэйшая?",
            "Хочаш, я дапамагу яе спланаваць?",
            "З чаго б ты хацеў пачаць?"
        ],
    },
    "kk": {
        "спорт": [
            "Қазір қандай да бір белсенділікпен айналысып жатырсың ба?",
            "Саған жеңіл тапсырма ұсынайын ба?",
            "Қандай жаттығу саған ұнайды?"
        ],
        "махаббат": [
            "Бұл адамға қазір не сезесің?",
            "Әрі қарай не болғанын айтасың ба?",
            "Қарым-қатынаста сен үшін ең маңызды не?"
        ],
        "жұмыс": [
            "Жұмысыңда не ұнайды, не ұнамайды?",
            "Бір нәрсені өзгерткің келе ме?",
            "Мансапқа қатысты арманың бар ма?"
        ],
        "ақша": [
            "Қаржылай қазір қалай сезініп жүрсің?",
            "Нені жақсартқың келеді?",
            "Қаржылық мақсатың бар ма?"
        ],
        "жалғыздық": [
            "Қазір саған не жетіспейді?",
            "Қасыңда жай отырайын ба?",
            "Өзіңді жалғыз сезінгенде уақытыңды қалай өткізесің?"
        ],
        "мотивация": [
            "Қазір сені не шабыттандырады?",
            "Қазір сенің мақсатың қандай?",
            "Соны орындағанда не сезінгің келеді?"
        ],
        "денсаулық": [
            "Соңғы кезде өзіңді қалай күттің?",
            "Бүгін демалдың ба?",
            "Саған жақсы күйде болу нені білдіреді?"
        ],
        "алаңдаушылық": [
            "Қазір не үшін ең көп алаңдап жүрсің?",
            "Саған көмектесейін бе?",
            "Тек сөйлескің келе ме?"
        ],
        "достар": [
            "Қазір кіммен сөйлескің келеді?",
            "Достарыңмен уақытты қалай өткізесің?",
            "Қасыңда біреу болғанын қалар ма едің?"
        ],
        "мақсаттар": [
            "Қазір қай мақсат саған ең жақын?",
            "Оны жоспарлауға көмектесейін бе?",
            "Бүгін неден бастағың келеді?"
        ],
    },
    "kg": {
        "спорт": [
            "Азыр кандайдыр бир активдүү нерсе менен алектенип жатасыңбы?",
            "Сага жеңил тапшырма сунуштайынбы?",
            "Кайсы машыгуу сага көбүрөөк жагат?"
        ],
        "сүйүү": [
            "Бул адамга азыр эмне сезесиң?",
            "Андан кийин эмне болгонун айткың келеби?",
            "Мамиледе сен үчүн эмнелер маанилүү?"
        ],
        "иш": [
            "Ишиңде эмнени жактырасың же жактырбайсың?",
            "Бир нерсени өзгөрткүң келеби?",
            "Кесипке байланышкан кыялың барбы?"
        ],
        "акча": [
            "Каржылык абалың азыр кандай?",
            "Эмне жакшырткың келет?",
            "Каржылык максат коюп көрдүң беле?"
        ],
        "жалгыздык": [
            "Азыр сага эмнеден эң көп жетишпейт?",
            "Жанында жөн гана отуруп турайынбы?",
            "Өзүңдү жалгыз сезгенде убактыңды кантип өткөрөсүң?"
        ],
        "мотивация": [
            "Азыр сени эмне шыктандырат?",
            "Азыркы максатың кандай?",
            "Аны аткарганда эмнени сезгиң келет?"
        ],
        "ден-соолук": [
            "Акыркы күндөрү өзүңдү кандай карадың?",
            "Бүгүн эс алдыңбы?",
            "Сен үчүн жакшы абалда болуу эмнени билдирет?"
        ],
        "тынчсыздануу": [
            "Азыр эмнеге көбүрөөк тынчсызданып жатасың?",
            "Сага жардам берейинби?",
            "Жөн эле сүйлөшкүң келеби?"
        ],
        "достор": [
            "Азыр ким менен сүйлөшкүм келет?",
            "Досторуң менен убакытты кантип өткөрөсүң?",
            "Азыр сенин жаныңда кимдир болгонуңду каалайсыңбы?"
        ],
        "максаттар": [
            "Азыр кайсы максат сага жакын?",
            "Аны пландаштырууга жардам берейинби?",
            "Бүгүн эмнеден баштагың келет?"
        ],
    },
    "hy": {
        "սպորտ": [
            "Հիմա ինչ-որ ակտիվ բանով զբաղվա՞ծ ես:",
            "Ուզում ես առաջարկեմ թեթև մարտահրավե՞ր:",
            "Ի՞նչ մարզում է քեզ ամենաշատ ուրախացնում:"
        ],
        "սեր": [
            "Ի՞նչ ես հիմա զգում այդ մարդու հանդեպ:",
            "Ուզու՞մ ես պատմես, ինչ եղավ հետո:",
            "Ինչն է քեզ համար կարևոր հարաբերություններում?"
        ],
        "աշխատանք": [
            "Ի՞նչն է քեզ դուր գալիս կամ չի դուր գալիս աշխատանքում:",
            "Ուզու՞մ ես ինչ-որ բան փոխել:",
            "Կարիերայի հետ կապված երազանք ունե՞ս:"
        ],
        "փող": [
            "Ինչպե՞ս ես քեզ զգում ֆինանսական առումով:",
            "Ի՞նչ կուզենայիր բարելավել:",
            "Ֆինանսական նպատակ ունե՞ս:"
        ],
        "միայնություն": [
            "Ի՞նչն է քեզ հիմա առավելապես պակասում:",
            "Ցանկանու՞մ ես, որ պարզապես կողքիդ լինեմ:",
            "Ինչպե՞ս ես ժամանակ անցկացնում, երբ քեզ միայնակ ես զգում:"
        ],
        "մոտիվացիա": [
            "Ի՞նչ է քեզ հիմա ոգեշնչում:",
            "Ո՞րն է քո այսօրվա նպատակը:",
            "Ի՞նչ ես ուզում զգալ, երբ հասնես դրան:"
        ],
        "առողջություն": [
            "Վերջին շրջանում ինչպես ես հոգացել քեզ:",
            "Այսօր հանգստացել ե՞ս:",
            "Ի՞նչ է նշանակում քեզ համար լինել լավ վիճակում:"
        ],
        "անհանգստություն": [
            "Ի՞նչն է հիմա քեզ ամենաշատ անհանգստացնում:",
            "Ցանկանու՞մ ես, որ օգնեմ քեզ:",
            "Պարզապես ուզում ե՞ս խոսել:"
        ],
        "ընկերներ": [
            "Ու՞մ հետ կուզենայիր հիմա խոսել:",
            "Ինչպե՞ս ես սովորաբար ժամանակ անցկացնում ընկերների հետ:",
            "Կուզենայիր, որ ինչ-որ մեկը հիմա կողքիդ լիներ?"
        ],
        "նպատակներ": [
            "Ո՞ր նպատակն է քեզ հիմա առավել մոտ:",
            "Ցանկանու՞մ ես, որ օգնենք այն պլանավորել:",
            "Ի՞նչից կցանկանայիր սկսել այսօր:"
        ],
    },
    "ce": {
        "спорт": [
            "Хьо тIехь кара хIинца тIехь хийца хIинца?",
            "БIаьргаш челлендж ва хаа?",
            "ХIинца спорт хIунга ца тIехь шарш лело?"
        ],
        "любовь": [
            "ХIинца хIо хIинца хьо хийцал?",
            "Кхета хьо воьшна хаа?",
            "Ма хIинца хьо оцу хаьрж?"
        ],
        "работа": [
            "Хьо хIинца ца яьлла дIайа?",
            "Кхета хаьрж хIинца хьо?",
            "Мансах лаьцна хьо тIехь?"
        ],
        "деньги": [
            "Финанс хьо тIехь яц?",
            "Хьо хIунга хьо шун?",
            "Финанс хьо ца яц?"
        ],
        "одиночество": [
            "Ма хIун хьо тIехь нахь хIун?",
            "Хьо хьал дIайаш?",
            "Ма хIун хьо йаьлла да?"
        ],
        "мотивация": [
            "Ма хIун хьо тIехь йоьлла?",
            "Ма ца тIехь ха?",
            "Ма хIун хьо тIехь хаа?"
        ],
        "здоровье": [
            "Ма хIун хьо ца яц?",
            "Ма хIун хьо хийца?",
            "Ма хIун хьо ца яц хьал?"
        ],
        "тревога": [
            "Ма хIун хьо хийца ха?",
            "Хьо хIунга кхета?",
            "Ма хIун хьо йаьлла?"
        ],
        "друзья": [
            "Ма хIун хьо хIинца ца?",
            "Ма хIун хьо хIунга ха?",
            "Ма хIун хьо хIунга хаьрж?"
        ],
        "цели": [
            "Ма хIун хьо ца ха?",
            "Ма хIун хьо плана ха?",
            "Ма хIун хьо ха?"
        ],
    },
    "md": {
        "sport": [
            "Te ocupi cu ceva activ acum?",
            "Vrei să îți dau o provocare ușoară?",
            "Ce fel de antrenament îți place cel mai mult?"
        ],
        "dragoste": [
            "Ce simți pentru această persoană acum?",
            "Vrei să îmi spui ce s-a întâmplat mai departe?",
            "Ce este important pentru tine într-o relație?"
        ],
        "muncă": [
            "Ce îți place sau nu îți place la munca ta?",
            "Vrei să schimbi ceva?",
            "Ai un vis legat de carieră?"
        ],
        "bani": [
            "Cum te simți acum din punct de vedere financiar?",
            "Ce ai vrea să îmbunătățești?",
            "Ai un obiectiv financiar?"
        ],
        "singurătate": [
            "Ce îți lipsește cel mai mult acum?",
            "Vrei să fiu doar alături de tine?",
            "Cum îți petreci timpul când te simți singur?"
        ],
        "motivație": [
            "Ce te inspiră acum?",
            "Care este obiectivul tău acum?",
            "Ce vrei să simți când vei reuși?"
        ],
        "sănătate": [
            "Cum ai grijă de tine în ultima vreme?",
            "Ai avut momente de odihnă astăzi?",
            "Ce înseamnă pentru tine să fii într-o stare bună?"
        ],
        "anxietate": [
            "Ce te îngrijorează cel mai mult acum?",
            "Vrei să te ajut cu asta?",
            "Vrei doar să vorbești despre asta?"
        ],
        "prieteni": [
            "Cu cine ai vrea să vorbești acum?",
            "Cum îți petreci timpul cu prietenii?",
            "Ai vrea să fie cineva acum lângă tine?"
        ],
        "obiective": [
            "Care obiectiv îți este acum mai aproape de suflet?",
            "Vrei să te ajut să îl planifici?",
            "Cu ce ai vrea să începi azi?"
        ],
    },
    "ka": {
        "სპორტი": [
            "ახლა რაღაც აქტიურზე მუშაობ?",
            "გინდა შემოგთავაზო მარტივი გამოწვევა?",
            "რა ვარჯიში მოგწონს ყველაზე მეტად?"
        ],
        "სიყვარული": [
            "რა გრძნობები გაქვს ამ ადამიანის მიმართ ახლა?",
            "გინდა მომიყვე, რა მოხდა მერე?",
            "რა არის შენთვის მნიშვნელოვანი ურთიერთობებში?"
        ],
        "სამუშაო": [
            "რა მოგწონს ან არ მოგწონს შენს სამუშაოში?",
            "გინდა რამე შეცვალო?",
            "გაქვს კარიერული ოცნება?"
        ],
        "ფული": [
            "როგორ გრძნობ თავს ფინანსურად ახლა?",
            "რა გსურს გააუმჯობესო?",
            "გაქვს ფინანსური მიზანი?"
        ],
        "მარტოობა": [
            "რისი ნაკლებობა ყველაზე მეტად გაწუხებს ახლა?",
            "გინდა, უბრალოდ გვერდით ვიყო?",
            "როგორ ატარებ დროს, როცა თავს მარტო გრძნობ?"
        ],
        "მოტივაცია": [
            "რა გაძლევს შთაგონებას ახლა?",
            "რა მიზანი გაქვს ახლა?",
            "რა გსურს იგრძნო, როცა ამას მიაღწევ?"
        ],
        "ჯანმრთელობა": [
            "როგორ ზრუნავ საკუთარ თავზე ბოლო დროს?",
            "დღეს დაისვენე?",
            "რა ნიშნავს შენთვის, იყო კარგ მდგომარეობაში?"
        ],
        "შფოთვა": [
            "რა გაწუხებს ყველაზე მეტად ახლა?",
            "გინდა, დაგეხმარო ამაში?",
            "უბრალოდ გინდა, რომ ვისაუბროთ?"
        ],
        "მეგობრები": [
            "ვისთან გინდა ახლა საუბარი?",
            "როგორ ატარებ დროს მეგობრებთან?",
            "გსურს, რომ ვინმე ახლოს იყოს ახლა?"
        ],
        "მიზნები": [
            "რომელი მიზანი გაქვს ახლავე?",
            "გინდა, დაგეხმარო მისი დაგეგმვაში?",
            "რით დაიწყებდი დღეს?"
        ],
    },
}

    # Определяем язык для текущего пользователя
    topic_questions = questions_by_topic_by_lang.get(lang, questions_by_topic_by_lang["ru"])
    # Пытаемся получить список вопросов для темы
    questions = topic_questions.get(topic.lower())
    if questions:
        follow_up = random.choice(questions)
        return reply.strip() + "\n\n" + follow_up
    return reply
    
MORNING_MESSAGES = {
    "ru": [
        "🌞 Доброе утро! Как ты сегодня? 💜",
        "☕ Доброе утро! Пусть твой день будет лёгким и приятным ✨",
        "💌 Приветик! Утро — самое время начать что-то классное. Расскажешь, как настроение?",
        "🌸 С добрым утром! Желаю тебе улыбок и тепла сегодня 🫶",
        "😇 Утро доброе! Я тут и думаю о тебе, как ты там?",
        "🌅 Доброе утро! Сегодня отличный день, чтобы сделать что-то для себя 💛",
        "💫 Привет! Как спалось? Желаю тебе продуктивного и яркого дня ✨",
        "🌻 Утро доброе! Пусть сегодня всё будет в твою пользу 💪",
        "🍀 Доброе утро! Сегодняшний день — новая возможность для чего-то прекрасного 💜",
        "☀️ Привет! Улыбнись новому дню, он тебе точно улыбнётся 🌈"
    ],
    "en": [
        "🌞 Good morning! How are you today? 💜",
        "☕ Good morning! May your day be light and pleasant ✨",
        "💌 Hi there! Morning is the best time to start something great. How’s your mood?",
        "🌸 Good morning! Wishing you smiles and warmth today 🫶",
        "😇 Morning! I’m here thinking of you, how are you?",
        "🌅 Good morning! Today is a great day to do something for yourself 💛",
        "💫 Hi! How did you sleep? Wishing you a productive and bright day ✨",
        "🌻 Good morning! May everything work out in your favor today 💪",
        "🍀 Good morning! Today is a new opportunity for something wonderful 💜",
        "☀️ Hey! Smile at the new day, and it will smile back 🌈"
    ],
    "uk": [
        "🌞 Доброго ранку! Як ти сьогодні? 💜",
        "☕ Доброго ранку! Нехай твій день буде легким і приємним ✨",
        "💌 Привітик! Ранок — найкращий час почати щось класне. Як настрій?",
        "🌸 З добрим ранком! Бажаю тобі усмішок і тепла сьогодні 🫶",
        "😇 Добрий ранок! Я тут і думаю про тебе, як ти?",
        "🌅 Доброго ранку! Сьогодні чудовий день, щоб зробити щось для себе 💛",
        "💫 Привіт! Як спалося? Бажаю тобі продуктивного і яскравого дня ✨",
        "🌻 Доброго ранку! Нехай сьогодні все буде на твою користь 💪",
        "🍀 Доброго ранку! Сьогоднішній день — нова можливість для чогось прекрасного 💜",
        "☀️ Привіт! Усміхнися новому дню, і він усміхнеться тобі 🌈"
    ],
    "be": [
        "🌞 Добрай раніцы! Як ты сёння? 💜",
        "☕ Добрай раніцы! Хай твой дзень будзе лёгкім і прыемным ✨",
        "💌 Прывітанне! Раніца — самы час пачаць нешта класнае. Як настрой?",
        "🌸 З добрай раніцай! Жадаю табе ўсмешак і цяпла сёння 🫶",
        "😇 Добрай раніцы! Я тут і думаю пра цябе, як ты?",
        "🌅 Добрай раніцы! Сёння выдатны дзень, каб зрабіць нешта для сябе 💛",
        "💫 Прывітанне! Як спалася? Жадаю табе прадуктыўнага і яркага дня ✨",
        "🌻 Добрай раніцы! Хай сёння ўсё будзе на тваю карысць 💪",
        "🍀 Добрай раніцы! Сённяшні дзень — новая магчымасць для чагосьці прыгожага 💜",
        "☀️ Прывітанне! Усміхніся новаму дню, і ён табе ўсміхнецца 🌈"
    ],
    "kk": [
        "🌞 Қайырлы таң! Бүгін қалайсың? 💜",
        "☕ Қайырлы таң! Күнің жеңіл әрі тамаша өтсін ✨",
        "💌 Сәлем! Таң — керемет бір нәрсені бастауға ең жақсы уақыт. Көңіл-күйің қалай?",
        "🌸 Қайырлы таң! Саған күлкі мен жылулық тілеймін 🫶",
        "😇 Қайырлы таң! Сен туралы ойлап отырмын, қалайсың?",
        "🌅 Қайырлы таң! Бүгін өзің үшін бір нәрсе істеуге тамаша күн 💛",
        "💫 Сәлем! Қалай ұйықтадың? Саған өнімді әрі жарқын күн тілеймін ✨",
        "🌻 Қайырлы таң! Бүгін бәрі сенің пайдаңа шешілсін 💪",
        "🍀 Қайырлы таң! Бүгінгі күн — керемет мүмкіндік 💜",
        "☀️ Сәлем! Жаңа күнге күл, ол саған да күліп жауап береді 🌈"
    ],
    "kg": [
        "🌞 Кайырдуу таң! Бүгүн кандайсың? 💜",
        "☕ Кайырдуу таң! Күнүң жеңил жана жагымдуу өтсүн ✨",
        "💌 Салам! Таң — мыкты нерсе баштоого эң жакшы убакыт. Көңүлүң кандай?",
        "🌸 Кайырдуу таң! Сага жылмайуу жана жылуулук каалайм 🫶",
        "😇 Кайырдуу таң! Сени ойлоп жатам, кандайсың?",
        "🌅 Кайырдуу таң! Бүгүн өзүң үчүн бир нерсе кылууга сонун күн 💛",
        "💫 Салам! Кантип уктадың? Сага жемиштүү жана жарык күн каалайм ✨",
        "🌻 Кайырдуу таң! Бүгүн баары сенин пайдаңа болсун 💪",
        "🍀 Кайырдуу таң! Бүгүнкү күн — сонун мүмкүнчүлүк 💜",
        "☀️ Салам! Жаңы күнгө жылмай, ал сага да жылмайт 🌈"
    ],
    "hy": [
        "🌞 Բարի լույս! Այսօր ինչպես ես? 💜",
        "☕ Բարի լույս! Թող քո օրը լինի թեթև ու հաճելի ✨",
        "💌 Բարև! Առավոտը՝ ամենալավ ժամանակն է նոր բան սկսելու։ Ինչպիսի՞ն է տրամադրությունդ?",
        "🌸 Բարի լույս! Ցանկանում եմ, որ այսօր լցված լինի ժպիտներով ու ջերմությամբ 🫶",
        "😇 Բարի լույս! Քեզ եմ մտածում, ինչպես ես?",
        "🌅 Բարի լույս! Այսօր հրաշալի օր է ինչ-որ բան քեզ համար անելու համար 💛",
        "💫 Բարև! Ինչպե՞ս քնեցիր: Ցանկանում եմ քեզ արդյունավետ և պայծառ օր ✨",
        "🌻 Բարի լույս! Թող այսօր ամեն ինչ լինի քո օգտին 💪",
        "🍀 Բարի լույս! Այսօր նոր հնարավորություն է ինչ-որ հրաշալի բանի համար 💜",
        "☀️ Բարև! Ժպտա այս նոր օրվան, և այն քեզ կժպտա 🌈"
    ],
    "ce": [
        "🌞 Дик маьрша дIа! Хьо ца хьун? 💜",
        "☕ Дик маьрша дIа! Цхьа дIа, ца дIа цхьаъ! ✨",
        "💌 Салам! Маьрша дIа — хьо хьуна йоI хийцам. Хьо ца?",
        "🌸 Дик маьрша дIа! Хьо велакъежа дIац цхьан 🫶",
        "😇 Дик маьрша дIа! Са хьуна йац, хьо ца?",
        "🌅 Дик маьрша дIа! Хьо ца ю хьо дIа! 💛",
        "💫 Салам! Хьо йац? Хьо лелоран цхьан ✨",
        "🌻 Дик маьрша дIа! Цхьа дIа хьуна къобал! 💪",
        "🍀 Дик маьрша дIа! Хьо къобал ден! 💜",
        "☀️ Салам! Хьо дIац, цхьа дIа хьуна дIац! 🌈"
    ],
    "md": [
        "🌞 Bună dimineața! Cum ești azi? 💜",
        "☕ Bună dimineața! Să ai o zi ușoară și plăcută ✨",
        "💌 Salut! Dimineața e cel mai bun moment să începi ceva frumos. Cum e dispoziția ta?",
        "🌸 Bună dimineața! Îți doresc zâmbete și căldură azi 🫶",
        "😇 Bună dimineața! Mă gândesc la tine, cum ești?",
        "🌅 Bună dimineața! Azi e o zi perfectă să faci ceva pentru tine 💛",
        "💫 Salut! Cum ai dormit? Îți doresc o zi productivă și plină de lumină ✨",
        "🌻 Bună dimineața! Să fie totul azi în favoarea ta 💪",
        "🍀 Bună dimineața! Ziua de azi e o nouă oportunitate pentru ceva minunat 💜",
        "☀️ Salut! Zâmbește zilei noi, și ea îți va zâmbi 🌈"
    ],
    "ka": [
        "🌞 დილა მშვიდობისა! როგორ ხარ დღეს? 💜",
        "☕ დილა მშვიდობისა! გისურვებ მსუბუქ და სასიამოვნო დღეს ✨",
        "💌 გამარჯობა! დილა საუკეთესო დროა, რომ რაღაც კარგი დაიწყო. როგორია განწყობა?",
        "🌸 დილა მშვიდობისა! გისურვებ ღიმილებს და სითბოს დღეს 🫶",
        "😇 დილა მშვიდობისა! შენზე ვფიქრობ, როგორ ხარ?",
        "🌅 დილა მშვიდობისა! დღეს შესანიშნავი დღეა საკუთარი თავისთვის რაღაც გასაკეთებლად 💛",
        "💫 გამარჯობა! როგორ გამოიძინე? გისურვებ პროდუქტიულ და ნათელ დღეს ✨",
        "🌻 დილა მშვიდობისა! ყველაფერმა დღეს შენს სასარგებლოდ ჩაიაროს 💪",
        "🍀 დილა მშვიდობისა! დღევანდელი დღე ახალი შესაძლებლობაა რაღაც მშვენიერისთვის 💜",
        "☀️ გამარჯობა! გაუღიმე ახალ დღეს და ისაც გაგიღიმებს 🌈"
    ],
}

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
    lang = user_languages.get(user_id, "ru")

    # 🎯 Тексты для разных языков
    goal_texts = {
        "ru": {
            "no_args": "✏️ Чтобы поставить цель, напиши так:\n`/goal Прочитать 10 страниц до 2025-06-28 напомни`",
            "limit": "🔒 В бесплатной версии можно ставить только 3 цели в день.\nХочешь больше? Оформи Mindra+ 💜",
            "bad_date": "❗ Неверный формат даты. Используй ГГГГ-ММ-ДД",
            "added": "🎯 Цель добавлена:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Напоминание включено"
        },
        "uk": {
            "no_args": "✏️ Щоб поставити ціль, напиши так:\n`/goal Прочитати 10 сторінок до 2025-06-28 нагадай`",
            "limit": "🔒 У безкоштовній версії можна ставити лише 3 цілі на день.\nХочеш більше? Оформи Mindra+ 💜",
            "bad_date": "❗ Невірний формат дати. Використовуй РРРР-ММ-ДД",
            "added": "🎯 Ціль додана:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Нагадування увімкнено"
        },
        "be": {
            "no_args": "✏️ Каб паставіць мэту, напішы так:\n`/goal Прачытай 10 старонак да 2025-06-28 нагадай`",
            "limit": "🔒 У бясплатнай версіі можна ставіць толькі 3 мэты на дзень.\nХочаш больш? Аформі Mindra+ 💜",
            "bad_date": "❗ Няправільны фармат даты. Выкарыстоўвай ГГГГ-ММ-ДД",
            "added": "🎯 Мэта дададзена:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 Напамін уключаны"
        },
        "kk": {
            "no_args": "✏️ Мақсат қою үшін былай жаз:\n`/goal 10 бет оқу 2025-06-28 дейін еске сал`",
            "limit": "🔒 Тегін нұсқада күніне тек 3 мақсат қоюға болады.\nКөбірек керек пе? Mindra+ алыңыз 💜",
            "bad_date": "❗ Күн форматы қате. ЖЖЖЖ-АА-КК түрінде жазыңыз",
            "added": "🎯 Мақсат қосылды:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Еске салу қосылды"
        },
        "kg": {
            "no_args": "✏️ Максат коюу үчүн мындай жаз:\n`/goal 10 бет оку 2025-06-28 чейин эскертип кой`",
            "limit": "🔒 Акысыз версияда күнүнө 3 гана максат коюуга болот.\nКөбүрөөк керекпи? Mindra+ жазылуу 💜",
            "bad_date": "❗ Датанын форматы туура эмес. ЖЖЖЖ-АА-КК колдон",
            "added": "🎯 Максат кошулду:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Эскертүү күйгүзүлдү"
        },
        "hy": {
            "no_args": "✏️ Նպատակ դնելու համար գրիր այսպես:\n`/goal Կարդալ 10 էջ մինչև 2025-06-28 հիշեցրու`",
            "limit": "🔒 Անվճար տարբերակում կարելի է օրական միայն 3 նպատակ դնել.\nՈւզում ես ավելին? Միացիր Mindra+ 💜",
            "bad_date": "❗ Սխալ ամսաթվի ձևաչափ. Օգտագործիր ՏՏՏՏ-ԱԱ-ՕՕ",
            "added": "🎯 Նպատակ ավելացվեց:",
            "deadline": "🗓 Վերջնաժամկետ:",
            "remind": "🔔 Հիշեցումը միացված է"
        },
        "ce": {
            "no_args": "✏️ Мацахь кхоллар, йаьллаца:\n`/goal Къобалле 10 агӀо 2025-06-28 даьлча эха`",
            "limit": "🔒 Аьтто версия хийцна, цхьаьнан 3 мацахь дина кхолларш йолуш.\nКъобал? Mindra+ 💜",
            "bad_date": "❗ Дата формат дукха. ГГГГ-ММ-ДД формата язде",
            "added": "🎯 Мацахь тӀетоха:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 ДӀадела хийна"
        },
        "md": {
            "no_args": "✏️ Pentru a seta un obiectiv, scrie așa:\n`/goal Citește 10 pagini până la 2025-06-28 amintește`",
            "limit": "🔒 În versiunea gratuită poți seta doar 3 obiective pe zi.\nVrei mai multe? Obține Mindra+ 💜",
            "bad_date": "❗ Format de dată incorect. Folosește AAAA-LL-ZZ",
            "added": "🎯 Obiectiv adăugat:",
            "deadline": "🗓 Termen limită:",
            "remind": "🔔 Memento activat"
        },
        "ka": {
            "no_args": "✏️ მიზნის დასაყენებლად დაწერე ასე:\n`/goal წავიკითხო 10 გვერდი 2025-06-28-მდე შემახსენე`",
            "limit": "🔒 უფასო ვერსიაში დღეში მხოლოდ 3 მიზნის დაყენება შეგიძლია.\nგინდა მეტი? გამოიწერე Mindra+ 💜",
            "bad_date": "❗ არასწორი თარიღის ფორმატი. გამოიყენე წწწწ-თთ-რრ",
            "added": "🎯 მიზანი დამატებულია:",
            "deadline": "🗓 ბოლო ვადა:",
            "remind": "🔔 შეხსენება ჩართულია"
        },
        "en": {
            "no_args": "✏️ To set a goal, write like this:\n`/goal Read 10 pages by 2025-06-28 remind`",
            "limit": "🔒 In the free version you can set only 3 goals per day.\nWant more? Get Mindra+ 💜",
            "bad_date": "❗ Wrong date format. Use YYYY-MM-DD",
            "added": "🎯 Goal added:",
            "deadline": "🗓 Deadline:",
            "remind": "🔔 Reminder is on"
        },
    }

    t = goal_texts.get(lang, goal_texts["ru"])

    # ✅ Проверка аргументов
    if not context.args:
        await update.message.reply_text(t["no_args"], parse_mode="Markdown")
        return

    # 📅 Лимит целей
    today = str(date.today())
    if user_id not in user_goal_count:
        user_goal_count[user_id] = {"date": today, "count": 0}
    else:
        if user_goal_count[user_id]["date"] != today:
            user_goal_count[user_id] = {"date": today, "count": 0}

    if user_id not in PREMIUM_USERS:
        if user_goal_count[user_id]["count"] >= 3:
            await update.message.reply_text(t["limit"])
            return

    user_goal_count[user_id]["count"] += 1

    # ✨ Логика постановки цели
    text = " ".join(context.args)
    deadline_match = re.search(r'до\s+(\d{4}-\d{2}-\d{2})', text)
    remind = "напомни" in text.lower()

    deadline = None
    if deadline_match:
        try:
            deadline = deadline_match.group(1)
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(t["bad_date"])
            return

    goal_text = re.sub(r'до\s+\d{4}-\d{2}-\d{2}', '', text, flags=re.IGNORECASE).replace("напомни", "").strip()

    add_goal(user_id, goal_text, deadline=deadline, remind=remind)
    add_points(user_id, 1)

    reply = f"{t['added']} *{goal_text}*"
    if deadline:
        reply += f"\n{t['deadline']} `{deadline}`"
    if remind:
        reply += f"\n{t['remind']}"

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
            "🌐 Please select the language of communication:",
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
        "md": ["🎯 Setează obiectiv", "📋 Obiectivele mele", "🌱 Adaugă obicei", "📊 Obiceiurile mele", "💎 Abonament Mindra+"],
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

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    about_texts = {
        "ru": (
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
        ),
        "uk": (
            "💜 *Привіт! Я — Mindra.*\n\n"
            "Я тут, щоб бути поруч, коли тобі потрібно виговоритися, знайти мотивацію чи просто відчути підтримку.\n"
            "Можемо поспілкуватися тепло, по‑доброму, з турботою — без осуду й тиску 🦋\n\n"
            "🔮 *Що я вмію:*\n"
            "• Підтримати, коли важко\n"
            "• Нагадати, що ти — не один(а)\n"
            "• Допомогти знайти фокус і натхнення\n"
            "• І інколи просто поговорити по душах 😊\n\n"
            "_Я не ставлю діагнози й не замінюю психолога, але намагаюся бути поруч у потрібний момент._\n\n"
            "✨ *Mindra — це простір для тебе.*"
        ),
        "be": (
            "💜 *Прывітанне! Я — Mindra.*\n\n"
            "Я тут, каб быць побач, калі табе трэба выказацца, знайсці матывацыю ці проста адчуць падтрымку.\n"
            "Мы можам пагаварыць цёпла, добразычліва, з клопатам — без асуджэння і ціску 🦋\n\n"
            "🔮 *Што я ўмею:*\n"
            "• Падтрымаць, калі цяжка\n"
            "• Нагадаць, што ты — не адзін(а)\n"
            "• Дапамагчы знайсці фокус і натхненне\n"
            "• І часам проста пагаварыць па душах 😊\n\n"
            "_Я не ставлю дыягназы і не замяняю псіхолага, але стараюся быць побач у патрэбны момант._\n\n"
            "✨ *Mindra — гэта прастора для цябе.*"
        ),
        "kk": (
            "💜 *Сәлем! Мен — Mindra.*\n\n"
            "Мен осындамын, саған сөйлесу, мотивация табу немесе жай ғана қолдау сезіну қажет болғанда жанында болу үшін.\n"
            "Біз жылы, мейірімді түрде сөйлесе аламыз — сынсыз, қысымсыз 🦋\n\n"
            "🔮 *Мен не істей аламын:*\n"
            "• Қиын сәтте қолдау көрсету\n"
            "• Сенің жалғыз емес екеніңді еске салу\n"
            "• Назар мен шабыт табуға көмектесу\n"
            "• Кейде жай ғана жан сырын бөлісу 😊\n\n"
            "_Мен диагноз қоймаймын және психологты алмастырмаймын, бірақ әрқашан жанында болуға тырысамын._\n\n"
            "✨ *Mindra — бұл сен үшін жасалған кеңістік.*"
        ),
        "kg": (
            "💜 *Салам! Мен — Mindra.*\n\n"
            "Мен бул жерде сени угуп, мотивация берип же жөн гана колдоо көрсөтүш үчүн жанында болоюн деп турам.\n"
            "Биз жылуу, боорукер сүйлөшө алабыз — айыптоосуз, басымсыз 🦋\n\n"
            "🔮 *Мен эмне кыла алам:*\n"
            "• Кыйын кезде колдоо көрсөтүү\n"
            "• Жалгыз эмес экениңди эскертүү\n"
            "• Фокус жана шыктанууну табууга жардам берүү\n"
            "• Кээде жөн гана жүрөккө жакын сүйлөшүү 😊\n\n"
            "_Мен диагноз койбойм жана психологду алмаштырбайм, бирок ар дайым жанында болууга аракет кылам._\n\n"
            "✨ *Mindra — бул сен үчүн аянтча.*"
        ),
        "hy": (
            "💜 *Բարև! Ես Mindra-ն եմ.*\n\n"
            "Ես այստեղ եմ, որ լինեմ կողքիդ, երբ ուզում ես բաց թողնել մտքերդ, գտնել մոտիվացիա կամ պարզապես զգալ աջակցություն։\n"
            "Կարող ենք խոսել ջերմությամբ, բարությամբ, հոգատարությամբ — առանց քննադատության և ճնշման 🦋\n\n"
            "🔮 *Ի՞նչ կարող եմ անել:*\n"
            "• Աջակցել, երբ դժվար է\n"
            "• Հիշեցնել, որ միայնակ չես\n"
            "• Օգնել գտնել կենտրոնացում և ներշնչանք\n"
            "• Եվ երբեմն պարզապես սրտից խոսել 😊\n\n"
            "_Ես չեմ ախտորոշում և չեմ փոխարինում հոգեբանին, բայց փորձում եմ լինել կողքիդ ճիշտ պահին._\n\n"
            "✨ *Mindra — սա տարածք է քեզ համար.*"
        ),
        "ce": (
            "💜 *Салам! Са — Mindra.*\n\n"
            "Са цуьнан хьоьшу, хьажа хьо дӀаагӀо, мотивация лаьа или йуьхала дӀац гӀо хӀума бо.\n"
            "Са даьлча, дошлаца, са а кхолларалла — без осуждения 🦋\n\n"
            "🔮 *Со хьоьшу болу:*\n"
            "• Къобалле хьо гойтах лаьцна\n"
            "• Хьо къобалле хьуна не яллац\n"
            "• Хьо мотивация йа фокус а лаха хьа\n"
            "• Ац цуьнан гойтан сийла кхолларалла 😊\n\n"
            "_Со психолог на, но кхеташ дӀаязде хьуна кхеташ са охар а._\n\n"
            "✨ *Mindra — хьоьшу хӀума.*"
        ),
        "md": (
            "💜 *Salut! Eu sunt Mindra.*\n\n"
            "Sunt aici ca să fiu alături de tine când ai nevoie să te descarci, să găsești motivație sau pur și simplu să simți sprijin.\n"
            "Putem vorbi cu căldură, blândețe și grijă — fără judecată sau presiune 🦋\n\n"
            "🔮 *Ce pot să fac:*\n"
            "• Să te susțin când îți este greu\n"
            "• Să îți reamintesc că nu ești singur(ă)\n"
            "• Să te ajut să găsești focus și inspirație\n"
            "• Și uneori doar să vorbim sincer 😊\n\n"
            "_Nu pun diagnostice și nu înlocuiesc un psiholog, dar încerc să fiu aici la momentul potrivit._\n\n"
            "✨ *Mindra — este spațiul tău.*"
        ),
        "ka": (
            "💜 *გამარჯობა! მე ვარ Mindra.*\n\n"
            "აქ ვარ, რომ შენთან ვიყო, როცა გინდა გულახდილად ილაპარაკო, იპოვო მოტივაცია ან უბრალოდ იგრძნო მხარდაჭერა.\n"
            "ჩვენ შეგვიძლია ვისაუბროთ სითბოთი, კეთილგანწყობით, ზრუნვით — განკითხვის გარეშე 🦋\n\n"
            "🔮 *რა შემიძლია:*\n"
            "• მოგცე მხარდაჭერა, როცა გიჭირს\n"
            "• შეგახსენო, რომ მარტო არ ხარ\n"
            "• დაგეხმარო ფოკუსსა და შთაგონებაში\n"
            "• ზოგჯერ უბრალოდ გულით მოგისმინო 😊\n\n"
            "_მე არ ვსვამ დიაგნოზებს და არ ვცვლი ფსიქოლოგს, მაგრამ ვცდილობ ვიყო შენს გვერდით საჭირო დროს._\n\n"
            "✨ *Mindra — ეს არის სივრცე შენთვის.*"
        ),
        "en": (
            "💜 *Hi! I’m Mindra.*\n\n"
            "I’m here to be by your side when you need to talk, find motivation, or simply feel supported.\n"
            "We can talk warmly, kindly, with care — without judgment or pressure 🦋\n\n"
            "🔮 *What I can do:*\n"
            "• Support you when things get tough\n"
            "• Remind you that you’re not alone\n"
            "• Help you find focus and inspiration\n"
            "• And sometimes just have a heart-to-heart 😊\n\n"
            "_I don’t give diagnoses and I’m not a replacement for a psychologist, but I try to be there when you need it._\n\n"
            "✨ *Mindra — a space just for you.*"
        ),
    }

    text = about_texts.get(lang, about_texts["ru"])
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
