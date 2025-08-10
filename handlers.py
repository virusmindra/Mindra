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
from texts import (
    VOICE_TEXTS_BY_LANG,
    REMIND_TEXTS,
    LOCKED_MSGS,
    MSGS,
    EXCLUSIVE_MODES_BY_LANG,
    PREMIUM_REPORT_TEXTS,
    PREMIUM_CHALLENGES_BY_LANG,
    POLL_MESSAGES_BY_LANG,
    SUPPORT_MESSAGES_BY_LANG,
    QUOTES_BY_LANG,
    EVENING_MESSAGES_BY_LANG,
    FEEDBACK_TEXTS,
    UNKNOWN_COMMAND_TEXTS,
    PREMIUM_ONLY_TEXTS,
    PREMIUM_TASK_TITLE,
    about_texts,
    help_texts,
    buttons_text,
    REACTION_THANKS_TEXTS,
    BUTTON_LABELS,
    MODE_NAMES,
    MODE_TEXTS,
    MODES,
    RESET_TEXTS,
    TRIAL_GRANTED_TEXT,
    REFERRAL_BONUS_TEXT,
    TRIAL_INFO_TEXT,
    reminder_headers,
    DAILY_TASKS_BY_LANG,
    goal_texts,
    POINTS_ADDED_HABIT,
    HABIT_SELECT_MESSAGE,
    LANG_PATTERNS,
    texts,
    references_by_lang,
    keywords_by_lang,
    headers,
    questions_by_topic_by_lang,
    HABIT_BUTTON_TEXTS,
    HABITS_TEXTS,
    HABIT_TEXTS,
    MYSTATS_TEXTS,
    STATS_TEXTS,
    topic_reference_by_lang,
    topic_patterns_full,
    topic_patterns_by_lang,
    emotion_keywords_by_lang,
    MORNING_MESSAGES_BY_LANG,
    PREMIUM_TASKS_BY_LANG,
    GOAL_DELETED_TEXTS,
    GOAL_NOT_FOUND_TEXTS,
    ERROR_SELECT_TEXTS,
    GOAL_DELETE_TEXTS,
    NO_GOALS_TEXTS,
    SYSTEM_PROMPT_BY_LANG,
    IDLE_MESSAGES,
    TIMEZONE_TEXTS,
    WELCOME_TEXTS,
    LANG_PROMPTS,
    HABIT_LANG_TEXTS,
    GOAL_LANG_TEXTS,
    TIMEZONES,
    TIMEZONE_NAMES,
    GOAL_DONE_MESSAGES,
    HABIT_DONE_MESSAGES,
    GOAL_SELECT_MESSAGE,
    POINTS_ADDED_GOAL,
    POINTS_HELP_TEXTS
)
from datetime import datetime, timedelta, timezone, date
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from telegram.constants import ChatAction, ParseMode
from config import client, TELEGRAM_BOT_TOKEN
from history import load_history, save_history, trim_history
from goals import  is_goal_like, goal_keywords_by_lang, REACTIONS_GOAL_DONE, DELETE_MESSAGES
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from storage import delete_goal, load_goals, save_goals, add_goal, get_goals, get_goals_for_user, mark_goal_done, load_habits, save_habits, add_habit, get_habits, mark_habit_done, delete_habit
from random import randint, choice
from stats import load_stats, save_stats, get_premium_until, set_premium_until, is_premium, got_trial, set_trial, add_referral, add_points, get_user_stats, get_user_title, load_json_file, get_stats, OWNER_ID, ADMIN_USER_IDS, _collect_activity_dates, get_user_points, get_next_title_info, build_titles_ladder
from telegram.error import BadRequest
global user_timezones

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
user_timezones = {}

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

MIN_HOURS_SINCE_LAST_MORNING_TASK = 20  # Не отправлять чаще 1 раза в 20 часов

def get_mode_prompt(mode, lang):
    return MODES.get(mode, MODES["default"]).get(lang, MODES["default"]["ru"])

openai.api_key = os.getenv("OPENAI_API_KEY")

GOALS_FILE = Path("user_goals.json")

YOUR_ID = "7775321566"  # твой ID

async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")  # Или как у тебя определяется язык

    if not context.args:
        await update.message.reply_text(
            TIMEZONE_TEXTS.get(lang, TIMEZONE_TEXTS["ru"]),
            parse_mode="Markdown"
        )
        return

    arg = context.args[0].lower()
    if arg in TIMEZONES:
        tz = TIMEZONES[arg]
        user_timezones[user_id] = tz
        await update.message.reply_text(
            f"✅ {TIMEZONE_NAMES[tz]}\n"
            + (
                {
                    "ru": "Теперь напоминания будут приходить по твоему времени!",
                    "uk": "Тепер нагадування будуть надходити за вашим часом!",
                    "be": "Цяпер напаміны будуць прыходзіць у ваш мясцовы час!",
                    "kk": "Еске салулар жергілікті уақытыңызда келеді!",
                    "kg": "Эскертмелер жергиликтүү убактыңызда келет!",
                    "hy": "Հիշեցումները կգան քո տեղական ժամով!",
                    "ce": "Цхьаьнан напоминаний чур дийцар локальнай хийцара!",
                    "md": "Mementourile vor veni la ora locală!",
                    "ka": "შეხსენებები მოვა თქვენს ადგილობრივ დროზე!",
                    "en": "Reminders will now be sent in your local time!"
                }.get(lang, "Теперь напоминания будут приходить по твоему времени!")
            )
        )
    else:
        await update.message.reply_text(
            {
                "ru": "❗ Неверная таймзона. Используй одну из: `kiev`, `moscow`, `ny`\nПример: `/timezone moscow`",
                "uk": "❗ Невірна таймзона. Використовуйте одну з: `kiev`, `moscow`, `ny`\nПриклад: `/timezone moscow`",
                "be": "❗ Няправільная таймзона. Выкарыстоўвайце адну з: `kiev`, `moscow`, `ny`\nПрыклад: `/timezone moscow`",
                "kk": "❗ Қате белдеу. Осыны қолданыңыз: `kiev`, `moscow`, `ny`\nМысал: `/timezone moscow`",
                "kg": "❗ Туура эмес зона. Булардын бирин колдонуңуз: `kiev`, `moscow`, `ny`\nМисал: `/timezone moscow`",
                "hy": "❗ Սխալ ժամանակային գոտի։ Օգտագործեք՝ `kiev`, `moscow`, `ny`\nՕրինակ՝ `/timezone moscow`",
                "ce": "❗ Нохчийн таймзона дукха. Цуьнан: `kiev`, `moscow`, `ny`\nМисал: `/timezone moscow`",
                "md": "❗ Fus orar greșit. Folosește: `kiev`, `moscow`, `ny`\nExemplu: `/timezone moscow`",
                "ka": "❗ არასწორი დროის სარტყელი. გამოიყენეთ: `kiev`, `moscow`, `ny`\nმაგალითი: `/timezone moscow`",
                "en": "❗ Wrong timezone. Use one of: `kiev`, `moscow`, `ny`\nExample: `/timezone moscow`",
            }.get(lang, "❗ Неверная таймзона. Используй одну из: `kiev`, `moscow`, `ny`\nПример: `/timezone moscow`"),
            parse_mode="Markdown"
        )

async def show_habits(update, context):
    # Универсальная поддержка и команды, и callback
    if hasattr(update, "callback_query") and update.callback_query is not None:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        send_func = query.edit_message_text
    else:
        user_id = str(update.effective_user.id)
        send_func = update.message.reply_text

    lang = user_languages.get(user_id, "ru")
    t = HABIT_LANG_TEXTS.get(lang, HABIT_LANG_TEXTS["ru"])
    habits = get_habits(user_id)

    if not habits:
        await send_func(t["no_habits"])
        return

    reply = f"{t['your_habits']}\n\n"
    for idx, habit in enumerate(habits, 1):
        status = t["done"] if habit.get("done") else t["not_done"]
        reply += f"{idx}. {status} {habit.get('text', '')}\n"

    # Кнопки: удалить и добавить
    buttons = [
        [
            InlineKeyboardButton(t["delete"], callback_data="delete_habit_choose"),
            InlineKeyboardButton(t["add"], callback_data="create_habit"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await send_func(reply, reply_markup=reply_markup, parse_mode="Markdown")

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

async def show_goals(update, context):
    # Универсальная точка входа: поддерживает и команду, и callback
    if hasattr(update, "callback_query") and update.callback_query is not None:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        send_func = query.edit_message_text
    else:
        user_id = str(update.effective_user.id)
        send_func = update.message.reply_text

    lang = user_languages.get(user_id, "ru")
    t = GOAL_LANG_TEXTS.get(lang, GOAL_LANG_TEXTS["ru"])
    goals = get_goals(user_id)

    if not goals:
        await send_func(t["no_goals"])
        return

    reply = f"{t['your_goals']}\n\n"
    for idx, goal in enumerate(goals, 1):
        status = t["done"] if goal.get("done") else "🔸"
        deadline = f" | {t['deadline']}: {goal['deadline']}" if goal.get("deadline") else ""
        remind = f" | {t['remind']}" if goal.get("remind") else ""
        reply += f"{idx}. {status} {goal.get('text', '')}{deadline}{remind}\n"

    # Кнопки: три внизу, как у привычек — добавить, выполнить, удалить (пирамидой)
    buttons = [
        [InlineKeyboardButton("➕ " + {
            "ru": "Добавить", "uk": "Додати", "be": "Дадаць", "kk": "Қосу", "kg": "Кошуу",
            "hy": "Ավելացնել", "ce": "Хила", "md": "Adaugă", "ka": "დამატება", "en": "Add"
        }.get(lang, "Добавить"), callback_data="create_goal")],
        [InlineKeyboardButton("✅ " + {
            "ru": "Выполнить", "uk": "Виконати", "be": "Выканаць", "kk": "Аяқтау", "kg": "Аткаруу",
            "hy": "Կատարել", "ce": "Батта", "md": "Finalizează", "ka": "შესრულება", "en": "Done"
        }.get(lang, "Выполнить"), callback_data="mark_goal_done_choose")],
        [InlineKeyboardButton("🗑️ " + {
            "ru": "Удалить", "uk": "Видалити", "be": "Выдаліць", "kk": "Өшіру", "kg": "Өчүрүү",
            "hy": "Ջնջել", "ce": "ДӀелла", "md": "Șterge", "ka": "წაშლა", "en": "Delete"
        }.get(lang, "Удалить"), callback_data="delete_goal_choose")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    try:
        await send_func(reply, reply_markup=reply_markup, parse_mode="Markdown")
    except BadRequest as e:
        if "Message is not modified" in str(e):
            if hasattr(update, "callback_query") and update.callback_query is not None:
                await update.callback_query.answer("Ты уже смотришь цели!", show_alert=False)
        else:
            raise

def parse_goal_index(goals, goal_name):
    for idx, goal in enumerate(goals):
        # если твои цели — строки:
        if goal == goal_name:
            return idx
        # если цели — словари:
        if isinstance(goal, dict) and (goal.get("name") == goal_name or goal.get("title") == goal_name):
            return idx
    return None

async def handle_done_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    data = query.data

    try:
        index = int(data.split("|", 1)[1])
    except Exception:
        await query.answer({"ru":"Некорректный индекс.","uk":"Некоректний індекс.","en":"Invalid index."}.get(lang,"Некорректный индекс."), show_alert=True)
        return

    goals = get_goals(user_id)
    if not (0 <= index < len(goals)):
        await query.answer({"ru":"Цель не найдена.","uk":"Ціль не знайдена.","en":"Goal not found."}.get(lang,"Цель не найдена."), show_alert=True)
        return

    if mark_goal_done(user_id, index):
        add_points(user_id, 5)
        title = goal_title(goals[index])
        text  = GOAL_DONE_MESSAGES.get(lang, GOAL_DONE_MESSAGES["ru"]).format(goal=title)
        toast = POINTS_ADDED_GOAL.get(lang, POINTS_ADDED_GOAL["ru"])

        await query.answer(toast)
        try:
            await query.edit_message_text(text)
        except Exception:
            await context.bot.send_message(chat_id=query.message.chat_id, text=text)
    else:
        await query.answer({"ru":"Не смог отметить. Смотрю логи.","uk":"Не вдалося відмітити. Перевіряю логи.","en":"Couldn’t mark as done. Checking logs."}.get(lang,"Не смог отметить. Смотрю логи."), show_alert=True)
        
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
    print("[DEBUG] check_custom_reminders запускается!")

    for user_id, reminders in list(user_reminders.items()):
        lang = user_languages.get(str(user_id), "ru")
        header = reminder_headers.get(lang, reminder_headers["ru"])
        tz_str = user_timezones.get(user_id, "Europe/Kiev")
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)

        for r in reminders[:]:
            reminder_time = r["time"]
            # Если reminder_time строка, конвертируем обратно (с учетом tz)
            if isinstance(reminder_time, str):
                try:
                    reminder_time = datetime.fromisoformat(reminder_time)
                    # reminder_time = tz.localize(reminder_time)  # Не нужно, если iso уже aware
                except Exception as e:
                    print(f"Ошибка конвертации времени: {e}")
                    continue

            print(f"[DEBUG] now={now}, reminder_time={reminder_time}")

            if now >= reminder_time and (now - reminder_time).total_seconds() < 120:
                try:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=f"{header} {r['text']}"
                    )
                    print(f"[DEBUG] Отправлено напоминание для {user_id}: {reminder_time}, текст: {r['text']}")
                except Exception as e:
                    print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")
                reminders.remove(r)

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

async def delete_goal_choose_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    goals = get_goals(user_id)

    t = GOAL_DELETE_TEXTS.get(lang, GOAL_DELETE_TEXTS["ru"])
    no_goals_text = NO_GOALS_TEXTS.get(lang, NO_GOALS_TEXTS["ru"])

    if not goals:
        await query.edit_message_text(no_goals_text)
        return

    # Формируем кнопки для каждой цели (обрезаем текст до 40 символов)
    buttons = [
        [InlineKeyboardButton(f"{i+1}. {g.get('text','')[:40]}", callback_data=f"delete_goal_{i}")]
        for i, g in enumerate(goals)
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(t, reply_markup=reply_markup)

async def delete_goal_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    data = query.data  # например, "delete_goal_2"

    try:
        index = int(data.split("_")[-1])
    except Exception:
        await query.answer(ERROR_SELECT_TEXTS.get(lang, ERROR_SELECT_TEXTS["ru"]), show_alert=True)
        return

    goals = get_goals(user_id)
    if not goals or index < 0 or index >= len(goals):
        await query.edit_message_text(GOAL_NOT_FOUND_TEXTS.get(lang, GOAL_NOT_FOUND_TEXTS["ru"]))
        return

    # Удаляем выбранную цель
    del goals[index]
    save_goals({user_id: goals})

    await query.edit_message_text(GOAL_DELETED_TEXTS.get(lang, GOAL_DELETED_TEXTS["ru"]))

def insert_followup_question(reply: str, user_input: str, lang: str = "ru") -> str:
    topic = detect_topic(user_input)
    if not topic:
        return reply
    # Определяем язык для текущего пользователя
    topic_questions = questions_by_topic_by_lang.get(lang, questions_by_topic_by_lang["ru"])
    # Пытаемся получить список вопросов для темы
    questions = topic_questions.get(topic.lower())
    if questions:
        follow_up = random.choice(questions)
        return reply.strip() + "\n\n" + follow_up
    return reply
    
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
    
def detect_topic_and_react(user_input: str, lang: str = "ru") -> str:
    text = user_input.lower()
    lang_patterns = topic_patterns_by_lang.get(lang, topic_patterns_by_lang["ru"])

    for topic_data in lang_patterns.values():
        if re.search(topic_data["patterns"], text):
            return topic_data["reply"]

    return ""

# 🔥 Функция определения темы
def detect_topic(text: str, lang: str = "ru") -> str:
    text = text.lower()
    lang_patterns = topic_patterns_full.get(lang, topic_patterns_full["ru"])
    for topic, pattern in lang_patterns.items():
        if re.search(pattern, text):
            return topic
    return ""

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
    
async def habits_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    texts = HABITS_TEXTS.get(lang, HABITS_TEXTS["ru"])
    habits = get_habits(user_id)

    if not habits:
        await update.message.reply_text(texts["no_habits"])
        return

     # Формируем текстовый список привычек
    reply = f"{texts['title']}\n"
    for i, habit in enumerate(habits, 1):
        status = texts["done"] if habit.get("done") else "🔸"
        reply += f"{i}. {status} {habit['text']}\n"

    # Клавиатура: только внизу
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ " + {
                    "ru": "Добавить", "uk": "Додати", "be": "Дадаць", "kk": "Қосу",
                    "kg": "Кошуу", "hy": "Ավելացնել", "ce": "Хила", "md": "Adaugă",
                    "ka": "დამატება", "en": "Add"
                }.get(lang, "Добавить"),
                callback_data="create_habit"
            ),
            InlineKeyboardButton(
                "✅ " + {
                    "ru": "Выполнить", "uk": "Виконати", "be": "Выканаць", "kk": "Аяқтау",
                    "kg": "Аткаруу", "hy": "Կատարել", "ce": "Батта", "md": "Finalizează",
                    "ka": "შესრულება", "en": "Done"
                }.get(lang, "Выполнить"),
                callback_data="mark_habit_done_choose"
            ),
            InlineKeyboardButton(
                "🗑️ " + {
                    "ru": "Удалить", "uk": "Видалити", "be": "Выдаліць", "kk": "Өшіру",
                    "kg": "Өчүрүү", "hy": "Ջնջել", "ce": "ДӀелла", "md": "Șterge",
                    "ka": "წაშლა", "en": "Delete"
                }.get(lang, "Удалить"),
                callback_data="delete_habit_choose"
            )
        ]
    ]

    await update.message.reply_text(
        reply, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
# ——— Handler: Показывает инструкцию по добавлению привычки ———
async def create_habit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    texts = HABIT_TEXTS.get(lang, HABIT_TEXTS["ru"])
    await query.answer()
    await query.edit_message_text(texts["how_to"])

# ——— Handler: Выбор привычки для удаления ———
async def delete_habit_choose_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    habits = get_habits(user_id)
    choose_texts = {
        "ru": "🗑️ Выбери привычку для удаления:",
        "uk": "🗑️ Обери звичку для видалення:",
        "be": "🗑️ Абяры звычку для выдалення:",
        "kk": "🗑️ Өшіру үшін әдетті таңда:",
        "kg": "🗑️ Өчүрүү үчүн көнүмүштү танда:",
        "hy": "🗑️ Ընտրիր սովորությունը ջնջելու համար:",
        "ce": "🗑️ Привычка дӀелла хетам:",
        "md": "🗑️ Alege obiceiul pentru ștergere:",
        "ka": "🗑️ აირჩიე ჩვევა წაშლისთვის:",
        "en": "🗑️ Choose a habit to delete:"
    }
    t = choose_texts.get(lang, choose_texts["ru"])
    if not habits:
        await query.edit_message_text(t + "\n\n❌ Нет привычек для удаления.")
        return
    buttons = [
        [InlineKeyboardButton(f"{i+1}. {h.get('text','')[:40]}", callback_data=f"delete_habit_{i}")]
        for i, h in enumerate(habits)
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(t, reply_markup=reply_markup)

# ——— Handler: Удаляет привычку по индексу ———
async def delete_habit_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    data = query.data
    try:
        index = int(data.split("_")[-1])
    except Exception:
        await query.answer("Ошибка выбора привычки.", show_alert=True)
        return
    habits = get_habits(user_id)
    if not habits or index < 0 or index >= len(habits):
        await query.edit_message_text("❌ Привычка не найдена.")
        return
    delete_texts = {
        "ru": "🗑️ Привычка удалена.",
        "uk": "🗑️ Звичка видалена.",
        "be": "🗑️ Звычка выдалена.",
        "kk": "🗑️ Әдет жойылды.",
        "kg": "🗑️ Көнүмүш өчүрүлдү.",
        "hy": "🗑️ Սովորությունը ջնջված է։",
        "ce": "🗑️ Привычка дӀелла.",
        "md": "🗑️ Obiceiul a fost șters.",
        "ka": "🗑️ ჩვევა წაიშალა.",
        "en": "🗑️ Habit deleted.",
    }
    # Удаляем
    if delete_habit(user_id, index):
        await query.edit_message_text(delete_texts.get(lang, delete_texts["ru"]))
    else:
        await query.edit_message_text(HABIT_BUTTON_TEXTS.get(lang, HABIT_BUTTON_TEXTS["ru"])["delete_error"])
        
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

def goal_title(g):
    # Красиво формируем заголовок для кнопки
    if isinstance(g, dict):
        text = g.get("text") or g.get("name") or g.get("title") or "Без названия"
        deadline = g.get("deadline") or g.get("date")
        badge = " ⏳" + str(deadline) if deadline else ""
        return (text + badge)[:60]
    return str(g)[:60]

def habit_title(h):
    if isinstance(h, dict):
        text = h.get("text") or h.get("name") or "Без названия"
        return text[:60]
    return str(h)[:60]

async def handle_mark_habit_done_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    habits = get_habits(user_id)
    active_indices = [i for i,h in enumerate(habits) if not (isinstance(h, dict) and h.get("done"))]

    if not active_indices:
        await query.edit_message_text("У тебя нет активных привычек.")
        return

    buttons = [
        [InlineKeyboardButton(f"{n}. {habit_title(habits[i])}", callback_data=f"done_habit|{i}")]
        for n, i in enumerate(active_indices, start=1)
    ]
    lang = user_languages.get(str(user_id), "ru")
    await query.edit_message_text(
        HABIT_SELECT_MESSAGE.get(lang, HABIT_SELECT_MESSAGE["ru"]),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_mark_goal_done_choose(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    goals = get_goals(user_id)  # та же функция, что читает mark_goal_done
    # берём только НЕвыполненные цели, но сохраняем ИСХОДНЫЙ индекс i
    active_indices = [i for i, g in enumerate(goals) if not (isinstance(g, dict) and g.get("done"))]

    if not active_indices:
        await query.edit_message_text("У тебя нет активных целей.")
        return

    buttons = [
        [InlineKeyboardButton(f"{n}. {goal_title(goals[i])}", callback_data=f"done_goal|{i}")]
        for n, i in enumerate(active_indices, start=1)
    ]
    lang = user_languages.get(user_id, "ru")
    await query.edit_message_text(
        GOAL_SELECT_MESSAGE.get(lang, GOAL_SELECT_MESSAGE["ru"]),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_done_habit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data

    if not data.startswith("done_habit|"):
        await query.answer("Некорректный выбор.", show_alert=True)
        return

    try:
        index = int(data.split("|", 1)[1])
    except Exception:
        await query.answer("Ошибка индекса.", show_alert=True)
        return

    # отмечаем
    if mark_habit_done(user_id, index):
        add_points(user_id, 2)  # +2 за привычку

        habits = get_habits(user_id)
        title = habit_title(habits[index]) if 0 <= index < len(habits) else "Привычка"

        lang = user_languages.get(user_id, "ru")
        toast = POINTS_ADDED_HABIT.get(lang, POINTS_ADDED_HABIT["ru"])
        text  = HABIT_DONE_MESSAGES.get(lang, HABIT_DONE_MESSAGES["ru"]).format(habit=title)

        # всплывашка
        await query.answer(toast)
        # редактируем исходное сообщение (в колбэк‑хендлере update.message == None)
        await query.edit_message_text(text)
        # Если хочешь не редактировать, а прислать новое сообщение — используй:
        # await context.bot.send_message(chat_id=query.message.chat_id, text=text)
    else:
        await query.answer("Ошибка при обновлении.", show_alert=True)

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_goal_count
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    t = goal_texts.get(lang, goal_texts["ru"])
    patterns = LANG_PATTERNS.get(lang, LANG_PATTERNS["ru"])
    deadline_pattern = patterns["deadline"]
    remind_kw = patterns["remind"]

    # Универсальная функция для ответа (через команду или кнопку)
    def get_send_func(update):
        if getattr(update, "message", None):
            return update.message.reply_text
        elif getattr(update, "callback_query", None):
            return update.callback_query.edit_message_text
        else:
            return None

    send_func = get_send_func(update)
    if send_func is None:
        return

    # ✅ Проверка аргументов
    if not context.args:
        await send_func(t["no_args"], parse_mode="Markdown")
        return

    today = str(date.today())
    if user_id not in user_goal_count:
        user_goal_count[user_id] = {"date": today, "count": 0}
    else:
        if user_goal_count[user_id]["date"] != today:
            user_goal_count[user_id] = {"date": today, "count": 0}

    if not is_premium(user_id):
        if user_goal_count[user_id]["count"] >= 3:
            await send_func(t["limit"])
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
            await send_func(t["bad_date"])
            return

    goal_text = re.sub(deadline_pattern, '', text, flags=re.IGNORECASE).replace(remind_kw, "").strip()

    add_goal(user_id, goal_text, deadline=deadline, remind=remind)
    add_points(user_id, 1)

    reply = f"{t['added']} *{goal_text}*"
    if deadline:
        reply += f"\n{t['deadline']} `{deadline}`"
    if remind:
        reply += f"\n{t['remind']}"

    await send_func(reply, parse_mode="Markdown")
    
# Загрузка истории и режимов
conversation_history = load_history()
user_modes = {}

def get_random_daily_task(user_id: str) -> str:
    # Получаем язык пользователя, если нет — по умолчанию русский
    lang = user_languages.get(user_id, "ru")
    # Выбираем список для языка или дефолтный
    tasks = DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG["ru"])
    # Возвращаем случайное задание
    return random.choice(tasks)

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

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text(RESET_TEXTS.get(lang, RESET_TEXTS["ru"]))

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

    # базовый help + кнопки
    help_text = help_texts.get(lang, help_texts["ru"])
    b = buttons_text.get(lang, buttons_text["ru"])
    keyboard = [
        [InlineKeyboardButton(b[0], callback_data="create_goal")],
        [InlineKeyboardButton(b[1], callback_data="show_goals")],
        [InlineKeyboardButton(b[2], callback_data="create_habit")],
        [InlineKeyboardButton(b[3], callback_data="show_habits")],
        [InlineKeyboardButton(b[4], url="https://t.me/talktomindra_bot")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # секция про поинты и звания
    points = get_user_points(user_id)
    title = get_user_title(points, lang)
    _, next_title, to_next = get_next_title_info(points, lang)
    ladder = build_titles_ladder(lang)

    points_block = POINTS_HELP_TEXTS.get(lang, POINTS_HELP_TEXTS["ru"]).format(
        points=points,
        title=title,
        next_title=next_title,
        to_next=to_next,
        ladder=ladder,
    )

    text = f"{help_text}\n\n{points_block}"

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
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

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    text = UNKNOWN_COMMAND_TEXTS.get(lang, UNKNOWN_COMMAND_TEXTS["ru"])
    await update.message.reply_text(text)

FEEDBACK_CHAT_ID = 7775321566  # <-- твой личный Telegram ID

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


async def send_daily_task(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(pytz.timezone("Europe/Kiev"))

    for user_id in user_last_seen.keys():
        # Проверяем, было ли уже утреннее задание
        last_prompted = user_last_prompted.get(f"{user_id}_morning_task")
        if last_prompted:
            try:
                last_prompted_dt = datetime.fromisoformat(last_prompted)
                if (now - last_prompted_dt) < timedelta(hours=MIN_HOURS_SINCE_LAST_MORNING_TASK):
                    continue  # Уже отправляли сегодня
            except Exception:
                pass

        # Не отправлять если человек был активен последний час
        last_seen = user_last_seen[user_id]
        if (now - last_seen) < timedelta(hours=1):
            continue

        try:
            lang = user_languages.get(str(user_id), "ru")
            greetings = MORNING_MESSAGES_BY_LANG.get(lang, MORNING_MESSAGES_BY_LANG["ru"])
            greeting = random.choice(greetings)
            tasks = DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG["ru"])
            task = random.choice(tasks)

            text = f"{greeting}\n\n🎯 {task}"
            await context.bot.send_message(chat_id=user_id, text=text)
            user_last_prompted[f"{user_id}_morning_task"] = now.isoformat()  # фиксируем отправку
            logging.info(f"✅ Утреннее задание отправлено пользователю {user_id} ({lang})")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке утреннего задания пользователю {user_id}: {e}")
                            
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

def get_premium_stats(user_id: str):
    stats = get_user_stats(user_id)
    return {
        "completed_goals": stats.get("completed_goals", stats.get("goals_completed", 0)),  # поддержка старых и новых ключей
        "habits_tracked": stats.get("habits", stats.get("total_habits", 0)),              # поддержка старых и новых ключей
        "days_active": stats.get("days_active", 0),
        "mood_entries": stats.get("mood_entries", 0)
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

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    t = REMIND_TEXTS.get(lang, REMIND_TEXTS["ru"])
    tz_str = user_timezones.get(user_id, "Europe/Kiev")  # Default — Киев

    # Проверка: премиум или нет
    is_premium = (user_id == str(YOUR_ID)) or (user_id in PREMIUM_USERS)

    if not is_premium:
        current_reminders = user_reminders.get(user_id, [])
        if len(current_reminders) >= 1:
            await update.message.reply_text(t["limit"], parse_mode="Markdown")
            return

    if len(context.args) < 2:
        await update.message.reply_text(t["usage"], parse_mode="Markdown")
        return

    try:
        time_part = context.args[0]
        text_part = " ".join(context.args[1:])
        hour, minute = map(int, time_part.split(":"))
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reminder_time < now:
            reminder_time += timedelta(days=1)

        if user_id not in user_reminders:
            user_reminders[user_id] = []
        # Сохраняем как ISO (строка), чтобы не было проблем с tz
        user_reminders[user_id].append({"time": reminder_time.isoformat(), "text": text_part})

        print(f"[DEBUG] Добавлено напоминание: {user_reminders[user_id]}")

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
    # --- Старт и информация
    CommandHandler("start", start),
    CommandHandler("help", help_command),
    CommandHandler("about", about),

    # --- Язык
    CommandHandler("language", language_command),
    CallbackQueryHandler(language_callback, pattern="^lang_"),

    # --- Цели и привычки
    CommandHandler("goal", goal),
    CommandHandler("goals", show_goals),
    CommandHandler("habit", habit),
    CommandHandler("habits", habits_list),
    CommandHandler("delete", delete_goal_command),

    # --- Кнопки целей/привычек
    # Для показа списка целей и кнопок "Добавить/Удалить"
    CallbackQueryHandler(show_goals, pattern="^show_goals$"),
    CallbackQueryHandler(goal, pattern="^create_goal$"),
    CallbackQueryHandler(delete_goal_choose_handler, pattern="^delete_goal_choose$"),
    CallbackQueryHandler(delete_goal_confirm_handler, pattern="^delete_goal_\\d+$"),
    CallbackQueryHandler(show_habits, pattern="^show_habits$"),
    CallbackQueryHandler(create_habit_handler, pattern="^create_habit$"),
    CallbackQueryHandler(delete_habit_choose_handler, pattern="^delete_habit_choose$"),
    CallbackQueryHandler(delete_habit_confirm_handler, pattern="^delete_habit_\\d+$"),
    # --- Работа с задачами
    CommandHandler("task", task),
    CommandHandler("premium_task", premium_task),
    CommandHandler("remind", remind_command),

    # --- Статистика и очки
    CommandHandler("stats", stats_command),
    CommandHandler("mypoints", mypoints_command),
    CommandHandler("mystats", my_stats_command),
    CommandHandler("premium_stats", premium_stats),

    # --- Премиум и челленджи
    CommandHandler("premium_report", premium_report),
    CommandHandler("premium_challenge", premium_challenge),
    CommandHandler("premium_mode", premium_mode),
    CallbackQueryHandler(premium_mode_callback, pattern="^premium_mode_"),
    CommandHandler("premium_days", premium_days),

    # --- Разное
    CommandHandler("timezone", set_timezone),
    CommandHandler("feedback", feedback),
    CommandHandler("mode", mode),
    CallbackQueryHandler(handle_mode_choice, pattern="^mode_"),
    CommandHandler("quote", quote),
    CommandHandler("invite", invite),
    CommandHandler("mytask", mytask_command),
    CommandHandler("reset", reset),
    CommandHandler("test_mood", test_mood),
    CallbackQueryHandler(handle_mark_goal_done_choose, pattern=r"^mark_goal_done_choose$"),
    CallbackQueryHandler(handle_done_goal_callback, pattern=r"^done_goal\|\d+$"),
    
    # --- Кнопки реакции и добавления цели
    CallbackQueryHandler(handle_reaction_button, pattern="^react_"),
    CallbackQueryHandler(handle_add_goal_callback, pattern="^add_goal\\|"),
    CallbackQueryHandler(handle_mark_habit_done_choose, pattern=r"^mark_habit_done_choose$"),
    CallbackQueryHandler(handle_done_habit_callback,    pattern=r"^done_habit\|\d+$"),
    
    # --- Чаты и голос
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.COMMAND, unknown_command),  # Unknown в самом конце!
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
