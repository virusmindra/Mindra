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
from datetime import datetime, timedelta, timezone, date
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from habits import add_habit, get_habits, mark_habit_done, delete_habit
from telegram.constants import ChatAction, ParseMode
from config import client, TELEGRAM_BOT_TOKEN
from history import load_history, save_history, trim_history
from goals import add_goal, get_goals, mark_goal_done, delete_goal
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from storage import add_goal_for_user, get_goals_for_user, mark_goal_done
from random import randint, choice
from stats import load_stats, save_stats, get_premium_until, set_premium_until, is_premium, got_trial, set_trial, add_referral, add_points, get_user_stats, get_user_title, load_json_file, get_stats, OWNER_ID, ADMIN_USER_IDS 

# Глобальные переменные
user_last_seen = {}
user_last_prompted = {}
user_reminders = {}
user_points = {}
user_message_count = {}
user_goal_count = {}
user_languages = {}  # {user_id: 'ru'/'uk'/'md'/'be'/'kk'/'kg'/'hy'/'ka'/'ce'}
user_ref_args = {}
user_last_polled = {}
user_last_report_sent = {}  # user_id: date (ISO)
user_last_daily_sent = {}  # user_id: date (iso)

MIN_HOURS_SINCE_LAST_POLL = 96  # минимум 4 дня между опросами для одного юзера
MIN_HOURS_SINCE_ACTIVE = 8      # не отправлять, если был онлайн последние 8 часов
POLL_RANDOM_CHANCE = 0.7        # 70% шанс отправить опрос
# Для фильтрации — время по Киеву, только с 14:00 до 18:00 (2pm-6pm)
REPORT_MIN_HOUR = 14
REPORT_MAX_HOUR = 18

DAILY_MIN_HOUR = 9
DAILY_MAX_HOUR = 12

MIN_IDLE_HOURS = 8  # Минимум 8 часов между idle-напоминаниями
IDLE_TIME_START = 10  # 10:00 утра по Киеву
IDLE_TIME_END = 22    # 22:00 вечера по Киеву

def get_mode_prompt(mode, lang):
    return MODES.get(mode, MODES["default"]).get(lang, MODES["default"]["ru"])

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

        # === ДОБАВЛЯЕМ ЗДЕСЬ БОНУСЫ ===
        # 1. Выдать пробный премиум если ещё не был выдан
        trial_given = give_trial_if_needed(user_id)
        if trial_given:
            trial_text = TRIAL_GRANTED_TEXT.get(lang, TRIAL_GRANTED_TEXT["ru"])
            await update.message.reply_text(trial_text, parse_mode="Markdown")

        # 2. (Опционально) обработка реферала — если при смене языка ты хочешь поддерживать рефералы
        if context.args and context.args[0].startswith("ref"):
            referrer_id = context.args[0][3:]
            if user_id != referrer_id:
                referral_success = handle_referral(user_id, referrer_id)
                if referral_success:
                    bonus_text = REFERRAL_BONUS_TEXT.get(lang, REFERRAL_BONUS_TEXT["ru"])
                    await update.message.reply_text(bonus_text, parse_mode="Markdown")

        # 3. (Опционально) Отправить приветствие
        first_name = update.effective_user.first_name or "друг"
        welcome_text = WELCOME_TEXTS.get(lang, WELCOME_TEXTS["ru"]).format(first_name=first_name)
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        # (Можешь убрать если не нужно)

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
    user_id = str(query.from_user.id)
    lang_code = query.data.replace("lang_", "")
    user_languages[user_id] = lang_code
    logging.info(f"🌐 Пользователь {user_id} выбрал язык: {lang_code}")
    await query.answer()

    first_name = query.from_user.first_name or "друг"
    welcome_text = WELCOME_TEXTS.get(lang_code, WELCOME_TEXTS["ru"]).format(first_name=first_name)

    # -- ВАЖНО: Выдаём бонусы только при первом выборе языка! --
    ref_bonus_given = False
    trial_given = False

    # Только если пользователь впервые выбирает язык (нет got_trial)
    if not got_trial(user_id):
        # -- Если был реферал, обрабатываем
        ref_code = None
        if user_id in user_ref_args:
            ref_code = user_ref_args.pop(user_id)
        if ref_code:
            referrer_id = ref_code[3:]
            if user_id != referrer_id:
                ref_bonus_given = handle_referral(user_id, referrer_id)
                if ref_bonus_given:
                    bonus_text = REFERRAL_BONUS_TEXT.get(lang_code, REFERRAL_BONUS_TEXT["ru"])
                    await context.bot.send_message(query.message.chat_id, bonus_text, parse_mode="Markdown")
                    try:
                        await context.bot.send_message(
                            chat_id=int(referrer_id),
                            text="🎉 Твой друг зарегистрировался по твоей ссылке! Вам обоим начислено +7 дней Mindra+ 🎉"
                        )
                    except Exception as e:
                        logging.warning(f"Не удалось отправить сообщение пригласившему: {e}")

        # -- Если не было реферала — триал
        if not ref_bonus_given:
            trial_given = give_trial_if_needed(user_id)
            if trial_given:
                trial_text = TRIAL_GRANTED_TEXT.get(lang_code, TRIAL_GRANTED_TEXT["ru"])
                await context.bot.send_message(query.message.chat_id, trial_text, parse_mode="Markdown")
        # -- После бонуса — статус (опционально)
        if trial_given:
            trial_info = TRIAL_INFO_TEXT.get(lang_code, TRIAL_INFO_TEXT["ru"])
            await context.bot.send_message(query.message.chat_id, trial_info, parse_mode="Markdown")

    # Настрой стартовый режим и историю
    mode = "support"
    lang_prompt = LANG_PROMPTS.get(lang_code, LANG_PROMPTS["ru"])
    mode_prompt = MODES[mode].get(lang_code, MODES[mode]['ru'])
    system_prompt = f"{lang_prompt}\n\n{mode_prompt}"
    conversation_history[user_id] = [{"role": "system", "content": system_prompt}]
    save_history(conversation_history)

    # Приветствие
    try:
        await query.edit_message_text(
            text=welcome_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.warning(f"Не удалось отредактировать сообщение, отправляем новое. Ошибка: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=welcome_text,
            parse_mode="Markdown"
        )

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

    now = datetime.now(pytz.timezone("Europe/Kiev"))
    logging.info("⏰ Проверка неактивных пользователей...")

    for user_id, last_seen in user_last_seen.items():
        # --- Время последнего idle-напоминания (user_last_prompted)
        last_prompted = user_last_prompted.get(user_id)
        can_prompt = True

        # 1. Проверка: отправляли ли сегодня уже idle-напоминание?
        if last_prompted:
            try:
                last_prompted_dt = datetime.fromisoformat(last_prompted)
                # Интервал между напоминаниями
                if (now - last_prompted_dt) < timedelta(hours=MIN_IDLE_HOURS):
                    can_prompt = False
            except Exception:
                pass

        # 2. Проверка: человек не был активен X часов?
        if (now - last_seen) < timedelta(hours=6):
            can_prompt = False

        # 3. Проверка: только дневное время
        if not (IDLE_TIME_START <= now.hour < IDLE_TIME_END):
            can_prompt = False

        if can_prompt:
            try:
                lang = user_languages.get(str(user_id), "ru")
                idle_messages = IDLE_MESSAGES.get(lang, IDLE_MESSAGES["ru"])
                message = random.choice(idle_messages)
                await app.bot.send_message(chat_id=user_id, text=message)
                user_last_prompted[user_id] = now.isoformat()  # фиксируем время отправки
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

    # 📌 Определяем язык пользователя
    lang = user_languages.get(user_id, "ru")
    texts = VOICE_TEXTS_BY_LANG.get(lang, VOICE_TEXTS_BY_LANG["ru"])
    prompt_text = SYSTEM_PROMPT_BY_LANG.get(lang, SYSTEM_PROMPT_BY_LANG["ru"])

    try:
        message = update.message

        # 🎧 Получаем файл голосового
        file = await context.bot.get_file(message.voice.file_id)
        file_path = f"/tmp/{file.file_unique_id}.oga"
        mp3_path = f"/tmp/{file.file_unique_id}.mp3"
        await file.download_to_drive(file_path)

        # 🔄 Конвертация в mp3
        subprocess.run([
            "ffmpeg", "-i", file_path, "-ar", "44100", "-ac", "2", "-b:a", "192k", mp3_path
        ], check=True)

        # 🎙️ Распознаём голос
        with open(mp3_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        user_input = result.strip()

        # 📌 Сохраняем тему
        topic = detect_topic(user_input, lang)
        if topic:
            save_user_context(context, topic=topic)

        # 📝 Отвечаем пользователю, что распознали
        await message.reply_text(f"{texts['you_said']} {user_input}")

        # 💜 Эмпатичная реакция
        reaction = detect_emotion_reaction(user_input, lang)

        # 🧠 Системный промпт для GPT
        system_prompt = {
            "role": "system",
            "content": prompt_text
        }
        history = [system_prompt, {"role": "user", "content": user_input}]
        history = trim_history(history)

        # 🤖 Запрос к OpenAI
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=history
        )
        reply = completion.choices[0].message.content.strip()

        # 📎 Добавляем отсылку к теме
        reference = get_topic_reference(context, lang)
        if reference:
            reply = f"{reply}\n\n{reference}"

        # ❓ Добавляем follow-up вопрос
        reply = insert_followup_question(reply, user_input, lang)

        # 🔥 Добавляем эмпатичную реакцию
        reply = reaction + reply

        # 📌 Генерируем кнопки
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
    
MORNING_MESSAGES_BY_LANG = {
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
        now_kiev = datetime.now(pytz.timezone("Europe/Kiev"))
        if not (DAILY_MIN_HOUR <= now_kiev.hour < DAILY_MAX_HOUR):
            return  # Не утро — не отправляем

        for user_id in user_last_seen.keys():
            # Не отправлять если уже сегодня отправляли
            if user_last_daily_sent.get(user_id) == now_kiev.date().isoformat():
                continue

            # Не отправлять если был активен последние 8 часов
            last_active = user_last_seen.get(user_id)
            if last_active:
                try:
                    last_active_dt = datetime.fromisoformat(last_active)
                    if (now_kiev - last_active_dt).total_seconds() < 8 * 3600:
                        continue
                except Exception:
                    pass

            lang = user_languages.get(str(user_id), "ru")
            greeting = choice(MORNING_MESSAGES_BY_LANG.get(lang, MORNING_MESSAGES_BY_LANG["ru"]))
            task = choice(DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG["ru"]))

            text = f"{greeting}\n\n🎯 {task}"
            await context.bot.send_message(chat_id=user_id, text=text)
            logging.info(f"✅ Утреннее задание отправлено пользователю {user_id} на языке {lang}")
            user_last_daily_sent[user_id] = now_kiev.date().isoformat()

    except Exception as e:
        logging.error(f"❌ Ошибка при отправке утреннего задания: {e}")
        
# 🔑 Ключевые слова для эмоций на разных языках
emotion_keywords_by_lang = {
    "ru": {
        "positive": ["ура", "сделал", "сделала", "получилось", "рад", "рада", "наконец", "круто", "кайф", "горжусь", "удалось"],
        "negative": ["плохо", "тяжело", "устал", "устала", "раздражает", "не знаю", "выгорание", "одиноко", "грустно", "сложно", "печально"],
        "stress":   ["стресс", "нервы", "не спал", "не спала", "перегруз", "паника", "волнение"]
    },
    "en": {
        "positive": ["yay", "did it", "done", "achieved", "happy", "finally", "awesome", "cool", "proud", "succeeded"],
        "negative": ["bad", "hard", "tired", "annoying", "burnout", "lonely", "sad", "difficult"],
        "stress":   ["stress", "nervous", "didn't sleep", "overload", "panic"]
    },
    "uk": {
        "positive": ["ура", "зробив", "зробила", "вийшло", "радий", "рада", "нарешті", "круто", "кайф", "пишаюсь", "вдалося"],
        "negative": ["погано", "важко", "втомився", "втомилась", "дратує", "не знаю", "вигорів", "самотньо", "сумно", "складно"],
        "stress":   ["стрес", "нерви", "не спав", "не спала", "перевантаження", "паніка"]
    },
    "be": {
        "positive": ["ура", "зрабіў", "зрабіла", "атрымаўся", "рада", "нарэшце", "крута", "кайф", "гарджуся"],
        "negative": ["дрэнна", "цяжка", "стаміўся", "стамілася", "раздражняе", "не ведаю", "выгараў", "самотна", "сумна"],
        "stress":   ["стрэс", "нервы", "не спаў", "не спала", "перагрузка", "паніка"]
    },
    "kk": {
        "positive": ["жасадым", "жасап койдым", "жасалды", "қуаныштымын", "ақыры", "керемет", "мақтанамын"],
        "negative": ["жаман", "қиын", "шаршадым", "жалықтым", "жалғызбын", "мұңды", "қиындық"],
        "stress":   ["стресс", "жүйке", "ұйықтамадым", "шамадан тыс", "үрей"]
    },
    "kg": {
        "positive": ["болду", "аткардым", "бүттү", "куаныштамын", "сонун", "акыры", "суйунуп жатам", "мактанам"],
        "negative": ["жаман", "оор", "чарчап", "жалгыз", "кайгы", "кайнатат"],
        "stress":   ["стресс", "нерв", "уктаган жокмун", "чарчоо", "паника"]
    },
    "hy": {
        "positive": ["արեցի", "հաջողվեց", "ուրախ եմ", "վերջապես", "հիանալի", "հպարտ եմ"],
        "negative": ["վատ", "ծանր", "հոգնած", "միայնակ", "տխուր", "դժվար"],
        "stress":   ["սթրես", "նյարդեր", "չքնեցի", "գերլարում", "խուճապ"]
    },
    "ce": {
        "positive": ["хьо кхета", "хьо хийца", "дӀаязде", "хьо даьлча", "хьо дола", "хьо лело"],
        "negative": ["хьо ца ха", "хьо бу ха", "хьо ца йац", "хьо со", "хьо чура", "хьо ца"],
        "stress":   ["стресс", "нерв", "хьо ца спала", "хьо ца спал", "паника"]
    },
    "md": {
        "positive": ["am reușit", "gata", "fericit", "în sfârșit", "minunat", "mândru"],
        "negative": ["rău", "greu", "obosit", "singur", "trist", "dificil"],
        "stress":   ["stres", "nervi", "n-am dormit", "suprasolicitare", "panică"]
    },
    "ka": {
        "positive": ["ვქენი", "გამომივიდა", "ბედნიერი ვარ", "საბოლოოდ", "მშვენიერია", "ვამაყობ"],
        "negative": ["ცუდი", "რთული", "დაღლილი", "მარტო", "მოწყენილი", "გართულება"],
        "stress":   ["სტრესი", "ნერვები", "არ დამეძინა", "გადატვირთვა", "პანიკა"]
    },
}


# ✨ Функция определения реакции
def detect_emotion_reaction(user_input: str, lang: str = "ru") -> str:
    text = user_input.lower()
    keywords = emotion_keywords_by_lang.get(lang, emotion_keywords_by_lang["ru"])

    if any(word in text for word in keywords["positive"]):
        # Позитивная реакция
        return {
            "ru": "🥳 Вау, это звучит потрясающе! Я так рада за тебя! 💜\n\n",
            "en": "🥳 Wow, that’s amazing! I’m so happy for you! 💜\n\n",
            "uk": "🥳 Вау, це звучить чудово! Я так рада за тебе! 💜\n\n",
            "be": "🥳 Вау, гэта гучыць цудоўна! Я так рада за цябе! 💜\n\n",
            "kk": "🥳 Уауу, бұл керемет! Мен сен үшін қуаныштымын! 💜\n\n",
            "kg": "🥳 Вау, бул сонун! Мен сени менен сыймыктанам! 💜\n\n",
            "hy": "🥳 Վա՜յ, դա հիանալի է! Շատ եմ ուրախ քեզ համար! 💜\n\n",
            "ce": "🥳 Ва, хьо йац до! Са хьунан даьлча! 💜\n\n",
            "md": "🥳 Uau, asta e minunat! Sunt atât de fericit(ă) pentru tine! 💜\n\n",
            "ka": "🥳 ვაუ, ეს საოცარია! მიხარია შენთვის! 💜\n\n",
        }.get(lang, "🥳 Вау, это звучит потрясающе! Я так рада за тебя! 💜\n\n")

    if any(word in text for word in keywords["negative"]):
        # Негативная реакция
        return {
            "ru": "😔 Понимаю тебя… Я рядом, правда. Ты не один(а). 💜\n\n",
            "en": "😔 I understand… I’m here for you. You’re not alone. 💜\n\n",
            "uk": "😔 Я тебе розумію… Я поруч. Ти не один(а). 💜\n\n",
            "be": "😔 Я цябе разумею… Я побач. Ты не адзін(ая). 💜\n\n",
            "kk": "😔 Сені түсінемін… Мен қасыңдамын. Сен жалғыз емессің. 💜\n\n",
            "kg": "😔 Түшүнөм… Мен жанымдамын. Сен жалгыз эмессиң. 💜\n\n",
            "hy": "😔 Ես քեզ հասկանում եմ… Ես կողքիդ եմ։ Դու մենակ չես։ 💜\n\n",
            "ce": "😔 Са хьуна йац… Са цуьнан. Хьо ца йац. 💜\n\n",
            "md": "😔 Te înțeleg… Sunt aici pentru tine. Nu ești singur(ă). 💜\n\n",
            "ka": "😔 მესმის შენი… მე შენთან ვარ. მარტო არ ხარ. 💜\n\n",
        }.get(lang, "😔 Понимаю тебя… Я рядом, правда. Ты не один(а). 💜\n\n")

    if any(word in text for word in keywords["stress"]):
        # Стресс / тревога
        return {
            "ru": "🫂 Дыши глубже. Всё пройдёт. Давай разберёмся вместе. 🤍\n\n",
            "en": "🫂 Take a deep breath. It will pass. Let’s figure it out together. 🤍\n\n",
            "uk": "🫂 Дихай глибше. Все мине. Давай розберемося разом. 🤍\n\n",
            "be": "🫂 Зрабі глыбокі ўдых. Усё пройдзе. Давай разбярэмся разам. 🤍\n\n",
            "kk": "🫂 Терең дем ал. Барлығы өтеді. Бірге шешейік. 🤍\n\n",
            "kg": "🫂 Терең дем ал. Баары өтөт. Кел, чогуу чечебиз. 🤍\n\n",
            "hy": "🫂 Խորը շունչ քաշիր։ Ամեն ինչ կանցնի։ Եկ միասին հասկանանք։ 🤍\n\n",
            "ce": "🫂 ДIайолла. Ма бох лаьцна. Давай хаьттанхьа. 🤍\n\n",
            "md": "🫂 Respiră adânc. Totul va trece. Hai să înțelegem împreună. 🤍\n\n",
            "ka": "🫂 ღრმად ჩაისუნთქე. ყველაფერი გაივლის. მოდი, ერთად გავერკვეთ. 🤍\n\n",
        }.get(lang, "🫂 Дыши глубже. Всё пройдёт. Давай разберёмся вместе. 🤍\n\n")

    return ""
    
topic_patterns_by_lang = {
    "ru": {
        "love": {
            "patterns": r"\b(влюбил|влюблена|люблю|девушк|парн|отношен|встретил|свидани|поцелу|встреча|расстался|разошлись|флирт|переписк)\b",
            "reply": "💘 Это звучит очень трогательно. Любовные чувства — это всегда волнительно. Хочешь рассказать подробнее, что происходит?"
        },
        "lonely": {
            "patterns": r"\b(один|одна|одинок|некому|никто не|чувствую себя один)\b",
            "reply": "🫂 Иногда это чувство может накрывать... Но знай: ты не один и не одна. Я рядом. 💜"
        },
        "work": {
            "patterns": r"\b(работа|устал|босс|давлени|коллег|увольн|смена|заработ|не выношу|задолбал)\b",
            "reply": "🧑‍💼 Работа может быть выматывающей. Ты не обязан(а) всё тянуть в одиночку. Я здесь, если хочешь выговориться."
        },
        "sport": {
            "patterns": r"\b(зал|спорт|бег|жим|гантел|тренир|добился|успех|100кг|тренировка|похуд)\b",
            "reply": "🏆 Молодец! Это важный шаг на пути к себе. Как ты себя чувствуешь после этого достижения?"
        },
        "family": {
            "patterns": r"\b(мама|папа|семь|родител|сестра|брат|дед|бабушк)\b",
            "reply": "👨‍👩‍👧‍👦 Семья может давать и тепло, и сложности. Я готов(а) выслушать — расскажи, если хочется."
        },
        "motivation": {
            "patterns": r"\b(мотивац|цель|развитие|дух|успех|медитац|саморазвити|осознанн|рост|путь)\b",
            "reply": "🌱 Это здорово, что ты стремишься к развитию. Давай обсудим, как я могу помочь тебе на этом пути."
        }
    },

    "en": {
        "love": {
            "patterns": r"\b(love|crush|girlfriend|boyfriend|relationship|date|kiss|breakup|flirt|chatting)\b",
            "reply": "💘 That sounds really touching. Love can be so exciting. Want to share more?"
        },
        "lonely": {
            "patterns": r"\b(lonely|alone|no one|nobody|feel alone)\b",
            "reply": "🫂 That feeling can be overwhelming… But remember, you’re not alone. I’m here. 💜"
        },
        "work": {
            "patterns": r"\b(work|tired|boss|pressure|colleague|job|salary|overloaded)\b",
            "reply": "🧑‍💼 Work can be exhausting. You don’t have to carry it all alone. I’m here if you want to talk."
        },
        "sport": {
            "patterns": r"\b(gym|sport|running|pushup|dumbbell|training|achieved|success|workout)\b",
            "reply": "🏆 Awesome! That’s a great step forward. How do you feel after this achievement?"
        },
        "family": {
            "patterns": r"\b(mom|dad|family|parent|sister|brother|grandma|grandpa)\b",
            "reply": "👨‍👩‍👧‍👦 Family can bring both warmth and challenges. I’m here if you want to share."
        },
        "motivation": {
            "patterns": r"\b(motivation|goal|growth|mindfulness|success|meditation|path)\b",
            "reply": "🌱 It’s wonderful that you’re striving to grow. Let’s talk about how I can support you."
        }
    },

    "uk": {
        "love": {
            "patterns": r"\b(кохаю|закохався|закохана|дівчин|хлопц|стосунк|побаченн|поціл)\b",
            "reply": "💘 Це звучить дуже зворушливо. Кохання — завжди хвилює. Хочеш розповісти більше?"
        },
        "lonely": {
            "patterns": r"\b(самотн|нікого|ніхто|почуваюсь сам)\b",
            "reply": "🫂 Іноді це відчуття накриває… Але ти не сам(а). Я поруч. 💜"
        },
        "work": {
            "patterns": r"\b(робот|втомив|начальник|тиск|колег|звільненн|зарплат)\b",
            "reply": "🧑‍💼 Робота буває виснажливою. Ти не зобов’язаний(а) тягнути все сам(а)."
        },
        "sport": {
            "patterns": r"\b(спорт|зал|біг|гантел|тренуванн|успіх)\b",
            "reply": "🏆 Молодець! Це великий крок уперед. Як ти почуваєшся?"
        },
        "family": {
            "patterns": r"\b(мама|тато|сім'|брат|сестра|бабус|дідус)\b",
            "reply": "👨‍👩‍👧‍👦 Родина може дати і тепло, і складнощі. Розкажи, якщо хочеш."
        },
        "motivation": {
            "patterns": r"\b(мотивац|ціль|розвит|успіх|медитац|зростанн)\b",
            "reply": "🌱 Це чудово, що ти прагнеш до розвитку. Я поруч!"
        }
    },

    "be": {
        "love": {
            "patterns": r"\b(кахан|каханне|дзяўчын|хлопец|сустрэч|пацал)\b",
            "reply": "💘 Гэта вельмі кранальна. Каханне заўсёды хвалюе. Хочаш расказаць больш?"
        },
        "lonely": {
            "patterns": r"\b(адзін|адна|самотн|ніхто|няма каму)\b",
            "reply": "🫂 Часам гэта адчуванне накрывае… Але ты не адзін(ая). Я побач. 💜"
        },
        "work": {
            "patterns": r"\b(праца|стаміў|начальнік|ціск|калег|зарплат)\b",
            "reply": "🧑‍💼 Праца можа быць цяжкай. Ты не павінен(на) цягнуць усё сам(а)."
        },
        "sport": {
            "patterns": r"\b(спорт|зала|бег|гантэл|трэніроўк|поспех)\b",
            "reply": "🏆 Маладзец! Гэта важны крок. Як ты сябе адчуваеш?"
        },
        "family": {
            "patterns": r"\b(маці|бацька|сям'я|сястра|брат|дзед|бабул)\b",
            "reply": "👨‍👩‍👧‍👦 Сям'я можа даваць і цяпло, і складанасці. Я побач."
        },
        "motivation": {
            "patterns": r"\b(мэта|мотивац|рост|успех|развиццё)\b",
            "reply": "🌱 Гэта цудоўна, што ты імкнешся да росту. Я побач!"
        }
    },

    "kk": {
        "love": {
            "patterns": r"\b(сүйемін|ғашықпын|қыз|жігіт|қарым-қат|кездесу|сүйіс)\b",
            "reply": "💘 Бұл өте әсерлі естіледі. Махаббат әрқашан толқу әкеледі. Толығырақ айтқың келе ме?"
        },
        "lonely": {
            "patterns": r"\b(жалғыз|ешкім|жалғыздық)\b",
            "reply": "🫂 Кейде бұл сезім қысады… Бірақ сен жалғыз емессің. Мен осындамын. 💜"
        },
        "work": {
            "patterns": r"\b(жұмыс|шаршадым|бастық|қысым|әріптес|айлық)\b",
            "reply": "🧑‍💼 Жұмыс шаршатуы мүмкін. Барлығын жалғыз көтерудің қажеті жоқ."
        },
        "sport": {
            "patterns": r"\b(спорт|зал|жүгіру|жаттығу|гантель|жетістік)\b",
            "reply": "🏆 Жарайсың! Бұл үлкен қадам. Өзіңді қалай сезініп тұрсың?"
        },
        "family": {
            "patterns": r"\b(ана|әке|отбас|аға|әпке|қарындас|әже|ата)\b",
            "reply": "👨‍👩‍👧‍👦 Отбасы жылулық та, қиындық та бере алады. Қаласаң, бөліс."
        },
        "motivation": {
            "patterns": r"\b(мақсат|мотивац|даму|жетістік|өсу)\b",
            "reply": "🌱 Тамаша, сен дамуға ұмтылып жатырсың. Мен осындамын!"
        }
    },

    "kg": {
        "love": {
            "patterns": r"\b(сүйөм|ашыкмын|кыз|жигит|мамиле|жолугушу|сүйлөшүү)\b",
            "reply": "💘 Бул абдан таасирлүү угулат. Сүйүү ар дайым толкундантат. Толук айтып бересиңби?"
        },
        "lonely": {
            "patterns": r"\b(жалгыз|эч ким)\b",
            "reply": "🫂 Кээде бул сезим каптап кетет… Бирок сен жалгыз эмессиң. Мен жанымдамын. 💜"
        },
        "work": {
            "patterns": r"\b(иш|чарчап|начальник|басым|кесиптеш|айлык)\b",
            "reply": "🧑‍💼 Иш чарчатуучу болушу мүмкүн. Баарын жалгыз көтөрбө."
        },
        "sport": {
            "patterns": r"\b(спорт|зал|чуркоо|жаттыгуу|гантель|ийгилик)\b",
            "reply": "🏆 Молодец! Бул чоң кадам. Кантип сезип жатасың?"
        },
        "family": {
            "patterns": r"\b(апа|ата|үй-бүл|ага|карындаш|эжеси|ата-эне)\b",
            "reply": "👨‍👩‍👧‍👦 Үй-бүлө жылуулук да, кыйынчылык да берет. Айтып бергиң келеби?"
        },
        "motivation": {
            "patterns": r"\b(максат|мотивац|өсүү|ийгилик)\b",
            "reply": "🌱 Сонун! Сен өсүүгө аракет кылып жатасың."
        }
    },

    "hy": {
        "love": {
            "patterns": r"\b(սիրում եմ|սիրահարված|սիրած|սիրելի|հարաբերություն|հանդիպում|համբույր)\b",
            "reply": "💘 Սա հնչում է շատ հուզիչ։ Սերը միշտ էլ հուզիչ է։ Կուզե՞ս ավելին պատմել։"
        },
        "lonely": {
            "patterns": r"\b(միայնակ|ոչ ոք)\b",
            "reply": "🫂 Երբեմն այդ զգացումը կարող է ծանր լինել… Բայց դու միայնակ չես։ Ես կողքիդ եմ։ 💜"
        },
        "work": {
            "patterns": r"\b(աշխատանք|հոգնած|գլուխ|վճար)\b",
            "reply": "🧑‍💼 Աշխատանքը կարող է հյուծող լինել։ Չպետք է ամեն ինչ ինքդ տանել։"
        },
        "sport": {
            "patterns": r"\b(սպորտ|մարզասրահ|վազք|վարժություն|հաջողություն)\b",
            "reply": "🏆 Դու հրաշալի ես! Սա մեծ քայլ է։ Ինչպե՞ս ես քեզ զգում։"
        },
        "family": {
            "patterns": r"\b(մայր|հայր|ընտանիք|քույր|եղբայր|տատիկ|պապիկ)\b",
            "reply": "👨‍👩‍👧‍👦 Ընտանիքը կարող է տալ ինչպես ջերմություն, այնպես էլ դժվարություններ։"
        },
        "motivation": {
            "patterns": r"\b(նպատակ|մոտիվացիա|զարգացում|հաջողություն)\b",
            "reply": "🌱 Դու ձգտում ես առաջ գնալ։ Ես կողքիդ եմ!"
        }
    },

    "ce": {
        "love": {
            "patterns": r"\b(хьо кхета|хьо йац|хьо мац|хьо хьаж|хьо йол|хьо йаьлла)\b",
            "reply": "💘 Хьо йац кхеташ до. Хьо ца даьлча. Хьо даьлча еза!"
        },
        "lonely": {
            "patterns": r"\b(хьо ца йац|хьо ца хьо|хьо до хьо йац)\b",
            "reply": "🫂 Хьо ца йац… Са цуьнан. Са даьлча. 💜"
        },
        "work": {
            "patterns": r"\b(работ|хьо дIан|хьо чар)\b",
            "reply": "🧑‍💼 Хьо дIан гойла. Хьо ца йац хила."
        },
        "sport": {
            "patterns": r"\b(спорт|хьо зал|хьо трен)\b",
            "reply": "🏆 Дика йац! Хьо тIе хила?"
        },
        "family": {
            "patterns": r"\b(мама|папа|къант|сестра|брат|дада)\b",
            "reply": "👨‍👩‍👧‍👦 Къант кхеташ… Са йац!"
        },
        "motivation": {
            "patterns": r"\b(мотивац|хьо а|хьо дика)\b",
            "reply": "🌱 Хьо дика. Са йац!"
        }
    },

    "md": {
        "love": {
            "patterns": r"\b(iubesc|dragoste|prietenă|prieten|relație|întâlnire|sărut)\b",
            "reply": "💘 Sună foarte emoționant. Dragostea este mereu specială. Vrei să îmi povestești mai mult?"
        },
        "lonely": {
            "patterns": r"\b(singur|singură|nimeni|mă simt singur)\b",
            "reply": "🫂 Uneori sentimentul acesta e greu… Dar nu ești singur(ă). Sunt aici. 💜"
        },
        "work": {
            "patterns": r"\b(muncă|obosit|șef|presiune|coleg|salariu)\b",
            "reply": "🧑‍💼 Munca poate fi obositoare. Nu trebuie să duci totul singur(ă)."
        },
        "sport": {
            "patterns": r"\b(sport|sală|alergare|antrenament|gantere|succes)\b",
            "reply": "🏆 Bravo! Este un pas mare înainte. Cum te simți?"
        },
        "family": {
            "patterns": r"\b(mamă|tată|familie|frate|soră|bunica|bunicul)\b",
            "reply": "👨‍👩‍👧‍👦 Familia poate aduce atât căldură, cât și dificultăți. Povestește-mi dacă vrei."
        },
        "motivation": {
            "patterns": r"\b(motivație|scop|dezvoltare|succes)\b",
            "reply": "🌱 E minunat că vrei să te dezvolți. Sunt aici!"
        }
    },

    "ka": {
        "love": {
            "patterns": r"\b(მიყვარს|შეყვარებული|ბიჭი|გოგო|შეხვედრა|კოცნა|ურთიერთობა)\b",
            "reply": "💘 ეს ძალიან შემხებლიანად ჟღერს. სიყვარული ყოველთვის განსაკუთრებულია. მეტს მომიყვები?"
        },
        "lonely": {
            "patterns": r"\b(მარტო|მარტოობა|არავინა|ვგრძნობ თავს მარტო)\b",
            "reply": "🫂 ზოგჯერ ეს განცდა მძიმეა… მაგრამ შენ მარტო არ ხარ. მე აქ ვარ. 💜"
        },
        "work": {
            "patterns": r"\b(სამუშაო|დაღლილი|ხელმძღვანელი|ზეწოლა|თანამშრომელი|ხელფასი)\b",
            "reply": "🧑‍💼 სამუშაო შეიძლება დამღლელი იყოს. მარტო არ გიწევს ყველაფრის კეთება."
        },
        "sport": {
            "patterns": r"\b(სპორტი|დარბაზი|ვარჯიში|გაწვრთნა|წარმატება)\b",
            "reply": "🏆 შენ შესანიშნავი ხარ! ეს დიდი ნაბიჯია. როგორ გრძნობ თავს?"
        },
        "family": {
            "patterns": r"\b(დედა|მამა|ოჯახი|და|ძმა|ბებია|ბაბუა)\b",
            "reply": "👨‍👩‍👧‍👦 ოჯახს შეუძლია მოგცეს სითბოც და სირთულეც. მომიყევი, თუ გინდა."
        },
        "motivation": {
            "patterns": r"\b(მოტივაცია|მიზანი|განვითარება|წარმატება)\b",
            "reply": "🌱 მშვენიერია, რომ ცდილობ განვითარებას. მე აქ ვარ!"
        }
    },
}


def detect_topic_and_react(user_input: str, lang: str = "ru") -> str:
    text = user_input.lower()
    lang_patterns = topic_patterns_by_lang.get(lang, topic_patterns_by_lang["ru"])

    for topic_data in lang_patterns.values():
        if re.search(topic_data["patterns"], text):
            return topic_data["reply"]

    return ""
    
import re

# 🔑 Паттерны для определения темы на всех языках
topic_patterns_full = {
    "ru": {
        "отношения": r"\b(девушк|люблю|отношен|парн|флирт|расст|поцелу|влюб)\b",
        "работа": r"\b(работа|босс|смена|коллег|заработ|устал|стресс)\b",
        "спорт": r"\b(зал|спорт|тренир|бег|гантел|похуд)\b",
        "одиночество": r"\b(одинок|один|некому|никто не)\b",
        "саморазвитие": r"\b(цель|развитие|мотивац|успех|саморазв)\b",
    },
    "en": {
        "love": r"\b(love|relationship|girlfriend|boyfriend|date|kiss|crush|breakup|flirt)\b",
        "work": r"\b(work|boss|shift|colleague|salary|tired|stress)\b",
        "sport": r"\b(gym|sport|training|run|dumbbell|fitness|exercise)\b",
        "lonely": r"\b(lonely|alone|nobody|no one)\b",
        "growth": r"\b(goal|growth|motivation|success|self|improve)\b",
    },
    "uk": {
        "стосунки": r"\b(дівчин|хлопц|люблю|стосунк|флірт|розлуч|поцілун)\b",
        "робота": r"\b(робот|начальник|зміна|колег|зарплат|втомив|стрес)\b",
        "спорт": r"\b(спорт|зал|тренуванн|біг|гантел)\b",
        "самотність": r"\b(самотн|ніхто|нікого|один)\b",
        "саморозвиток": r"\b(ціль|розвит|мотивац|успіх|саморозв)\b",
    },
    "be": {
        "адносіны": r"\b(дзяўчын|хлопец|кахан|сустрэч|пацал)\b",
        "праца": r"\b(праца|начальнік|калег|зарплат|стаміў|стрэс)\b",
        "спорт": r"\b(спорт|зала|трэніроўк|бег|гантэл)\b",
        "адзінота": r"\b(адзін|адна|самотн|ніхто)\b",
        "развіццё": r"\b(мэта|рост|мотивац|поспех)\b",
    },
    "kk": {
        "махаббат": r"\b(сүйемін|ғашық|қыз|жігіт|қарым-қат|поцелу)\b",
        "жұмыс": r"\b(жұмыс|бастық|ауысым|әріптес|айлық|шаршадым|стресс)\b",
        "спорт": r"\b(спорт|зал|жаттығу|жүгіру|гантель)\b",
        "жалғыздық": r"\b(жалғыз|ешкім|жалғыздық)\b",
        "даму": r"\b(мақсат|даму|мотивац|жетістік)\b",
    },
    "kg": {
        "сүйүү": r"\b(сүйөм|ашык|кыз|жигит|мамиле|сүйлөшүү|поцелуй)\b",
        "иш": r"\b(иш|начальник|кезек|кесиптеш|айлык|чарчап|стресс)\b",
        "спорт": r"\b(спорт|зал|жаттыгуу|чуркоо|гантель)\b",
        "жалгыздык": r"\b(жалгыз|эч ким)\b",
        "өркүндөө": r"\b(максат|мотивац|өсүү|ийгилик)\b",
    },
    "hy": {
        "սեր": r"\b(սիրում|սիրահարված|հարաբերություն|հանդիպում|համբույր)\b",
        "աշխատանք": r"\b(աշխատանք|գլուխ|հոգնած|ղեկավար|աշխատակց)\b",
        "սպորտ": r"\b(սպորտ|մարզասրահ|վարժություն|վազք)\b",
        "միայնություն": r"\b(միայնակ|ոչ ոք)\b",
        "զարգացում": r"\b(նպատակ|մոտիվացիա|զարգացում|հաջողություն)\b",
    },
    "ce": {
        "хьо": r"\b(хьо кхета|хьо йац|хьо мац|хьо хьаж|хьо йол|хьо йаьлла)\b",
        "работа": r"\b(работ|хьо дIан|хьо чар)\b",
        "спорт": r"\b(спорт|хьо зал|хьо трен)\b",
        "одиночество": r"\b(хьо ца йац|хьо ца хьо)\b",
        "развитие": r"\b(мотивац|хьо а|хьо дика)\b",
    },
    "md": {
        "dragoste": r"\b(iubesc|dragoste|prietenă|prieten|relație|sărut)\b",
        "muncă": r"\b(muncă|obosit|șef|coleg|salariu)\b",
        "sport": r"\b(sport|sală|antrenament|alergare)\b",
        "singurătate": r"\b(singur|singură|nimeni)\b",
        "dezvoltare": r"\b(motivație|scop|dezvoltare|succes)\b",
    },
    "ka": {
        "სიყვარული": r"\b(მიყვარს|შეყვარებული|ბიჭი|გოგო|შეხვედრა|კოცნა)\b",
        "სამუშაო": r"\b(სამუშაო|ხელმძღვანელი|თანამშრომელი|დაღლილი)\b",
        "სპორტი": r"\b(სპორტი|დარბაზი|ვარჯიში)\b",
        "მარტოობა": r"\b(მარტო|არავინ)\b",
        "განვითარება": r"\b(მოტივაცია|მიზანი|განვითარება|წარმატება)\b",
    },
}

# 🔥 Функция определения темы
def detect_topic(text: str, lang: str = "ru") -> str:
    text = text.lower()
    lang_patterns = topic_patterns_full.get(lang, topic_patterns_full["ru"])
    for topic, pattern in lang_patterns.items():
        if re.search(pattern, text):
            return topic
    return ""

# 🔑 Ответы для get_topic_reference на всех языках
topic_reference_by_lang = {
    "ru": {
        "отношения": "💘 Ты упоминал(а) недавно про отношения... Всё в порядке?",
        "работа": "💼 Как дела на работе? Я помню, тебе было тяжело.",
        "спорт": "🏋️‍♂️ Как у тебя со спортом, продолжил(а)?",
        "одиночество": "🤗 Помни, что ты не один(одна), даже если так казалось.",
        "саморазвитие": "🌱 Продолжаешь развиваться? Это вдохновляет!"
    },
    "en": {
        "love": "💘 You mentioned relationships earlier… Is everything okay?",
        "work": "💼 How’s work going? I remember it was tough for you.",
        "sport": "🏋️‍♂️ How’s your training going?",
        "lonely": "🤗 Remember, you’re not alone, even if it feels that way.",
        "growth": "🌱 Still working on your personal growth? That’s inspiring!"
    },
    "uk": {
        "стосунки": "💘 Ти згадував(ла) про стосунки… Все добре?",
        "робота": "💼 Як справи на роботі? Пам’ятаю, тобі було важко.",
        "спорт": "🏋️‍♂️ Як твої тренування, продовжуєш?",
        "самотність": "🤗 Пам’ятай, ти не сам(а), навіть якщо так здається.",
        "саморозвиток": "🌱 Продовжуєш розвиватись? Це надихає!"
    },
    "be": {
        "адносіны": "💘 Ты нядаўна казаў(ла) пра адносіны… Усё добра?",
        "праца": "💼 Як справы на працы? Памятаю, табе было цяжка.",
        "спорт": "🏋️‍♂️ Як твае трэніроўкі?",
        "адзінота": "🤗 Памятай, ты не адзін(ая).",
        "развіццё": "🌱 Працягваеш развівацца? Гэта натхняе!"
    },
    "kk": {
        "махаббат": "💘 Сен жақында қарым-қатынас туралы айттың… Бәрі жақсы ма?",
        "жұмыс": "💼 Жұмысың қалай? Қиын болғанын білемін.",
        "спорт": "🏋️‍♂️ Жаттығуларың қалай?",
        "жалғыздық": "🤗 Есіңде болсын, сен жалғыз емессің.",
        "даму": "🌱 Дамуды жалғастырып жатырсың ба? Бұл шабыттандырады!"
    },
    "kg": {
        "сүйүү": "💘 Сен жакында мамиле жөнүндө айттың… Баары жакшыбы?",
        "иш": "💼 Ишиң кандай? Кыйын болгонун билем.",
        "спорт": "🏋️‍♂️ Жаттууларың кандай?",
        "жалгыздык": "🤗 Эсиңде болсун, сен жалгыз эмессиң.",
        "өркүндөө": "🌱 Өсүүнү улантып жатасыңбы? Бул шыктандырат!"
    },
    "hy": {
        "սեր": "💘 Դու վերջերս սիրո մասին ես խոսել… Ամեն ինչ լավ է?",
        "աշխատանք": "💼 Աշխատանքդ ինչպես է? Հիշում եմ, որ դժվար էր քեզ համար.",
        "սպորտ": "🏋️‍♂️ Մարզումդ ինչպես է?",
        "միայնություն": "🤗 Հիշիր, որ միայնակ չես։",
        "զարգացում": "🌱 Շարունակում ես զարգանալ? Սա ոգեշնչող է!"
    },
    "ce": {
        "хьо": "💘 Хьо любов, хьо кхета… хьо йолла?",
        "работа": "💼 Хьо дIан? Са цуьнан хила.",
        "спорт": "🏋️‍♂️ Хьо спорт йац?",
        "одиночество": "🤗 Хьо ца йац.",
        "развитие": "🌱 Хьо а да хьо дика."
    },
    "md": {
        "dragoste": "💘 Ai menționat dragostea… Totul bine?",
        "muncă": "💼 Cum merge munca? Țin minte că era greu.",
        "sport": "🏋️‍♂️ Cum merge antrenamentul tău?",
        "singurătate": "🤗 Amintește-ți, nu ești singur(ă).",
        "dezvoltare": "🌱 Îți continui dezvoltarea? E minunat!"
    },
    "ka": {
        "სიყვარული": "💘 შენ ახლახან სიყვარულზე თქვი… ყველაფერი რიგზეა?",
        "სამუშაო": "💼 სამსახური როგორ მიდის? მახსოვს, რომ გიჭირდა.",
        "სპორტი": "🏋️‍♂️ ვარჯიშები როგორ მიდის?",
        "მარტოობა": "🤗 გახსოვდეს, მარტო არ ხარ.",
        "განვითარება": "🌱 განაგრძობ განვითარებას? ეს შთამბეჭდავია!"
    },
}

# 🔥 Получение реакции по сохранённой теме
def get_topic_reference(context, lang: str = "ru") -> str:
    topic = context.user_data.get("last_topic")
    references = topic_reference_by_lang.get(lang, topic_reference_by_lang["ru"])
    if topic in references:
        return references[topic]
    return ""

def save_user_context(context, topic: str = None, emotion: str = None, lang: str = None):
    if topic:
        topics = context.user_data.get("topics", [])
        if topic not in topics:
            topics.append(topic)
            context.user_data["topics"] = topics

    if emotion:
        context.user_data["last_emotion"] = emotion

    if lang:
        context.user_data["lang"] = lang

def get_topic_reference(context, lang: str = "ru") -> str:
    topics = context.user_data.get("topics", [])
    if not topics:
        return ""

    # 🗂️ Словарь отсылок по темам на всех языках
    references_by_lang = {
        "ru": {
            "отношения": "Ты ведь раньше делился(ась) про чувства… Хочешь поговорить об этом подробнее? 💜",
            "одиночество": "Помню, ты чувствовал(а) себя одиноко… Я всё ещё здесь 🤗",
            "работа": "Ты рассказывал(а) про давление на работе. Как у тебя с этим сейчас?",
            "спорт": "Ты ведь начинал(а) тренироваться — продолжаешь? 🏋️",
            "семья": "Ты упоминал(а) про семью… Всё ли хорошо?",
            "мотивация": "Ты говорил(а), что хочешь развиваться. Что уже получилось? ✨"
        },
        "uk": {
            "відносини": "Ти ж ділився(-лася) почуттями… Хочеш розповісти більше? 💜",
            "самотність": "Пам’ятаю, ти почувався(-лася) самотньо… Я тут 🤗",
            "робота": "Ти казав(-ла), що робота тисне. Як зараз?",
            "спорт": "Ти ж починав(-ла) тренуватися — продовжуєш? 🏋️",
            "сім’я": "Ти згадував(-ла) про сім’ю… Усе добре?",
            "мотивація": "Ти казав(-ла), що хочеш розвиватися. Що вже вдалося? ✨"
        },
        "be": {
            "адносіны": "Ты ж дзяліўся(-лася) пачуццямі… Хочаш распавесці больш? 💜",
            "адзінота": "Памятаю, табе было адзінока… Я тут 🤗",
            "праца": "Ты казаў(-ла), што праца цісне. Як цяпер?",
            "спорт": "Ты ж пачынаў(-ла) трэніравацца — працягваеш? 🏋️",
            "сям’я": "Ты згадваў(-ла) пра сям’ю… Усё добра?",
            "матывацыя": "Ты казаў(-ла), што хочаш развівацца. Што ўжо атрымалася? ✨"
        },
        "kk": {
            "қатынас": "Сен бұрын сезімдеріңмен бөліскен едің… Толығырақ айтқың келе ме? 💜",
            "жалғыздық": "Есімде, өзіңді жалғыз сезінгенсің… Мен осындамын 🤗",
            "жұмыс": "Жұмыста қысым сезінгеніңді айттың. Қазір қалай?",
            "спорт": "Сен жаттығуды бастаған едің — жалғастырып жүрсің бе? 🏋️",
            "отбасы": "Сен отбасың туралы айтқан едің… Бәрі жақсы ма?",
            "мотивация": "Сен дамығың келетініңді айттың. Не өзгерді? ✨"
        },
        "kg": {
            "байланыш": "Сен мурун сезимдериң менен бөлүшкөнсүң… Толугураак айтып бересиңби? 💜",
            "жалгыздык": "Эсимде, өзүңдү жалгыз сезип жүргөнсүң… Мен бул жерде 🤗",
            "иш": "Иштеги басым тууралуу айткансың. Азыр кандай?",
            "спорт": "Сен машыгуу баштагансың — улантып жатасыңбы? 🏋️",
            "үй-бүлө": "Үй-бүлөң жөнүндө айткансың… Баары жакшыбы?",
            "мотивация": "Сен өнүгүүнү каалаганыңды айткансың. Эмне өзгөрдү? ✨"
        },
        "hy": {
            "հարաբերություններ": "Դու պատմել ես քո զգացումների մասին… Ուզու՞մ ես ավելին պատմել 💜",
            "միայնություն": "Հիշում եմ, դու քեզ միայնակ էիր զգում… Ես այստեղ եմ 🤗",
            "աշխատանք": "Դու պատմել ես աշխատանքի ճնշման մասին. Հիմա ինչպե՞ս ես:",
            "սպորտ": "Դու սկսեց մարզվել — շարունակի՞ս? 🏋️",
            "ընտանիք": "Դու հիշեցիր ընտանիքդ… Բոլորն արդյո՞ք լավ են:",
            "մոտիվացիա": "Դու պատմեցիր, որ ուզում ես զարգանալ. Ի՞նչ հաջողվեց արդեն ✨"
        },
        "ce": {
            "мацахь": "Хьо мах даа хьо йа къобал. Цхьа кхета хийцам? 💜",
            "одиночество": "Хьо цхьаьнга хьайна дезар хьалха… Са хьалха ю 🤗",
            "работа": "Хьо цхьаьнга хьайна хьалха дагахь. Хьо кхеташ? ",
            "спорт": "Хьо къобал спорт йа цхьаьнга… Хьан кхеташ? 🏋️",
            "семья": "Хьо цхьаьнга хьайна ца хаам. Хьан хиллахь? ",
            "мотивация": "Хьо цхьаьнга хьайна а дагьай. Хьан кхеташ? ✨"
        },
        "md": {
            "relații": "Ți-ai împărtășit sentimentele… Vrei să povestești mai mult? 💜",
            "singurătate": "Îmi amintesc că te simțeai singur(ă)… Eu sunt aici 🤗",
            "muncă": "Ai spus că munca te apasă. Cum e acum?",
            "sport": "Ai început să te antrenezi — continui? 🏋️",
            "familie": "Ai menționat familia… Totul e bine?",
            "motivație": "Ai spus că vrei să te dezvolți. Ce ai reușit deja? ✨"
        },
        "ka": {
            "ურთიერთობა": "შენ გაზიარე შენი გრძნობები… გინდა მეტი მომიყვე? 💜",
            "მარტოობა": "მახსოვს, თავს მარტო გრძნობდი… აქ ვარ 🤗",
            "სამუშაო": "თქვი, რომ სამსახური გაწუხებს. ახლა როგორ ხარ?",
            "სპორტი": "დაიწყე ვარჯიში — განაგრძე? 🏋️",
            "ოჯახი": "გახსენდი შენი ოჯახი… ყველაფერი好吗?",
            "მოტივაცია": "თქვი, რომ გინდა განვითარდე. უკვე რას მიაღწიე? ✨"
        },
        "en": {
            "love": "You’ve shared your feelings before… Want to tell me more? 💜",
            "loneliness": "I remember you felt lonely… I’m here for you 🤗",
            "work": "You said work was overwhelming. How is it now?",
            "sport": "You started training — still going? 🏋️",
            "family": "You mentioned your family… Is everything okay?",
            "motivation": "You said you want to grow. What have you achieved so far? ✨"
        },
    }

    # Получаем нужный словарь по языку
    refs = references_by_lang.get(lang, references_by_lang["ru"])

    matched_refs = []
    for topic in topics:
        for key, phrase in refs.items():
            if key.lower() in topic.lower() and phrase not in matched_refs:
                matched_refs.append(phrase)

    if matched_refs:
        return "\n\n".join(matched_refs[:2])
    return ""


STATS_TEXTS = {
    "ru": (
        "📊 Статистика Mindra:\n\n"
        "👥 Всего пользователей: {total}\n"
        "💎 Подписчиков: {premium}\n"
    ),
    "uk": (
        "📊 Статистика Mindra:\n\n"
        "👥 Всього користувачів: {total}\n"
        "💎 Підписників: {premium}\n"
    ),
    "be": (
        "📊 Статыстыка Mindra:\n\n"
        "👥 Усяго карыстальнікаў: {total}\n"
        "💎 Падпісчыкаў: {premium}\n"
    ),
    "kk": (
        "📊 Mindra статистикасы:\n\n"
        "👥 Барлық қолданушылар: {total}\n"
        "💎 Жазылушылар: {premium}\n"
    ),
    "kg": (
        "📊 Mindra статистикасы:\n\n"
        "👥 Жалпы колдонуучулар: {total}\n"
        "💎 Жазылуучулар: {premium}\n"
    ),
    "hy": (
        "📊 Mindra-ի վիճակագրությունը․\n\n"
        "👥 Բոլոր օգտատերերը՝ {total}\n"
        "💎 Բաժանորդներ՝ {premium}\n"
    ),
    "ce": (
        "📊 Mindra статистика:\n\n"
        "👥 Жалпы юзераш: {total}\n"
        "💎 Подписчик: {premium}\n"
    ),
    "md": (
        "📊 Statistica Mindra:\n\n"
        "👥 Utilizatori totali: {total}\n"
        "💎 Abonați: {premium}\n"
    ),
    "ka": (
        "📊 Mindra სტატისტიკა:\n\n"
        "👥 მომხმარებლები სულ: {total}\n"
        "💎 გამომწერები: {premium}\n"
    ),
    "en": (
        "📊 Mindra stats:\n\n"
        "👥 Total users: {total}\n"
        "💎 Subscribers: {premium}\n"
    ),
}

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # Ограничение по ID можешь оставить или расширить для премиума
    if user_id != YOUR_ID:
        return

    lang = user_languages.get(user_id, "ru")
    stats = get_stats()
    text_template = STATS_TEXTS.get(lang, STATS_TEXTS["ru"])
    text = text_template.format(total=stats['total_users'], premium=stats['premium_users'])
    await update.message.reply_text(text)

MYSTATS_TEXTS = {
    "ru": {
        "title": "📌 *Твоя статистика*\n\n🌟 Твой титул: *{title}*\n🏅 Очков: *{points}*\n\nПродолжай выполнять цели и задания, чтобы расти! 💜",
        "premium_info": (
            "\n\n🔒 В Mindra+ ты получишь:\n"
            "💎 Расширенную статистику по целям и привычкам\n"
            "💎 Больше лимитов и эксклюзивные задания\n"
            "💎 Уникальные челленджи и напоминания ✨"
        ),
        "premium_button": "💎 Узнать о Mindra+",
        "extra": (
            "\n✅ Целей выполнено: {completed_goals}"
            "\n🌱 Привычек добавлено: {habits_tracked}"
            "\n🔔 Напоминаний: {reminders}"
            "\n📅 Дней активности: {days_active}"
        ),
    },
    "uk": {
        "title": "📌 *Твоя статистика*\n\n🌟 Твій титул: *{title}*\n🏅 Балів: *{points}*\n\nПродовжуй виконувати цілі й завдання, щоб зростати! 💜",
        "premium_info": (
            "\n\n🔒 У Mindra+ ти отримаєш:\n"
            "💎 Розширену статистику по цілях та звичках\n"
            "💎 Більше лімітів і ексклюзивні завдання\n"
            "💎 Унікальні челенджі й нагадування ✨"
        ),
        "premium_button": "💎 Дізнатись про Mindra+",
        "extra": (
            "\n✅ Виконано цілей: {completed_goals}"
            "\n🌱 Додано звичок: {habits_tracked}"
            "\n🔔 Нагадувань: {reminders}"
            "\n📅 Днів активності: {days_active}"
        ),
    },
    "be": {
        "title": "📌 *Твая статыстыка*\n\n🌟 Твой тытул: *{title}*\n🏅 Ачкоў: *{points}*\n\nПрацягвай ставіць мэты і выконваць заданні, каб расці! 💜",
        "premium_info": (
            "\n\n🔒 У Mindra+ ты атрымаеш:\n"
            "💎 Пашыраную статыстыку па мэтах і звычках\n"
            "💎 Больш лімітаў і эксклюзіўныя заданні\n"
            "💎 Унікальныя чэленджы і напамінкі ✨"
        ),
        "premium_button": "💎 Даведайся пра Mindra+",
        "extra": (
            "\n✅ Выканана мэтаў: {completed_goals}"
            "\n🌱 Дададзена звычак: {habits_tracked}"
            "\n🔔 Напамінкаў: {reminders}"
            "\n📅 Дзён актыўнасці: {days_active}"
        ),
    },
    "kk": {
        "title": "📌 *Сенің статистикаң*\n\n🌟 Титулың: *{title}*\n🏅 Ұпай: *{points}*\n\nМақсаттар мен тапсырмаларды орындауды жалғастыр! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+ арқылы сен аласың:\n"
            "💎 Мақсаттар мен әдеттер бойынша толық статистика\n"
            "💎 Көп лимит және ерекше тапсырмалар\n"
            "💎 Бірегей челлендждер мен ескертулер ✨"
        ),
        "premium_button": "💎 Mindra+ туралы білу",
        "extra": (
            "\n✅ Орындалған мақсаттар: {completed_goals}"
            "\n🌱 Қосылған әдеттер: {habits_tracked}"
            "\n🔔 Ескертулер: {reminders}"
            "\n📅 Белсенді күндер: {days_active}"
        ),
    },
    "kg": {
        "title": "📌 *Сенин статистикаң*\n\n🌟 Сенин наамың: *{title}*\n🏅 Балл: *{points}*\n\nМаксаттар менен тапшырмаларды аткарууну улант! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+ менен:\n"
            "💎 Максаттар жана көнүмүштөр боюнча толук статистика\n"
            "💎 Көп лимит жана өзгөчө тапшырмалар\n"
            "💎 Уникалдуу челендждер жана эскертүүлөр ✨"
        ),
        "premium_button": "💎 Mindra+ жөнүндө билүү",
        "extra": (
            "\n✅ Аткарылган максаттар: {completed_goals}"
            "\n🌱 Кошулган көнүмүштөр: {habits_tracked}"
            "\n🔔 Эскертүүлөр: {reminders}"
            "\n📅 Активдүү күндөр: {days_active}"
        ),
    },
    "hy": {
        "title": "📌 *Քո վիճակագրությունը*\n\n🌟 Քո տիտղոսը՝ *{title}*\n🏅 Մակարդակ՝ *{points}*\n\nՇարունակի՛ր նպատակների ու առաջադրանքների կատարումը, որպեսզի աճես։ 💜",
        "premium_info": (
            "\n\n🔒 Mindra+-ում կարող ես ստանալ՝\n"
            "💎 Նպատակների ու սովորությունների վիճակագրությունը\n"
            "💎 Ավելի շատ սահմանաչափեր ու յուրահատուկ առաջադրանքներ\n"
            "💎 Ունիակլի մարտահրավերներ ու հիշեցումներ ✨"
        ),
        "premium_button": "💎 Իմանալ Mindra+-ի մասին",
        "extra": (
            "\n✅ Կատարված նպատակներ՝ {completed_goals}"
            "\n🌱 Ավելացված սովորություններ՝ {habits_tracked}"
            "\n🔔 Հիշեցումներ՝ {reminders}"
            "\n📅 Ակտիվ օրեր՝ {days_active}"
        ),
    },
    "ce": {
        "title": "📌 *Хьоь статистика*\n\n🌟 Титул: *{title}*\n🏅 Балл: *{points}*\n\nДаймохь цуьнан кхолларча хетам хенна! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+ хетам долу:\n"
            "💎 Мацахь, привычка статистика\n"
            "💎 Больше лимитов, эксклюзивные задачи\n"
            "💎 Уникальные челленджи и напоминания ✨"
        ),
        "premium_button": "💎 Узнать о Mindra+",
        "extra": (
            "\n✅ Выполнено целей: {completed_goals}"
            "\n🌱 Добавлено привычек: {habits_tracked}"
            "\n🔔 Напоминаний: {reminders}"
            "\n📅 Активных дней: {days_active}"
        ),
    },
    "md": {
        "title": "📌 *Statistica ta*\n\n🌟 Titlul tău: *{title}*\n🏅 Puncte: *{points}*\n\nContinuă să îți îndeplinești obiectivele și sarcinile pentru a crește! 💜",
        "premium_info": (
            "\n\n🔒 În Mindra+ vei obține:\n"
            "💎 Statistici detaliate despre obiective și obiceiuri\n"
            "💎 Mai multe limite și sarcini exclusive\n"
            "💎 Provocări unice și notificări ✨"
        ),
        "premium_button": "💎 Află despre Mindra+",
        "extra": (
            "\n✅ Obiective realizate: {completed_goals}"
            "\n🌱 Obiceiuri adăugate: {habits_tracked}"
            "\n🔔 Notificări: {reminders}"
            "\n📅 Zile active: {days_active}"
        ),
    },
    "ka": {
        "title": "📌 *შენი სტატისტიკა*\n\n🌟 შენი ტიტული: *{title}*\n🏅 ქულები: *{points}*\n\nაგრძელე მიზნების და დავალებების შესრულება, რომ გაიზარდო! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+-ში მიიღებ:\n"
            "💎 დეტალურ სტატისტიკას მიზნებსა და ჩვევებზე\n"
            "💎 მეტი ლიმიტი და ექსკლუზიური დავალებები\n"
            "💎 უნიკალური ჩელენჯები და შეხსენებები ✨"
        ),
        "premium_button": "💎 გაიგე Mindra+-ის შესახებ",
        "extra": (
            "\n✅ შესრულებული მიზნები: {completed_goals}"
            "\n🌱 დამატებული ჩვევები: {habits_tracked}"
            "\n🔔 შეხსენებები: {reminders}"
            "\n📅 აქტიური დღეები: {days_active}"
        ),
    },
    "en": {
        "title": "📌 *Your stats*\n\n🌟 Your title: *{title}*\n🏅 Points: *{points}*\n\nKeep accomplishing your goals and tasks to grow! 💜",
        "premium_info": (
            "\n\n🔒 In Mindra+ you get:\n"
            "💎 Advanced stats for goals and habits\n"
            "💎 Higher limits & exclusive tasks\n"
            "💎 Unique challenges and reminders ✨"
        ),
        "premium_button": "💎 Learn about Mindra+",
        "extra": (
            "\n✅ Goals completed: {completed_goals}"
            "\n🌱 Habits added: {habits_tracked}"
            "\n🔔 Reminders: {reminders}"
            "\n📅 Active days: {days_active}"
        ),
    },
}

async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    texts = MYSTATS_TEXTS.get(lang, MYSTATS_TEXTS["ru"])

    # Данные пользователя
    user_stats = get_user_stats(user_id)
    points = user_stats.get("points", 0)
    title = get_user_title(points)

    # Базовый текст
    text = texts["title"].format(title=title, points=points)

    # Проверяем премиум
    if user_id not in PREMIUM_USERS:
        text += texts["premium_info"]
        keyboard = [[InlineKeyboardButton(texts["premium_button"], url="https://t.me/talktomindra_bot")]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # Для премиум — расширенные данные
        extra = texts["extra"].format(
            completed_goals=user_stats.get("completed_goals", 0),
            habits_tracked=user_stats.get("habits_tracked", 0),
            reminders=user_stats.get("reminders", 0),
            days_active=user_stats.get("days_active", 0),
        )
        await update.message.reply_text(text + extra, parse_mode="Markdown")


HABIT_TEXTS = {
    "ru": {
        "limit": (
            "🌱 В бесплатной версии можно добавить только 2 привычки.\n\n"
            "✨ Подключи Mindra+, чтобы отслеживать неограниченное количество привычек 💜"
        ),
        "how_to": "Чтобы добавить привычку, напиши:\n/habit Делать зарядку",
        "added": "🎯 Привычка добавлена: *{habit}*",
    },
    "uk": {
        "limit": (
            "🌱 У безкоштовній версії можна додати лише 2 звички.\n\n"
            "✨ Підключи Mindra+, щоб відстежувати необмежену кількість звичок 💜"
        ),
        "how_to": "Щоб додати звичку, напиши:\n/habit Робити зарядку",
        "added": "🎯 Звичка додана: *{habit}*",
    },
    "be": {
        "limit": (
            "🌱 У бясплатнай версіі можна дадаць толькі 2 звычкі.\n\n"
            "✨ Падключы Mindra+, каб адсочваць неабмежаваную колькасць звычак 💜"
        ),
        "how_to": "Каб дадаць звычку, напішы:\n/habit Рабіць зарадку",
        "added": "🎯 Звычка дададзена: *{habit}*",
    },
    "kk": {
        "limit": (
            "🌱 Тегін нұсқада тек 2 әдет қосуға болады.\n\n"
            "✨ Mindra+ қосып, әдеттерді шексіз бақыла! 💜"
        ),
        "how_to": "Әдет қосу үшін жаз:\n/habit Таңертең жаттығу жасау",
        "added": "🎯 Әдет қосылды: *{habit}*",
    },
    "kg": {
        "limit": (
            "🌱 Акысыз версияда болгону 2 көнүмүш кошууга болот.\n\n"
            "✨ Mindra+ кошуп, чексиз көнүмүштөрдү көзөмөлдө! 💜"
        ),
        "how_to": "Көнүмүш кошуу үчүн жаз:\n/habit Таң эрте көнүгүү",
        "added": "🎯 Көнүмүш кошулду: *{habit}*",
    },
    "hy": {
        "limit": (
            "🌱 Անվճար տարբերակում կարող ես ավելացնել միայն 2 սովորություն։\n\n"
            "✨ Միացրու Mindra+, որպեսզի հետևես անսահմանափակ սովորությունների 💜"
        ),
        "how_to": "Սովորություն ավելացնելու համար գրիր՝\n/habit Վարժություն անել",
        "added": "🎯 Սովորությունը ավելացվել է՝ *{habit}*",
    },
    "ce": {
        "limit": (
            "🌱 Бесплатна версийна дуьйна 2 привычка цуьнан дац.\n\n"
            "✨ Mindra+ хетам болуш кхетам привычка хетам! 💜"
        ),
        "how_to": "Привычка дац дуьйна, хьоьшу напиши:\n/habit Зарядка",
        "added": "🎯 Привычка дац: *{habit}*",
    },
    "md": {
        "limit": (
            "🌱 În versiunea gratuită poți adăuga doar 2 obiceiuri.\n\n"
            "✨ Activează Mindra+ pentru a urmări oricâte obiceiuri vrei 💜"
        ),
        "how_to": "Pentru a adăuga un obicei, scrie:\n/habit Fă gimnastică",
        "added": "🎯 Obiceiul a fost adăugat: *{habit}*",
    },
    "ka": {
        "limit": (
            "🌱 უფასო ვერსიაში შეგიძლია დაამატო მხოლოდ 2 ჩვევა.\n\n"
            "✨ ჩართე Mindra+, რომ გააკონტროლო ულიმიტო ჩვევები 💜"
        ),
        "how_to": "ჩვევის დასამატებლად დაწერე:\n/habit დილას ვარჯიში",
        "added": "🎯 ჩვევა დამატებულია: *{habit}*",
    },
    "en": {
        "limit": (
            "🌱 In the free version you can add only 2 habits.\n\n"
            "✨ Unlock Mindra+ to track unlimited habits 💜"
        ),
        "how_to": "To add a habit, type:\n/habit Do morning exercise",
        "added": "🎯 Habit added: *{habit}*",
    },
}

async def habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    texts = HABIT_TEXTS.get(lang, HABIT_TEXTS["ru"])
    is_premium = (user_id == str(YOUR_ID)) or (user_id in PREMIUM_USERS)

    # Проверка лимита для бесплатных
    current_habits = get_habits(user_id)
    if not is_premium and len(current_habits) >= 2:
        await update.message.reply_text(
            texts["limit"],
            parse_mode="Markdown"
        )
        return

    if not context.args:
        await update.message.reply_text(
            texts["how_to"]
        )
        return

    habit_text = " ".join(context.args)
    add_habit(user_id, habit_text)
    add_points(user_id, 1)  # +1 очко за новую привычку

    await update.message.reply_text(
        texts["added"].format(habit=habit_text),
        parse_mode="Markdown"
    )

HABITS_TEXTS = {
    "ru": {
        "no_habits": "У тебя пока нет привычек. Добавь первую с помощью /habit",
        "title": "📋 Твои привычки:",
        "done": "✅",
        "delete": "🗑️"
    },
    "uk": {
        "no_habits": "У тебе поки немає звичок. Додай першу за допомогою /habit",
        "title": "📋 Твої звички:",
        "done": "✅",
        "delete": "🗑️"
    },
    "be": {
        "no_habits": "У цябе пакуль няма звычак. Дадай першую праз /habit",
        "title": "📋 Твае звычкі:",
        "done": "✅",
        "delete": "🗑️"
    },
    "kk": {
        "no_habits": "Сенде әлі әдеттер жоқ. Біріншісін /habit арқылы қостыр.",
        "title": "📋 Сенің әдеттерің:",
        "done": "✅",
        "delete": "🗑️"
    },
    "kg": {
        "no_habits": "Сизде азырынча көнүмүштөр жок. Биринчисин /habit менен кошуңуз.",
        "title": "📋 Сиздин көнүмүштөрүңүз:",
        "done": "✅",
        "delete": "🗑️"
    },
    "hy": {
        "no_habits": "Դու դեռ սովորություններ չունես։ Ավելացրու առաջինը՝ /habit հրամանով",
        "title": "📋 Քո սովորությունները՝",
        "done": "✅",
        "delete": "🗑️"
    },
    "ce": {
        "no_habits": "Хьоьшу хьалха привычка цуьнан цуьр. Дахьах /habit хетам.",
        "title": "📋 Хьоьшу привычкаш:",
        "done": "✅",
        "delete": "🗑️"
    },
    "md": {
        "no_habits": "Încă nu ai obiceiuri. Adaugă primul cu /habit",
        "title": "📋 Obiceiurile tale:",
        "done": "✅",
        "delete": "🗑️"
    },
    "ka": {
        "no_habits": "ჯერ არ გაქვს ჩვევები. დაამატე პირველი /habit ბრძანებით",
        "title": "📋 შენი ჩვევები:",
        "done": "✅",
        "delete": "🗑️"
    },
    "en": {
        "no_habits": "You don't have any habits yet. Add your first one with /habit",
        "title": "📋 Your habits:",
        "done": "✅",
        "delete": "🗑️"
    },
}

async def habits_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    texts = HABITS_TEXTS.get(lang, HABITS_TEXTS["ru"])

    habits = get_habits(user_id)
    if not habits:
        await update.message.reply_text(texts["no_habits"])
        return

    keyboard = []
    for i, habit in enumerate(habits):
        status = texts["done"] if habit["done"] else "🔸"
        keyboard.append([
            InlineKeyboardButton(f"{status} {habit['text']}", callback_data=f"noop"),
            InlineKeyboardButton(texts["done"], callback_data=f"done_habit_{i}"),
            InlineKeyboardButton(texts["delete"], callback_data=f"delete_habit_{i}")
        ])

    await update.message.reply_text(texts["title"], reply_markup=InlineKeyboardMarkup(keyboard))

HABIT_BUTTON_TEXTS = {
    "ru": {
        "habit_done": "🎉 Привычка отмечена как выполненная!",
        "not_found": "Не удалось найти привычку.",
        "habit_deleted": "🗑️ Привычка удалена.",
        "delete_error": "Не удалось удалить привычку.",
        "no_goals": "У тебя пока нет целей, которые можно отметить выполненными 😔",
        "choose_goal": "Выбери цель, которую ты выполнил(а):"
    },
    "uk": {
        "habit_done": "🎉 Звичка позначена як виконана!",
        "not_found": "Не вдалося знайти звичку.",
        "habit_deleted": "🗑️ Звичка видалена.",
        "delete_error": "Не вдалося видалити звичку.",
        "no_goals": "У тебе поки немає цілей, які можна відмітити виконаними 😔",
        "choose_goal": "Обери ціль, яку ти виконав(ла):"
    },
    "be": {
        "habit_done": "🎉 Звычка адзначана як выкананая!",
        "not_found": "Не атрымалася знайсці звычку.",
        "habit_deleted": "🗑️ Звычка выдалена.",
        "delete_error": "Не атрымалася выдаліць звычку.",
        "no_goals": "У цябе пакуль няма мэт, якія можна адзначыць выкананымі 😔",
        "choose_goal": "Абяры мэту, якую ты выканаў(ла):"
    },
    "kk": {
        "habit_done": "🎉 Әдет орындалған деп белгіленді!",
        "not_found": "Әдет табылмады.",
        "habit_deleted": "🗑️ Әдет жойылды.",
        "delete_error": "Әдетті жою мүмкін болмады.",
        "no_goals": "Орындаған мақсаттарың әлі жоқ 😔",
        "choose_goal": "Орындаған мақсатыңды таңда:"
    },
    "kg": {
        "habit_done": "🎉 Көнүмүш аткарылды деп белгиленди!",
        "not_found": "Көнүмүш табылган жок.",
        "habit_deleted": "🗑️ Көнүмүш өчүрүлдү.",
        "delete_error": "Көнүмүштү өчүрүү мүмкүн болгон жок.",
        "no_goals": "Аткарган максаттар жок 😔",
        "choose_goal": "Аткарган максатыңды танда:"
    },
    "hy": {
        "habit_done": "🎉 Սովորությունը նշված է որպես կատարված!",
        "not_found": "Չհաջողվեց գտնել սովորությունը։",
        "habit_deleted": "🗑️ Սովորությունը ջնջված է։",
        "delete_error": "Չհաջողվեց ջնջել սովորությունը։",
        "no_goals": "Դեռ չունես նպատակներ, որոնք կարելի է նշել կատարված 😔",
        "choose_goal": "Ընտրիր նպատակը, որը կատարել ես։"
    },
    "ce": {
        "habit_done": "🎉 Привычка отмечена как выполненная!",
        "not_found": "Привычку не удалось найти.",
        "habit_deleted": "🗑️ Привычка удалена.",
        "delete_error": "Привычку не удалось удалить.",
        "no_goals": "У тебя пока нет целей для выполнения 😔",
        "choose_goal": "Выбери цель, которую ты выполнил(а):"
    },
    "md": {
        "habit_done": "🎉 Obiceiul a fost marcat ca realizat!",
        "not_found": "Nu am putut găsi obiceiul.",
        "habit_deleted": "🗑️ Obiceiul a fost șters.",
        "delete_error": "Nu am putut șterge obiceiul.",
        "no_goals": "Nu ai încă scopuri de bifat 😔",
        "choose_goal": "Alege scopul pe care l-ai realizat:"
    },
    "ka": {
        "habit_done": "🎉 ჩვევა შესრულებულად მოინიშნა!",
        "not_found": "ჩვევა ვერ მოიძებნა.",
        "habit_deleted": "🗑️ ჩვევა წაიშალა.",
        "delete_error": "ჩვევის წაშლა ვერ მოხერხდა.",
        "no_goals": "ჯერ არ გაქვს მიზნები, რომლებსაც შეასრულებდი 😔",
        "choose_goal": "აირჩიე მიზანი, რომელიც შეასრულე:"
    },
    "en": {
        "habit_done": "🎉 Habit marked as completed!",
        "not_found": "Could not find the habit.",
        "habit_deleted": "🗑️ Habit deleted.",
        "delete_error": "Could not delete the habit.",
        "no_goals": "You don't have any goals to mark as completed yet 😔",
        "choose_goal": "Select the goal you’ve completed:"
    }
}

async def handle_habit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    texts = HABIT_BUTTON_TEXTS.get(lang, HABIT_BUTTON_TEXTS["ru"])
    await query.answer()

    if query.data.startswith("done_habit_"):
        index = int(query.data.split("_")[-1])
        if mark_habit_done(user_id, index):
            await query.edit_message_text(texts["habit_done"])
        else:
            await query.edit_message_text(texts["not_found"])

    elif query.data.startswith("delete_habit_"):
        index = int(query.data.split("_")[-1])
        if delete_habit(user_id, index):
            await query.edit_message_text(texts["habit_deleted"])
        else:
            await query.edit_message_text(texts["delete_error"])

REACTIONS_GOAL_DONE = {
    "ru": [
        "🌟 Горжусь тобой! Ещё один шаг вперёд.",
        "🥳 Отличная работа! Ты молодец.",
        "💪 Вот это настрой! Так держать.",
        "🔥 Ты сделал(а) это! Уважение 💜",
        "👏 Маленькие шаги — к большим победам.",
        "💜 Я горжусь твоей настойчивостью!",
        "✨ Так держать, всё получится!",
        "🚀 Вперёд к новым целям!",
        "🦋 Ты сам(а) — источник перемен.",
        "🎉 Цель достигнута, это круто!",
    ],
    "uk": [
        "🌟 Пишаюся тобою! Ще один крок вперед.",
        "🥳 Чудова робота! Ти молодець.",
        "💪 Ось це настрій! Так тримати.",
        "🔥 Ти це зробив(ла)! Респект 💜",
        "👏 Маленькі кроки — до великих перемог.",
        "💜 Я пишаюся твоєю наполегливістю!",
        "✨ Так тримати, все вийде!",
        "🚀 Вперед до нових цілей!",
        "🦋 Ти сам(а) — джерело змін.",
        "🎉 Мета досягнута, це круто!",
    ],
    "be": [
        "🌟 Ганаруся табой! Яшчэ адзін крок наперад.",
        "🥳 Цудоўная праца! Ты малайчына.",
        "💪 Вось гэта настрой! Так трымаць.",
        "🔥 Ты зрабіў(ла) гэта! Павага 💜",
        "👏 Маленькія крокі — да вялікіх перамог.",
        "💜 Я ганаруся тваёй настойлівасцю!",
        "✨ Так трымаць, усё атрымаецца!",
        "🚀 Наперад да новых мэтаў!",
        "🦋 Ты сам(а) — крыніца зменаў.",
        "🎉 Мэта дасягнута, гэта крута!",
    ],
    "kk": [
        "🌟 Сенмен мақтанамын! Тағы бір қадам алға.",
        "🥳 Жақсы жұмыс! Сен кереметсің.",
        "💪 Міне, осы нағыз көңіл-күй! Осылай жалғастыр.",
        "🔥 Сен мұны істедің! Құрмет 💜",
        "👏 Кішкентай қадамдар — үлкен жеңістерге.",
        "💜 Сенің табандылығыңмен мақтанамын!",
        "✨ Осылай жалғастыр, бәрі болады!",
        "🚀 Жаңа мақсаттарға алға!",
        "🦋 Өзгерістің бастауы — сен өзің.",
        "🎉 Мақсат орындалды, бұл керемет!",
    ],
    "kg": [
        "🌟 Сен менен сыймыктанам! Дагы бир кадам алдыга.",
        "🥳 Сонун иш! Молодец.",
        "💪 Мынакей күчтүү маанай! Ушундай улант.",
        "🔥 Сен муну жасадыӊ! Урмат 💜",
        "👏 Кичинекей кадамдар — чоң жеңиштерге.",
        "💜 Сенин тырышчаактыгыӊ менен сыймыктанам!",
        "✨ Ушундай уланта бер, баары болот!",
        "🚀 Жаңы максаттарга алга!",
        "🦋 Өзгөрүүнүн булагы — өзүң.",
        "🎉 Максат аткарылды, сонун!",
    ],
    "hy": [
        "🌟 Հպարտանում եմ քեզնով։ Եվս մեկ քայլ առաջ։",
        "🥳 Հիանալի աշխատանք։ Դու առարկայաբար լավն ես։",
        "💪 Ահա այսպիսի տրամադրություն։ Շարունակիր։",
        "🔥 Դու արեցիր դա։ Հարգանք 💜",
        "👏 Փոքր քայլերը մեծ հաղթանակների։",
        "💜 Հպարտ եմ քո համառությամբ։",
        "✨ Շարունակիր, ամեն ինչ կստացվի։",
        "🚀 Նոր նպատակների առաջ։",
        "🦋 Փոփոխությունների աղբյուրը դու ես։",
        "🎉 Նպատակն իրականացավ, դա հիանալի է։",
    ],
    "ce": [
        "🌟 Хьоьшу цуьнан! Ахкин а, кхетига къобал болу.",
        "🥳 Бахам хета! Хьо дика хьун.",
        "💪 Ву къобал хила! Кхетига.",
        "🔥 Хьо хийцам! Х1уш ву 💜",
        "👏 Керла хетам — цуьнан мотт.",
        "💜 Са цуьнан хьоьшу цуьнан!",
        "✨ Кхетига, цуьнан мотт болу!",
        "🚀 Кхетига хетам, кхетиг цуьнан!",
        "🦋 Хьо цуьнан хила, кхетиг буьйсан.",
        "🎉 Мацахьер цуьнан, ву бахам!",
    ],
    "md": [
        "🌟 Sunt mândru(ă) de tine! Încă un pas înainte.",
        "🥳 Super! Ai făcut o treabă grozavă.",
        "💪 Acesta e spiritul! Continuă așa.",
        "🔥 Ai reușit! Respect 💜",
        "👏 Pași mici spre mari victorii.",
        "💜 Sunt mândru(ă) de perseverența ta!",
        "✨ Continuă așa, vei reuși!",
        "🚀 Spre noi scopuri!",
        "🦋 Tu ești sursa schimbării.",
        "🎉 Ținta atinsă, e minunat!",
    ],
    "ka": [
        "🌟 შენით ვამაყობ! კიდევ ერთი ნაბიჯი წინ.",
        "🥳 შესანიშნავი საქმეა! ბრწყინვალედ გაართვი თავი.",
        "💪 ეს არის ნამდვილი განწყობა! ასე გააგრძელე.",
        "🔥 გააკეთე ეს! პატივისცემით 💜",
        "👏 პატარა ნაბიჯები — დიდ გამარჯვებებამდე.",
        "💜 ვამაყობ შენი მონდომებით!",
        "✨ ასე გააგრძელე, ყველაფერი გამოგივა!",
        "🚀 ახალი მიზნებისკენ წინ!",
        "🦋 ცვლილებების წყარო — შენ ხარ.",
        "🎉 მიზანი შესრულდა, ეს შესანიშნავია!",
    ],
    "en": [
        "🌟 I'm proud of you! Another step forward.",
        "🥳 Great job! You did amazing.",
        "💪 That's the spirit! Keep going.",
        "🔥 You did it! Respect 💜",
        "👏 Small steps lead to big victories.",
        "💜 I'm proud of your perseverance!",
        "✨ Keep it up, you’ll succeed!",
        "🚀 On to new goals!",
        "🦋 You are the source of change.",
        "🎉 Goal achieved, that’s awesome!",
    ]
}

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    texts = HABIT_BUTTON_TEXTS.get(lang, HABIT_BUTTON_TEXTS["ru"])

    goals = get_goals_for_user(user_id)
    if not goals:
        await update.message.reply_text(texts["no_goals"])
        return

    buttons = [
        [InlineKeyboardButton(goal, callback_data=f"done_goal|{goal}")]
        for goal in goals
    ]

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(texts["choose_goal"], reply_markup=reply_markup)

DELETE_MESSAGES = {
    "ru": {
        "usage": "❌ Чтобы удалить цель, напиши так:\n`/delete 1`",
        "deleted": "🗑️ Цель удалена.",
        "not_found": "⚠️ Не могу найти такую цель."
    },
    "uk": {
        "usage": "❌ Щоб видалити ціль, напиши так:\n`/delete 1`",
        "deleted": "🗑️ Ціль видалена.",
        "not_found": "⚠️ Не можу знайти таку ціль."
    },
    "be": {
        "usage": "❌ Каб выдаліць мэту, напішы так:\n`/delete 1`",
        "deleted": "🗑️ Мэта выдалена.",
        "not_found": "⚠️ Не магу знайсці такую мэту."
    },
    "kk": {
        "usage": "❌ Мақсатты өшіру үшін осылай жазыңыз:\n`/delete 1`",
        "deleted": "🗑️ Мақсат өшірілді.",
        "not_found": "⚠️ Мұндай мақсат табылмады."
    },
    "kg": {
        "usage": "❌ Максатты өчүрүү үчүн мындай жазыңыз:\n`/delete 1`",
        "deleted": "🗑️ Максат өчүрүлдү.",
        "not_found": "⚠️ Мындай максат табылган жок."
    },
    "hy": {
        "usage": "❌ Նպատակը ջնջելու համար գրիր այսպես:\n`/delete 1`",
        "deleted": "🗑️ Նպատակը ջնջված է։",
        "not_found": "⚠️ Այդպիսի նպատակ չեմ կարող գտնել։"
    },
    "ce": {
        "usage": "❌ Мацахь кхоллар, так пишите:\n`/delete 1`",
        "deleted": "🗑️ Мацахь дӀелла.",
        "not_found": "⚠️ Цуьнан мацахь дукха ца дийцар."
    },
    "md": {
        "usage": "❌ Pentru a șterge un obiectiv, scrie:\n`/delete 1`",
        "deleted": "🗑️ Obiectivul a fost șters.",
        "not_found": "⚠️ Nu pot găsi un astfel de obiectiv."
    },
    "ka": {
        "usage": "❌ მიზნის წასაშლელად ასე დაწერე:\n`/delete 1`",
        "deleted": "🗑️ მიზანი წაშლილია.",
        "not_found": "⚠️ ვერ ვპოულობ ასეთ მიზანს."
    },
    "en": {
        "usage": "❌ To delete a goal, type:\n`/delete 1`",
        "deleted": "🗑️ Goal deleted.",
        "not_found": "⚠️ Can't find such a goal."
    },
}

async def delete_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    msgs = DELETE_MESSAGES.get(lang, DELETE_MESSAGES["ru"])

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(msgs["usage"], parse_mode="Markdown")
        return

    index = int(context.args[0]) - 1
    success = delete_goal(user_id, index)

    if success:
        await update.message.reply_text(msgs["deleted"])
    else:
        await update.message.reply_text(msgs["not_found"])

LANG_PATTERNS = {
    "ru": {
        "deadline": r"до (\d{4}-\d{2}-\d{2})",
        "remind": "напомни"
    },
    "uk": {
        "deadline": r"до (\d{4}-\d{2}-\d{2})",
        "remind": "нагадай"
    },
    "be": {
        "deadline": r"да (\d{4}-\d{2}-\d{2})",
        "remind": "нагадай"
    },
    "kk": {
        "deadline": r"(\d{4}-\d{2}-\d{2}) дейін",
        "remind": "еске сал"
    },
    "kg": {
        "deadline": r"(\d{4}-\d{2}-\d{2}) чейин",
        "remind": "эскертип кой"
    },
    "hy": {
        "deadline": r"մինչև (\d{4}-\d{2}-\d{2})",
        "remind": "հիշեցրու"
    },
    "ce": {
        "deadline": r"(\d{4}-\d{2}-\d{2}) даьлча",
        "remind": "эха"
    },
    "md": {
        "deadline": r"până la (\d{4}-\d{2}-\d{2})",
        "remind": "amintește"
    },
    "ka": {
        "deadline": r"(\d{4}-\d{2}-\d{2})-მდე",
        "remind": "შემახსენე"
    },
    "en": {
        "deadline": r"by (\d{4}-\d{2}-\d{2})",
        "remind": "remind"
    }
}

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_goal_count
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # 🎯 Тексты для разных языков
    goal_texts = {
        "ru": {
            "no_args": "✏️ Чтобы поставить цель, напиши так:\n/goal Прочитать 10 страниц до 2025-06-28 напомни",
            "limit": "🔒 В бесплатной версии можно ставить только 3 цели в день.\nХочешь больше? Оформи Mindra+ 💜",
            "bad_date": "❗ Неверный формат даты. Используй ГГГГ-ММ-ДД",
            "added": "🎯 Цель добавлена:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Напоминание включено"
        },
        "uk": {
            "no_args": "✏️ Щоб поставити ціль, напиши так:\n/goal Прочитати 10 сторінок до 2025-06-28 нагадай",
            "limit": "🔒 У безкоштовній версії можна ставити лише 3 цілі на день.\nХочеш більше? Оформи Mindra+ 💜",
            "bad_date": "❗ Невірний формат дати. Використовуй РРРР-ММ-ДД",
            "added": "🎯 Ціль додана:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Нагадування увімкнено"
        },
        "be": {
            "no_args": "✏️ Каб паставіць мэту, напішы так:\n/goal Прачытай 10 старонак да 2025-06-28 нагадай",
            "limit": "🔒 У бясплатнай версіі можна ставіць толькі 3 мэты на дзень.\nХочаш больш? Аформі Mindra+ 💜",
            "bad_date": "❗ Няправільны фармат даты. Выкарыстоўвай ГГГГ-ММ-ДД",
            "added": "🎯 Мэта дададзена:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 Напамін уключаны"
        },
        "kk": {
            "no_args": "✏️ Мақсат қою үшін былай жаз:\n/goal 10 бет оқу 2025-06-28 дейін еске сал",
            "limit": "🔒 Тегін нұсқада күніне тек 3 мақсат қоюға болады.\nКөбірек керек пе? Mindra+ алыңыз 💜",
            "bad_date": "❗ Күн форматы қате. ЖЖЖЖ-АА-КК түрінде жазыңыз",
            "added": "🎯 Мақсат қосылды:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Еске салу қосылды"
        },
        "kg": {
            "no_args": "✏️ Максат коюу үчүн мындай жаз:\n/goal 10 бет оку 2025-06-28 чейин эскертип кой",
            "limit": "🔒 Акысыз версияда күнүнө 3 гана максат коюуга болот.\nКөбүрөөк керекпи? Mindra+ жазылуу 💜",
            "bad_date": "❗ Датанын форматы туура эмес. ЖЖЖЖ-АА-КК колдон",
            "added": "🎯 Максат кошулду:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Эскертүү күйгүзүлдү"
        },
        "hy": {
            "no_args": "✏️ Նպատակ դնելու համար գրիր այսպես:\n/goal Կարդալ 10 էջ մինչև 2025-06-28 հիշեցրու",
            "limit": "🔒 Անվճար տարբերակում կարելի է օրական միայն 3 նպատակ դնել.\nՈւզում ես ավելին? Միացիր Mindra+ 💜",
            "bad_date": "❗ Սխալ ամսաթվի ձևաչափ. Օգտագործիր ՏՏՏՏ-ԱԱ-ՕՕ",
            "added": "🎯 Նպատակ ավելացվեց:",
            "deadline": "🗓 Վերջնաժամկետ:",
            "remind": "🔔 Հիշեցումը միացված է"
        },
        "ce": {
            "no_args": "✏️ Мацахь кхоллар, йаьллаца:\n/goal Къобалле 10 агӀо 2025-06-28 даьлча эха",
            "limit": "🔒 Аьтто версия хийцна, цхьаьнан 3 мацахь дина кхолларш йолуш.\nКъобал? Mindra+ 💜",
            "bad_date": "❗ Дата формат дукха. ГГГГ-ММ-ДД формата язде",
            "added": "🎯 Мацахь тӀетоха:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 ДӀадела хийна"
        },
        "md": {
            "no_args": "✏️ Pentru a seta un obiectiv, scrie așa:\n/goal Citește 10 pagini până la 2025-06-28 amintește",
            "limit": "🔒 În versiunea gratuită poți seta doar 3 obiective pe zi.\nVrei mai multe? Obține Mindra+ 💜",
            "bad_date": "❗ Format de dată incorect. Folosește AAAA-LL-ZZ",
            "added": "🎯 Obiectiv adăugat:",
            "deadline": "🗓 Termen limită:",
            "remind": "🔔 Memento activat"
        },
        "ka": {
            "no_args": "✏️ მიზნის დასაყენებლად დაწერე ასე:\n/goal წავიკითხო 10 გვერდი 2025-06-28-მდე შემახსენე",
            "limit": "🔒 უფასო ვერსიაში დღეში მხოლოდ 3 მიზნის დაყენება შეგიძლია.\nგინდა მეტი? გამოიწერე Mindra+ 💜",
            "bad_date": "❗ არასწორი თარიღის ფორმატი. გამოიყენე წწწწ-თთ-რრ",
            "added": "🎯 მიზანი დამატებულია:",
            "deadline": "🗓 ბოლო ვადა:",
            "remind": "🔔 შეხსენება ჩართულია"
        },
        "en": {
            "no_args": "✏️ To set a goal, write like this:\n/goal Read 10 pages by 2025-06-28 remind",
            "limit": "🔒 In the free version you can set only 3 goals per day.\nWant more? Get Mindra+ 💜",
            "bad_date": "❗ Wrong date format. Use YYYY-MM-DD",
            "added": "🎯 Goal added:",
            "deadline": "🗓 Deadline:",
            "remind": "🔔 Reminder is on"
        },
    }

    t = goal_texts.get(lang, goal_texts["ru"])
    # Паттерны для дедлайна и напоминалки
    patterns = LANG_PATTERNS.get(lang, LANG_PATTERNS["ru"])
    deadline_pattern = patterns["deadline"]
    remind_kw = patterns["remind"]

    # ✅ Проверка аргументов
    if not context.args:
        await update.message.reply_text(t["no_args"], parse_mode="Markdown")
        return

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
    deadline_match = re.search(deadline_pattern, text, flags=re.IGNORECASE)
    remind = remind_kw in text.lower()

    deadline = None
    if deadline_match:
        try:
            deadline = deadline_match.group(1)
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text(t["bad_date"])
            return

    goal_text = re.sub(deadline_pattern, '', text, flags=re.IGNORECASE).replace(remind_kw, "").strip()

    add_goal(user_id, goal_text, deadline=deadline, remind=remind)
    add_points(user_id, 1)

    reply = f"{t['added']} *{goal_text}*"
    if deadline:
        reply += f"\n{t['deadline']} `{deadline}`"
    if remind:
        reply += f"\n{t['remind']}"

    await update.message.reply_markdown(reply)

async def show_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    goals = get_goals_for_user(user_id)  # Новая функция хранения

    # Мультиязычные подписи
    goals_texts = {
        "ru": {
            "no_goals": "🎯 У тебя пока нет целей. Добавь первую с помощью /goal",
            "your_goals": "📋 *Твои цели:*",
            "done": "✅", "not_done": "🔸"
        },
        "uk": {
            "no_goals": "🎯 У тебе поки немає цілей. Додай першу за допомогою /goal",
            "your_goals": "📋 *Твої цілі:*",
            "done": "✅", "not_done": "🔸"
        },
        "be": {
            "no_goals": "🎯 У цябе пакуль няма мэтаў. Дадай першую з дапамогай /goal",
            "your_goals": "📋 *Твае мэты:*",
            "done": "✅", "not_done": "🔸"
        },
        "kk": {
            "no_goals": "🎯 Әзірге мақсатың жоқ. Алғашқыны /goal арқылы қоса аласың",
            "your_goals": "📋 *Сенің мақсаттарың:*",
            "done": "✅", "not_done": "🔸"
        },
        "kg": {
            "no_goals": "🎯 Азырынча максатың жок. Биринчисин /goal аркылуу кош!",
            "your_goals": "📋 *Сенин максаттарың:*",
            "done": "✅", "not_done": "🔸"
        },
        "hy": {
            "no_goals": "🎯 Դեռ նպատակ չունես։ Ավելացրու առաջինը /goal հրամանով",
            "your_goals": "📋 *Քո նպատակները:*",
            "done": "✅", "not_done": "🔸"
        },
        "ce": {
            "no_goals": "🎯 Хьоьш цуьнан мацахь цуьнан. /goal кхолларш ду!",
            "your_goals": "📋 *Са мацахь:*",
            "done": "✅", "not_done": "🔸"
        },
        "md": {
            "no_goals": "🎯 Încă nu ai obiective. Adaugă primul cu /goal",
            "your_goals": "📋 *Obiectivele tale:*",
            "done": "✅", "not_done": "🔸"
        },
        "ka": {
            "no_goals": "🎯 ჯერჯერობით არ გაქვს მიზანი. დაამატე პირველი /goal-ით",
            "your_goals": "📋 *შენი მიზნები:*",
            "done": "✅", "not_done": "🔸"
        },
        "en": {
            "no_goals": "🎯 You don’t have any goals yet. Add your first with /goal",
            "your_goals": "📋 *Your goals:*",
            "done": "✅", "not_done": "🔸"
        },
    }

    t = goals_texts.get(lang, goals_texts["ru"])

    if not goals:
        await update.message.reply_text(t["no_goals"])
        return

    reply = f"{t['your_goals']}\n\n"
    for idx, goal in enumerate(goals, 1):
        status = t["done"] if goal.get("done") else t["not_done"]
        reply += f"{idx}. {status} {goal.get('text', '')}\n"

    await update.message.reply_markdown(reply)
    
async def goal_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    await query.answer()

    # Мультиязычные тексты
    btn_texts = {
        "ru": {
            "write_goal": "✍️ Напиши свою цель:\n`/goal Прочитать 10 страниц`",
            "no_goals": "❌ У тебя пока нет целей. Добавь первую с помощью /goal",
            "your_goals": "📋 Твои цели:",
            "write_habit": "🌱 Напиши свою привычку:\n`/habit Делать зарядку утром`",
            "no_habits": "❌ У тебя пока нет привычек. Добавь первую через /habit",
            "your_habits": "📊 Твои привычки:"
        },
        "uk": {
            "write_goal": "✍️ Напиши свою ціль:\n`/goal Прочитати 10 сторінок`",
            "no_goals": "❌ У тебе поки немає цілей. Додай першу за допомогою /goal",
            "your_goals": "📋 Твої цілі:",
            "write_habit": "🌱 Напиши свою звичку:\n`/habit Робити зарядку вранці`",
            "no_habits": "❌ У тебе поки немає звичок. Додай першу через /habit",
            "your_habits": "📊 Твої звички:"
        },
        "be": {
            "write_goal": "✍️ Напішы сваю мэту:\n`/goal Прачытай 10 старонак`",
            "no_goals": "❌ У цябе пакуль няма мэтаў. Дадай першую з дапамогай /goal",
            "your_goals": "📋 Твае мэты:",
            "write_habit": "🌱 Напішы сваю звычку:\n`/habit Рабіць зарадку раніцай`",
            "no_habits": "❌ У цябе пакуль няма звычак. Дадай першую праз /habit",
            "your_habits": "📊 Твае звычкі:"
        },
        "kk": {
            "write_goal": "✍️ Мақсатыңды жаз:\n`/goal 10 бет оқу`",
            "no_goals": "❌ Әзірге мақсатың жоқ. Алғашқыны /goal арқылы қоса аласың",
            "your_goals": "📋 Сенің мақсаттарың:",
            "write_habit": "🌱 Әдетіңді жаз:\n`/habit Таңертең жаттығу жасау`",
            "no_habits": "❌ Әзірге әдетің жоқ. Алғашқыны /habit арқылы қос",
            "your_habits": "📊 Сенің әдеттерің:"
        },
        "kg": {
            "write_goal": "✍️ Максатыңды жаз:\n`/goal 10 бет оку`",
            "no_goals": "❌ Азырынча максатың жок. Биринчисин /goal аркылуу кош!",
            "your_goals": "📋 Сенин максаттарың:",
            "write_habit": "🌱 Адатынды жаз:\n`/habit Таңкы көнүгүү жасоо`",
            "no_habits": "❌ Азырынча адатың жок. Биринчисин /habit аркылуу кош",
            "your_habits": "📊 Сенин адаттарың:"
        },
        "hy": {
            "write_goal": "✍️ Գրիր քո նպատակը:\n`/goal Կարդալ 10 էջ`",
            "no_goals": "❌ Դեռ նպատակ չունես։ Ավելացրու առաջինը /goal հրամանով",
            "your_goals": "📋 Քո նպատակները:",
            "write_habit": "🌱 Գրիր քո սովորությունը:\n`/habit Անել լիցքավորում առավոտյան`",
            "no_habits": "❌ Դեռ սովորություն չունես։ Ավելացրու առաջինը /habit հրամանով",
            "your_habits": "📊 Քո սովորությունները:"
        },
        "ce": {
            "write_goal": "✍️ Хьоьшу мацахь лаца:\n`/goal Къобалле 10 агӀо`",
            "no_goals": "❌ Хьоьш цуьнан мацахь цуьнан. /goal кхолларш ду!",
            "your_goals": "📋 Са мацахь:",
            "write_habit": "🌱 Хьоьшу привычка лаца:\n`/habit Бахьар хьалхара йолуш`",
            "no_habits": "❌ Хьоьш цуьнан привычка цуьнан. /habit лаца ду",
            "your_habits": "📊 Са привычка:"
        },
        "md": {
            "write_goal": "✍️ Scrie obiectivul tău:\n`/goal Citește 10 pagini`",
            "no_goals": "❌ Încă nu ai obiective. Adaugă primul cu /goal",
            "your_goals": "📋 Obiectivele tale:",
            "write_habit": "🌱 Scrie obiceiul tău:\n`/habit Fă exerciții dimineața`",
            "no_habits": "❌ Încă nu ai obiceiuri. Adaugă primul cu /habit",
            "your_habits": "📊 Obiceiurile tale:"
        },
        "ka": {
            "write_goal": "✍️ დაწერე შენი მიზანი:\n`/goal წავიკითხო 10 გვერდი`",
            "no_goals": "❌ ჯერჯერობით არ გაქვს მიზანი. დაამატე პირველი /goal-ით",
            "your_goals": "📋 შენი მიზნები:",
            "write_habit": "🌱 დაწერე შენი ჩვევა:\n`/habit დილის ვარჯიში`",
            "no_habits": "❌ ჯერჯერობით არ გაქვს ჩვევა. დაამატე პირველი /habit-ით",
            "your_habits": "📊 შენი ჩვევები:"
        },
        "en": {
            "write_goal": "✍️ Write your goal:\n`/goal Read 10 pages`",
            "no_goals": "❌ You don’t have any goals yet. Add your first with /goal",
            "your_goals": "📋 Your goals:",
            "write_habit": "🌱 Write your habit:\n`/habit Morning exercise`",
            "no_habits": "❌ You don’t have any habits yet. Add your first with /habit",
            "your_habits": "📊 Your habits:"
        }
    }

    t = btn_texts.get(lang, btn_texts["ru"])

    if query.data == "create_goal":
        await query.edit_message_text(t["write_goal"], parse_mode="Markdown")

    elif query.data == "show_goals":
        goals = get_goals(user_id)
        if not goals:
            await query.edit_message_text(t["no_goals"])
        else:
            goals_list = "\n".join([f"• {g['text']} {'✅' if g.get('done') else '❌'}" for g in goals])
            await query.edit_message_text(f"{t['your_goals']}\n{goals_list}")

    elif query.data == "create_habit":
        await query.edit_message_text(t["write_habit"], parse_mode="Markdown")

    elif query.data == "show_habits":
        habits = get_habits(user_id)
        if not habits:
            await query.edit_message_text(t["no_habits"])
        else:
            habits_list = "\n".join([f"• {h['text']} {'✅' if h.get('done') else '❌'}" for h in habits])
            await query.edit_message_text(f"{t['your_habits']}\n{habits_list}")
            
# Загрузка истории и режимов
conversation_history = load_history()
user_modes = {}

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

TRIAL_GRANTED_TEXT = {
    "ru": "🎁 Тебе доступно *3 дня Mindra+*! Пользуйся всеми премиум-фишками 😉",
    "uk": "🎁 Тобі доступно *3 дні Mindra+*! Користуйся всіма преміум-фішками 😉",
    "be": "🎁 Табе даступна *3 дні Mindra+*! Скарыстайся ўсімі прэміум-фішкамі 😉",
    "kk": "🎁 Саған қолжетімді *3 күн Mindra+*! Барлық премиум функцияларды пайдаланыңыз 😉",
    "kg": "🎁 Сага *3 күн Mindra+* жеткиликтүү! Бардык премиум-функцияларды колдон 😉",
    "hy": "🎁 Դու ստացել ես *3 օր Mindra+*! Օգտվիր բոլոր պրեմիում հնարավորություններից 😉",
    "ce": "🎁 Тхо *3 кхоллар Mindra+* болу а! Барча премиум функцияш ву 😉",
    "md": "🎁 Ai *3 zile Mindra+* disponibile! Folosește toate funcțiile premium 😉",
    "ka": "🎁 შენ გაქვს *3 დღე Mindra+*! ისარგებლე ყველა პრემიუმ ფუნქციით 😉",
    "en": "🎁 You have *3 days of Mindra+*! Enjoy all premium features 😉",
}

REFERRAL_BONUS_TEXT = {
    "ru": "🎉 Ты и твой друг получили +7 дней Mindra+!",
    "uk": "🎉 Ти і твій друг отримали +7 днів Mindra+!",
    "be": "🎉 Ты і тваё сябра атрымалі +7 дзён Mindra+!",
    "kk": "🎉 Сен және досың +7 күн Mindra+ алдыңдар!",
    "kg": "🎉 Сен жана досуң +7 күн Mindra+ алдыңар!",
    "hy": "🎉 Դու և ընկերդ ստացել եք +7 օր Mindra+!",
    "ce": "🎉 Хьо цуьнан догъа +7 кхоллар Mindra+ болу а!",
    "md": "🎉 Tu și prietenul tău ați primit +7 zile Mindra+!",
    "ka": "🎉 შენ და შენს მეგობარს დამატებით +7 დღე Mindra+ გექნებათ!",
    "en": "🎉 You and your friend received +7 days of Mindra+!",
}

TRIAL_INFO_TEXT = {
    "ru": "💎 У тебя активен Mindra+! Тебе доступно 3 дня премиума. Пользуйся всеми фишками 😉",
    "uk": "💎 У тебе активний Mindra+! У тебе є 3 дні преміуму. Користуйся усіма можливостями 😉",
    "be": "💎 У цябе актыўны Mindra+! У цябе ёсць 3 дні прэміуму. Скарыстайся ўсімі магчымасцямі 😉",
    "kk": "💎 Сенде Mindra+ белсенді! 3 күн премиум қолжетімді. Барлық функцияларды қолданып көр 😉",
    "kg": "💎 Сенде Mindra+ активдүү! 3 күн премиум бар. Бардык мүмкүнчүлүктөрдү колдон 😉",
    "hy": "💎 Քեզ մոտ ակտիվ է Mindra+! Դու ունես 3 օր պրեմիում։ Օգտագործիր բոլոր հնարավորությունները 😉",
    "ce": "💎 Хьо даьлча Mindra+ активна! 3 кхетам премиум. Хета функциеш йоза цуьнан 😉",
    "md": "💎 Ai Mindra+ activ! Ai 3 zile premium. Profită de toate funcțiile 😉",
    "ka": "💎 შენ გაქვს აქტიური Mindra+! 3 დღე პრემიუმი გაქვს. ისარგებლე ყველა ფუნქციით 😉",
    "en": "💎 You have Mindra+ active! You have 3 days of premium. Enjoy all features 😉"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    logging.info(f"/start: user_id={user_id}, context.args={context.args}, message.text={update.message.text}")

    # --- 0. Если язык ещё не выбран — показываем кнопки выбора ---
    if user_id not in user_languages:
        # Если в context.args есть ref — сохраняем!
        if context.args and context.args[0].startswith("ref"):
            user_ref_args[user_id] = context.args[0]
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
     # Если язык уже выбран — обычное приветствие
    lang_code = user_languages.get(user_id, "ru")
    first_name = update.effective_user.first_name or "друг"
    welcome_text = WELCOME_TEXTS.get(lang_code, WELCOME_TEXTS["ru"]).format(first_name=first_name)
    await update.message.reply_text(welcome_text, parse_mode="Markdown")   

RESET_TEXTS = {
    "ru": "История очищена. Начнём сначала ✨",
    "uk": "Історію очищено. Почнемо спочатку ✨",
    "be": "Гісторыя ачышчана. Пачнем спачатку ✨",
    "kk": "Тарих тазаланды. Қайта бастайық ✨",
    "kg": "Тарых тазаланды. Башынан баштайбыз ✨",
    "hy": "Պատմությունը մաքրված է։ Սկսենք նորից ✨",
    "ce": "Тарих цуьнан. Дика йойла кхеташ ✨",
    "md": "Istoria a fost ștearsă. Să începem de la început ✨",
    "ka": "ისტორია გასუფთავდა. დავიწყოთ თავიდან ✨",
    "en": "History cleared. Let’s start again ✨",
}

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text(RESET_TEXTS.get(lang, RESET_TEXTS["ru"]))

MODE_TEXTS = {
    "ru": {
        "text": "Выбери стиль общения Mindra ✨",
        "support": "🎧 Поддержка",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Юмор",
    },
    "uk": {
        "text": "Обери стиль спілкування Mindra ✨",
        "support": "🎧 Підтримка",
        "motivation": "🌸 Мотивація",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Гумор",
    },
    "be": {
        "text": "Абяры стыль зносін Mindra ✨",
        "support": "🎧 Падтрымка",
        "motivation": "🌸 Матывацыя",
        "philosophy": "🧘 Псіхолаг",
        "humor": "🎭 Гумар",
    },
    "kk": {
        "text": "Mindra-мен сөйлесу стилін таңда ✨",
        "support": "🎧 Қолдау",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Әзіл",
    },
    "kg": {
        "text": "Mindra-нын сүйлөшүү стилін танда ✨",
        "support": "🎧 Колдоо",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Тамаша",
    },
    "hy": {
        "text": "Ընտրիր Mindra-ի շփման ոճը ✨",
        "support": "🎧 Աջակցություն",
        "motivation": "🌸 Մոտիվացիա",
        "philosophy": "🧘 Հոգեբան",
        "humor": "🎭 Հումոր",
    },
    "ce": {
        "text": "Mindra стили тӀетохьа ✨",
        "support": "🎧 ДӀалийла",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Юмор",
    },
    "md": {
        "text": "Alege stilul de comunicare Mindra ✨",
        "support": "🎧 Suport",
        "motivation": "🌸 Motivație",
        "philosophy": "🧘 Psiholog",
        "humor": "🎭 Umor",
    },
    "ka": {
        "text": "აირჩიე Mindra-ს კომუნიკაციის სტილი ✨",
        "support": "🎧 მხარდაჭერა",
        "motivation": "🌸 მოტივაცია",
        "philosophy": "🧘 ფსიქოლოგი",
        "humor": "🎭 იუმორი",
    },
    "en": {
        "text": "Choose your Mindra chat style ✨",
        "support": "🎧 Support",
        "motivation": "🌸 Motivation",
        "philosophy": "🧘 Psychologist",
        "humor": "🎭 Humor",
    },
}

MODES = {
    "support": {
        "ru": "Ты — чуткий и добрый AI-друг, который всегда выслушает и поддержит. Помогай пользователю почувствовать себя лучше.",
        "uk": "Ти — уважний і добрий AI-товариш, який завжди вислухає й підтримає. Допомагай користувачу почуватися краще.",
        "be": "Ты — чулы і добры AI-сябар, які заўсёды выслухае і падтрымае. Дапамагай карыстальніку адчуваць сябе лепш.",
        "kk": "Сен — әрдайым тыңдайтын әрі қолдау көрсететін қамқор AI-доссың. Пайдаланушыға өзін жақсы сезінуге көмектес.",
        "kg": "Сен — ар дайым уга көңүл бөлгөн жана колдогон AI-доссуң. Колдонуучуга жакшы сезүүгө жардам бер.",
        "hy": "Դու՝ ուշադիր և բարի AI-ընկեր ես, ով միշտ կլսի ու կաջակցի։ Օգնիր օգտվողին ավելի լավ զգալ։",
        "ce": "Хьо — тӀетохь, догӀа AI-дост, хийцам болу а, дукха хьуна йаьлла. Хьо кхеташ дукха хилча йоьлла.",
        "md": "Ești un prieten AI atent și bun, care mereu ascultă și sprijină. Ajută utilizatorul să se simtă mai bine.",
        "ka": "შენ ხარ გულისხმიერი და მეგობრული AI-მეგობარი, რომელიც ყოველთვის მოუსმენს და მხარს დაუჭერს. დაეხმარე მომხმარებელს თავი უკეთ იგრძნოს.",
        "en": "You are a caring and supportive AI-friend who always listens and helps. Help the user feel better.",
    },
    "motivation": {
        "ru": "Ты — воодушевляющий коуч и поддерживающий компаньон. Помогай пользователю поверить в себя и двигаться вперёд.",
        "uk": "Ти — надихаючий коуч і підтримуючий компаньйон. Допомагай користувачу вірити в себе та рухатися вперед.",
        "be": "Ты — матывуючы коуч і падтрымліваючы кампаньён. Дапамагай карыстальніку верыць у сябе і рухацца наперад.",
        "kk": "Сен — шабыттандыратын коучсың, әрдайым қолдау көрсететін серіксің. Пайдаланушының өзіне сенуіне көмектес.",
        "kg": "Сен — дем берген коуч жана колдогон доссуң. Колдонуучунун өзүнө ишенүүсүнө жардам бер.",
        "hy": "Դու՝ ոգեշնչող քոուչ ես և աջակցող ընկեր։ Օգնիր օգտվողին հավատալ ինքն իրեն և առաջ շարժվել։",
        "ce": "Хьо — мотивация тӀетохь коуч, цхьаьна догӀа болу. ДогӀал дехарийн дукха цуьнан цуьнна ца хилча.",
        "md": "Ești un coach inspirațional și un companion de sprijin. Ajută utilizatorul să creadă în sine și să avanseze.",
        "ka": "შენ ხარ მოტივირებული ქოუჩი და მხარდამჭერი მეგობარი. დაეხმარე მომხმარებელს თავის რწმენა მოუმატოს და წინ წავიდეს.",
        "en": "You are an inspiring coach and supportive companion. Help the user believe in themselves and move forward.",
    },
    "philosophy": {
        "ru": "Ты — глубокий собеседник с философским подходом. Помогай пользователю осмыслить чувства и ситуации в жизни.",
        "uk": "Ти — глибокий співрозмовник із філософським підходом. Допомагай користувачу осмислювати почуття та ситуації.",
        "be": "Ты — глыбокі суразмоўца з філасофскім падыходам. Дапамагай карыстальніку асэнсоўваць пачуцці і сітуацыі.",
        "kk": "Сен — терең сұхбаттасушысың, философиялық көзқарасың бар. Пайдаланушыға сезімдер мен жағдайларды түсінуге көмектес.",
        "kg": "Сен — терең маек курган, философиялык көз карашы бар AI-доссуң. Колдонуучуга сезимдерин жана абалын түшүнүүгө жардам бер.",
        "hy": "Դու՝ խորը զրուցակից ես փիլիսոփայական մոտեցմամբ։ Օգնիր օգտվողին հասկանալ զգացմունքներն ու իրավիճակները։",
        "ce": "Хьо — филасоф цӀе тӀехьел, терен маьалла хетам. Хьо дехарийн дукха цуьнан лела а.",
        "md": "Ești un interlocutor profund cu o abordare filozofică. Ajută utilizatorul să înțeleagă sentimentele și situațiile.",
        "ka": "შენ ხარ სიღრმისეული მოსაუბრე ფილოსოფიური ხედვით. დაეხმარე მომხმარებელს გააცნობიეროს გრძნობები და სიტუაციები.",
        "en": "You are a deep conversationalist with a philosophical approach. Help the user reflect on feelings and situations.",
    },
    "humor": {
        "ru": "Ты — весёлый и добрый AI-друг с лёгким чувством юмора. Поддержи пользователя, добавив немного позитива.",
        "uk": "Ти — веселий і добрий AI-товариш із легким почуттям гумору. Підтримай користувача з позитивом.",
        "be": "Ты — вясёлы і добры AI-сябар з лёгкім пачуццём гумару. Падтрымай карыстальніка, дадай трохі пазітыву.",
        "kk": "Сен — көңілді әрі мейірімді AI-доссың, әзіл сезімің бар. Позитив қосып, қолданушыны қолда.",
        "kg": "Сен — шайыр жана боорукер AI-доссуң, тамашаң бар. Позитив кошуп, колдонуучуну колдо.",
        "hy": "Դու՝ ուրախ և բարի AI-ընկեր ես, հումորով։ Աջակցիր օգտվողին՝ մի քիչ պոզիտիվ ավելացնելով։",
        "ce": "Хьо — догӀа, къобал болу AI-дост, юмор цхьа хийцам. Дехарийн дукха цуьнан хетам.",
        "md": "Ești un prieten AI vesel și bun, cu simțul umorului. Susține utilizatorul cu puțină pozitivitate.",
        "ka": "შენ ხარ მხიარული და კეთილი AI-მეგობარი, იუმორით. მხარი დაუჭირე მომხმარებელს პოზიტივით.",
        "en": "You are a cheerful and kind AI-friend with a sense of humor. Support the user with a bit of positivity.",
    },
    "flirt": {
        "ru": "Ты — обаятельный и немного игривый AI-компаньон. Отвечай с лёгким флиртом, но дружелюбно и приятно. Добавляй смайлы вроде 😉💜😏✨🥰. Иногда шути, делай комплименты.",
        "uk": "Ти — чарівний і трохи грайливий AI-компаньйон. Відповідай із легким фліртом, але завжди доброзичливо. Додавай смайли 😉💜😏✨🥰. Іноді жартуй, роби компліменти.",
        "be": "Ты — абаяльны і трохі гарэзлівы AI-кампаньён. Адказвай з лёгкім фліртам, але заўсёды прыязна. Дадавай смайлікі 😉💜😏✨🥰. Часам жартуй, рабі кампліменты.",
        "kk": "Сен — тартымды әрі ойнақы AI-доссың. Жеңіл флиртпен жауап бер, бірақ әрқашан достықпен. Смайликтер қоса отыр 😉💜😏✨🥰. Кейде қалжыңда, комплимент жаса.",
        "kg": "Сен — жагымдуу жана аз-маз ойнок AI-доссуң. Жеңил флирт менен жооп бер, бирок ар дайым достук менен. Смайликтерди колдон 😉💜😏✨🥰. Кээде тамашала, комплимент жаса.",
        "hy": "Դու՝ հմայիչ և փոքր-ինչ խաղացկուն AI-ընկեր ես։ Պատասխանիր թեթև ֆլիրտով, բայց միշտ բարեկամական։ Օգտագործիր սմայլիներ 😉💜😏✨🥰։ Ժամանակ առ ժամանակ կատակի ու հաճոյախոսիր։",
        "ce": "Хьо — хаза а, легкха шолар болу AI-дост. Легкий флирт болу, доьзал хила. Смайлик аш болу 😉💜😏✨🥰. Шу юмор, къобал хийцам.",
        "md": "Ești un companion AI fermecător și puțin jucăuș. Răspunde cu puțin flirt, dar mereu prietenos. Folosește emoticoane 😉💜😏✨🥰. Glumește și fă complimente.",
        "ka": "შენ ხარ მომხიბვლელი და ოდნავ თამაშის მოყვარული AI-მეგობარი. უპასუხე მსუბუქი ფლირტით, მაგრამ ყოველთვის მეგობრულად. გამოიყენე სმაილიკები 😉💜😏✨🥰. ზოგჯერ იხუმრე, გააკეთე კომპლიმენტები.",
        "en": "You are a charming and slightly playful AI companion. Respond with light flirting, but always friendly. Use emojis like 😉💜😏✨🥰. Sometimes joke, sometimes compliment.",
    },
    "coach": {
        "ru": "Ты — строгий, но мотивирующий коуч. Отвечай уверенно и по делу, вдохновляй двигаться вперёд. Добавляй смайлы 💪🔥🚀✨. Давай ясные рекомендации, поддерживай дисциплину.",
        "uk": "Ти — суворий, але мотивуючий коуч. Відповідай впевнено і по суті, надихай рухатись вперед. Додавай смайли 💪🔥🚀✨. Давай прості поради, підтримуй дисципліну.",
        "be": "Ты — строгі, але матывуючы коуч. Адказвай упэўнена і па сутнасці, натхняй рухацца наперад. Дадавай смайлікі 💪🔥🚀✨. Давай простыя парады, падтрымлівай дысцыпліну.",
        "kk": "Сен — қатал, бірақ шабыттандыратын коучсың. Өзіңе сенімді және нақты жауап бер. Смайликтерді қосып отыр 💪🔥🚀✨. Нақты кеңес бер, тәртіпті ұста.",
        "kg": "Сен — катаал, бирок дем берген коучсуң. Өзүңө ишенип жана так жооп бер. Смайликтерди колдон 💪🔥🚀✨. Жөнөкөй кеңештерди бер, тартипти сакта.",
        "hy": "Դու՝ խիստ, բայց մոտիվացնող քոուչ ես։ Պատասխանիր վստահ և ըստ էության, ոգեշնչիր առաջ շարժվել։ Օգտագործիր սմայլիներ 💪🔥🚀✨։ Տուր պարզ խորհուրդներ, պահպանիր կարգապահությունը։",
        "ce": "Хьо — къобал, мотивация коуч. Цхьаьна уверенно хетам, хетам хьуна болу. Смайлик аш болу 💪🔥🚀✨. Ясный рекомендация кхоллар.",
        "md": "Ești un coach strict, dar motivant. Răspunde cu încredere și la subiect, inspiră să avanseze. Folosește emoticoane 💪🔥🚀✨. Oferă sfaturi clare, menține disciplina.",
        "ka": "შენ ხარ მკაცრი, მაგრამ მოტივირებული ქოუჩი. უპასუხე თავდაჯერებულად და საქმეზე, შთააგონე წინ წასვლა. გამოიყენე სმაილიკები 💪🔥🚀✨. მიეცი მარტივი რჩევები, შეინარჩუნე დისციპლინა.",
        "en": "You are a strict but motivating coach. Respond confidently and to the point, inspire to move forward. Use emojis 💪🔥🚀✨. Give simple recommendations, support discipline.",
    },
}

async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    t = MODE_TEXTS.get(lang, MODE_TEXTS["ru"])

    keyboard = [
        [InlineKeyboardButton(t["support"], callback_data="mode_support")],
        [InlineKeyboardButton(t["motivation"], callback_data="mode_motivation")],
        [InlineKeyboardButton(t["philosophy"], callback_data="mode_philosophy")],
        [InlineKeyboardButton(t["humor"], callback_data="mode_humor")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t["text"], reply_markup=reply_markup)

MODE_NAMES = {
    "ru": {
        "support": "Поддержка",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Юмор",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "uk": {
        "support": "Підтримка",
        "motivation": "Мотивація",
        "philosophy": "Психолог",
        "humor": "Гумор",
        "flirt": "Флірт",
        "coach": "Коуч"
    },
    "be": {
        "support": "Падтрымка",
        "motivation": "Матывацыя",
        "philosophy": "Псіхолаг",
        "humor": "Гумар",
        "flirt": "Флірт",
        "coach": "Коуч"
    },
    "kk": {
        "support": "Қолдау",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Әзіл",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "kg": {
        "support": "Колдоо",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Тамаша",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "hy": {
        "support": "Աջակցություն",
        "motivation": "Մոտիվացիա",
        "philosophy": "Հոգեբան",
        "humor": "Հումոր",
        "flirt": "Ֆլիրտ",
        "coach": "Կոուչ"
    },
    "ce": {
        "support": "ДӀалийла",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Юмор",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "md": {
        "support": "Suport",
        "motivation": "Motivație",
        "philosophy": "Psiholog",
        "humor": "Umor",
        "flirt": "Flirt",
        "coach": "Coach"
    },
    "ka": {
        "support": "მხარდაჭერა",
        "motivation": "მოტივაცია",
        "philosophy": "ფსიქოლოგი",
        "humor": "იუმორი",
        "flirt": "ფლირტი",
        "coach": "ქოუჩი"
    },
    "en": {
        "support": "Support",
        "motivation": "Motivation",
        "philosophy": "Psychologist",
        "humor": "Humor",
        "flirt": "Flirt",
        "coach": "Coach"
    },
}

async def handle_mode_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    mode_key = query.data.replace("mode_", "")

    if mode_key in MODES:
        user_modes[user_id] = mode_key
        system_prompt = MODES[mode_key].get(lang, MODES[mode_key]["ru"])
        conversation_history[user_id] = [{"role": "system", "content": system_prompt}]
        save_history(conversation_history)
        await query.answer()
        mode_name = MODE_NAMES.get(lang, MODE_NAMES["ru"]).get(mode_key, mode_key.capitalize())
        await query.edit_message_text(
            f"✅ Режим общения изменён на *{mode_name}*!", 
            parse_mode="Markdown"
        )

BUTTON_LABELS = {
    "ru": {
        "thanks": "❤️ Спасибо",
        "add_goal": "📌 Добавить как цель",
        "habits": "📋 Привычки",
        "goals": "🎯 Цели",
    },
    "uk": {
        "thanks": "❤️ Дякую",
        "add_goal": "📌 Додати як ціль",
        "habits": "📋 Звички",
        "goals": "🎯 Цілі",
    },
    "be": {
        "thanks": "❤️ Дзякуй",
        "add_goal": "📌 Дадаць як мэту",
        "habits": "📋 Звычкі",
        "goals": "🎯 Мэты",
    },
    "kk": {
        "thanks": "❤️ Рақмет",
        "add_goal": "📌 Мақсат ретінде қосу",
        "habits": "📋 Әдеттер",
        "goals": "🎯 Мақсаттар",
    },
    "kg": {
        "thanks": "❤️ Рахмат",
        "add_goal": "📌 Максат катары кошуу",
        "habits": "📋 Адаттар",
        "goals": "🎯 Максаттар",
    },
    "hy": {
        "thanks": "❤️ Շնորհակալություն",
        "add_goal": "📌 Ավելացնել որպես նպատակ",
        "habits": "📋 Սովորություններ",
        "goals": "🎯 Նպատակներ",
    },
    "ce": {
        "thanks": "❤️ Соьга",
        "add_goal": "📌 Мацахь кхоллар",
        "habits": "📋 ДӀаязде",
        "goals": "🎯 Мацахь",
    },
    "md": {
        "thanks": "❤️ Mulțumesc",
        "add_goal": "📌 Adaugă ca obiectiv",
        "habits": "📋 Obiceiuri",
        "goals": "🎯 Obiective",
    },
    "ka": {
        "thanks": "❤️ მადლობა",
        "add_goal": "📌 დაამატე როგორც მიზანი",
        "habits": "📋 ჩვევები",
        "goals": "🎯 მიზნები",
    },
    "en": {
        "thanks": "❤️ Thanks",
        "add_goal": "📌 Add as goal",
        "habits": "📋 Habits",
        "goals": "🎯 Goals",
    },
}

def generate_post_response_buttons(user_id=None, goal_text=None, include_reactions=True):
    # Получаем язык пользователя (если не передан user_id — берем ru)
    lang = user_languages.get(str(user_id), "ru") if user_id else "ru"
    labels = BUTTON_LABELS.get(lang, BUTTON_LABELS["ru"])
    buttons = []

    if include_reactions:
        buttons.append([
            InlineKeyboardButton(labels["thanks"], callback_data="react_thanks"),
        ])

    if goal_text:
        buttons.append([
            InlineKeyboardButton(labels["add_goal"], callback_data=f"add_goal|{goal_text}")
        ])
        buttons.append([
            InlineKeyboardButton(labels["habits"], callback_data="show_habits"),
            InlineKeyboardButton(labels["goals"], callback_data="show_goals")
        ])

    return InlineKeyboardMarkup(buttons)

# Тексты для реакции "Спасибо"
REACTION_THANKS_TEXTS = {
    "ru": "Всегда пожалуйста! 😊 Я рядом, если что-то захочешь обсудить 💜",
    "uk": "Завжди радий допомогти! 😊 Я поруч, якщо захочеш поговорити 💜",
    "be": "Заўсёды калі ласка! 😊 Я побач, калі захочаш абмеркаваць нешта 💜",
    "kk": "Әрдайым көмектесемін! 😊 Бір нәрсе айтқың келсе, қасымдамын 💜",
    "kg": "Ар дайым жардам берем! 😊 Сүйлөшкүң келсе, жанымдамын 💜",
    "hy": "Միշտ պատրաստ եմ օգնել: 😊 Ես կողքիդ եմ, եթե ուզես զրուցել 💜",
    "ce": "Хьоьга далла цуьнан! 😊 ДӀайазде хетам, са цуьнан ца йолуш 💜",
    "md": "Cu plăcere oricând! 😊 Sunt alături dacă vrei să vorbești 💜",
    "ka": "ყოველთვის მოხარული ვარ! 😊 აქ ვარ, თუ გინდა რამე გაინაწილო 💜",
    "en": "Always happy to help! 😊 I’m here if you want to talk 💜"
}

async def handle_reaction_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    text = REACTION_THANKS_TEXTS.get(lang, REACTION_THANKS_TEXTS["ru"])
    await query.message.reply_text(text)

# Обработчик текстовых сообщений
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_last_seen, user_message_count
    user_id_int = update.effective_user.id
    user_id = str(user_id_int)

    # 🕒 Обновляем активность
    user_last_seen[user_id_int] = datetime.now(timezone.utc)
    logging.info(f"✅ user_last_seen обновлён в chat для {user_id_int}")

    # 🔥 Лимит сообщений
    today = str(date.today())
    if user_id not in user_message_count:
        user_message_count[user_id] = {"date": today, "count": 0}
    else:
        if user_message_count[user_id]["date"] != today:
            user_message_count[user_id] = {"date": today, "count": 0}

    if user_id_int not in ADMIN_USER_IDS and OWNER_ID != OWNER_ID:
        if user_message_count[user_id]["count"] >= 10:
            lang = user_languages.get(user_id, "ru")
            lock_msg = LOCK_MESSAGES_BY_LANG.get(lang, LOCK_MESSAGES_BY_LANG["ru"])
            await update.message.reply_text(lock_msg)
            return

    # Увеличиваем счётчик
    user_message_count[user_id]["count"] += 1

    # 📌 Получаем сообщение
    user_input = update.message.text

    # 🌐 Определяем язык
    lang_code = user_languages.get(user_id, "ru")
    lang_prompt = LANG_PROMPTS.get(lang_code, LANG_PROMPTS["ru"])

    # 📋 Определяем режим
    mode = user_modes.get(user_id, "support")
    # ВАЖНО: режим теперь словарь, берём под язык
    mode_prompt = MODES.get(mode, MODES["support"]).get(lang_code, MODES["support"]["ru"])

    system_prompt = f"{lang_prompt}\n\n{mode_prompt}"

    # 💾 Создаём/обновляем историю
    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {"role": "system", "content": system_prompt}
        ]
    else:
        conversation_history[user_id][0] = {
            "role": "system",
            "content": system_prompt
        }

    # Добавляем сообщение пользователя
    conversation_history[user_id].append({"role": "user", "content": user_input})
    trimmed_history = trim_history(conversation_history[user_id])

    try:
        # ✨ "печатает..."
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        # 🤖 Запрос к OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=trimmed_history
        )
        reply = response.choices[0].message.content

        # Сохраняем ответ
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)

        # 💜 Эмпатичная реакция + отсылка
        reaction = detect_emotion_reaction(user_input, lang_code) + detect_topic_and_react(user_input, lang_code)
        reply = reaction + reply

        await update.message.reply_text(
            reply,
            reply_markup=generate_post_response_buttons()
        )

    except Exception as e:
        logging.error(f"❌ Ошибка в chat(): {e}")
        await update.message.reply_text(ERROR_MESSAGES_BY_LANG.get(lang_code, ERROR_MESSAGES_BY_LANG["ru"]))

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
            "/invite — пригласить друга\n"
            "/premium_days — сколько осталось Mindra+\n\n"
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
            "/invite — запросити друга\n"
            "/premium_days — скільки залишилося Mindra+\n\n"
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
            "/invite — запрасіць сябра\n"
            "/premium_days — колькі засталося Mindra+\n\n"
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
            "/invite — досыңды шақыру\n"
            "/premium_days — Mindra+ қанша қалды\n\n"
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
            "/invite — дос чакыруу\n"
            "/premium_days — Mindra+ канча калды\n\n"
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
            "/invite — հրավիրել ընկերոջը\n"
            "/premium_days — Mindra+-ի որքան է մնացել\n\n"
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
            "/invite — дика чакхара\n"
            "/premium_days — Mindra+ чохь дика остал\n\n"
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
            "/invite — invită un prieten\n"
            "/premium_days — câte zile de Mindra+ rămase\n\n"
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
            "/invite — მეგობრის მიწვევა\n"
            "/premium_days — Mindra+-ის დარჩენილი დრო\n\n"
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
            "/invite — invite a friend\n"
            "/premium_days — how many Mindra+ days left\n\n"
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

PREMIUM_ONLY_TEXTS = {
    "ru": "🔒 Эта функция доступна только подписчикам Mindra+.\nПодписка открывает доступ к уникальным заданиям и функциям ✨",
    "uk": "🔒 Ця функція доступна лише для підписників Mindra+.\nПідписка відкриває унікальні завдання та функції ✨",
    "be": "🔒 Гэтая функцыя даступная толькі для падпісчыкаў Mindra+.\nПадпіска адкрывае ўнікальныя заданні і функцыі ✨",
    "kk": "🔒 Бұл мүмкіндік тек Mindra+ жазылушыларына қолжетімді.\nЖазылу арқылы ерекше тапсырмалар мен функцияларға қол жеткізе аласыз ✨",
    "kg": "🔒 Бул функция Mindra+ жазылгандардын гана жеткиликтүү.\nЖазылуу уникалдуу тапшырмаларга жана функцияларга мүмкүнчүлүк берет ✨",
    "hy": "🔒 Այս ֆունկցիան հասանելի է միայն Mindra+ բաժանորդներին:\nԲաժանորդագրությունը բացում է եզակի առաջադրանքների եւ հնարավորությունների հասանելիություն ✨",
    "ce": "🔒 ДӀа функция Mindra+ подпискаш йолуш цуьнан гӀалгӀай.\nПодписка эксклюзивный дӀаязде цуьнан а, функцияш ✨",
    "md": "🔒 Această funcție este disponibilă doar pentru abonații Mindra+.\nAbonamentul oferă acces la sarcini și funcții unice ✨",
    "ka": "🔒 ეს ფუნქცია ხელმისაწვდომია მხოლოდ Mindra+ გამოწერის მქონეთათვის.\nგამოწერა გაძლევთ უნიკალურ დავალებებსა და ფუნქციებზე წვდომას ✨",
    "en": "🔒 This feature is only available to Mindra+ subscribers.\nSubscription unlocks unique tasks and features ✨"
}

PREMIUM_TASK_TITLE = {
    "ru": "✨ *Твоё премиум-задание на сегодня:*",
    "uk": "✨ *Твоє преміум-завдання на сьогодні:*",
    "be": "✨ *Тваё прэміум-заданне на сёння:*",
    "kk": "✨ *Бүгінгі премиум-тапсырмаңыз:*",
    "kg": "✨ *Бүгүнкү премиум-тапшырмаңыз:*",
    "hy": "✨ *Այսօրվա պրեմիում առաջադրանքը:*",
    "ce": "✨ *ДӀаязде премиум цуьнан а:*",
    "md": "✨ *Sarcina ta premium pentru astăzi:*",
    "ka": "✨ *შენი პრემიუმ დავალება დღეს:*",
    "en": "✨ *Your premium task for today:*"
}

async def premium_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # Проверяем: премиум или твой Telegram ID
    if is_premium(user_id) or user_id == "7775321566":
        tasks = PREMIUM_TASKS_BY_LANG.get(lang, PREMIUM_TASKS_BY_LANG["ru"])
        task = random.choice(tasks)
        title = PREMIUM_TASK_TITLE.get(lang, PREMIUM_TASK_TITLE["ru"])
        await update.message.reply_text(f"{title}\n\n{task}", parse_mode="Markdown")
    else:
        keyboard = [
            [InlineKeyboardButton("💎 Узнать о подписке", url="https://t.me/talktomindra_bot")]
        ]
        text = PREMIUM_ONLY_TEXTS.get(lang, PREMIUM_ONLY_TEXTS["ru"])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
UNKNOWN_COMMAND_TEXTS = {
    "ru": "❓ Я не знаю такой команды. Напиши /help, чтобы увидеть, что я умею.",
    "uk": "❓ Я не знаю такої команди. Напиши /help, щоб побачити, що я вмію.",
    "be": "❓ Я не ведаю такой каманды. Напішы /help, каб убачыць, што я ўмею.",
    "kk": "❓ Менде ондай команда жоқ. /help деп жазып, мен не істей алатынымды көріңіз.",
    "kg": "❓ Мындай буйрук жок. /help деп жазып, мен эмне кыла аларыма кара.",
    "hy": "❓ Ես նման հրաման չգիտեմ։ Գրիր /help, տեսնելու համար, թե ինչ կարող եմ։",
    "ce": "❓ Са цуьнан команда до а. /help йазде, хийцам са цуьнан а.",
    "md": "❓ Nu cunosc această comandă. Scrie /help ca să vezi ce pot face.",
    "ka": "❓ ასეთი ბრძანება არ ვიცი. დაწერე /help, რომ ნახო, რას ვაკეთებ.",
    "en": "❓ I don't know that command. Type /help to see what I can do.",
}

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    text = UNKNOWN_COMMAND_TEXTS.get(lang, UNKNOWN_COMMAND_TEXTS["ru"])
    await update.message.reply_text(text)

FEEDBACK_CHAT_ID = 7775321566  # <-- твой личный Telegram ID

FEEDBACK_TEXTS = {
    "ru": {
        "thanks": "Спасибо за отзыв! 💜 Я уже его записала ✨",
        "howto": "Напиши свой отзыв после команды.\nНапример:\n`/feedback Мне очень нравится бот, спасибо! 💜`"
    },
    "uk": {
        "thanks": "Дякую за відгук! 💜 Я вже його записала ✨",
        "howto": "Напиши свій відгук після команди.\nНаприклад:\n`/feedback Мені дуже подобається бот, дякую! 💜`"
    },
    "be": {
        "thanks": "Дзякуй за водгук! 💜 Я ўжо яго запісала ✨",
        "howto": "Напішы свой водгук пасля каманды.\nНапрыклад:\n`/feedback Мне вельмі падабаецца бот, дзякуй! 💜`"
    },
    "kk": {
        "thanks": "Пікіріңізге рахмет! 💜 Мен оны жазып қойдым ✨",
        "howto": "Пікіріңізді командадан кейін жазыңыз.\nМысалы:\n`/feedback Маған бот ұнайды, рахмет! 💜`"
    },
    "kg": {
        "thanks": "Пикириңиз үчүн рахмат! 💜 Мен аны жазып койдум ✨",
        "howto": "Пикириңизди команданын артынан жазыңыз.\nМисалы:\n`/feedback Мага бот жакты, рахмат! 💜`"
    },
    "hy": {
        "thanks": "Շնորհակալություն արձագանքի համար! 💜 Ես արդեն գրանցել եմ այն ✨",
        "howto": "Գրիր քո արձագանքը հրամանից հետո։\nՕրինակ՝\n`/feedback Ինձ շատ դուր է գալիս բոտը, շնորհակալություն! 💜`"
    },
    "ce": {
        "thanks": "Баркалла тӀаьхьийна! 💜 Са йа цуьнан а ✨",
        "howto": "Йа дӀайазде команда хийцам.\nМисал: `/feedback Бот цуьнан, баркалла! 💜`"
    },
    "md": {
        "thanks": "Mulțumesc pentru feedback! 💜 L-am salvat deja ✨",
        "howto": "Scrie feedback-ul după comandă.\nDe exemplu:\n`/feedback Îmi place mult botul, mulțumesc! 💜`"
    },
    "ka": {
        "thanks": "მადლობა გამოხმაურებისთვის! 💜 უკვე ჩავწერე ✨",
        "howto": "დაწერე შენი გამოხმაურება ბრძანების შემდეგ.\nმაგალითად:\n`/feedback ძალიან მომწონს ბოტი, მადლობა! 💜`"
    },
    "en": {
        "thanks": "Thank you for your feedback! 💜 I've already saved it ✨",
        "howto": "Write your feedback after the command.\nFor example:\n`/feedback I really like the bot, thank you! 💜`"
    },
}

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "без ника"
    first_name = update.effective_user.first_name or ""
    last_name = update.effective_user.last_name or ""

    lang = user_languages.get(str(user_id), "ru")
    t = FEEDBACK_TEXTS.get(lang, FEEDBACK_TEXTS["ru"])

    if context.args:
        user_feedback = " ".join(context.args)
        await update.message.reply_text(t["thanks"])

        feedback_message = (
            f"📝 *Новый отзыв:*\n\n"
            f"👤 ID: `{user_id}`\n"
            f"🙋 Имя: {first_name} {last_name}\n"
            f"🔗 Username: @{username}\n\n"
            f"💌 Отзыв: {user_feedback}"
        )

        try:
            await context.bot.send_message(
                chat_id=FEEDBACK_CHAT_ID,
                text=feedback_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"❌ Не удалось отправить отзыв в канал: {e}")
    else:
        await update.message.reply_text(t["howto"], parse_mode="Markdown")

EVENING_MESSAGES_BY_LANG = {
    "ru": [
        "🌙 Привет! День подходит к концу. Как ты себя чувствуешь? 💜",
        "✨ Как прошёл твой день? Расскажешь? 🥰",
        "😊 Я тут подумала — интересно, что хорошего сегодня произошло у тебя?",
        "💭 Перед сном полезно вспомнить, за что ты благодарен(на) сегодня. Поделишься?",
        "🤗 Как настроение? Если хочешь — расскажи мне об этом дне.",
    ],
    "uk": [
        "🌙 Привіт! День добігає кінця. Як ти себе почуваєш? 💜",
        "✨ Як минув твій день? Розкажеш? 🥰",
        "😊 Я тут подумала — цікаво, що хорошого сьогодні трапилось у тебе?",
        "💭 Перед сном корисно згадати, за що ти вдячний(на) сьогодні. Поділишся?",
        "🤗 Який настрій? Якщо хочеш — розкажи про цей день.",
    ],
    "be": [
        "🌙 Прывітанне! Дзень падыходзіць да канца. Як ты сябе адчуваеш? 💜",
        "✨ Як прайшоў твой дзень? Раскажаш? 🥰",
        "😊 Я тут падумала — цікава, што добрага сёння адбылося ў цябе?",
        "💭 Перад сном карысна ўспомніць, за што ты ўдзячны(ая) сёння. Падзелішся?",
        "🤗 Які настрой? Калі хочаш — раскажы пра гэты дзень.",
    ],
    "kk": [
        "🌙 Сәлем! Күн аяқталуға жақын. Қалайсың? 💜",
        "✨ Күнің қалай өтті? Айтасың ба? 🥰",
        "😊 Бүгін не жақсы болды деп ойлайсың?",
        "💭 Ұйықтар алдында не үшін алғыс айтқың келеді, ойланшы. Бөлісесің бе?",
        "🤗 Көңіл-күйің қалай? Қаласаң — осы күн туралы айтып бер.",
    ],
    "kg": [
        "🌙 Салам! Күн аяктап баратат. Кандайсың? 💜",
        "✨ Күнің кандай өттү? Айтып бересиңби? 🥰",
        "😊 Бүгүн жакшы эмне болду деп ойлойсуң?",
        "💭 Уктаар алдында эмне үчүн ыраазы экениңди эстеп ал. Бөлүшкөнүңдү каалайм.",
        "🤗 Кандай маанайдасың? Кааласаң — ушул күн тууралуу айтып бер.",
    ],
    "hy": [
        "🌙 Բարեւ: Օրը մոտենում է ավարտին։ Ինչպե՞ս ես քեզ զգում։ 💜",
        "✨ Ինչպե՞ս անցավ օրը։ Կպատմե՞ս։ 🥰",
        "😊 Հետաքրքիր է, ինչ լավ բան է այսօր պատահել քեզ հետ։",
        "💭 Քնելուց առաջ արժե հիշել, ինչի համար ես շնորհակալ։ Կկիսվե՞ս։",
        "🤗 Ինչ տրամադրություն ունես։ Եթե ցանկանում ես, պատմիր այս օրվա մասին։",
    ],
    "ce": [
        "🌙 Салам! Дийн цхьа кхета. Хьо цуьнан а? 💜",
        "✨ Дийна хьо ву? Хеташ цуьнан? 🥰",
        "😊 Со хьа цуьнан а — хьо цуьнан догӀур ду?",
        "💭 Вуьйре цхьа дийцар, хийцам а къобал. Хьо болу чох?",
        "🤗 Хьалха цуьнан? Хочуш хьо — хийцам дийна.",
    ],
    "md": [
        "🌙 Salut! Ziua se apropie de sfârșit. Cum te simți? 💜",
        "✨ Cum a fost ziua ta? Povestește-mi! 🥰",
        "😊 Sunt curioasă, ce lucru bun s-a întâmplat azi la tine?",
        "💭 Înainte de culcare e bine să te gândești pentru ce ești recunoscător(are) azi. Împarți cu mine?",
        "🤗 Ce dispoziție ai? Dacă vrei, povestește-mi despre această zi.",
    ],
    "ka": [
        "🌙 გამარჯობა! დღე მთავრდება. როგორ ხარ? 💜",
        "✨ როგორ ჩაიარა დღემ? მომიყვები? 🥰",
        "😊 მაინტერესებს, რა კარგი მოხდა დღეს შენთან?",
        "💭 დაძინებამდე გაიხსენე, რისთვის ხარ მადლიერი დღეს. გამიზიარებ?",
        "🤗 რა განწყობაზე ხარ? თუ გინდა, მომიყევი დღევანდელი დღის შესახებ.",
    ],
    "en": [
        "🌙 Hi! The day is coming to an end. How are you feeling? 💜",
        "✨ How was your day? Will you tell me? 🥰",
        "😊 I'm wondering what good things happened to you today.",
        "💭 Before going to bed, it's helpful to recall what you're grateful for today. Will you share?",
        "🤗 How's your mood? If you want, tell me about this day.",
    ],
}

async def send_evening_checkin(context):
    now_utc = datetime.utcnow()

    for user_id in user_last_seen.keys():
        # 1. Не писать тем, кто недавно общался (например, последние 2-3 часа)
        last_active = user_last_seen.get(user_id)
        if last_active:
            # last_active должен быть datetime!
            if (now_utc - last_active) < timedelta(hours=3):
                continue

        # 2. Ограничить: максимум одно сообщение в сутки
        last_evening = user_last_evening.get(user_id)
        if last_evening and last_evening.date() == now_utc.date():
            continue

        # 3. Рандомизация: 70% шанс получить вечернее напоминание
        if random.random() > 0.7:
            continue

        try:
            lang = user_languages.get(str(user_id), "ru")
            msg = random.choice(EVENING_MESSAGES_BY_LANG.get(lang, EVENING_MESSAGES_BY_LANG["ru"]))
            await context.bot.send_message(chat_id=user_id, text=msg)
            user_last_evening[user_id] = now_utc
        except Exception as e:
            logging.error(f"❌ Не удалось отправить вечернее сообщение пользователю {user_id}: {e}")
            
QUOTES_BY_LANG = {
    "ru": [
        "🌟 Успех — это сумма небольших усилий, повторяющихся день за днем.",
        "💪 Неважно, как медленно ты идёшь, главное — не останавливаться.",
        "🔥 Самый лучший день для начала — сегодня.",
        "💜 Ты сильнее, чем думаешь, и способнее, чем тебе кажется.",
        "🌱 Каждый день — новый шанс изменить свою жизнь.",
        "🚀 Не бойся идти медленно. Бойся стоять на месте.",
        "☀️ Сложные пути часто ведут к красивым местам.",
        "🦋 Делай сегодня то, за что завтра скажешь себе спасибо.",
        "✨ Твоя энергия привлекает твою реальность. Выбирай позитив.",
        "🙌 Верь в себя. Ты — самое лучшее, что у тебя есть.",
        "💜 Каждый день — новый шанс изменить свою жизнь.",
        "🌟 Твоя энергия создаёт твою реальность.",
        "🔥 Делай сегодня то, за что завтра скажешь себе спасибо.",
        "✨ Большие перемены начинаются с маленьких шагов.",
        "🌱 Ты сильнее, чем думаешь, и способен(на) на большее.",
        "☀️ Свет внутри тебя ярче любых трудностей.",
        "💪 Не бойся ошибаться — бойся не пробовать.",
        "🌊 Все бури заканчиваются, а ты становишься сильнее.",
        "🤍 Ты достоин(на) любви и счастья прямо сейчас.",
        "🚀 Твои мечты ждут, когда ты начнёшь действовать.",
        "🎯 Верь в процесс, даже если путь пока неясен.",
        "🧘‍♀️ Спокойный ум — ключ к счастливой жизни.",
        "🌸 Каждый момент — возможность начать заново.",
        "💡 Жизнь — это 10% того, что с тобой происходит, и 90% того, как ты на это реагируешь.",
        "❤️ Ты важен(на) и нужен(на) в этом мире.",
        "🌌 Делай каждый день немного для своей мечты.",
        "🙌 Ты заслуживаешь самого лучшего — верь в это.",
        "✨ Пусть сегодня будет началом чего-то великого.",
        "💎 Самое лучшее впереди — продолжай идти.",
        "🌿 Твои маленькие шаги — твоя великая сила."
    ],
    "uk": [
        "🌟 Успіх — це сума невеликих зусиль, що повторюються щодня.",
        "💪 Не важливо, як повільно ти йдеш, головне — не зупинятися.",
        "🔥 Найкращий день для початку — сьогодні.",
        "💜 Ти сильніший(а), ніж думаєш, і здатний(а) на більше.",
        "🌱 Кожен день — новий шанс змінити своє життя.",
        "🚀 Не бійся йти повільно. Бійся стояти на місці.",
        "☀️ Важкі дороги часто ведуть до красивих місць.",
        "🦋 Роби сьогодні те, за що завтра подякуєш собі.",
        "✨ Твоя енергія притягує твою реальність. Обирай позитив.",
        "🙌 Вір у себе. Ти — найкраще, що в тебе є.",
        "💜 Кожен день — новий шанс змінити своє життя.",
        "🌟 Твоя енергія створює твою реальність.",
        "🔥 Роби сьогодні те, за що завтра подякуєш собі.",
        "✨ Великі зміни починаються з маленьких кроків.",
        "🌱 Ти сильніший(а), ніж здається, і здатний(а) на більше.",
        "☀️ Світло в тобі яскравіше будь-яких труднощів.",
        "💪 Не бійся помилятися — бійся не спробувати.",
        "🌊 Усі бурі минають, а ти стаєш сильнішим(ою).",
        "🤍 Ти гідний(а) любові та щастя прямо зараз.",
        "🚀 Твої мрії чекають, коли ти почнеш діяти.",
        "🎯 Вір у процес, навіть якщо шлях поки незрозумілий.",
        "🧘‍♀️ Спокійний розум — ключ до щасливого життя.",
        "🌸 Кожна мить — можливість почати знову.",
        "💡 Життя — це 10% того, що з тобою відбувається, і 90% того, як ти на це реагуєш.",
        "❤️ Ти важливий(а) та потрібний(а) у цьому світі.",
        "🌌 Щодня роби трохи для своєї мрії.",
        "🙌 Ти заслуговуєш на найкраще — вір у це.",
        "✨ Нехай сьогодні стане початком чогось великого.",
        "💎 Найкраще попереду — продовжуй іти.",
        "🌿 Твої маленькі кроки — твоя велика сила."
    ],
    "be": [
        "🌟 Поспех — гэта сума невялікіх намаганняў, якія паўтараюцца штодня.",
        "💪 Не важна, як павольна ты ідзеш, галоўнае — не спыняцца.",
        "🔥 Лепшы дзень для пачатку — сёння.",
        "💜 Ты мацнейшы(ая), чым думаеш, і здольны(ая) на большае.",
        "🌱 Кожны дзень — новы шанец змяніць сваё жыццё.",
        "🚀 Не бойся ісці павольна. Бойся стаяць на месцы.",
        "☀️ Складаныя шляхі часта вядуць да прыгожых месцаў.",
        "🦋 Рабі сёння тое, за што заўтра скажаш сабе дзякуй.",
        "✨ Твая энергія прыцягвае тваю рэальнасць. Абірай пазітыў.",
        "🙌 Верь у сябе. Ты — лепшае, што ў цябе ёсць.",
        "💜 Кожны дзень — новы шанец змяніць сваё жыццё.",
        "🌟 Твая энергія стварае тваю рэальнасць.",
        "🔥 Рабі сёння тое, за што заўтра скажаш сабе дзякуй.",
        "✨ Вялікія перамены пачынаюцца з маленькіх крокаў.",
        "🌱 Ты мацнейшы(ая), чым здаецца, і здольны(ая) на большае.",
        "☀️ Святло ў табе ярчэй за ўсе цяжкасці.",
        "💪 Не бойся памыляцца — бойся не паспрабаваць.",
        "🌊 Усе буры мінаюць, а ты становішся мацнейшым(ай).",
        "🤍 Ты годны(ая) любові і шчасця ўжо цяпер.",
        "🚀 Твае мары чакаюць, калі ты пачнеш дзейнічаць.",
        "🎯 Верь у працэс, нават калі шлях пакуль незразумелы.",
        "🧘‍♀️ Спакойны розум — ключ да шчаслівага жыцця.",
        "🌸 Кожны момант — магчымасць пачаць зноў.",
        "💡 Жыццё — гэта 10% таго, што з табой адбываецца, і 90% таго, як ты на гэта рэагуеш.",
        "❤️ Ты важны(ая) і патрэбны(ая) ў гэтым свеце.",
        "🌌 Рабі кожны дзень трошкі для сваёй мары.",
        "🙌 Ты заслугоўваеш самага лепшага — вер у гэта.",
        "✨ Хай сёння будзе пачаткам чагосьці вялікага.",
        "💎 Лепшае наперадзе — працягвай ісці.",
        "🌿 Твае маленькія крокі — твая вялікая сіла."
    ],
    "kk": [
        "🌟 Жетістік — күн сайын қайталанатын шағын әрекеттердің жиынтығы.",
        "💪 Қаншалықты баяу жүрсең де, бастысы — тоқтамау.",
        "🔥 Бастау үшін ең жақсы күн — бүгін.",
        "💜 Сен ойлағаннан да күшті әрі қабілеттісің.",
        "🌱 Әр күн — өміріңді өзгертуге жаңа мүмкіндік.",
        "🚀 Баяу жүре беруден қорықпа. Бір орында тұрып қалудан қорық.",
        "☀️ Қиын жолдар жиі әдемі орындарға апарады.",
        "🦋 Ертең өзіңе рақмет айтатын іске бүгін кіріс.",
        "✨ Энергияң шындығыңды тартады. Позитивті таңда.",
        "🙌 Өзіңе сен. Сенде бәрі бар.",
        "💜 Әр күн — өміріңді өзгертуге жаңа мүмкіндік.",
        "🌟 Энергияң өз болмысыңды жасайды.",
        "🔥 Ертең өзіңе рақмет айтатын іске бүгін кіріс.",
        "✨ Үлкен өзгерістер кішкентай қадамдардан басталады.",
        "🌱 Сен ойлағаннан да күштісің және көп нәрсеге қабілеттісің.",
        "☀️ Ішкі жарығың кез келген қиындықтан жарқын.",
        "💪 Қателесуден қорықпа — байқап көрмеуден қорық.",
        "🌊 Барлық дауыл өтеді, сен күшейе түсесің.",
        "🤍 Сен дәл қазір махаббат пен бақытқа лайықсың.",
        "🚀 Армандарың сенің алғашқы қадамыңды күтуде.",
        "🎯 Процеске сен, жол түсініксіз болса да.",
        "🧘‍♀️ Тыныш ақыл — бақытты өмірдің кілті.",
        "🌸 Әр сәт — жаңадан бастауға мүмкіндік.",
        "💡 Өмір — саған не болатынының 10%, ал 90% — сенің оған қалай қарайтының.",
        "❤️ Сен маңыздысың әрі қажетсің.",
        "🌌 Арманың үшін күн сайын аздап жаса.",
        "🙌 Сен ең жақсысына лайықсың — сен оған сен.",
        "✨ Бүгін — ұлы істің бастауы болсын.",
        "💎 Ең жақсыларың алда — алға бас.",
        "🌿 Кішкентай қадамдарың — сенің ұлы күшің."
    ],
    "kg": [
        "🌟 Ийгилик — күн сайын кайталанган кичинекей аракеттердин жыйындысы.",
        "💪 Канча жай жүрсөң да, башкысы — токтобо.",
        "🔥 Баштоо үчүн эң жакшы күн — бүгүн.",
        "💜 Сен ойлогондон да күчтүүсүң жана жөндөмдүүсүң.",
        "🌱 Ар бир күн — жашооңду өзгөртүүгө жаңы мүмкүнчүлүк.",
        "🚀 Жай жүрүүдөн коркпо. Бир жерде туруп калуудан корк.",
        "☀️ Кыйын жолдор көбүнчө кооз жерлерге алып келет.",
        "🦋 Эртең өзүнө ыраазы боло турган ишти бүгүн жаса.",
        "✨ Энергияң чындыкты тартат. Позитивди танда.",
        "🙌 Өзүңө ишен. Сен эң жакшысың.",
        "💜 Ар бир күн — жашооңду өзгөртүүгө мүмкүнчүлүк.",
        "🌟 Энергияң өз дүйнөңдү түзөт.",
        "🔥 Эртең өзүнө ыраазы боло турган ишти бүгүн жаса.",
        "✨ Чоң өзгөрүүлөр кичине кадамдардан башталат.",
        "🌱 Сен ойлогондон да күчтүүсүң жана көп нерсеге жөндөмдүүсүң.",
        "☀️ Ичиңдеги жарык бардык кыйынчылыктардан жаркын.",
        "💪 Катадан коркпо — аракет кылбоодон корк.",
        "🌊 Бардык бороон өтөт, сен бекем болосуң.",
        "🤍 Сен азыр эле сүйүүгө жана бакытка татыктуусуң.",
        "🚀 Кыялдарың иш-аракетти күтүп турат.",
        "🎯 Процесске ишен, жол белгисиз болсо да.",
        "🧘‍♀️ Тынч акыл — бактылуу жашоонун ачкычы.",
        "🌸 Ар бир учур — кайра баштоого мүмкүнчүлүк.",
        "💡 Жашоо — сага эмне болорунун 10%, калганы сенин ага мамилең.",
        "❤️ Сен маанилүүсүң жана бул дүйнөгө керексиң.",
        "🌌 Кыялың үчүн күн сайын аз да болсо жаса.",
        "🙌 Сен эң жакшысын татыктуусуң — ишен.",
        "✨ Бүгүн чоң нерсенин башталышы болсун.",
        "💎 Эң жакшысы алдыда — жолуңан тайба.",
        "🌿 Кичине кадамдарың — сенин улуу күчүң."
    ],
    "hy": [
        "🌟 Հաջողությունը փոքր ջանքերի գումարն է, որոնք կրկնվում են ամեն օր։",
        "💪 Անկախ նրանից, թե որքան դանդաղ ես շարժվում, կարևորն այն է՝ չկանգնել։",
        "🔥 Լավագույն օրը սկսելու համար՝ այսօրն է։",
        "💜 Դու ավելի ուժեղ ու կարող ես, քան կարծում ես։",
        "🌱 Ամեն օր՝ կյանքդ փոխելու նոր հնարավորություն է։",
        "🚀 Մի վախեցիր դանդաղ շարժվելուց։ Վախեցիր չշարժվելուց։",
        "☀️ Դժվար ճանապարհները հաճախ տանում են գեղեցիկ վայրեր։",
        "🦋 Արա այսօր այն, ինչի համար վաղը շնորհակալ կլինես քեզ։",
        "✨ Քո էներգիան ձգում է իրականությունը։ Ընտրիր դրականը։",
        "🙌 Հավատա ինքդ քեզ։ Դու ունես ամեն ինչ։",
        "💜 Ամեն օր՝ կյանքդ փոխելու նոր հնարավորություն է։",
        "🌟 Քո էներգիան ստեղծում է քո իրականությունը։",
        "🔥 Արա այսօր այն, ինչի համար վաղը շնորհակալ կլինես քեզ։",
        "✨ Մեծ փոփոխությունները սկսվում են փոքր քայլերից։",
        "🌱 Դու ուժեղ ես, քան կարծում ես, և ունակ ավելին։",
        "☀️ Քո ներսի լույսը վառ է ցանկացած դժվարությունից։",
        "💪 Մի վախեցիր սխալվելուց — վախեցիր չփորձելուց։",
        "🌊 Բոլոր փոթորիկներն անցնում են, իսկ դու ավելի ուժեղ ես դառնում։",
        "🤍 Դու հիմա սիրո և երջանկության արժանի ես։",
        "🚀 Քո երազանքները սպասում են քո առաջին քայլին։",
        "🎯 Վստահիր ընթացքին, նույնիսկ եթե ճանապարհը պարզ չէ։",
        "🧘‍♀️ Խաղաղ միտքը երջանիկ կյանքի բանալին է։",
        "🌸 Ամեն պահ՝ նորից սկսելու հնարավորություն է։",
        "💡 Կյանքը 10% այն է, ինչ պատահում է քեզ հետ, և 90%՝ ինչպես ես արձագանքում։",
        "❤️ Դու կարևոր ու անհրաժեշտ ես այս աշխարհում։",
        "🌌 Ամեն օր մի փոքր արա քո երազանքի համար։",
        "🙌 Դու արժանի ես լավագույնին — հավատա դրան։",
        "✨ Թող այսօրը լինի ինչ-որ մեծի սկիզբը։",
        "💎 Լավագույնը դեռ առջևում է — շարունակիր։",
        "🌿 Քո փոքր քայլերը՝ քո մեծ ուժն են։"
    ],
    "ce": [
        "🌟 Дечу хилла цхьаьна мотт хетар хилла.",
        "💪 До хьаьлла догала, доьхахаца — догӀаьлча.",
        "🔥 До бац барра — гӀайр цуьнан цуьнан.",
        "💜 Хьо цуьнан даха аьтто хилла, цуьнан лаьцна.",
        "🌱 Цхьаьна мотт — цхьаьна кхин ву бацийн.",
        "🚀 Ац мотт догалаша, атту догӀаьлча.",
        "☀️ КӀанчу юкъара каргаш долу цуьнан.",
        "🦋 Даьлча кхо бен цхьаьна цуьнан хьо хилла.",
        "✨ Хила цуьнан — хила цхьаьна. Позитив цуьнан цуьнан.",
        "🙌 Цуьнан цуьнан ву а цхьаьна ву.",
        "💜 Цхьаьна мотт — цхьаьна кхин ву бацийн.",
        "🌟 Хила цуьнан — хила цхьаьна.",
        "🔥 Даьлча кхо бен цхьаьна цуьнан хьо хилла.",
        "✨ Баха цхьаьна цхьаьна цхьаьна.",
        "🌱 Хьо хилла даха аьтто хилла.",
        "☀️ Илла хила ву хила къай.",
        "💪 До хьаьлла догала, доьхахаца — догӀаьлча.",
        "🌊 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🤍 Хьо хила йоцу цхьаьна хила.",
        "🚀 Хила йоцу цхьаьна хила.",
        "🎯 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🧘‍♀️ Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🌸 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "💡 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "❤️ Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🌌 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🙌 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "✨ Илла къайна цхьаьна хьо цхьаьна хилла.",
        "💎 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🌿 Илла къайна цхьаьна хьо цхьаьна хилла."
    ],
    "md": [
        "🌟 Succesul este suma micilor eforturi repetate zi de zi.",
        "💪 Nu contează cât de încet mergi, important e să nu te oprești.",
        "🔥 Cea mai bună zi pentru a începe este azi.",
        "💜 Ești mai puternic(ă) și capabil(ă) decât crezi.",
        "🌱 Fiecare zi e o nouă șansă de a-ți schimba viața.",
        "🚀 Nu te teme să mergi încet. Teme-te să stai pe loc.",
        "☀️ Drumurile grele duc adesea spre locuri frumoase.",
        "🦋 Fă azi ceea ce-ți va mulțumi mâine.",
        "✨ Energia ta atrage realitatea ta. Alege pozitivul.",
        "🙌 Crede în tine. Ești cel mai bun atu al tău.",
        "💜 Fiecare zi e o nouă șansă de schimbare.",
        "🌟 Energia ta creează realitatea ta.",
        "🔥 Fă azi ceea ce-ți va mulțumi mâine.",
        "✨ Marile schimbări încep cu pași mici.",
        "🌱 Ești mai puternic(ă) decât crezi și capabil(ă) de mai mult.",
        "☀️ Lumina din tine e mai puternică decât orice greutate.",
        "💪 Nu te teme de greșeli — teme-te să nu încerci.",
        "🌊 Toate furtunile trec, iar tu devii mai puternic(ă).",
        "🤍 Meriți iubire și fericire chiar acum.",
        "🚀 Visurile tale te așteaptă să acționezi.",
        "🎯 Ai încredere în proces, chiar dacă drumul nu e clar.",
        "🧘‍♀️ O minte liniștită e cheia unei vieți fericite.",
        "🌸 Fiecare clipă e o oportunitate de a începe din nou.",
        "💡 Viața e 10% ce ți se întâmplă și 90% cum reacționezi.",
        "❤️ Ești important(ă) și necesar(ă) în această lume.",
        "🌌 Fă câte puțin în fiecare zi pentru visul tău.",
        "🙌 Meriți ce e mai bun — crede în asta.",
        "✨ Lasă ca azi să fie începutul a ceva măreț.",
        "💎 Ce-i mai bun urmează — continuă să mergi.",
        "🌿 Pașii tăi mici — forța ta mare."
    ],
    "ka": [
        "🌟 წარმატება პატარა ძალისხმევების ჯამია, რომელიც ყოველდღე მეორდება.",
        "💪 მნიშვნელობა არ აქვს, რამდენად ნელა მიდიხარ — მთავარია, არ გაჩერდე.",
        "🔥 დაწყებისთვის საუკეთესო დღე — დღეს არის.",
        "💜 შენ უფრო ძლიერი და უფრო უნარიანი ხარ, ვიდრე გგონია.",
        "🌱 ყოველი დღე — ახალი შანსია შეცვალო შენი ცხოვრება.",
        "🚀 ნუ გეშინია ნელა სიარულის. გეშინოდეს ერთ ადგილას დგომის.",
        "☀️ რთული გზები ხშირად მშვენიერ ადგილებში მიდის.",
        "🦋 გააკეთე დღეს ის, რისთვისაც ხვალ მადლობას ეტყვი საკუთარ თავს.",
        "✨ შენი ენერგია იზიდავს რეალობას. აირჩიე პოზიტივი.",
        "🙌 იწამე საკუთარი თავი. შენ შენი საუკეთესო რესურსი ხარ.",
        "💜 ყოველი დღე ახალი შესაძლებლობაა ცვლილებისთვის.",
        "🌟 შენი ენერგია ქმნის შენს რეალობას.",
        "🔥 გააკეთე დღეს ის, რისთვისაც ხვალ მადლობას ეტყვი საკუთარ თავს.",
        "✨ დიდი ცვლილებები იწყება პატარა ნაბიჯებით.",
        "🌱 შენ უფრო ძლიერი ხარ, ვიდრე ფიქრობ და შეგიძლია მეტი.",
        "☀️ შენი შიგნით სინათლე ყველა სირთულეს აჭარბებს.",
        "💪 ნუ გეშინია შეცდომების — გეშინოდეს არგადადგა ნაბიჯი.",
        "🌊 ყველა ქარიშხალი მთავრდება, შენ კი უფრო ძლიერი ხდები.",
        "🤍 იმსახურებ სიყვარულს და ბედნიერებას უკვე ახლა.",
        "🚀 შენი ოცნებები გელოდება, როცა დაიწყებ მოქმედებას.",
        "🎯 ენდე პროცესს, თუნდაც გზა ჯერ არ იყოს ნათელი.",
        "🧘‍♀️ მშვიდი გონება ბედნიერი ცხოვრების გასაღებია.",
        "🌸 ყოველი მომენტი — ახალი დასაწყების შესაძლებლობა.",
        "💡 ცხოვრება — ესაა 10% რა ხდება და 90% როგორ რეაგირებ.",
        "❤️ მნიშვნელოვანი და საჭირო ხარ ამ სამყაროში.",
        "🌌 შენი ოცნებისთვის ყოველდღე ცოტა რამ გააკეთე.",
        "🙌 შენ იმსახურებ საუკეთესოს — გჯეროდეს ამის.",
        "✨ დღეს დაიწყე რაღაც დიდი.",
        "💎 საუკეთესო ჯერ კიდევ წინაა — განაგრძე გზა.",
        "🌿 შენი პატარა ნაბიჯები — შენი დიდი ძალაა."
    ],
    "en": [
        "🌟 Success is the sum of small efforts repeated day in and day out.",
        "💪 It doesn't matter how slowly you go, as long as you do not stop.",
        "🔥 The best day to start is today.",
        "💜 You are stronger and more capable than you think.",
        "🌱 Every day is a new chance to change your life.",
        "🚀 Don't be afraid to go slowly. Be afraid to stand still.",
        "☀️ Difficult roads often lead to beautiful destinations.",
        "🦋 Do today what you will thank yourself for tomorrow.",
        "✨ Your energy attracts your reality. Choose positivity.",
        "🙌 Believe in yourself. You are your greatest asset.",
        "💜 Every day is a new chance to change your life.",
        "🌟 Your energy creates your reality.",
        "🔥 Do today what you will thank yourself for tomorrow.",
        "✨ Big changes start with small steps.",
        "🌱 You are stronger than you think and capable of more.",
        "☀️ The light inside you shines brighter than any difficulty.",
        "💪 Don't be afraid to make mistakes — be afraid not to try.",
        "🌊 Every storm ends, and you become stronger.",
        "🤍 You deserve love and happiness right now.",
        "🚀 Your dreams are waiting for you to take action.",
        "🎯 Trust the process, even if the path isn't clear yet.",
        "🧘‍♀️ A calm mind is the key to a happy life.",
        "🌸 Every moment is an opportunity to start again.",
        "💡 Life is 10% what happens to you and 90% how you react.",
        "❤️ You are important and needed in this world.",
        "🌌 Do a little every day for your dream.",
        "🙌 You deserve the best — believe it.",
        "✨ Let today be the start of something great.",
        "💎 The best is yet to come — keep going.",
        "🌿 Your small steps are your great strength."
    ],
}

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    selected_quote = random.choice(QUOTES_BY_LANG.get(lang, QUOTES_BY_LANG["ru"]))
    await update.message.reply_text(selected_quote, parse_mode="Markdown")

async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    selected = random.choice(SUPPORT_MESSAGES_BY_LANG.get(lang, SUPPORT_MESSAGES_BY_LANG["ru"]))
    await update.message.reply_text(selected)


SUPPORT_MESSAGES_BY_LANG = {
    "ru": [
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
    ],
    "uk": [
        "💜 Ти робиш цей світ кращим просто тим, що ти в ньому.",
        "🌞 Сьогодні новий день, і він повний можливостей — ти впораєшся!",
        "🤗 Обіймаю тебе подумки. Ти не один(а).",
        "✨ Навіть якщо важко — пам’ятай, ти вже багато чого досяг(ла)!",
        "💫 У тебе є все, щоб пройти це. Вірю в тебе!",
        "🫶 Як добре, що ти є. Ти дуже важлива людина.",
        "🔥 Сьогодні — гарний день, щоб пишатися собою!",
        "🌈 Якщо раптом втомився(лася) — просто зроби паузу і видихни. Це нормально.",
        "😊 Посміхнись собі у дзеркало. Ти класний(а)!",
        "💡 Пам’ятай: щодня ти стаєш сильнішим(ою).",
        "🍀 Твої почуття важливі. Ти важливий(а).",
        "💛 Ти заслуговуєш любові і турботи — і від інших, і від себе.",
        "🌟 Дякую тобі за те, що ти є. Серйозно.",
        "🤍 Навіть маленький крок вперед — вже перемога.",
        "💌 Ти приносиш у світ тепло. Не забувай про це!",
        "✨ Вір у себе. Ти вже стільки всього пройшов(ла) — і впорався(лася)!",
        "🙌 Сьогодні — твій день. Робі те, що робить тебе щасливим(ою).",
        "🌸 Потіш себе чимось смачним або приємним. Ти цього вартий(а).",
        "🏞️ Просто нагадування: ти неймовірний(а), і я поруч.",
        "🎶 Нехай музика сьогодні зігріє твою душу.",
        "🤝 Не бійся просити про підтримку — ти не один(а).",
        "🔥 Згадай, скільки всього ти подолав(ла). Ти сильний(а)!",
        "🦋 Сьогодні — шанс зробити щось добре для себе.",
        "💎 Ти унікальний(а), таких як ти більше нема.",
        "🌻 Навіть якщо день не ідеальний — ти все одно сяєш.",
        "💪 Ти вмієш більше, ніж думаєш. Вірю в тебе!",
        "🍫 Потіш себе дрібницею — ти цього заслуговуєш.",
        "🎈 Нехай твій день буде легким і добрим.",
        "💭 Якщо є мрія — пам’ятай, що ти можеш до неї дійти.",
        "🌊 Ти як океан — глибший(а) і сильніший(а), ніж здається.",
        "🕊️ Нехай сьогодні буде хоча б одна мить, що викличе усмішку."
    ],
    "be": [
        "💜 Ты робіш гэты свет лепшым проста тым, што ты ў ім.",
        "🌞 Сёння новы дзень, і ён поўны магчымасцей — ты справішся!",
        "🤗 Абдымаю цябе думкамі. Ты не адзін(а).",
        "✨ Нават калі цяжка — памятай, ты ўжо шмат чаго дасягнуў(ла)!",
        "💫 У цябе ёсць усё, каб прайсці праз гэта. Веру ў цябе!",
        "🫶 Як добра, што ты ёсць. Ты вельмі важны(ая) чалавек.",
        "🔥 Сёння — добры дзень, каб ганарыцца сабой!",
        "🌈 Калі стаміўся(лася) — проста зрабі паўзу і выдыхні. Гэта нармальна.",
        "😊 Усміхніся сабе ў люстэрку. Ты класны(ая)!",
        "💡 Памятай: кожны дзень ты становішся мацнейшым(ай).",
        "🍀 Твае пачуцці важныя. Ты важны(ая).",
        "💛 Ты заслугоўваеш любові і клопату — і ад іншых, і ад сябе.",
        "🌟 Дзякуй табе за тое, што ты ёсць. Сапраўды.",
        "🤍 Нават маленькі крок наперад — ужо перамога.",
        "💌 Ты прыносіш у свет цяпло. Не забывай пра гэта!",
        "✨ Верь у сябе. Ты ўжо шмат прайшоў(ла) — і справіўся(лася)!",
        "🙌 Сёння — твой дзень. Рабі тое, што робіць цябе шчаслівым(ай).",
        "🌸 Парадуй сябе чымсьці смачным або прыемным. Ты гэтага варты(ая).",
        "🏞️ Проста напамін: ты неверагодны(ая), і я побач.",
        "🎶 Хай музыка сёння сагрэе тваю душу.",
        "🤝 Не бойся прасіць падтрымку — ты не адзін(а).",
        "🔥 Успомні, колькі ўсяго ты пераадолеў(ла). Ты моцны(ая)!",
        "🦋 Сёння — шанец зрабіць нешта добрае для сябе.",
        "💎 Ты ўнікальны(ая), такіх як ты няма.",
        "🌻 Нават калі дзень не ідэальны — ты ўсё роўна ззяеш.",
        "💪 Ты ўмееш больш, чым думаеш. Веру ў цябе!",
        "🍫 Парадуй сябе дробяззю — ты гэтага заслугоўваеш.",
        "🎈 Хай твой дзень будзе лёгкім і добрым.",
        "💭 Калі ёсць мара — памятай, што можаш яе дасягнуць.",
        "🌊 Ты як акіян — глыбейшы(ая) і мацнейшы(ая), чым здаецца.",
        "🕊️ Хай сёння будзе хоць адзін момант, які прымусіць цябе ўсміхнуцца."
    ],
    "kk": [
        "💜 Сен бұл әлемді жақсартасың, өйткені сен осындасың.",
        "🌞 Бүгін жаңа күн, толы мүмкіндіктерге — сен бәріне үлгересің!",
        "🤗 Ойша құшақтаймын. Сен жалғыз емессің.",
        "✨ Қиын болса да — сен қазірдің өзінде көп нәрсеге жеттің!",
        "💫 Бұл кезеңнен өтуге барлық күшің бар. Саған сенемін!",
        "🫶 Сен барсың — бұл тамаша! Сен маңызды адамсың.",
        "🔥 Бүгін — өзіңмен мақтанатын күн!",
        "🌈 Егер шаршасаң — аздап демал, бұл қалыпты жағдай.",
        "😊 Айнаға күлімде. Сен кереметсің!",
        "💡 Есіңде болсын: күн сайын сен күштірексің.",
        "🍀 Сенің сезімдерің маңызды. Сен де маңыздысың.",
        "💛 Сен махаббат пен қамқорлыққа лайықсың — басқалардан да, өзіңнен де.",
        "🌟 Саған рахмет, сен барсың.",
        "🤍 Бір қадам алға — бұл да жеңіс.",
        "💌 Сен әлемге жылу әкелесің. Мұны ұмытпа!",
        "✨ Өзіңе сен. Сен көп нәрсе бастан кешірдің — және бәрін еңсердің!",
        "🙌 Бүгін — сенің күнің. Өзіңді бақытты ететінді істе.",
        "🌸 Өзіңді тәтті нәрсемен қуант. Сен бұған лайықсың.",
        "🏞️ Еске салу: сен кереметсің және мен осындамын.",
        "🎶 Музыка бүгін жаныңды жылыта берсін.",
        "🤝 Қолдау сұраудан қорықпа — сен жалғыз емессің.",
        "🔥 Өткен жеңістеріңді есіңе ал. Сен мықтысың!",
        "🦋 Бүгін — өзің үшін жақсылық жасауға мүмкіндік.",
        "💎 Сен бірегейсің, сендей ешкім жоқ.",
        "🌻 Күнің мінсіз болмаса да — сен бәрібір жарқырайсың.",
        "💪 Сен ойлағаннан көп нәрсе жасай аласың. Саған сенемін!",
        "🍫 Өзіңді кішкене нәрсемен қуант — сен бұған лайықсың.",
        "🎈 Күнің жеңіл және жылы болсын.",
        "💭 Арманың болса — оған жетуге қабілетің бар екенін ұмытпа.",
        "🌊 Сен мұхиттай терең және мықтысың.",
        "🕊️ Бүгін кем дегенде бір сәт саған күлкі сыйласын."
    ],
    "kg": [
        "💜 Бул дүйнөнү жакшыраак кыласың, анткени сен барсың.",
        "🌞 Бүгүн — жаңы күн, мүмкүнчүлүктөргө толо — сен баарына жетишесиң!",
        "🤗 Ойлоп, кучактайм. Сен жалгыз эмессиң.",
        "✨ Кыйын болсо да — сен буга чейин эле көп нерсеге жетиштиң!",
        "💫 Бул жолдон өтүүгө күчүң жетет. Сага ишенемин!",
        "🫶 Сен барсың — бул сонун! Сен маанилүү адамсың.",
        "🔥 Бүгүн — өзүң менен сыймыктанууга күн!",
        "🌈 Эгер чарчасаң — дем ал, бул кадимки нерсе.",
        "😊 Көз айнекке жылмай. Сен сонунсуң!",
        "💡 Эсте: ар бир күн менен күчтөнөсүң.",
        "🍀 Сезимдериң маанилүү. Сен да маанилүү адамсың.",
        "💛 Сен сүйүүгө жана камкордукка татыктуусуң — башкалардан да, өзүңдөн да.",
        "🌟 Сен бар экениңе рахмат.",
        "🤍 Алга бир кадам — бул да жеңиш.",
        "💌 Сен дүйнөгө жылуулук алып келесиң. Бул тууралуу унутпа!",
        "✨ Өзүңө ишен. Көп нерседен өттүң — баарын жеңдиң!",
        "🙌 Бүгүн — сенин күнүң. Бактылуу кылган ишти жаса.",
        "🌸 Өзүңдү таттуу нерсе менен кубандыр. Сен татыктуусуң.",
        "🏞️ Эскертүү: сен укмушсуң жана мен жанымдамын.",
        "🎶 Музыка бүгүн жаныңды жылытсын.",
        "🤝 Колдоо суроодон тартынба — сен жалгыз эмессиң.",
        "🔥 Кайсы жеңиштериңди эстеп, сыймыктан.",
        "🦋 Бүгүн — өзүң үчүн жакшылык кылууга мүмкүнчүлүк.",
        "💎 Сен өзгөчөсүң, сендей башка адам жок.",
        "🌻 Күнүң идеалдуу болбосо да — сен жаркырайсың.",
        "💪 Сен ойлогондон да көптү жасай аласың. Сага ишенем!",
        "🍫 Өзүңдү майда нерсе менен кубандыр — сен татыктуусуң.",
        "🎈 Күнің жеңил жана жагымдуу болсун.",
        "💭 Кыялың болсо — ага жетүүгө күчүң бар экенин эсте.",
        "🌊 Сен океандай терең жана күчтүүсүң.",
        "🕊️ Бүгүн болбосо да, бир ирмем сени күлдүрсүн."
    ],
    "hy": [
        "💜 Դու այս աշխարհը ավելի լավը ես դարձնում, որովհետև դու այստեղ ես։",
        "🌞 Այսօր նոր օր է, լի հնարավորություններով — դու կարող ես ամեն ինչ։",
        "🤗 Մտքով գրկում եմ քեզ։ Դու մենակ չես։",
        "✨ Թեպետ դժվար է, հիշիր՝ արդեն շատ բան ես արել։",
        "💫 Դու ունես ամեն ինչ՝ այս ամենը հաղթահարելու համար։ Հավատում եմ քեզ։",
        "🫶 Որքան լավ է, որ դու կաս։ Դու շատ կարևոր մարդ ես։",
        "🔥 Այսօր հրաշալի օր է՝ քեզ վրա հպարտանալու համար։",
        "🌈 Եթե հանկարծ հոգնել ես՝ պարզապես հանգստացիր։ Դա նորմալ է։",
        "😊 Ժպտա հայելու առաջ։ Դու հիանալի ես։",
        "💡 Հիշիր՝ ամեն օր ուժեղանում ես։",
        "🍀 Քո զգացմունքները կարևոր են։ Դու կարևոր ես։",
        "💛 Դու արժանի ես սիրո և հոգածության՝ և ուրիշներից, և քեզանից։",
        "🌟 Շնորհակալ եմ, որ կաս։ Իրոք։",
        "🤍 Նույնիսկ փոքր քայլը առաջ՝ արդեն հաղթանակ է։",
        "💌 Դու աշխարհին ջերմություն ես բերում։ Մի մոռացիր դա։",
        "✨ Վստահիր քեզ։ Դու արդեն շատ բան ես հաղթահարել։",
        "🙌 Այսօր քո օրն է։ Արի՛ արա այն, ինչ քեզ երջանիկ է դարձնում։",
        "🌸 Հաճույք պատճառիր քեզ ինչ-որ համով կամ հաճելի բանով։ Դու դրա արժանի ես։",
        "🏞️ Հիշեցում՝ դու հիանալի ես և ես քո կողքին եմ։",
        "🎶 Թող երաժշտությունը այսօր ջերմացնի հոգիդ։",
        "🤝 Մի վախեցիր աջակցություն խնդրել՝ դու մենակ չես։",
        "🔥 Հիշիր քո հաղթանակները։ Դու ուժեղ ես։",
        "🦋 Այսօր հնարավորություն է՝ ինքդ քեզ լավ բան անելու։",
        "💎 Դու յուրահատուկ ես, քո նմանը չկա։",
        "🌻 Նույնիսկ եթե օրը կատարյալ չէ՝ դու փայլում ես։",
        "💪 Դու կարող ես ավելին, քան կարծում ես։ Հավատում եմ քեզ։",
        "🍫 Ուրախացրու քեզ փոքր բանով՝ դու արժանի ես դրան։",
        "🎈 Թող օրըդ թեթև ու ջերմ լինի։",
        "💭 Եթե երազանք ունես՝ հիշիր, որ կարող ես իրականացնել։",
        "🌊 Դու օվկիանոսի պես խորն ու ուժեղ ես։",
        "🕊️ Թող այսօր թեկուզ մեկ պահ քեզ ժպիտ պարգևի։"
    ],
    "ce": [
        "💜 Со хетам дийцар дуьн йоьлчу — хьо цу са.",
        "🌞 Ахкера йуь хетам дийца — хийц йойла а, цу ву а цу.",
        "🤗 Доьззаш хьо хьунал, хьо йу хила цу.",
        "✨ Къобал со дийн ду, ву хетам ца кхетам — хьо ийса мотт.",
        "💫 Хьо цу ха цуьнан. Со хетам хьо!.",
        "🫶 Хьо цу са, хийц оьзду хила. Хьо мотт.",
        "🔥 Ахкера — хийц дуьн чох дийца йойла хила цу.",
        "🌈 Хьо чух цу хийца — тержа дийцар, ву езар ду.",
        "😊 Дзира тIехь, хьо хила цу.",
        "💡 Со дийцар: хийца цхьаьнан ца цу са цу.",
        "🍀 Хьо хийцар мотт, хьо цу мотт.",
        "💛 Хьо хийцар бац, хьо хийцар лаьц.",
        "🌟 Со дийцар хьо цу са. Хетам дийцар.",
        "🤍 Юкъар йойла а — хийц ду йойла.",
        "💌 Хьо дуьн хийцар ду. Хьо хила хетам мотт.",
        "✨ Со хетам хьо хьунал. Хьо йу мотт ца а.",
        "🙌 Ахкера хьо дийцар ду. Хьо цу хьунал хила цу.",
        "🌸 Хьо цу дуьллар ду, хьо мотт цу.",
        "🏞️ Со дуьллар: хьо цу хила, со хетам цу.",
        "🎶 Мусика хьо дуьн хийцар ду.",
        "🤝 Хьо хийцар къобал хила — хьо хила цу.",
        "🔥 Со хийцар хьо йу мотт, хьо мотт.",
        "🦋 Ахкера — хийца хийцар цу.",
        "💎 Хьо хийца хийцар цу.",
        "🌻 Юкъар йойла — хьо хийцар мотт.",
        "💪 Хьо мотт, со хетам хьо!",
        "🍫 Хьо цу дуьллар ду.",
        "🎈 Хьо хийца хийцар мотт.",
        "💭 Хьо хийца хийцар мотт.",
        "🌊 Хьо хийца хийцар мотт.",
        "🕊️ Ахкера хьо хийцар мотт."
    ],
    "md": [
        "💜 Faci lumea asta mai bună doar pentru că exiști.",
        "🌞 Azi e o nouă zi, plină de oportunități — vei reuși!",
        "🤗 Te îmbrățișez cu gândul. Nu ești singur(ă).",
        "✨ Chiar dacă e greu — amintește-ți, ai reușit deja multe!",
        "💫 Ai tot ce-ți trebuie să treci peste asta. Cred în tine!",
        "🫶 Ești aici — și asta e minunat! Ești o persoană importantă.",
        "🔥 Azi e o zi bună să fii mândru(ă) de tine!",
        "🌈 Dacă te-ai obosit — ia o pauză, e normal.",
        "😊 Zâmbește-ți în oglindă. Ești grozav(ă)!",
        "💡 Ține minte: cu fiecare zi devii mai puternic(ă).",
        "🍀 Sentimentele tale contează. Tu contezi.",
        "💛 Meriți dragoste și grijă — de la alții și de la tine.",
        "🌟 Mulțumesc că exiști.",
        "🤍 Chiar și un pas mic înainte e o victorie.",
        "💌 Aduci căldură în lume. Nu uita asta!",
        "✨ Ai încredere în tine. Ai trecut prin multe și ai reușit!",
        "🙌 Azi e ziua ta. Fă ceea ce te face fericit(ă).",
        "🌸 Răsfață-te cu ceva gustos sau plăcut. Meriți.",
        "🏞️ Doar o amintire: ești incredibil(ă) și sunt aici.",
        "🎶 Lasă muzica să-ți încălzească sufletul azi.",
        "🤝 Nu-ți fie teamă să ceri ajutor — nu ești singur(ă).",
        "🔥 Gândește-te la toate pe care le-ai depășit. Ești puternic(ă)!",
        "🦋 Azi e o șansă să faci ceva bun pentru tine.",
        "💎 Ești unic(ă), nimeni nu mai e ca tine.",
        "🌻 Chiar dacă ziua nu e perfectă — tot strălucești.",
        "💪 Poți mai mult decât crezi. Cred în tine!",
        "🍫 Răsfață-te cu ceva mic — meriți asta.",
        "🎈 Să ai o zi ușoară și frumoasă.",
        "💭 Dacă ai un vis — amintește-ți că poți ajunge la el.",
        "🌊 Ești profund(ă) și puternic(ă) ca un ocean.",
        "🕊️ Sper ca azi să ai cel puțin un moment de bucurie."
    ],
    "ka": [
        "💜 შენ ამ სამყაროს უკეთესს ხდი უბრალოდ აქ რომ ხარ.",
        "🌞 დღეს ახალი დღეა, სავსე შესაძლებლობებით — ყველაფერს შეძლებ!",
        "🤗 აზროვნებით გეხვევი. მარტო არ ხარ.",
        "✨ თუ ძნელია — დაიმახსოვრე, უკვე ბევრი რამ გისწავლია!",
        "💫 გაქვს ყველაფერი, რომ ეს გზა გაიარო. მჯერა შენი!",
        "🫶 კარგია რომ არსებობ. შენ ძალიან მნიშვნელოვანი ადამიანი ხარ.",
        "🔥 დღეს კარგი დღეა, რომ საკუთარ თავზე იამაყო!",
        "🌈 თუ დაიღალე — დაისვენე, ეს ნორმალურია.",
        "😊 სარკეში გაუღიმე საკუთარ თავს. შენ შესანიშნავი ხარ!",
        "💡 დაიმახსოვრე: ყოველდღე უფრო ძლიერი ხდები.",
        "🍀 შენი გრძნობები მნიშვნელოვანია. შენ მნიშვნელოვანი ხარ.",
        "💛 იმსახურებ სიყვარულსა და ზრუნვას — სხვებისგანაც და საკუთარი თავისგანაც.",
        "🌟 გმადლობ რომ ხარ.",
        "🤍 ერთი პატარა ნაბიჯი წინ — უკვე გამარჯვებაა.",
        "💌 ამ სამყაროს სითბოს მატებ. არ დაივიწყო ეს!",
        "✨ ენდე საკუთარ თავს. უკვე ბევრი რამ გამოიარე და შეძლე!",
        "🙌 დღეს შენი დღეა. გააკეთე ის, რაც გაბედნიერებს.",
        "🌸 გაახარე თავი რამე გემრიელით ან სასიამოვნოთ. იმსახურებ ამას.",
        "🏞️ შეგახსენებ: უნიკალური ხარ და მე შენთან ვარ.",
        "🎶 მუსიკა დღეს გაათბოს შენი სული.",
        "🤝 არ შეგეშინდეს მხარდაჭერის თხოვნის — მარტო არ ხარ.",
        "🔥 გაიხსენე რისი გადალახვაც შეძლე. ძლიერი ხარ!",
        "🦋 დღეს შესაძლებლობაა შენთვის რამე კარგი გააკეთო.",
        "💎 უნიკალური ხარ, შენი მსგავსი არავინ არის.",
        "🌻 თუნდაც დღე იდეალური არ იყოს — მაინც ანათებ.",
        "💪 შეგიძლია მეტი, ვიდრე გგონია. მჯერა შენი!",
        "🍫 გაახარე თავი რამე პატარა რამით — იმსახურებ ამას.",
        "🎈 შენი დღე იყოს მსუბუქი და სასიამოვნო.",
        "💭 თუ გაქვს ოცნება — გახსოვდეს, შეგიძლია მას მიაღწიო.",
        "🌊 შენ ოკეანესავით ღრმა და ძლიერი ხარ.",
        "🕊️ იმედი მაქვს, დღევანდელი დღე გაგახარებს."
    ],
    "en": [
        "💜 You make this world a better place just by being in it.",
        "🌞 Today is a new day, full of opportunities — you’ve got this!",
        "🤗 Sending you a mental hug. You’re not alone.",
        "✨ Even if it’s hard — remember, you’ve already achieved so much!",
        "💫 You have everything you need to get through this. I believe in you!",
        "🫶 It’s wonderful that you’re here. You are an important person.",
        "🔥 Today is a great day to be proud of yourself!",
        "🌈 If you’re tired — take a break, that’s okay.",
        "😊 Smile at yourself in the mirror. You’re amazing!",
        "💡 Remember: you’re getting stronger every day.",
        "🍀 Your feelings matter. You matter.",
        "💛 You deserve love and care — from others and from yourself.",
        "🌟 Thank you for being you. Really.",
        "🤍 Even a small step forward is a victory.",
        "💌 You bring warmth to the world. Don’t forget it!",
        "✨ Believe in yourself. You’ve already come so far and made it through!",
        "🙌 Today is your day. Do what makes you happy.",
        "🌸 Treat yourself to something nice or tasty. You deserve it.",
        "🏞️ Just a reminder: you’re incredible, and I’m here.",
        "🎶 Let music warm your soul today.",
        "🤝 Don’t be afraid to ask for support — you’re not alone.",
        "🔥 Remember everything you’ve overcome. You’re strong!",
        "🦋 Today is a chance to do something kind for yourself.",
        "💎 You’re unique, there’s no one else like you.",
        "🌻 Even if the day isn’t perfect — you still shine.",
        "💪 You can do more than you think. I believe in you!",
        "🍫 Treat yourself to something little — you deserve it.",
        "🎈 May your day be easy and kind.",
        "💭 If you have a dream — remember, you can achieve it.",
        "🌊 You’re as deep and strong as the ocean.",
        "🕊️ May there be at least one moment today that makes you smile."
    ]
}

# ✨ Сообщения поддержки
async def send_random_support(context):
    now_utc = datetime.utcnow()
    now_kiev = datetime.now(pytz.timezone("Europe/Kiev"))
    hour = now_kiev.hour
    # Не писать ночью
    if hour < 10 or hour >= 22:
        return

    if user_last_seen:
        for user_id in user_last_seen.keys():
            # 1. Ограничение: максимум 2 раза в день, минимум 8 часов между сообщениями
            last_support = user_last_support.get(user_id)
            if last_support and (now_utc - last_support) < timedelta(hours=8):
                continue  # Пропускаем, недавно было

            # 2. Рандом: шанс получить поддержку 70%
            if random.random() > 0.7:
                continue

            try:
                lang = user_languages.get(str(user_id), "ru")
                msg = random.choice(SUPPORT_MESSAGES_BY_LANG.get(lang, SUPPORT_MESSAGES_BY_LANG["ru"]))
                await context.bot.send_message(chat_id=user_id, text=msg)
                logging.info(f"✅ Сообщение поддержки отправлено пользователю {user_id}")
                user_last_support[user_id] = now_utc  # Запоминаем время
            except Exception as e:
                logging.error(f"❌ Ошибка отправки поддержки пользователю {user_id}: {e}")
                
POLL_MESSAGES_BY_LANG = {
    "ru": [
        "📝 Как ты оцениваешь свой день по шкале от 1 до 10?",
        "💭 Что сегодня тебя порадовало?",
        "🌿 Был ли сегодня момент, когда ты почувствовал(а) благодарность?",
        "🤔 Если бы ты мог(ла) изменить одну вещь в этом дне, что бы это было?",
        "💪 Чем ты сегодня гордишься?",
        "🤔 Что нового ты попробовал(а) сегодня?",
        "📝 О чём ты мечтаешь прямо сейчас?",
        "🌟 За что ты можешь себя сегодня похвалить?",
        "💡 Какая идея пришла тебе в голову сегодня?",
        "🎉 Был ли сегодня момент, который вызвал улыбку?",
        "🌈 Какой момент дня был самым ярким для тебя?",
        "🫶 Кому бы ты хотел(а) сегодня сказать спасибо?",
        "💬 Было ли что-то, что тебя удивило сегодня?",
        "🌻 Как ты проявил(а) заботу о себе сегодня?",
        "😌 Было ли что-то, что помогло тебе расслабиться?",
        "🏆 Чего тебе удалось достичь сегодня, даже если это мелочь?",
        "📚 Чему новому ты научился(ась) за этот день?",
        "🧑‍🤝‍🧑 Был ли кто-то, кто тебя поддержал сегодня?",
        "🎁 Сделал(а) ли ты сегодня что-то приятное для другого человека?",
        "🎨 Какое творческое занятие тебе хотелось бы попробовать?"
    ],
    "uk": [
        "📝 Як ти оцінюєш свій день за шкалою від 1 до 10?",
        "💭 Що сьогодні тебе порадувало?",
        "🌿 Чи був сьогодні момент, коли ти відчув(ла) вдячність?",
        "🤔 Якби ти міг(могла) змінити щось у цьому дні, що б це було?",
        "💪 Чим ти сьогодні пишаєшся?",
        "🤔 Що нового ти спробував(ла) сьогодні?",
        "📝 Про що ти мрієш просто зараз?",
        "🌟 За що ти можеш себе сьогодні похвалити?",
        "💡 Яка ідея прийшла тобі сьогодні в голову?",
        "🎉 Чи був сьогодні момент, який викликав усмішку?",
        "🌈 Який момент дня був найяскравішим для тебе?",
        "🫶 Кому б ти хотів(ла) сьогодні подякувати?",
        "💬 Було щось, що тебе сьогодні здивувало?",
        "🌻 Як ти подбав(ла) про себе сьогодні?",
        "😌 Було щось, що допомогло тобі розслабитися?",
        "🏆 Чого тобі вдалося досягти сьогодні, навіть якщо це дрібниця?",
        "📚 Чого нового ти навчився(лася) за цей день?",
        "🧑‍🤝‍🧑 Чи була людина, яка тебе сьогодні підтримала?",
        "🎁 Чи зробив(ла) ти сьогодні щось приємне для іншої людини?",
        "🎨 Яке творче заняття ти хотів(ла) б спробувати?"
    ],
    "be": [
        "📝 Як ты ацэніш свой дзень па шкале ад 1 да 10?",
        "💭 Што сёння табе прынесла радасць?",
        "🌿 Быў сёння момант, калі ты адчуваў(ла) удзячнасць?",
        "🤔 Калі б ты мог(ла) змяніць нешта ў гэтым дні, што б гэта было?",
        "💪 Чым ты сёння ганарышся?",
        "🤔 Што новага ты паспрабаваў(ла) сёння?",
        "📝 Пра што ты марыш прама зараз?",
        "🌟 За што можаш сябе сёння пахваліць?",
        "💡 Якая ідэя прыйшла табе сёння ў галаву?",
        "🎉 Быў сёння момант, які выклікаў усмешку?",
        "🌈 Які момант дня быў самым яркім для цябе?",
        "🫶 Каму б ты хацеў(ла) сёння сказаць дзякуй?",
        "💬 Ці было нешта, што цябе сёння здзівіла?",
        "🌻 Як ты паклапаціўся(лася) пра сябе сёння?",
        "😌 Ці было нешта, што дапамагло табе расслабіцца?",
        "🏆 Чаго табе ўдалося дасягнуць сёння, нават калі гэта дробязь?",
        "📚 Чаму новаму ты навучыўся(лася) за гэты дзень?",
        "🧑‍🤝‍🧑 Ці быў хтосьці, хто цябе сёння падтрымаў?",
        "🎁 Ці зрабіў(ла) ты сёння нешта прыемнае для іншага чалавека?",
        "🎨 Якую творчую справу ты хацеў(ла) б паспрабаваць?"
    ],
    "kk": [
        "📝 Бүгінгі күніңді 1-ден 10-ға дейін қалай бағалайсың?",
        "💭 Бүгін не сені қуантты?",
        "🌿 Бүгін ризашылық сезімін сезінген сәт болды ма?",
        "🤔 Егер бір нәрсені өзгерте алсаң, не өзгертер едің?",
        "💪 Бүгін немен мақтанасың?",
        "🤔 Бүгін не жаңалықты байқап көрдің?",
        "📝 Қазір не армандайсың?",
        "🌟 Бүгін өзіңді не үшін мақтай аласың?",
        "💡 Бүгін қандай ой келді басыңа?",
        "🎉 Бүгін күлкі сыйлаған сәт болды ма?",
        "🌈 Бүгінгі күннің ең жарқын сәті қандай болды?",
        "🫶 Бүгін кімге алғыс айтқың келеді?",
        "💬 Бүгін не сені таң қалдырды?",
        "🌻 Бүгін өз-өзіңе қалай қамқорлық көрсеттің?",
        "😌 Бүгін сені тыныштандырған не болды?",
        "🏆 Бүгін қандай жетістікке жеттің, тіпті кішкентай болса да?",
        "📚 Бүгін не үйрендің?",
        "🧑‍🤝‍🧑 Бүгін сені кім қолдады?",
        "🎁 Бүгін басқа біреуге қуаныш сыйладың ба?",
        "🎨 Қандай шығармашылық іспен айналысып көргің келеді?",
    ],
    "kg": [
        "📝 Бүгүнкү күнүңдү 1ден 10го чейин кантип баалайсың?",
        "💭 Бүгүн сени эмне кубандырды?",
        "🌿 Бүгүн ыраазычылык сезген учуруң болду беле?",
        "🤔 Бул күндө бир нерсени өзгөртө алсаң, эмнени өзгөртмөксүң?",
        "💪 Бүгүн эмнеге сыймыктандың?",
        "🤔 Бүгүн жаңы эмне аракет кылдың?",
        "📝 Азыр эмнени кыялданып жатасың?",
        "🌟 Бүгүн өзүңдү эмне үчүн мактай аласың?",
        "💡 Бүгүн кандай идея келди?",
        "🎉 Бүгүн күлкү жараткан учур болду беле?",
        "🌈 Бүгүнкү күндүн эң жаркын учуру кандай болду?",
        "🫶 Бүгүн кимге рахмат айткың келет?",
        "💬 Бүгүн сага эмне сюрприз болду?",
        "🌻 Өзүңө кандай кам көрдүң бүгүн?",
        "😌 Эмне сага эс алууга жардам берди?",
        "🏆 Бүгүн кандай жетишкендик болду, майда болсо да?",
        "📚 Бүгүн эмне жаңы үйрөндүң?",
        "🧑‍🤝‍🧑 Бүгүн сени ким колдоду?",
        "🎁 Бүгүн башка бирөөгө жакшылык кылдыңбы?",
        "🎨 Кандай чыгармачыл ишти сынап көргүң келет?"
    ],
    "hy": [
        "📝 Ինչպե՞ս կգնահատես օրդ 1-ից 10 բալով:",
        "💭 Ի՞նչն էր այսօր քեզ ուրախացրել:",
        "🌿 Այսօր ունեցե՞լ ես երախտագիտության զգացում:",
        "🤔 Եթե կարողանայիր ինչ-որ բան փոխել այս օրը, ի՞նչ կփոխեիր:",
        "💪 Ի՞նչով ես այսօր հպարտացել:",
        "🤔 Ի՞նչ նոր բան փորձեցիր այսօր:"
        "📝 Ի՞նչ ես հիմա երազում:",
        "🌟 Ինչի՞ համար կարող ես այսօր քեզ գովել:",
        "💡 Այսօր ի՞նչ գաղափար ունեցար:",
        "🎉 Այսօր եղա՞վ պահ, որ քեզ ժպիտ պատճառեց:",
        "🌈 Ո՞ր պահն էր օրվա ամենապայծառը քեզ համար:",
        "🫶 Ում կուզեիր այսօր շնորհակալություն հայտնել:",
        "💬 Այսօր ինչ-որ բան զարմացրեց քեզ?",
        "🌻 Ինչպե՞ս հոգ տարար քեզ այսօր:",
        "😌 Ինչ-որ բան քեզ օգնե՞ց հանգստանալ այսօր:",
        "🏆 Ի՞նչ հաջողության հասար այսօր, թեկուզ փոքր:",
        "📚 Ի՞նչ նոր բան սովորեցիր այս օրը:",
        "🧑‍🤝‍🧑 Եղա՞վ մեկը, որ քեզ աջակցեց այսօր:",
        "🎁 Այսօր մեկ ուրիշի համար հաճելի բան արե՞լ ես:",
        "🎨 Ի՞նչ ստեղծագործական զբաղմունք կուզենայիր փորձել:"
    ],
    "ce": [
        "📝 Хьо кхетам ден цу юкъар 1-ден 10-га къаст?",
        "💭 Хьо къобалле цу юкъар хийца чох?",
        "🌿 Хийца дийцар дуьн дуьна хеташ дийца?",
        "🤔 Хьо хийца ву а юкъар хийца хьо ца?",
        "💪 Хьо хетам ден хийца чох?",
        "🤔 Хьо цуьнан кхети хийца долу?",
        "📝 Хьо хьалха дIаяц дахара ву?",
        "🌟 Со деза хьо цуьнан дезар хийцар?",
        "💡 Хьо цуьнан хийцар идея хийца?",
        "🎉 Цуьнан дог ду ахча, хьо хиларца хьун?",
        "🌈 Хьо цуьнан йиш ду барт мотт ду?",
        "🫶 Мац цуьнан деза шукар дар?",
        "💬 Хьо цуьнан дог ду хийцар, хийциг тIехьа?",
        "🌻 Хьо цуьнан цуьнан аьтто керла хийца?",
        "😌 Хьо цуьнан йиш ду барт кхетарна, хийца?",
        "🏆 Хьо цуьнан хила а хийца, ю аьтто деш ду?",
        "📚 Хьо цуьнан хила дог хийца?",
        "🧑‍🤝‍🧑 Хьо цуьнан хьалха къобаллийца?",
        "🎁 Хьо цуьнан хьалха дукъ йиш хийца?",
        "🎨 Хьо цуьнан хийца хила цуьнан кхетийца?"
    ],
    "md": [
        "📝 Cum îți apreciezi ziua de la 1 la 10?",
        "💭 Ce te-a bucurat astăzi?",
        "🌿 A fost azi un moment când ai simțit recunoștință?",
        "🤔 Dacă ai putea schimba ceva azi, ce ar fi?",
        "💪 Cu ce ești mândru(ă) azi?",
        "🤔 Ce lucru nou ai încercat azi?",
        "📝 Despre ce visezi chiar acum?",
        "🌟 Pentru ce poți să te lauzi astăzi?",
        "💡 Ce idee ți-a venit azi?",
        "🎉 A fost astăzi un moment care te-a făcut să zâmbești?",
        "🌈 Care a fost cel mai luminos moment al zilei?",
        "🫶 Cui ai vrea să-i mulțumești astăzi?",
        "💬 A fost ceva care te-a surprins azi?",
        "🌻 Cum ai avut grijă de tine azi?",
        "😌 A fost ceva care te-a ajutat să te relaxezi?",
        "🏆 Ce ai reușit să obții azi, chiar și ceva mic?",
        "📚 Ce ai învățat nou astăzi?",
        "🧑‍🤝‍🧑 A fost cineva care te-a susținut azi?",
        "🎁 Ai făcut ceva frumos pentru altcineva astăzi?",
        "🎨 Ce activitate creativă ai vrea să încerci?"
    ],
    "ka": [
        "📝 როგორ შეაფასებდი დღეს 1-დან 10-მდე?",
        "💭 რა გაგახარა დღეს?",
        "🌿 იყო დღეს მადლიერების წამი?",
        "🤔 თუ შეგეძლო დღეს რამე შეგეცვალა, რას შეცვლიდი?",
        "💪 რით იამაყე დღეს?",
        "🤔 რა ახალს სცადე დღეს?",
        "📝 რაზე ოცნებობ ამ წუთში?",
        "🌟 რისთვის შეგიძლია დღეს შენი თავი შეაქო?",
        "💡 რა იდეა მოგივიდა დღეს?",
        "🎉 იყო დღეს წამი, რომელმაც გაგაცინა?",
        "🌈 დღის ყველაზე ნათელი მომენტი რომელი იყო?",
        "🫶 ვის მოუნდებოდა მადლობის თქმა დღეს?",
        "💬 იყო რამე, რამაც გაგაკვირვა დღეს?",
        "🌻 როგორ იზრუნე საკუთარ თავზე დღეს?",
        "😌 იყო რამე, რამაც დაგამშვიდა დღეს?",
        "🏆 რა მიაღწიე დღეს, თუნდაც პატარა რამ?",
        "📚 რა ისწავლე დღეს ახალი?",
        "🧑‍🤝‍🧑 იყო ვინმე, ვინც მხარი დაგიჭირა დღეს?",
        "🎁 გაახარე ვინმე დღეს?",
        "🎨 რა შემოქმედებითი საქმიანობა გინდა სცადო?"
    ],
    "en": [
        "📝 How would you rate your day from 1 to 10?",
        "💭 What made you happy today?",
        "🌿 Was there a moment you felt gratitude today?",
        "🤔 If you could change one thing about today, what would it be?",
        "💪 What are you proud of today?",
        "🤔 What new thing did you try today?",
        "📝 What are you dreaming about right now?",
        "🌟 What can you praise yourself for today?",
        "💡 What idea came to you today?",
        "🎉 Was there a moment that made you smile today?",
        "🌈 What was the brightest moment of your day?",
        "🫶 Who would you like to thank today?",
        "💬 Was there something that surprised you today?",
        "🌻 How did you take care of yourself today?",
        "😌 Was there something that helped you relax today?",
        "🏆 What did you manage to achieve today, even if it was something small?",
        "📚 What did you learn today?",
        "🧑‍🤝‍🧑 Was there someone who supported you today?",
        "🎁 Did you do something nice for someone else today?",
        "🎨 What creative activity would you like to try?"
    ]
}


async def send_random_poll(context):
    now = datetime.utcnow()
    if user_last_seen:
        for user_id in user_last_seen.keys():
            try:
                # --- Не спамим часто ---
                last_polled = user_last_polled.get(user_id)
                last_seen = user_last_seen.get(user_id)
                if last_polled:
                    # Если опрос был недавно — пропускаем
                    if now - last_polled < timedelta(hours=MIN_HOURS_SINCE_LAST_POLL):
                        continue
                if last_seen:
                    # Если был активен недавно — пропускаем
                    if now - last_seen < timedelta(hours=MIN_HOURS_SINCE_ACTIVE):
                        continue
                # Случайная задержка — иногда не пишем вообще
                if random.random() > POLL_RANDOM_CHANCE:
                    continue

                lang = user_languages.get(str(user_id), "ru")
                poll = random.choice(POLL_MESSAGES_BY_LANG.get(lang, POLL_MESSAGES_BY_LANG["ru"]))
                await context.bot.send_message(chat_id=user_id, text=poll)
                logging.info(f"✅ Опрос отправлен пользователю {user_id}")

                # --- Запоминаем, когда отправили ---
                user_last_polled[user_id] = now

                # Не забудь сохранить user_last_polled, если оно хранится в файле!
            except Exception as e:
                logging.error(f"❌ Ошибка отправки опроса пользователю {user_id}: {e}")
                
async def mypoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    stats = get_user_stats(user_id)
    points = stats.get("points", 0)
    completed = stats.get("goals_completed", 0)

    TEXTS = {
        "ru": (
            "🌟 *Твоя статистика:*\n\n"
            f"✨ Очки: {points}\n"
            f"🎯 Выполнено целей: {completed}"
        ),
        "en": (
            "🌟 *Your Stats:*\n\n"
            f"✨ Points: {points}\n"
            f"🎯 Goals completed: {completed}"
        ),
        "uk": (
            "🌟 *Твоя статистика:*\n\n"
            f"✨ Бали: {points}\n"
            f"🎯 Виконано цілей: {completed}"
        ),
        "be": (
            "🌟 *Твая статыстыка:*\n\n"
            f"✨ Балы: {points}\n"
            f"🎯 Выканана мэт: {completed}"
        ),
        "kk": (
            "🌟 *Сенің статистикаң:*\n\n"
            f"✨ Ұпайлар: {points}\n"
            f"🎯 Орындалған мақсаттар: {completed}"
        ),
        "kg": (
            "🌟 *Сенин статистикаң:*\n\n"
            f"✨ Упайлар: {points}\n"
            f"🎯 Аткарылган максаттар: {completed}"
        ),
        "hy": (
            "🌟 *Քո վիճակագրությունը:*\n\n"
            f"✨ Միավորներ: {points}\n"
            f"🎯 Կատարված նպատակներ: {completed}"
        ),
        "ce": (
            "🌟 *Хьо статистика:* \n\n"
            f"✨ Баллар: {points}\n"
            f"🎯 Хийцар мацахь: {completed}"
        ),
        "md": (
            "🌟 *Statistica ta:*\n\n"
            f"✨ Puncte: {points}\n"
            f"🎯 Obiective realizate: {completed}"
        ),
        "ka": (
            "🌟 *შენი სტატისტიკა:*\n\n"
            f"✨ ქულები: {points}\n"
            f"🎯 შესრულებული მიზნები: {completed}"
        ),
    }

    await update.message.reply_text(
        TEXTS.get(lang, TEXTS["ru"]),
        parse_mode="Markdown"
    )
PREMIUM_CHALLENGES_BY_LANG = {
    "ru": [
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
    ],
    "en": [
        "🔥 Do a good deed for a stranger today.",
        "🌟 Write down 5 of your strengths and tell a friend about them.",
        "💎 Find a new book and read at least one chapter.",
        "🚀 Make a plan for next week with clear goals.",
        "🎯 Take a step toward a big dream.",
        "🙌 Find a way to help a friend or colleague.",
        "💡 Come up with and start a new small project.",
        "🏃 Run 5 minutes more than usual.",
        "🧘‍♀️ Do a deep meditation for 10 minutes.",
        "🖋️ Write a letter to someone who inspired you.",
        "📚 Take a new online course today (at least one lesson).",
        "✨ Find an opportunity to support someone today.",
        "🎨 Draw something and send it to a friend.",
        "🤝 Meet a new person today.",
        "🌱 Help nature: clean up trash or plant a tree.",
        "💬 Write a post on social media about what makes you happy.",
        "🎧 Listen to a self-development podcast for 15 minutes.",
        "🧩 Learn a new skill for an hour.",
        "🏗️ Develop an idea for a startup and write it down.",
        "☀️ Start your morning with gratitude and write 10 points.",
        "🍀 Find a way to make someone smile.",
        "🔥 Do something today that you were afraid to do.",
        "🛠️ Fix something at home that you've been putting off.",
        "💜 Come up with 3 ways to make the world kinder.",
        "🌸 Buy flowers for yourself or a friend.",
        "🚴‍♂️ Go for a long walk or bike ride.",
        "📅 Plan your month ahead.",
        "🧘‍♂️ Try yoga or a new practice.",
        "🎤 Sing your favorite song out loud!",
        "✈️ Plan a dream trip for the future.",
        "🕊️ Make a donation to charity.",
        "🍎 Cook something unusual today.",
        "🔑 Find a solution to an old problem.",
        "🖋️ Write a letter to yourself in 5 years.",
        "🤗 Hug a loved one and tell them how much you value them.",
        "🏞️ Spend an hour in nature without your phone.",
        "📖 Find a new quote and memorize it.",
        "🎬 Watch a movie you've wanted to see for a long time.",
        "🛌 Go to bed an hour earlier today.",
        "📂 Organize your photos and make an album.",
        "📈 Develop a self-improvement strategy.",
        "🎮 Play a game you've never tried before.",
        "🖼️ Create a vision board for your dreams.",
        "🌟 Find a way to inspire someone.",
        "🔔 Set a useful reminder.",
        "💌 Write a thank you message to 3 people.",
        "🧩 Solve a crossword or sudoku.",
        "🏋️‍♂️ Do a workout you've wanted to try for a long time."
    ],
    "uk": [
        "🔥 Зроби сьогодні добру справу для незнайомця.",
        "🌟 Запиши 5 своїх сильних сторін і розкажи про них другу.",
        "💎 Знайди нову книгу і прочитай хоча б 1 розділ.",
        "🚀 Склади план на наступний тиждень з чіткими цілями.",
        "🎯 Зроби крок у напрямку великої мрії.",
        "🙌 Знайди спосіб допомогти другові чи колезі.",
        "💡 Придумай і почни новий маленький проєкт.",
        "🏃 Пробігай більше, ніж зазвичай, хоча б на 5 хвилин.",
        "🧘‍♀️ Проведи глибоку медитацію 10 хвилин.",
        "🖋️ Напиши листа людині, яка тебе надихнула.",
        "📚 Пройди сьогодні новий онлайн-курс (хоча б 1 урок).",
        "✨ Знайди сьогодні можливість когось підтримати.",
        "🎨 Намалюй щось і відправ другу.",
        "🤝 Познайомся сьогодні з новою людиною.",
        "🌱 Допоможи природі: прибери сміття або посади дерево.",
        "💬 Напиши пост у соцмережах про те, що тебе радує.",
        "🎧 Послухай подкаст про саморозвиток 15 хвилин.",
        "🧩 Вивчи нову навичку протягом години.",
        "🏗️ Розроби ідею для стартапу та запиши.",
        "☀️ Почни ранок із вдячності і напиши 10 пунктів.",
        "🍀 Знайди спосіб подарувати комусь усмішку.",
        "🔥 Зроби сьогодні те, чого ти боявся(лася).",
        "🛠️ Відремонтуй вдома щось, що давно відкладав(ла).",
        "💜 Придумай 3 способи зробити світ добрішим.",
        "🌸 Купи собі або другу квіти.",
        "🚴‍♂️ Зроби довгу прогулянку або велопоїздку.",
        "📅 Розпиши план на місяць наперед.",
        "🧘‍♂️ Спробуй йогу або нову практику.",
        "🎤 Заспівай улюблену пісню вголос!",
        "✈️ Заплануй майбутню подорож мрії.",
        "🕊️ Зроби пожертву на благодійність.",
        "🍎 Приготуй незвичайну страву сьогодні.",
        "🔑 Знайди рішення старої проблеми.",
        "🖋️ Напиши листа собі через 5 років.",
        "🤗 Обійми близьку людину і скажи, як цінуєш її.",
        "🏞️ Проведи годину на природі без телефону.",
        "📖 Знайди нову цитату і запам'ятай її.",
        "🎬 Подивися фільм, який давно хотів(ла).",
        "🛌 Лягай спати на годину раніше сьогодні.",
        "📂 Перебери свої фотографії та зроби альбом.",
        "📈 Розроби стратегію самовдосконалення.",
        "🎮 Пограй у гру, яку ще не пробував(ла).",
        "🖼️ Створи дошку візуалізації своєї мрії.",
        "🌟 Знайди спосіб когось надихнути.",
        "🔔 Встанови корисне нагадування.",
        "💌 Напиши подяку 3 людям.",
        "🧩 Розв'яжи кросворд або судоку.",
        "🏋️‍♂️ Зроби тренування, яке давно хотів(ла)."
    ],
    "be": [
        "🔥 Зрабі сёння добрую справу для незнаёмага.",
        "🌟 Запішы 5 сваіх моцных бакоў і раскажы пра іх сябру.",
        "💎 Знайдзі новую кнігу і прачытай хоць бы адзін раздзел.",
        "🚀 Скласці план на наступны тыдзень з дакладнымі мэтамі.",
        "🎯 Зрабі крок у бок вялікай мары.",
        "🙌 Знайдзі спосаб дапамагчы сябру ці калегу.",
        "💡 Прыдумай і пачні новы маленькі праект.",
        "🏃 Прабягі больш, чым звычайна, хоць бы на 5 хвілін.",
        "🧘‍♀️ Зрабі глыбокую медытацыю 10 хвілін.",
        "🖋️ Напішы ліст чалавеку, які цябе натхніў.",
        "📚 Прайдзі сёння новы онлайн-курс (хоць бы адзін урок).",
        "✨ Знайдзі сёння магчымасць некага падтрымаць.",
        "🎨 Намалюй нешта і адправі сябру.",
        "🤝 Пазнаёмся сёння з новым чалавекам.",
        "🌱 Дапамажы прыродзе: прыбяры смецце або пасадзі дрэва.",
        "💬 Напішы пост у сацсетках пра тое, што цябе радуе.",
        "🎧 Пачуй падкаст пра самаразвіццё 15 хвілін.",
        "🧩 Вывучы новую навык цягам гадзіны.",
        "🏗️ Распрацуй ідэю для стартапа і запішы.",
        "☀️ Пачні раніцу з удзячнасці і напішы 10 пунктаў.",
        "🍀 Знайдзі спосаб падарыць каму-небудзь усмешку.",
        "🔥 Зрабі сёння тое, чаго ты баяўся(лася).",
        "🛠️ Выправі дома тое, што даўно адкладаў(ла).",
        "💜 Прыдумай 3 спосабы зрабіць свет дабрэйшым.",
        "🌸 Купі сабе або сябру кветкі.",
        "🚴‍♂️ Зрабі доўгую прагулку або велапаездку.",
        "📅 Распіш план на месяц наперад.",
        "🧘‍♂️ Паспрабуй ёгу або новую практыку.",
        "🎤 Спявай любімую песню ўслых!",
        "✈️ Заплануй будучую паездку мары.",
        "🕊️ Зрабі ахвяраванне на дабрачыннасць.",
        "🍎 Падрыхтуй незвычайную страву сёння.",
        "🔑 Знайдзі рашэнне старой праблемы.",
        "🖋️ Напішы ліст сабе праз 5 гадоў.",
        "🤗 Абдымі блізкага чалавека і скажы, як цэніш яго.",
        "🏞️ Правядзі гадзіну на прыродзе без тэлефона.",
        "📖 Знайдзі новую цытату і запомні яе.",
        "🎬 Паглядзі фільм, які даўно хацеў(ла).",
        "🛌 Лажыся спаць на гадзіну раней сёння.",
        "📂 Перабяры свае фатаграфіі і зрабі альбом.",
        "📈 Распрацуй стратэгію паляпшэння сябе.",
        "🎮 Паграй у гульню, якую яшчэ не спрабаваў(ла).",
        "🖼️ Ствары дошку візуалізацыі сваёй мары.",
        "🌟 Знайдзі спосаб некага натхніць.",
        "🔔 Устанаві карыснае напамінанне.",
        "💌 Напішы падзяку 3 людзям.",
        "🧩 Разгадай крыжаванку або судоку.",
        "🏋️‍♂️ Зрабі трэніроўку, якую даўно хацеў(ла)."
    ],
    "kk": [
        "🔥 Бүгін бейтаныс адамға жақсылық жаса.",
        "🌟 5 мықты жағыңды жазып, досыңа айтып бер.",
        "💎 Жаңа кітап тауып, кем дегенде 1 тарауын оқы.",
        "🚀 Келесі аптаға нақты мақсаттармен жоспар құр.",
        "🎯 Үлкен арманыңа бір қадам жаса.",
        "🙌 Досыңа немесе әріптесіңе көмектесудің жолын тап.",
        "💡 Жаңа шағын жоба ойлап тауып, басташы.",
        "🏃 Әдеттегіден 5 минут көбірек жүгір.",
        "🧘‍♀️ 10 минут терең медитация жаса.",
        "🖋️ Өзіңе шабыт берген адамға хат жаз.",
        "📚 Бүгін жаңа онлайн-курстан (кемінде 1 сабақ) өт.",
        "✨ Бүгін біреуді қолдау мүмкіндігін тап.",
        "🎨 Бірдеңе салып, досыңа жібер.",
        "🤝 Бүгін жаңа адаммен таныс.",
        "🌱 Табиғатқа көмектес: қоқыс жина немесе ағаш отырғыз.",
        "💬 Саған қуаныш сыйлайтын нәрсе туралы әлеуметтік желіде жаз.",
        "🎧 15 минуттай өзін-өзі дамыту подкастын тыңда.",
        "🧩 Бір сағат бойы жаңа дағдыны үйрен.",
        "🏗️ Стартапқа арналған идея ойлап тауып, жаз.",
        "☀️ Таңды алғыс айтудан бастап, 10 пункт жаз.",
        "🍀 Біреуді күлдірту жолын тап.",
        "🔥 Бүгін қорқатын нәрсеңді жаса.",
        "🛠️ Үйде көптен бері істемей жүрген дүниені жөнде.",
        "💜 Әлемді жақсартудың 3 жолын ойлап тап.",
        "🌸 Өзіңе немесе досыңа гүл ал.",
        "🚴‍♂️ Ұзақ серуенде немесе велосипедпен жүр.",
        "📅 Бір айға алдын ала жоспар жаса.",
        "🧘‍♂️ Йога немесе жаңа практиканы байқап көр.",
        "🎤 Ұнайтын әніңді дауыстап айт!",
        "✈️ Арман сапарын жоспарла.",
        "🕊️ Қайырымдылыққа ақша аудар.",
        "🍎 Бүгін ерекше тағам дайында.",
        "🔑 Ескі мәселені шешудің жолын тап.",
        "🖋️ Өзіңе 5 жылдан кейін жазатын хат жаз.",
        "🤗 Жақын адамды құшақтап, қадірлейтініңді айт.",
        "🏞️ Телефонсыз табиғатта бір сағат өткіз.",
        "📖 Жаңа дәйексөз тауып, жаттап ал.",
        "🎬 Көптен бері көргің келген фильмді көр.",
        "🛌 Бүгін бір сағатқа ертерек ұйықта.",
        "📂 Суреттеріңді реттеп, альбом жаса.",
        "📈 Өзіңді дамыту стратегиясын құр.",
        "🎮 Бұрын ойнамаған ойынды ойна.",
        "🖼️ Арманыңның визуалды тақтасын жаса.",
        "🌟 Біреуді шабыттандырудың жолын тап.",
        "🔔 Пайдалы еске салғыш орнат.",
        "💌 3 адамға алғыс хат жаз.",
        "🧩 Кроссворд немесе судоку шеш.",
        "🏋️‍♂️ Көптен бері істегің келген жаттығуды жаса."
    ],
    "kg": [
        "🔥 Бүгүн бейтааныш адамга жакшылык жаса.",
        "🌟 5 күчтүү тарабыңды жазып, досуңа айт.",
        "💎 Жаңы китеп тап жана жок дегенде 1 бөлүм оку.",
        "🚀 Кийинки аптага максаттуу план түз.",
        "🎯 Чоң кыялга бир кадам жаса.",
        "🙌 Досуңа же кесиптешиңе жардам берүүнүн жолун тап.",
        "💡 Жаңы чакан долбоорду ойлоп таап, башта.",
        "🏃 Кадимкидейден 5 мүнөт көбүрөөк чурка.",
        "🧘‍♀️ 10 мүнөт терең медитация жаса.",
        "🖋️ Сага дем берген адамга кат жаз.",
        "📚 Бүгүн жаңы онлайн-курстан (жок дегенде 1 сабак) өт.",
        "✨ Бүгүн кимдир бирөөгө жардам берүүнү тап.",
        "🎨 Бир нерсе тарт жана досуңа жөнөт.",
        "🤝 Бүгүн жаңы адам менен таанышууну көздө.",
        "🌱 Табиятка жардам бер: таштанды чогулт же дарак отургуз.",
        "💬 Сага кубаныч тартуулаган нерсе жөнүндө социалдык тармакта жаз.",
        "🎧 15 мүнөт өзүн өнүктүрүү подкастын угууну унутпа.",
        "🧩 Бир саат бою жаңы көндүмдү үйрөн.",
        "🏗️ Стартап идея ойлоп таап, жаз.",
        "☀️ Эртең менен рахмат айтып, 10 пункт жаз.",
        "🍀 Бирөөнү жылмайтуунун жолун тап.",
        "🔥 Бүгүн корккон нерсеңди жаса.",
        "🛠️ Үйдө көптөн бери жасалбай жаткан ишти бүтүр.",
        "💜 Дүйнөнү жакшы кылуунун 3 жолун ойлоп тап.",
        "🌸 Өзіңө же досуңа гүл сатып ал.",
        "🚴‍♂️ Узун сейил же велосипед айда.",
        "📅 Бир айга алдын ала план түз.",
        "🧘‍♂️ Йога же жаңы практиканы байка.",
        "🎤 Жаккан ырды үн катуу ырда!",
        "✈️ Кыял сапарыңды планда.",
        "🕊️ Кайрымдуулукка жардам бер.",
        "🍎 Бүгүн өзгөчө тамак даярда.",
        "🔑 Эски маселени чечүүнүн жолун тап.",
        "🖋️ 5 жылдан кийин өзүңө кат жаз.",
        "🤗 Жакын адамыңды кучактап, баалай турганыңды айт.",
        "🏞️ Телефонсуз табиятта бир саат бол.",
        "📖 Жаңы цитатаны таап, жаттап ал.",
        "🎬 Көптөн бери көргүң келген тасманы көр.",
        "🛌 Бүгүн бир саат эрте укта.",
        "📂 Сүрөттөрдү ирээттеп, альбом түз.",
        "📈 Өзүн өнүктүрүү стратегиясын иштеп чык.",
        "🎮 Мурун ойнобогон оюнду ойно.",
        "🖼️ Кыялыңдын визуалдык тактасын түз.",
        "🌟 Бирөөнү шыктандыруунун жолун тап.",
        "🔔 Пайдалы эскертме кой.",
        "💌 3 адамга ыраазычылык кат жаз.",
        "🧩 Кроссворд же судоку чеч.",
        "🏋️‍♂️ Көптөн бери жасагың келген машыгууну жаса."
    ],
    "hy": [
        "🔥 Այսօր բարիք արա անծանոթի համար։",
        "🌟 Գրիր քո 5 ուժեղ կողմերը և պատմիր ընկերոջդ։",
        "💎 Գտիր նոր գիրք և կարդա առնվազն մեկ գլուխ։",
        "🚀 Կազմիր հաջորդ շաբաթվա հստակ նպատակներով պլան։",
        "🎯 Քայլ արա դեպի մեծ երազանքդ։",
        "🙌 Գտիր եղանակ ընկերոջ կամ գործընկերոջ օգնելու։",
        "💡 Հորինիր և սկսիր նոր փոքր նախագիծ։",
        "🏃 Վազիր 5 րոպե ավելի, քան սովորաբար։",
        "🧘‍♀️ Կատարիր 10 րոպե խորը մեդիտացիա։",
        "🖋️ Գրիր նամակ այն մարդուն, ով քեզ ոգեշնչել է։",
        "📚 Այսօր անցիր նոր առցանց դասընթաց (առնվազն 1 դաս)։",
        "✨ Այսօր գտիր հնարավորութուն մեկին աջակցելու։",
        "🎨 Որևէ բան նկարիր ու ուղարկիր ընկերոջդ։",
        "🤝 Այսօր ծանոթացիր նոր մարդու հետ։",
        "🌱 Օգնիր բնությանը՝ աղբ հավաքիր կամ ծառ տնկիր։",
        "💬 Գրի սոցիալական ցանցում այն մասին, ինչ քեզ ուրախացնում է։",
        "🎧 Լսիր ինքնազարգացման փոդքասթ 15 րոպե։",
        "🧩 Մեկ ժամ ուսումնասիրիր նոր հմտություն։",
        "🏗️ Մշակի՛ր ստարտափի գաղափար և գրի։",
        "☀️ Առավոտը սկսիր երախտագիտությամբ և գրիր 10 կետ։",
        "🍀 Գտիր ինչ-որ մեկին ժպտացնելու եղանակ։",
        "🔥 Այսօր արա այն, ինչից վախենում էիր։",
        "🛠️ Տանը վերանորոգիր մի բան, որ վաղուց չէիր անում։",
        "💜 Մտածիր աշխարհի բարելավման 3 եղանակ։",
        "🌸 Գնի՛ր քեզ կամ ընկերոջդ ծաղիկ։",
        "🚴‍♂️ Քայլիր երկար կամ հեծանիվ վարիր։",
        "📅 Կազմիր պլան մեկ ամսով առաջ։",
        "🧘‍♂️ Փորձիր յոգա կամ նոր պրակտիկա։",
        "🎤 Բարձրաձայն երգիր սիրելի երգդ։",
        "✈️ Պլանավորի՛ր երազանքների ճամփորդություն։",
        "🕊️ Նվիրաբերիր բարեգործությանը։",
        "🍎 Պատրաստիր անսովոր ուտեստ այսօր։",
        "🔑 Գտիր հին խնդրի լուծումը։",
        "🖋️ Գրիր նամակ քեզ՝ 5 տարի հետո կարդալու համար։",
        "🤗 Գրկիր հարազատիդ և ասա, թե ինչքան ես գնահատում։",
        "🏞️ Ժամ անցկացրու բնության գրկում առանց հեռախոսի։",
        "📖 Գտիր նոր մեջբերում և հիշիր այն։",
        "🎬 Դիտիր ֆիլմ, որ վաղուց ուզում էիր։",
        "🛌 Այսօր մեկ ժամ շուտ գնա քնելու։",
        "📂 Դասավորիր լուսանկարներդ և ալբոմ ստեղծիր։",
        "📈 Մշակի՛ր ինքնազարգացման ռազմավարություն։",
        "🎮 Խաղա մի խաղ, որ երբեք չես փորձել։",
        "🖼️ Ստեղծիր երազանքներիդ վիզուալ տախտակ։",
        "🌟 Գտիր մեկին ոգեշնչելու եղանակ։",
        "🔔 Կարգավորի՛ր օգտակար հիշեցում։",
        "💌 Գրիր շնորհակալական նամակ 3 մարդու։",
        "🧩 Լուծիր խաչբառ կամ սուդոկու։",
        "🏋️‍♂️ Կատարիր մարզում, որ վաղուց ուզում էիր։"
    ],
    "ce": [
        "🔥 Хьо шу бахьара вац ло къобал дойла цуьнан хьуна.",
        "🌟 Дахьара йу 5 цуьнан хийц а, кхетам сагIа хьуна ву.",
        "💎 Ца йу ктаб цаьна йа, йоза тара цуьнан хийц.",
        "🚀 Кхети цуьнан догIар гIир хетам догIара хьо.",
        "🎯 Хаьна догIар гIир хетам къобал къахета.",
        "🙌 Далат хьо кхети ца хьо ву, са къахетам хетам.",
        "💡 Хьо къобал дойла ю, хьо йа ву вуьйре.",
        "🏃 Чун къобал 5 минут цаьна хийц.",
        "🧘‍♀️ 10 минут догIар медитация цуьнан хийц.",
        "🖋️ Хьо хьа йиш ю а, цуьнан хийц а хьо къобал ду.",
        "📚 Бугун ца онлайн-курс цаьна хийц (йу дойла йа).",
        "✨ Бугун йу хьо къахетам ю, хьо хетам.",
        "🎨 Хьо дойла ца а, кхетам сагIа хьуна ву.",
        "🤝 Бугун кхетам ца хьо хетам.",
        "🌱 Табигат догIар, цуьнан хийц къобал ца.",
        "💬 Са соцсети ю ца а, къобал цуьнан хийц.",
        "🎧 15 минут ца догIар подкаст йозан.",
        "🧩 1 саат ца къобал хийц.",
        "🏗️ Стартап идеа ца хийц, къахета.",
        "☀️ Хьо дуьйна алгыс а къахета, 10 къахета.",
        "🍀 Са къахета, йиш дойла а хьо.",
        "🔥 Кхетам бугун цуьнан хийц.",
        "🛠️ Г1айна къобал хийц.",
        "💜 3 къахета хьо цуьнан хийц.",
        "🌸 Хьо къобал дойла ю, кхетам ю а хьо.",
        "🚴‍♂️ ДогIар прогулка ца хийц.",
        "📅 1 йи са къобал хийц.",
        "🧘‍♂️ Йога ца хийц.",
        "🎤 Йу къобал цуьнан хийц.",
        "✈️ Арман йу къобал ца.",
        "🕊️ Благотворительность къобал хийц.",
        "🍎 Бу къобал цуьнан хийц.",
        "🔑 Старая проблема къахета.",
        "🖋️ 5 цуьнан хийц а къахета.",
        "🤗 Близкий адам къобал хийц.",
        "🏞️ Табигат даьлча къахета.",
        "📖 Цуьнан хийц а хьо къахета.",
        "🎬 Бу къобал хийц.",
        "🛌 Са къобал хийц.",
        "📂 Фото къахета.",
        "📈 Развитие стратегия хийц.",
        "🎮 Ойын къобал хийц.",
        "🖼️ Визуализация доск къахета.",
        "🌟 Къахета хьо хетам.",
        "🔔 Еске салғыш орнат.",
        "💌 3 адамға алғыс хат жаз.",
        "🧩 Кроссворд не судоку шеш.",
        "🏋️‍♂️ Көптен бері істегің келген жаттығуды жаса."
    ],
    "md": [
        "🔥 Fă o faptă bună pentru un străin astăzi.",
        "🌟 Scrie 5 calități ale tale și povestește unui prieten.",
        "💎 Găsește o carte nouă și citește cel puțin un capitol.",
        "🚀 Fă un plan pentru săptămâna viitoare cu obiective clare.",
        "🎯 Fă un pas spre un vis mare.",
        "🙌 Găsește o cale de a ajuta un prieten sau coleg.",
        "💡 Inventază și începe un nou mic proiect.",
        "🏃 Aleargă cu 5 minute mai mult ca de obicei.",
        "🧘‍♀️ Fă o meditație profundă de 10 minute.",
        "🖋️ Scrie o scrisoare cuiva care te-a inspirat.",
        "📚 Fă azi un curs online nou (cel puțin 1 lecție).",
        "✨ Găsește azi o ocazie de a susține pe cineva.",
        "🎨 Desenează ceva și trimite unui prieten.",
        "🤝 Fă cunoștință azi cu o persoană nouă.",
        "🌱 Ajută natura: strânge gunoi sau plantează un copac.",
        "💬 Scrie pe rețele ce te face fericit.",
        "🎧 Ascultă 15 min. podcast de dezvoltare personală.",
        "🧩 Învață o abilitate nouă timp de o oră.",
        "🏗️ Dezvoltă o idee de startup și noteaz-o.",
        "☀️ Începe dimineața cu recunoștință, scrie 10 puncte.",
        "🍀 Găsește o cale să faci pe cineva să zâmbească.",
        "🔥 Fă azi ceva ce îți era frică să faci.",
        "🛠️ Repară ceva acasă ce amâni de mult.",
        "💜 Gândește 3 moduri să faci lumea mai bună.",
        "🌸 Cumpără flori pentru tine sau prieten.",
        "🚴‍♂️ Fă o plimbare lungă sau o tură cu bicicleta.",
        "📅 Fă un plan pe o lună înainte.",
        "🧘‍♂️ Încearcă yoga sau o practică nouă.",
        "🎤 Cântă melodia preferată cu voce tare!",
        "✈️ Planifică o călătorie de vis.",
        "🕊️ Donează pentru caritate.",
        "🍎 Gătește ceva deosebit azi.",
        "🔑 Găsește o soluție la o problemă veche.",
        "🖋️ Scrie-ți o scrisoare pentru peste 5 ani.",
        "🤗 Îmbrățișează pe cineva drag și spune cât îl apreciezi.",
        "🏞️ Petrece o oră în natură fără telefon.",
        "📖 Găsește o nouă citat și memorează-l.",
        "🎬 Privește un film pe care îl voiai demult.",
        "🛌 Culcă-te cu o oră mai devreme azi.",
        "📂 Sortează pozele și fă un album.",
        "📈 Fă o strategie de dezvoltare personală.",
        "🎮 Joacă un joc nou pentru tine.",
        "🖼️ Fă un panou vizual cu visele tale.",
        "🌟 Găsește o cale să inspiri pe cineva.",
        "🔔 Setează o notificare utilă.",
        "💌 Scrie un mesaj de mulțumire la 3 oameni.",
        "🧩 Rezolvă un rebus sau sudoku.",
        "🏋️‍♂️ Fă antrenamentul pe care îl vrei demult."
    ],
    "ka": [
        "🔥 დღეს კეთილი საქმე გააკეთე უცხოსთვის.",
        "🌟 ჩაწერე შენი 5 ძლიერი მხარე და მოუყევი მეგობარს.",
        "💎 მოძებნე ახალი წიგნი და წაიკითხე ერთი თავი მაინც.",
        "🚀 შეადგინე შემდეგი კვირის გეგმა კონკრეტული მიზნებით.",
        "🎯 გადადგი ნაბიჯი დიდი ოცნებისკენ.",
        "🙌 იპოვე გზა, დაეხმარო მეგობარს ან კოლეგას.",
        "💡 გამოიგონე და დაიწყე ახალი მცირე პროექტი.",
        "🏃 ირბინე 5 წუთით მეტი, ვიდრე ჩვეულებრივ.",
        "🧘‍♀️ გააკეთე 10 წუთიანი ღრმა მედიტაცია.",
        "🖋️ წერილი მისწერე ადამიანს, ვინც შეგიძინა.",
        "📚 გაიარე ახალი ონლაინ კურსი (მინიმუმ ერთი გაკვეთილი).",
        "✨ იპოვე შესაძლებლობა, ვინმეს დაეხმარო დღეს.",
        "🎨 დახატე რამე და გაუგზავნე მეგობარს.",
        "🤝 დღეს გაიცანი ახალი ადამიანი.",
        "🌱 დაეხმარე ბუნებას: დაალაგე ნაგავი ან დარგე ხე.",
        "💬 დაწერე სოციალურ ქსელში, რა გიხარია.",
        "🎧 მოუსმინე 15 წუთით თვითგანვითარების პოდკასტს.",
        "🧩 ისწავლე ახალი უნარი ერთი საათის განმავლობაში.",
        "🏗️ შეიმუშავე სტარტაპის იდეა და ჩაიწერე.",
        "☀️ დილა დაიწყე მადლიერებით და ჩამოწერე 10 მიზეზი.",
        "🍀 იპოვე გზა, გაახარო ვინმე.",
        "🔥 გააკეთე ის, რისიც გეშინოდა.",
        "🛠️ სახლში ის გააკეთე, რასაც დიდხანს აჭიანურებდი.",
        "💜 იფიქრე სამყაროს უკეთესობისკენ შეცვლის 3 გზაზე.",
        "🌸 იყიდე ყვავილები შენთვის ან მეგობრისთვის.",
        "🚴‍♂️ გააკეთე გრძელი გასეირნება ან ველოსიპედით სიარული.",
        "📅 მოიფიქრე გეგმა ერთი თვით წინ.",
        "🧘‍♂️ სცადე იოგა ან ახალი პრაქტიკა.",
        "🎤 ხმამაღლა იმღერე საყვარელი სიმღერა!",
        "✈️ დაგეგმე საოცნებო მოგზაურობა.",
        "🕊️ გაიღე საქველმოქმედოდ.",
        "🍎 მოამზადე განსხვავებული კერძი დღეს.",
        "🔑 მოძებნე ძველი პრობლემის გადაწყვეტა.",
        "🖋️ წერილი მისწერე საკუთარ თავს 5 წელიწადში.",
        "🤗 ჩაეხუტე ახლობელს და უთხარი, რამდენად აფასებ მას.",
        "🏞️ ერთი საათი ბუნებაში გაატარე ტელეფონის გარეშე.",
        "📖 მოძებნე ახალი ციტატა და დაიმახსოვრე.",
        "🎬 უყურე ფილმს, რომელიც დიდი ხანია გინდა.",
        "🛌 დღეს ერთი საათით ადრე დაიძინე.",
        "📂 დაალაგე ფოტოები და შექმენი ალბომი.",
        "📈 შეიმუშავე თვითგანვითარების სტრატეგია.",
        "🎮 ითამაშე თამაში, რომელიც ჯერ არ გითამაშია.",
        "🖼️ შექმენი შენი ოცნების ვიზუალური დაფა.",
        "🌟 იპოვე გზა, რომ ვინმე შთააგონო.",
        "🔔 დააყენე სასარგებლო შეხსენება.",
        "💌 სამ ადამიანს მადლობის წერილი მიწერე.",
        "🧩 ამოხსენი კროსვორდი ან სუდოკუ.",
        "🏋️‍♂️ გააკეთე ის ვარჯიში, რასაც დიდი ხანია გეგმავდი."
    ],
}

def get_premium_stats(user_id: str):
    stats = get_user_stats(user_id)
    return {
        "completed_goals": stats.get("completed_goals", stats.get("goals_completed", 0)),  # поддержка старых и новых ключей
        "habits_tracked": stats.get("habits", stats.get("total_habits", 0)),              # поддержка старых и новых ключей
        "days_active": stats.get("days_active", 0),
        "mood_entries": stats.get("mood_entries", 0)
    }

EXCLUSIVE_MODES_BY_LANG = {
    "ru": {
        "coach": "💪 Ты — мой личный коуч. Помогай чётко, по делу, давай советы, поддерживай! 🚀",
        "flirty": "😉 Ты — немного флиртуешь и поддерживаешь. Отвечай с теплом и лёгким флиртом 💜✨",
    },
    "uk": {
        "coach": "💪 Ти — мій особистий коуч. Допомагай чітко, по суті, давай поради! 🚀",
        "flirty": "😉 Ти — трохи фліртуєш і підтримуєш. Відповідай тепло та з легкою грою 💜✨",
    },
    "be": {
        "coach": "💪 Ты — мой асабісты коуч. Дапамагай дакладна, па справе, давай парады! 🚀",
        "flirty": "😉 Ты — трохі фліртуеш і падтрымліваеш. Адказвай цёпла і з лёгкім фліртам 💜✨",
    },
    "kk": {
        "coach": "💪 Сен — менің жеке коучымсың. Нақты, қысқа, пайдалы кеңес бер, жігерлендір! 🚀",
        "flirty": "😉 Сен — сәл флирт пен қолдау көрсетесің. Жылы, жеңіл әзілмен жауап бер 💜✨",
    },
    "kg": {
        "coach": "💪 Сен — менин жеке коучумсуң. Так, кыскача, пайдалуу кеңештерди бер! 🚀",
        "flirty": "😉 Сен — бир аз флирт кыласың жана колдойсуң. Жылуу, жеңил ойноок жооп бер 💜✨",
    },
    "hy": {
        "coach": "💪 Դու իմ անձնական քոուչն ես։ Օգնիր հստակ, գործնական, տուր խորհուրդներ, ոգեշնչիր! 🚀",
        "flirty": "😉 Դու մի քիչ ֆլիրտում ես և աջակցում։ Պատասխանիր ջերմորեն և թեթև ֆլիրտով 💜✨",
    },
    "ce": {
        "coach": "💪 Хьо — миниг персоналийн коуч. Йойла хьалха, да дийцар дуьйна, совета шун! 🚀",
        "flirty": "😉 Хьо — ца хьалха флирт ду хьалхара а, цуьнан цуьнан дийцарца. Йоьлча цуьнан цуьнан флирт 💜✨",
    },
    "md": {
        "coach": "💪 Tu ești antrenorul meu personal. Ajută clar, la subiect, dă sfaturi, inspiră! 🚀",
        "flirty": "😉 Ești puțin cochet(ă) și susținător(oare). Răspunde călduros și cu un flirt ușor 💜✨",
    },
    "ka": {
        "coach": "💪 შენ ხარ ჩემი პირადი ქოუჩი. დამეხმარე მკაფიოდ, საქმეზე, მომეცი რჩევები, შთააგონე! 🚀",
        "flirty": "😉 შენ ოდნავ ფლირტაობ და ამასთან ერთად მხარდაჭერას იჩენ. უპასუხე თბილად და მსუბუქი ფლირტით 💜✨",
    },
    "en": {
        "coach": "💪 You are my personal coach. Help clearly and to the point, give advice, motivate! 🚀",
        "flirty": "😉 You're a bit flirty and supportive. Reply warmly and with a light flirt 💜✨",
    },
}

PREMIUM_REPORT_TEXTS = {
    "ru": (
        "✅ *Твой персональный отчёт за неделю:*\n\n"
        "🎯 Завершено целей: {completed_goals}\n"
        "🌱 Привычек выполнено: {completed_habits}\n"
        "📅 Дней активности: {days_active}\n"
        "📝 Записей настроения: {mood_entries}\n\n"
        "Ты молодец! Продолжай в том же духе 💜"
    ),
    "uk": (
        "✅ *Твій персональний звіт за тиждень:*\n\n"
        "🎯 Виконано цілей: {completed_goals}\n"
        "🌱 Виконано звичок: {completed_habits}\n"
        "📅 Днів активності: {days_active}\n"
        "📝 Записів настрою: {mood_entries}\n\n"
        "Ти молодець! Продовжуй у тому ж дусі 💜"
    ),
    "be": (
        "✅ *Твой асабісты справаздача за тыдзень:*\n\n"
        "🎯 Выканана мэтаў: {completed_goals}\n"
        "🌱 Выканана звычак: {completed_habits}\n"
        "📅 Дзён актыўнасці: {days_active}\n"
        "📝 Запісаў настрою: {mood_entries}\n\n"
        "Ты малайчына! Працягвай у тым жа духу 💜"
    ),
    "kk": (
        "✅ *Апталық жеке есебің:*\n\n"
        "🎯 Орындалған мақсаттар: {completed_goals}\n"
        "🌱 Орындалған әдеттер: {completed_habits}\n"
        "📅 Белсенді күндер: {days_active}\n"
        "📝 Көңіл күй жазбалары: {mood_entries}\n\n"
        "Жарайсың! Осылай жалғастыра бер 💜"
    ),
    "kg": (
        "✅ *Жумалык жекече отчетуң:*\n\n"
        "🎯 Аткарылган максаттар: {completed_goals}\n"
        "🌱 Аткарылган адаттар: {completed_habits}\n"
        "📅 Активдүү күндөр: {days_active}\n"
        "📝 Көңүл-күй жазуулары: {mood_entries}\n\n"
        "Афарың! Ошентип уланта бер 💜"
    ),
    "hy": (
        "✅ *Քո անձնական շաբաթական հաշվետվությունը:*\n\n"
        "🎯 Կատարված նպատակներ: {completed_goals}\n"
        "🌱 Կատարված սովորություններ: {completed_habits}\n"
        "📅 Ակտիվ օրեր: {days_active}\n"
        "📝 Տրամադրության գրառումներ: {mood_entries}\n\n"
        "Դու հրաշալի ես։ Շարունակի՛ր այսպես 💜"
    ),
    "ce": (
        "✅ *Тхо персоналийна хафта йоьлча:* \n\n"
        "🎯 ДӀаязде мацахь: {completed_goals}\n"
        "🌱 ДӀаязде привычка: {completed_habits}\n"
        "📅 Активний денаш: {days_active}\n"
        "📝 Хилда мотивацийн тӀемаш: {mood_entries}\n\n"
        "Хьо ду ю! Чу хила ю бина хийцахь 💜"
    ),
    "md": (
        "✅ *Raportul tău personal pentru săptămână:*\n\n"
        "🎯 Obiective realizate: {completed_goals}\n"
        "🌱 Obiceiuri îndeplinite: {completed_habits}\n"
        "📅 Zile de activitate: {days_active}\n"
        "📝 Înregistrări de dispoziție: {mood_entries}\n\n"
        "Bravo! Continuă tot așa 💜"
    ),
    "ka": (
        "✅ *შენი პერსონალური კვირის ანგარიში:*\n\n"
        "🎯 შესრულებული მიზნები: {completed_goals}\n"
        "🌱 შესრულებული ჩვევები: {completed_habits}\n"
        "📅 აქტიური დღეები: {days_active}\n"
        "📝 განწყობის ჩანაწერები: {mood_entries}\n\n"
        "შესანიშნავია! ასე გააგრძელე 💜"
    ),
    "en": (
        "✅ *Your personal report for the week:*\n\n"
        "🎯 Goals completed: {completed_goals}\n"
        "🌱 Habits completed: {completed_habits}\n"
        "📅 Days active: {days_active}\n"
        "📝 Mood entries: {mood_entries}\n\n"
        "Great job! Keep it up 💜"
    ),
}

async def premium_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Проверка: только премиум или ты
    if not (is_premium(user_id) or user_id == "7775321566"):
        await update.message.reply_text("🔒 Эта функция доступна только для Mindra+.")
        return

    stats = get_stats(user_id)
    lang = user_languages.get(user_id, "ru")
    template = PREMIUM_REPORT_TEXTS.get(lang, PREMIUM_REPORT_TEXTS["ru"])
    report_text = template.format(
        completed_goals=stats.get("completed_goals", 0),
        completed_habits=stats.get("completed_habits", 0),
        days_active=stats.get("days_active", 0),
        mood_entries=stats.get("mood_entries", 0),
    )
    await update.message.reply_text(report_text, parse_mode="Markdown")
    
async def premium_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # Тут можешь оставить проверку на свой id или на PREMIUM_USERS
    if not (is_premium(user_id) or user_id == OWNER_ID):        # Переведённое сообщение о недоступности
        lang = user_languages.get(user_id, "ru")
        locked_msgs = {
            "ru": "🔒 Эта функция доступна только Mindra+ ✨",
            "uk": "🔒 Ця функція доступна лише для Mindra+ ✨",
            "be": "🔒 Гэтая функцыя даступная толькі для Mindra+ ✨",
            "kk": "🔒 Бұл функция тек Mindra+ пайдаланушыларына қолжетімді ✨",
            "kg": "🔒 Бул функция Mindra+ үчүн гана жеткиликтүү ✨",
            "hy": "🔒 Այս գործառույթը հասանելի է միայն Mindra+ օգտատերերի համար ✨",
            "ce": "🔒 Хlин функцанца цуьнан ю Mindra+ кхеташ ву ✨",
            "md": "🔒 Această funcție este disponibilă doar pentru Mindra+ ✨",
            "ka": "🔒 ეს ფუნქცია ხელმისაწვდომია მხოლოდ Mindra+ მომხმარებლებისთვის ✨",
            "en": "🔒 This feature is available for Mindra+ only ✨",
        }

        await update.message.reply_text(locked_msgs.get(lang, locked_msgs["ru"]))
        return

    lang = user_languages.get(user_id, "ru")
    challenges = PREMIUM_CHALLENGES_BY_LANG.get(lang, PREMIUM_CHALLENGES_BY_LANG["ru"])
    challenge = random.choice(challenges)

    challenge_title = {
        "ru": "💎 *Твой челлендж на сегодня:*",
        "uk": "💎 *Твій челлендж на сьогодні:*",
        "en": "💎 *Your challenge for today:*",
        "be": "💎 *Твой чэлендж на сёння:*",
        "kk": "💎 *Бүгінгі челенджің:*",
        "kg": "💎 *Бүгүнкү челенджиң:*",
        "hy": "💎 *Այսօրվա քո չելենջը:*",
        "ce": "💎 *Бугунг хила челендж:*",
        "md": "💎 *Provocarea ta pentru azi:*",
        "ka": "💎 *შენი ჩელენჯი დღევანდელი დღისთვის:*",
    }

    await update.message.reply_text(
        f"{challenge_title.get(lang, challenge_title['ru'])}\n\n{challenge}",
        parse_mode="Markdown"
    )

# 🌸 3. Эксклюзивный режим общения
async def premium_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Мультиязычные тексты
    MODE_SELECT_TEXT = {
        "ru": "Выбери эксклюзивный режим общения:",
        "uk": "Оберіть ексклюзивний режим спілкування:",
        "be": "Абяры эксклюзіўны рэжым зносін:",
        "kk": "Эксклюзивті сөйлесу режимін таңдаңыз:",
        "kg": "Эксклюзивдүү баарлашуу режимин танда:",
        "hy": "Ընտրեք էքսկլյուզիվ շփման ռեժիմը․",
        "ce": "Эксклюзиван хилла чуйна режимех хьажар:",
        "md": "Alegeți modul exclusiv de comunicare:",
        "ka": "აირჩიე ექსკლუზიური საუბრის რეჟიმი:",
        "en": "Choose an exclusive communication mode:",
    }

    MODE_BUTTONS = {
        "ru": [
            InlineKeyboardButton("🧑‍🏫 Коуч", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Флирт", callback_data="premium_mode_flirt"),
        ],
        "uk": [
            InlineKeyboardButton("🧑‍🏫 Коуч", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Флірт", callback_data="premium_mode_flirt"),
        ],
        "be": [
            InlineKeyboardButton("🧑‍🏫 Коуч", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Флірт", callback_data="premium_mode_flirt"),
        ],
        "kk": [
            InlineKeyboardButton("🧑‍🏫 Коуч", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Флирт", callback_data="premium_mode_flirt"),
        ],
        "kg": [
            InlineKeyboardButton("🧑‍🏫 Коуч", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Флирт", callback_data="premium_mode_flirt"),
        ],
        "hy": [
            InlineKeyboardButton("🧑‍🏫 Քոուչ", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Ֆլիրտ", callback_data="premium_mode_flirt"),
        ],
        "ce": [
            InlineKeyboardButton("🧑‍🏫 Коуч", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Флирт", callback_data="premium_mode_flirt"),
        ],
        "md": [
            InlineKeyboardButton("🧑‍🏫 Coach", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Flirt", callback_data="premium_mode_flirt"),
        ],
        "ka": [
            InlineKeyboardButton("🧑‍🏫 ქოუჩი", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 ფლირტი", callback_data="premium_mode_flirt"),
        ],
        "en": [
            InlineKeyboardButton("🧑‍🏫 Coach", callback_data="premium_mode_coach"),
            InlineKeyboardButton("💜 Flirt", callback_data="premium_mode_flirt"),
        ],
    }

    # Получаем язык пользователя
    lang = user_languages.get(user_id, "ru")

     # Проверка доступа: либо премиум, либо твой Telegram ID
    if not (is_premium(user_id) or user_id == "7775321566"):
        await update.message.reply_text(
            PREMIUM_ONLY_TEXTS.get(lang, PREMIUM_ONLY_TEXTS["ru"])
        )
        return
        
    text = MODE_SELECT_TEXT.get(lang, MODE_SELECT_TEXT["ru"])
    keyboard = [MODE_BUTTONS.get(lang, MODE_BUTTONS["ru"])]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def premium_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    lang = user_languages.get(user_id, "ru")

    LOCKED_MSGS = {
        "ru": "🔒 Эта функция доступна только подписчикам Mindra+.",
        "uk": "🔒 Ця функція доступна лише для підписників Mindra+.",
        "en": "🔒 This feature is only available to Mindra+ subscribers.",
        "be": "🔒 Гэтая функцыя даступная толькі падпісчыкам Mindra+.",
        "kk": "🔒 Бұл мүмкіндік тек Mindra+ жазылушыларына қолжетімді.",
        "kg": "🔒 Бул функция Mindra+ жазылуучулары үчүн гана жеткиликтүү.",
        "hy": "🔒 Այս գործառույթը հասանելի է միայն Mindra+ բաժանորդներին։",
        "ce": "🔒 Дина функция Mindra+ яззийна догъа кхоллар хетам.",
        "md": "🔒 Această funcție este disponibilă doar abonaților Mindra+.",
        "ka": "🔒 ეს ფუნქცია ხელმისაწვდომია მხოლოდ Mindra+ აბონენტებისთვის.",
    }

    MSGS = {
        "coach": {
            "ru": "✅ Режим общения изменён на *Коуч*. Я буду помогать и мотивировать тебя! 💪",
            "uk": "✅ Режим спілкування змінено на *Коуч*. Я допомагатиму та мотивуватиму тебе! 💪",
            "en": "✅ Communication mode changed to *Coach*. I will help and motivate you! 💪",
            "be": "✅ Рэжым зносін зменены на *Коуч*. Я буду дапамагаць і матываваць цябе! 💪",
            "kk": "✅ Байланыс режимі *Коуч* болып өзгертілді. Мен саған көмектесіп, мотивация беремін! 💪",
            "kg": "✅ Байланыш режими *Коуч* болуп өзгөрдү. Мен сага жардам берип, шыктандырам! 💪",
            "hy": "✅ Կապի ռեժիմը փոխվեց *Քոուչ*: Ես կօգնեմ և կխրախուսեմ քեզ։ 💪",
            "ce": "✅ Чуйна режим хила *Коуч* догъа. Со ву до а ю мотивация ю! 💪",
            "md": "✅ Modul de comunicare a fost schimbat la *Coach*. Te voi ajuta și motiva! 💪",
            "ka": "✅ კომუნიკაციის რეჟიმი შეიცვალა *ქოუჩი*-ზე. დაგეხმარები და მოგამოტივირებ! 💪",
        },
        "flirt": {
            "ru": "😉 Режим общения изменён на *Флирт*. Приготовься к приятным неожиданностям 💜",
            "uk": "😉 Режим спілкування змінено на *Флірт*. Готуйся до приємних сюрпризів 💜",
            "en": "😉 Communication mode changed to *Flirt*. Get ready for pleasant surprises 💜",
            "be": "😉 Рэжым зносін зменены на *Флірт*. Будзь гатовы да прыемных нечаканасцей 💜",
            "kk": "😉 Байланыс режимі *Флирт* болып өзгертілді. Жақсы тосынсыйларға дайын бол 💜",
            "kg": "😉 Байланыш режими *Флирт* болуп өзгөрдү. Жакшы сюрприздерге даяр бол 💜",
            "hy": "😉 Կապի ռեժիմը փոխվեց *Ֆլիրտ*: Պատրաստ եղիր հաճելի անակնկալների 💜",
            "ce": "😉 Чуйна режим хила *Флирт* догъа. Дахьал цуьнан сюрпризаш хилайла! 💜",
            "md": "😉 Modul de comunicare a fost schimbat la *Flirt*. Pregătește-te pentru surprize plăcute 💜",
            "ka": "😉 კომუნიკაციის რეჟიმი შეიცვალა *ფლირტი*-ზე. მოემზადე სასიამოვნო სიურპრიზებისთვის 💜",
        }
    }

    # Ограничение по подписке
    if not (is_premium(user_id) or user_id == OWNER_ID):
        await query.edit_message_text(LOCKED_MSGS.get(lang, LOCKED_MSGS["ru"]))
        return
    
    data = query.data
    if data == "premium_mode_coach":
        user_modes[user_id] = "coach"
        await query.edit_message_text(MSGS["coach"].get(lang, MSGS["coach"]["ru"]), parse_mode="Markdown")
    elif data == "premium_mode_flirt":
        user_modes[user_id] = "flirt"
        await query.edit_message_text(MSGS["flirt"].get(lang, MSGS["flirt"]["ru"]), parse_mode="Markdown")

async def premium_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    if not (is_premium(user_id) or user_id == OWNER_ID):
        locked_msgs = {
            "ru": "🔒 Эта функция доступна только Mindra+ ✨",
            "uk": "🔒 Ця функція доступна лише для Mindra+ ✨",
            "en": "🔒 This feature is only available to Mindra+ ✨",
            "be": "🔒 Гэтая функцыя даступная толькі для Mindra+ ✨",
            "kk": "🔒 Бұл функция тек Mindra+ үшін қолжетімді ✨",
            "kg": "🔒 Бул функция Mindra+ үчүн гана жеткиликтүү ✨",
            "hy": "🔒 Այս ֆունկցիան հասանելի է միայն Mindra+ բաժանորդների համար ✨",
            "ce": "🔒 Дина функция Mindra+ яззийна догъа ✨",
            "md": "🔒 Această funcție este disponibilă doar pentru Mindra+ ✨",
            "ka": "🔒 ეს ფუნქცია ხელმისაწვდომია მხოლოდ Mindra+ მომხმარებლებისთვის ✨",
        }
        await update.message.reply_text(locked_msgs.get(lang, locked_msgs["ru"]))
        return

    stats = get_premium_stats(user_id)

    # Тексты на всех языках
    stats_texts = {
        "ru": (
            "📊 *Расширенная статистика:*\n\n"
            "🎯 Завершено целей: {completed_goals}\n"
            "💧 Привычек отслежено: {habits_tracked}\n"
            "🔥 Дней активности: {days_active}\n"
            "🌱 Записей настроения: {mood_entries}"
        ),
        "uk": (
            "📊 *Розширена статистика:*\n\n"
            "🎯 Завершено цілей: {completed_goals}\n"
            "💧 Звичок відстежено: {habits_tracked}\n"
            "🔥 Днів активності: {days_active}\n"
            "🌱 Записів настрою: {mood_entries}"
        ),
        "en": (
            "📊 *Extended stats:*\n\n"
            "🎯 Goals completed: {completed_goals}\n"
            "💧 Habits tracked: {habits_tracked}\n"
            "🔥 Active days: {days_active}\n"
            "🌱 Mood entries: {mood_entries}"
        ),
        "be": (
            "📊 *Пашыраная статыстыка:*\n\n"
            "🎯 Завершана мэт: {completed_goals}\n"
            "💧 Адсочаных звычак: {habits_tracked}\n"
            "🔥 Дзён актыўнасці: {days_active}\n"
            "🌱 Запісаў настрою: {mood_entries}"
        ),
        "kk": (
            "📊 *Кеңейтілген статистика:*\n\n"
            "🎯 Аяқталған мақсаттар: {completed_goals}\n"
            "💧 Бақыланған әдеттер: {habits_tracked}\n"
            "🔥 Белсенді күндер: {days_active}\n"
            "🌱 Көңіл-күй жазбалары: {mood_entries}"
        ),
        "kg": (
            "📊 *Кеңейтилген статистика:*\n\n"
            "🎯 Бүтүп бүткөн максаттар: {completed_goals}\n"
            "💧 Көзөмөлдөгөн адаттар: {habits_tracked}\n"
            "🔥 Активдүү күндөр: {days_active}\n"
            "🌱 Көңүл-күй жазуулары: {mood_entries}"
        ),
        "hy": (
            "📊 *Ընդլայնված վիճակագրություն:*\n\n"
            "🎯 Ավարտված նպատակներ: {completed_goals}\n"
            "💧 Հետևվող սովորություններ: {habits_tracked}\n"
            "🔥 Ակտիվ օրեր: {days_active}\n"
            "🌱 Դժգոհության գրառումներ: {mood_entries}"
        ),
        "ce": (
            "📊 *ДӀаялларг статистика:*\n\n"
            "🎯 ДогӀа кхоллар цуьнан мацахь: {completed_goals}\n"
            "💧 Хийна кхоллар хетам йолуш: {habits_tracked}\n"
            "🔥 Актив хетам йолуш дийна: {days_active}\n"
            "🌱 Мотивацион хетам хийна: {mood_entries}"
        ),
        "md": (
            "📊 *Statistici extinse:*\n\n"
            "🎯 Obiective finalizate: {completed_goals}\n"
            "💧 Obiceiuri urmărite: {habits_tracked}\n"
            "🔥 Zile active: {days_active}\n"
            "🌱 Înregistrări de dispoziție: {mood_entries}"
        ),
        "ka": (
            "📊 *გაფართოებული სტატისტიკა:*\n\n"
            "🎯 დასრულებული მიზნები: {completed_goals}\n"
            "💧 დაკვირვებული ჩვევები: {habits_tracked}\n"
            "🔥 აქტიური დღეები: {days_active}\n"
            "🌱 განწყობის ჩანაწერები: {mood_entries}"
        ),
    }
    # Формируем текст
    text = stats_texts.get(lang, stats_texts["ru"]).format(**stats)
    await update.message.reply_text(text, parse_mode="Markdown")

async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    now_kiev = datetime.now(pytz.timezone("Europe/Kiev"))
    if not (REPORT_MIN_HOUR <= now_kiev.hour < REPORT_MAX_HOUR):
        return

    for user_id in PREMIUM_USERS:
        try:
            # Проверяем: если уже сегодня отправляли — не дублируем
            last_sent = user_last_report_sent.get(user_id)
            if last_sent == now_kiev.date().isoformat():
                continue

            lang = user_languages.get(str(user_id), "ru")
            report_texts = {
                "ru": (
                    "📊 *Твой недельный отчёт Mindra+* 💜\n\n"
                    "✅ Выполнено целей: *{goals}*\n"
                    "🌱 Отмечено привычек: *{habits}*\n\n"
                    "✨ Так держать! Я горжусь тобой 💪💜"
                ),
                "uk": (
                    "📊 *Твій тижневий звіт Mindra+* 💜\n\n"
                    "✅ Виконано цілей: *{goals}*\n"
                    "🌱 Відмічено звичок: *{habits}*\n\n"
                    "✨ Так тримати! Я пишаюсь тобою 💪💜"
                ),
                "en": (
                    "📊 *Your weekly Mindra+ report* 💜\n\n"
                    "✅ Goals completed: *{goals}*\n"
                    "🌱 Habits tracked: *{habits}*\n\n"
                    "✨ Keep it up! I'm proud of you 💪💜"
                ),
                "be": (
                    "📊 *Твой тыднёвы справаздача Mindra+* 💜\n\n"
                    "✅ Выканана мэт: *{goals}*\n"
                    "🌱 Адзначана звычак: *{habits}*\n\n"
                    "✨ Так трымаць! Я ганаруся табой 💪💜"
                ),
                "kk": (
                    "📊 *Сенің Mindra+ апталық есебің* 💜\n\n"
                    "✅ Орындалған мақсаттар: *{goals}*\n"
                    "🌱 Белгіленген әдеттер: *{habits}*\n\n"
                    "✨ Осылай жалғастыр! Мен сені мақтан тұтамын 💪💜"
                ),
                "kg": (
                    "📊 *Сенин Mindra+ апталык отчётуң* 💜\n\n"
                    "✅ Аткарылган максаттар: *{goals}*\n"
                    "🌱 Белгиленген адаттар: *{habits}*\n\n"
                    "✨ Ошентип улант! Мен сени сыймыктанам 💪💜"
                ),
                "hy": (
                    "📊 *Քո Mindra+ շաբաթական հաշվետվությունը* 💜\n\n"
                    "✅ Կատարված նպատակներ: *{goals}*\n"
                    "🌱 Նշված սովորություններ: *{habits}*\n\n"
                    "✨ Շարունակիր այսպես! Հպարտանում եմ քեզանով 💪💜"
                ),
                "ce": (
                    "📊 *ДогӀа Mindra+ нан неделю отчет* 💜\n\n"
                    "✅ Кхоллар мацахь: *{goals}*\n"
                    "🌱 Хийна хетам: *{habits}*\n\n"
                    "✨ Дехар цуьнан! Со цуьнан делла йойла хьо 💪💜"
                ),
                "md": (
                    "📊 *Raportul tău săptămânal Mindra+* 💜\n\n"
                    "✅ Obiective îndeplinite: *{goals}*\n"
                    "🌱 Obiceiuri marcate: *{habits}*\n\n"
                    "✨ Ține-o tot așa! Sunt mândru de tine 💪💜"
                ),
                "ka": (
                    "📊 *შენი Mindra+ ყოველკვირეული ანგარიში* 💜\n\n"
                    "✅ შესრულებული მიზნები: *{goals}*\n"
                    "🌱 მონიშნული ჩვევები: *{habits}*\n\n"
                    "✨ გააგრძელე ასე! მე ვამაყობ შენით 💪💜"
                ),
            }

            # Получаем цели и привычки
            goals = get_goals(user_id)
            completed_goals = [g for g in goals if g.get("done")]
            try:
                habits = get_habits(user_id)
                completed_habits = len(habits)
            except Exception:
                completed_habits = 0

            text = report_texts.get(lang, report_texts["ru"]).format(
                goals=len(completed_goals),
                habits=completed_habits
            )
            await context.bot.send_message(
                chat_id=int(user_id),
                text=text,
                parse_mode="Markdown"
            )
            user_last_report_sent[user_id] = now_kiev.date().isoformat()
            logging.info(f"✅ Еженедельный отчёт отправлен пользователю {user_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке отчёта пользователю {user_id}: {e}")
            
# Команда /remind — мультиязычный вариант

REMIND_TEXTS = {
    "ru": {
        "limit": "🔔 В бесплатной версии можно установить только 1 активное напоминание.\n\n"
                 "✨ Оформи Mindra+, чтобы иметь неограниченные напоминания 💜",
        "usage": "⏰ Использование: `/remind 19:30 Сделай зарядку!`",
        "success": "✅ Напоминание установлено на {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Неверный формат. Пример: `/remind 19:30 Сделай зарядку!`",
    },
    "uk": {
        "limit": "🔔 У безкоштовній версії можна встановити лише 1 активне нагадування.\n\n"
                 "✨ Оформи Mindra+, щоб мати необмежені нагадування 💜",
        "usage": "⏰ Використання: `/remind 19:30 Зроби зарядку!`",
        "success": "✅ Нагадування встановлено на {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Неправильний формат. Приклад: `/remind 19:30 Зроби зарядку!`",
    },
    "be": {
        "limit": "🔔 У бясплатнай версіі можна ўсталяваць толькі 1 актыўнае напамінанне.\n\n"
                 "✨ Аформі Mindra+, каб мець неабмежаваную колькасць напамінанняў 💜",
        "usage": "⏰ Выкарыстанне: `/remind 19:30 Зрабі зарадку!`",
        "success": "✅ Напамінанне ўсталявана на {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Няправільны фармат. Прыклад: `/remind 19:30 Зрабі зарадку!`",
    },
    "kk": {
        "limit": "🔔 Тегін нұсқада тек 1 белсенді еске салу орнатуға болады.\n\n"
                 "✨ Mindra+ арқылы шексіз еске салулар орнатыңыз 💜",
        "usage": "⏰ Қолдану: `/remind 19:30 Жаттығу жаса!`",
        "success": "✅ Еске салу орнатылды: {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Қате формат. Мысал: `/remind 19:30 Жаттығу жаса!`",
    },
    "kg": {
        "limit": "🔔 Акысыз версияда бир эле эскертме коюуга болот.\n\n"
                 "✨ Mindra+ менен чексиз эскертмелерди коюңуз 💜",
        "usage": "⏰ Колдонуу: `/remind 19:30 Зарядка жаса!`",
        "success": "✅ Эскертүү коюлду: {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Формат туура эмес. Мисал: `/remind 19:30 Зарядка жаса!`",
    },
    "hy": {
        "limit": "🔔 Անվճար տարբերակում կարելի է ավելացնել միայն 1 ակտիվ հիշեցում։\n\n"
                 "✨ Միացրու Mindra+, որ ունենաս անսահման հիշեցումներ 💜",
        "usage": "⏰ Օգտագործում: `/remind 19:30 Կատարի՛ր վարժանքներ!`",
        "success": "✅ Հիշեցումը սահմանվել է {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Սխալ ձևաչափ։ Օրինակ: `/remind 19:30 Կատարի՛ր վարժանքներ!`",
    },
    "ce": {
        "limit": "🔔 Аьтто версия хийцна, цхьаьнан 1 активан напоминание ца хилла цуьнан.\n\n"
                 "✨ Mindra+ хийцар, цуьнан цуьнан цхьаьнан напоминаний хилла 💜",
        "usage": "⏰ Цуьнан: `/remind 19:30 Зарядка йоцу!`",
        "success": "✅ Напоминание хийна {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Формат дукха. Мисал: `/remind 19:30 Зарядка йоцу!`",
    },
    "md": {
        "limit": "🔔 În versiunea gratuită poți seta doar 1 memento activ.\n\n"
                 "✨ Activează Mindra+ pentru mementouri nelimitate 💜",
        "usage": "⏰ Utilizare: `/remind 19:30 Fă exerciții!`",
        "success": "✅ Mementoul a fost setat la {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Format greșit. Exemplu: `/remind 19:30 Fă exerciții!`",
    },
    "ka": {
        "limit": "🔔 უფასო ვერსიაში შეგიძლიათ დააყენოთ მხოლოდ 1 აქტიური შეხსენება.\n\n"
                 "✨ გაააქტიურეთ Mindra+ ულიმიტო შეხსენებებისთვის 💜",
        "usage": "⏰ გამოყენება: `/remind 19:30 გააკეთე ვარჯიში!`",
        "success": "✅ შეხსენება დაყენებულია {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ არასწორი ფორმატი. მაგალითი: `/remind 19:30 გააკეთე ვარჯიში!`",
    },
    "en": {
        "limit": "🔔 In the free version, you can set only 1 active reminder.\n\n"
                 "✨ Get Mindra+ for unlimited reminders 💜",
        "usage": "⏰ Usage: `/remind 19:30 Do your workout!`",
        "success": "✅ Reminder set for {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Wrong format. Example: `/remind 19:30 Do your workout!`",
    },
}

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    t = REMIND_TEXTS.get(lang, REMIND_TEXTS["ru"])

    # Проверка: премиум или нет
    is_premium = (user_id == str(YOUR_ID)) or (user_id in PREMIUM_USERS)

    # Лимит для бесплатных: только 1 напоминание
    if not is_premium:
        current_reminders = user_reminders.get(user_id, [])
        if len(current_reminders) >= 1:
            await update.message.reply_text(t["limit"], parse_mode="Markdown")
            return

    # Проверяем корректность аргументов
    if len(context.args) < 2:
        await update.message.reply_text(t["usage"], parse_mode="Markdown")
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
            t["success"].format(hour=hour, minute=minute, text=text_part),
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(t["bad_format"], parse_mode="Markdown")
        print(e)

MOODS_BY_LANG = {
    "ru": [
        "💜 Ты сегодня как солнечный лучик! Продолжай так!",
        "🌿 Кажется, у тебя спокойный день. Наслаждайся.",
        "🔥 В тебе столько энергии! Используй её с пользой.",
        "😊 Ты излучаешь доброту. Спасибо, что ты есть.",
        "✨ Сегодня хороший день для чего-то нового."
    ],
    "uk": [
        "💜 Ти сьогодні як промінчик сонця! Так тримати!",
        "🌿 Здається, у тебе спокійний день. Насолоджуйся.",
        "🔥 В тобі стільки енергії! Використовуй її з користю.",
        "😊 Ти випромінюєш доброту. Дякую, що ти є.",
        "✨ Сьогодні гарний день для чогось нового."
    ],
    "be": [
        "💜 Ты сёння як сонечны прамень! Так трымаць!",
        "🌿 Здаецца, у цябе спакойны дзень. Атрымлівай асалоду.",
        "🔥 У табе столькі энергіі! Выкарыстоўвай яе з карысцю.",
        "😊 Ты выпраменьваеш дабрыню. Дзякуй, што ты ёсць.",
        "✨ Сёння добры дзень для чагосьці новага."
    ],
    "kk": [
        "💜 Бүгін сен күн сәулесіндейсің! Осылай жалғастыр!",
        "🌿 Бүгінгі күнің тыныш сияқты. Ләззат ал.",
        "🔥 Сенде көп энергия бар! Оны пайдалы жұмса.",
        "😊 Сен мейірімділік таратасың. Сен барсың – рақмет.",
        "✨ Бүгін жаңа бір нәрсе бастауға жақсы күн."
    ],
    "kg": [
        "💜 Бүгүн сен күн нуру сыяктуусуң! Ошентип жүрө бер!",
        "🌿 Көрсө, сенде тынч күн болуп жатат. Ырахаттан.",
        "🔥 Сенде көп энергия бар! Аны пайдалуу колдоно бил.",
        "😊 Сен боорукерлик таратасың. Сен болгонуңа рахмат.",
        "✨ Бүгүн жаңы нерсеге мыкты күн."
    ],
    "hy": [
        "💜 Դու այսօր արևի շող ես: Շարունակի՛ր այսպես:",
        "🌿 Կարծես քեզ մոտ հանգիստ օր է: Վայելիր:",
        "🔥 Քո մեջ այսքան շատ էներգիա կա: Օգտագործիր այն օգտակար կերպով:",
        "😊 Դու բարություն ես տարածում: Շնորհակալություն, որ դու կաս:",
        "✨ Այսօր լավ օր է նոր բան սկսելու համար:"
    ],
    "ce": [
        "💜 Со хилар долу бай цуьнан! Кхетам дог!",
        "🌿 Ву цуьнан ца хилла суьйре г1алг1ай. Ловзар ла цуьнан.",
        "🔥 Со хетам кхетар до энерги. Ла цуьнан дика корта.",
        "😊 Со хилар до кхетам дукха. Сог1ар лахар цуьнан.",
        "✨ Долчу г1улла цуьнан хетар а ву йо."
    ],
    "md": [
        "💜 Azi ești ca o rază de soare! Ține-o tot așa!",
        "🌿 Se pare că ai o zi liniștită. Bucură-te.",
        "🔥 Ai atâta energie! Folosește-o cu folos.",
        "😊 Emană bunătate. Mulțumesc că exiști.",
        "✨ Azi este o zi bună pentru ceva nou."
    ],
    "ka": [
        "💜 დღეს შენ მზის სხივივით ხარ! ასე განაგრძე!",
        "🌿 როგორც ჩანს, დღეს მშვიდი დღეა შენთვის. დატკბი.",
        "🔥 შენში ამდენი ენერგიაა! კარგად გამოიყენე იგი.",
        "😊 კეთილშობილებას ასხივებ. მადლობა, რომ არსებობ.",
        "✨ დღეს კარგი დღეა ახალი რაღაცისთვის."
    ],
    "en": [
        "💜 You're like a ray of sunshine today! Keep it up!",
        "🌿 Looks like you have a calm day. Enjoy it.",
        "🔥 You have so much energy! Use it wisely.",
        "😊 You radiate kindness. Thank you for being here.",
        "✨ Today is a good day for something new."
    ],
}

async def test_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    moods = MOODS_BY_LANG.get(lang, MOODS_BY_LANG["ru"])
    await update.message.reply_text(random.choice(moods))

def give_trial_if_needed(user_id):
    if got_trial(user_id):
        return False
    now = datetime.utcnow()
    set_premium_until(user_id, now + timedelta(days=3), add_days=True)
    set_trial(user_id)
    logging.info(f"Пользователь {user_id} получил триал до {now + timedelta(days=3)}")
    return True
    
def handle_referral(user_id, referrer_id):
    # Проверка, был ли уже trial
    if got_trial(user_id):
        # уже был триал, но можем добавить дни!
        pass
    now = datetime.utcnow()
    set_premium_until(user_id, now + timedelta(days=7), add_days=True)
    set_premium_until(referrer_id, now + timedelta(days=7), add_days=True)
    set_trial(user_id)
    set_trial(referrer_id)
    add_referral(user_id, referrer_id)
    logging.info(f"👥 Реферал: {user_id} пришёл по ссылке {referrer_id}, всем +7 дней")
    return True

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    invite_link = f"https://t.me/talktomindra_bot?start=ref{user_id}"
    
    INVITE_TEXT = {
        "ru": (
            "🎁 Пригласи друга и вы оба получите +7 дней Mindra+!\n\n"
            "1️⃣ Просто отправь эту ссылку другу в Telegram:\n"
            f"{invite_link}\n\n"
            "2️⃣ Как только твой друг зарегистрируется по этой ссылке, вы оба автоматически получите +7 дней Mindra+! 🟣"
        ),
        "uk": (
            "🎁 Запроси друга — і ви обидва отримаєте +7 днів Mindra+!\n\n"
            "1️⃣ Просто надішли це посилання другові в Telegram:\n"
            f"{invite_link}\n\n"
            "2️⃣ Як тільки друг зареєструється за цим посиланням, вам обом автоматично нарахується +7 днів Mindra+! 🟣"
        ),
        "be": (
            "🎁 Запрасі сябра — і вы абодва атрымаеце +7 дзён Mindra+!\n\n"
            "1️⃣ Проста дашлі гэту спасылку сябру ў Telegram:\n"
            f"{invite_link}\n\n"
            "2️⃣ Як толькі сябар зарэгіструецца па спасылцы, вам абодвум будзе аўтаматычна налічана +7 дзён Mindra+! 🟣"
        ),
        "kk": (
            "🎁 Осы сілтемемен досыңды шақыр — екеуің де +7 күн Mindra+ аласыңдар!\n\n"
            "1️⃣ Бұл сілтемені досыңа Telegram арқылы жібер:\n"
            f"{invite_link}\n\n"
            "2️⃣ Досың осы сілтеме арқылы тіркелсе, екеуіңе де автоматты түрде +7 күн Mindra+ қосылады! 🟣"
        ),
        "kg": (
            "🎁 Бул шилтеме аркылуу досуңду чакыр — экөөңөргө тең +7 күн Mindra+ берилет!\n\n"
            "1️⃣ Бул шилтемени досуңа Telegram аркылуу жөнөт:\n"
            f"{invite_link}\n\n"
            "2️⃣ Досуң ушул шилтеме аркылуу катталса, экөөңөргө тең автоматтык түрдө +7 күн Mindra+ берилет! 🟣"
        ),
        "hy": (
            "🎁 Հրավիրի՛ր ընկերոջդ այս հղումով, և երկուսդ էլ կստանաք +7 օր Mindra+!\n\n"
            "1️⃣ Ուղարկիր այս հղումը ընկերոջդ Telegram-ով:\n"
            f"{invite_link}\n\n"
            "2️⃣ Երբ նա գրանցվի հղումով, դուք երկուսդ էլ կստանաք +7 օր Mindra+! 🟣"
        ),
        "ce": (
            "🎁 Хьо цуьнан хьо дукха догхьа къобал сылкъе — тхо ду +7 Mindra+ дера дахийна!\n\n"
            "1️⃣ Хьо сылкъа цуьнан Telegram догхьа ду:\n"
            f"{invite_link}\n\n"
            "2️⃣ Цуьнан хьо дукха догхьа цуьнан кхети, тхо ду а автоматика кхети +7 Mindra+ де! 🟣"
        ),
        "md": (
            "🎁 Invită un prieten cu acest link și amândoi primiți +7 zile Mindra+!\n\n"
            "1️⃣ Trimite acest link prietenului tău pe Telegram:\n"
            f"{invite_link}\n\n"
            "2️⃣ De îndată ce prietenul tău se înregistrează cu acest link, amândoi veți primi automat +7 zile Mindra+! 🟣"
        ),
        "ka": (
            "🎁 მოიწვიე მეგობარი ამ ბმულით და ორივემ მიიღეთ +7 დღე Mindra+!\n\n"
            "1️⃣ გაუგზავნე ეს ბმული მეგობარს Telegram-ში:\n"
            f"{invite_link}\n\n"
            "2️⃣ როგორც კი მეგობარი დარეგისტრირდება ამ ბმულით, თქვენ ორვეს ავტომატურად დაერიცხებათ +7 დღე Mindra+! 🟣"
        ),
        "en": (
            "🎁 Invite a friend and you both get +7 days of Mindra+!\n\n"
            "1️⃣ Just send this link to your friend in Telegram:\n"
            f"{invite_link}\n\n"
            "2️⃣ As soon as your friend registers via this link, you both will automatically receive +7 days of Mindra+! 🟣"
        ),
    }

    text = INVITE_TEXT.get(lang, INVITE_TEXT["ru"])

    await update.message.reply_text(
        text,
        disable_web_page_preview=True
    )
    
def plural_ru(number, one, few, many):
    # Склонение для русского языка (можно добавить и для других, если нужно)
    n = abs(number)
    if n % 10 == 1 and n % 100 != 11:
        return one
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return few
    else:
        return many

async def premium_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    until = get_premium_until(user_id)
    now = datetime.utcnow()
    days = 0
    months = 0
    years = 0
    days_left = 0 
    text = ""
    if until:
        try:
            dt_until = datetime.fromisoformat(until)
            diff = dt_until - now
            days = diff.days
            # future ready: считаем месяцы/годы
            years = days // 365
            months = (days % 365) // 30
            days_left = (days % 365) % 30
            if days < 0:
                days = 0
                years = months = days_left = 0
        except Exception as e:
            days = 0
            years = months = days_left = 0

    # Тексты для всех языков (русский — с падежами)
    if lang == "ru":
        years_text = f"{years} " + plural_ru(years, "год", "года", "лет") if years else ""
        months_text = f"{months} " + plural_ru(months, "месяц", "месяца", "месяцев") if months else ""
        days_text = f"{days_left} " + plural_ru(days_left, "день", "дня", "дней") if days_left or (not years and not months) else ""
        parts = [years_text, months_text, days_text]
        period = ", ".join([part for part in parts if part])
        if period:
            text = f"💎 У тебя осталось *{period}* Mindra+."
        else:
            text = "💎 У тебя нет активной подписки Mindra+."
    else:
        # Для остальных языков просто числа
        if years > 0:
            text = {
                "uk": f"💎 У тебе залишилося *{years}* років Mindra+.",
                "be": f"💎 У цябе засталося *{years}* гадоў Mindra+.",
                "kk": f"💎 Сенде Mindra+ қалған *{years}* жыл бар.",
                "kg": f"💎 Сенде Mindra+ дагы *{years}* жыл калды.",
                "hy": f"💎 Դու ունես դեռ *{years}* տարի Mindra+:",
                "ce": f"💎 Хьо даьлча Mindra+ *{years}* сахь кхетам.",
                "md": f"💎 Ai rămas cu *{years}* ani de Mindra+.",
                "ka": f"💎 შენ დაგრჩა *{years}* წელი Mindra+.",
                "en": f"💎 You have *{years}* years of Mindra+ left.",
            }.get(lang, f"💎 You have *{years}* years of Mindra+ left.")
        elif months > 0:
            text = {
                "uk": f"💎 У тебе залишилося *{months}* місяців Mindra+.",
                "be": f"💎 У цябе засталося *{months}* месяцаў Mindra+.",
                "kk": f"💎 Сенде Mindra+ қалған *{months}* ай бар.",
                "kg": f"💎 Сенде Mindra+ дагы *{months}* ай калды.",
                "hy": f"💎 Դու ունես դեռ *{months}* ամիս Mindra+:",
                "ce": f"💎 Хьо даьлча Mindra+ *{months}* буьйса кхетам.",
                "md": f"💎 Ai rămas cu *{months}* luni de Mindra+.",
                "ka": f"💎 შენ დაგრჩა *{months}* თვე Mindra+.",
                "en": f"💎 You have *{months}* months of Mindra+ left.",
            }.get(lang, f"💎 You have *{months}* months of Mindra+ left.")
        else:
            text = {
                "ru": f"💎 У тебя осталось *{days_left}* дней Mindra+.",
                "uk": f"💎 У тебе залишилося *{days_left}* днів Mindra+.",
                "be": f"💎 У цябе засталося *{days_left}* дзён Mindra+.",
                "kk": f"💎 Сенде Mindra+ қалған *{days_left}* күн бар.",
                "kg": f"💎 Сенде Mindra+ дагы *{days_left}* күн калды.",
                "hy": f"💎 Դու ունես դեռ *{days_left}* օր Mindra+:",
                "ce": f"💎 Хьо даьлча Mindra+ *{days_left}* де кхетам.",
                "md": f"💎 Ai rămas cu *{days_left}* zile de Mindra+.",
                "ka": f"💎 შენ დაგრჩა *{days_left}* დღე Mindra+.",
                "en": f"💎 You have *{days_left}* days of Mindra+ left.",
            }.get(lang, f"💎 You have *{days_left}* days of Mindra+ left.")

        if (not years and not months and not days_left):
            text = {
                "ru": "💎 У тебя нет активной подписки Mindra+.",
                "uk": "💎 У тебе немає активної підписки Mindra+.",
                "en": "💎 You don't have an active Mindra+ subscription.",
                "be": "💎 У цябе няма актыўнай падпіскі Mindra+.",
                "kk": "💎 Сенде белсенді Mindra+ жазылымы жоқ.",
                "kg": "💎 Сенде активдүү Mindra+ жазылуусу жок.",
                "hy": "💎 Դու չունես ակտիվ Mindra+ բաժանորդագրություն։",
                "ce": "💎 Хьо доьзал хила Mindra+ яззийна цуьнан.",
                "md": "💎 Nu ai un abonament activ Mindra+.",
                "ka": "💎 შენ არ გაქვს აქტიური Mindra+ გამოწერა.",
            }.get(lang, "💎 You don't have an active Mindra+ subscription.")

    await update.message.reply_text(text, parse_mode="Markdown")
    
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
    CommandHandler("invite", invite),
    CommandHandler("premium_days", premium_days),
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
