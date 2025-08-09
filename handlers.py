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
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from telegram.constants import ChatAction, ParseMode
from config import client, TELEGRAM_BOT_TOKEN
from history import load_history, save_history, trim_history
from goals import  is_goal_like, goal_keywords_by_lang, REACTIONS_GOAL_DONE, DELETE_MESSAGES
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from storage import delete_goal, load_goals, save_goals, add_goal, get_goals, get_goals_for_user, mark_goal_done, load_habits, save_habits, add_habit, get_habits, mark_habit_done, delete_habit
from random import randint, choice
from stats import load_stats, save_stats, get_premium_until, set_premium_until, is_premium, got_trial, set_trial, add_referral, add_points, get_user_stats, get_user_title, load_json_file, get_stats, OWNER_ID, ADMIN_USER_IDS 
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

help_texts = {
    "ru": (
        "✨ Вот что я умею:\n\n"
        "💬 Просто напиши мне сообщение — я отвечу.\n"
        "🧠 Я запоминаю историю общения (можно сбросить).\n\n"
        "📎 Основные команды:\n"
        "🚀 /start — приветствие\n"
        "🔄 /reset — сброс истории\n"
        "🆘 /help — показать это сообщение\n"
        "ℹ️ /about — немного обо мне\n"
        "🎭 /mode — изменить стиль общения\n"
        "🎯 /goal — поставить личную цель\n"
        "🏆 /goals — список твоих целей\n"
        "🌱 /habit — добавить привычку\n"
        "📋 /habits — список твоих привычек\n"
        "📌 /task — задание на день\n"
        "✉️ /feedback — отправить отзыв\n"
        "⏰ /remind — напомнить о цели\n"
        "✅ /done — отметить цель выполненной\n"
        "🧩 /mytask — персонализированное задание\n"
        "🎭 /test_mood — протестировать настрой/эмоции\n\n"
        "🌐 /language — выбрать язык общения\n\n"
        "🌍 /timezone  — сменить свой часовой пояс для напоминаний\n"
        "👫 /invite — пригласить друга\n"
        "💎 /premium_days — сколько осталось Mindra+\n\n"
        "💎 Mindra+ функции:\n"
        "📊 /premium_report — личный отчёт\n"
        "🏅 /premium_challenge — уникальный челлендж\n"
        "🦄 /premium_mode — эксклюзивный режим\n"
        "📈 /premium_stats — расширенная статистика\n\n"
        "😉 Попробуй! А с подпиской возможностей будет ещё больше 💜"
    ),
    "uk": (
        "✨ Ось що я вмію:\n\n"
        "💬 Просто напиши мені повідомлення — я відповім.\n"
        "🧠 Я запам’ятовую історію спілкування (можна скинути).\n\n"
        "📎 Основні команди:\n"
        "🚀 /start — привітання\n"
        "🔄 /reset — скинути історію\n"
        "🆘 /help — показати це повідомлення\n"
        "ℹ️ /about — трохи про мене\n"
        "🎭 /mode — змінити стиль спілкування\n"
        "🎯 /goal — поставити ціль\n"
        "🏆 /goals — список цілей\n"
        "🌱 /habit — додати звичку\n"
        "📋 /habits — список звичок\n"
        "📌 /task — завдання на день\n"
        "✉️ /feedback — надіслати відгук\n"
        "⏰ /remind — нагадати про ціль\n"
        "✅ /done — позначити ціль виконаною\n"
        "🧩 /mytask — персональне завдання\n"
        "🎭 /test_mood — протестувати настрій\n\n"
        "🌐 /language — вибрати мову\n\n"
        "🌍 /timezone  — змінити свій часовий пояс для нагадувань\n"
        "👫 /invite — запросити друга\n"
        "💎 /premium_days — скільки залишилося Mindra+\n\n"
        "💎 Mindra+ функції:\n"
        "📊 /premium_report — звіт\n"
        "🏅 /premium_challenge — унікальний челендж\n"
        "🦄 /premium_mode — ексклюзивний режим\n"
        "📈 /premium_stats — розширена статистика\n\n"
        "😉 Спробуй! З підпискою можливостей більше 💜"
    ),
    "be": (
        "✨ Вось што я ўмею:\n\n"
        "💬 Проста напішы мне паведамленне — я адкажу.\n"
        "🧠 Я запамінаю гісторыю зносін (можна скінуць).\n\n"
        "📎 Асноўныя каманды:\n"
        "🚀 /start — прывітанне\n"
        "🔄 /reset — скінуць гісторыю\n"
        "🆘 /help — паказаць гэта паведамленне\n"
        "ℹ️ /about — трохі пра мяне\n"
        "🎭 /mode — змяніць стыль зносін\n"
        "🎯 /goal — паставіць мэту\n"
        "🏆 /goals — спіс мэт\n"
        "🌱 /habit — дадаць звычку\n"
        "📋 /habits — спіс звычак\n"
        "📌 /task — заданне на дзень\n"
        "✉️ /feedback — даслаць водгук\n"
        "⏰ /remind — нагадаць пра мэту\n"
        "✅ /done — адзначыць мэту выкананай\n"
        "🧩 /mytask — персаналізаванае заданне\n"
        "🎭 /test_mood — праверыць настрой\n\n"
        "🌐 /language — выбраць мову\n\n"
        "🌍 /timezone  — змяніць свой гадзінны пояс для напамінаў\n"
        "👫 /invite — запрасіць сябра\n"
        "💎 /premium_days — колькі засталося Mindra+\n\n"
        "💎 Mindra+ функцыі:\n"
        "📊 /premium_report — асабісты справаздачу\n"
        "🏅 /premium_challenge — унікальны чэлендж\n"
        "🦄 /premium_mode — эксклюзіўны рэжым\n"
        "📈 /premium_stats — пашыраная статыстыка\n\n"
        "😉 Паспрабуй! З падпіскай магчымасцей больш 💜"
    ),
    "kk": (
        "✨ Міне не істей аламын:\n\n"
        "💬 Маған хабарлама жаз — мен жауап беремін.\n"
        "🧠 Мен сөйлесу тарихын есте сақтаймын (тазалауға болады).\n\n"
        "📎 Негізгі командалар:\n"
        "🚀 /start — сәлемдесу\n"
        "🔄 /reset — тарихты тазалау\n"
        "🆘 /help — осы хабарламаны көрсету\n"
        "ℹ️ /about — мен туралы\n"
        "🎭 /mode — сөйлесу стилін өзгерту\n"
        "🎯 /goal — мақсат қою\n"
        "🏆 /goals — мақсаттар тізімі\n"
        "🌱 /habit — әдет қосу\n"
        "📋 /habits — әдеттер тізімі\n"
        "📌 /task — күннің тапсырмасы\n"
        "✉️ /feedback — пікір жіберу\n"
        "⏰ /remind — мақсат туралы еске салу\n"
        "✅ /done — мақсатты орындалған деп белгілеу\n"
        "🧩 /mytask — жеке тапсырма\n"
        "🎭 /test_mood — көңіл-күйді тексеру\n\n"
        "🌐 /language — тілді таңдау\n\n"
        "🌍 /timezone  — уақыт белдеуін өзгерту (еске салу үшін)\n"
        "👫 /invite — досыңды шақыру\n"
        "💎 /premium_days — Mindra+ қанша қалды\n\n"
        "💎 Mindra+ мүмкіндіктері:\n"
        "📊 /premium_report — жеке есеп\n"
        "🏅 /premium_challenge — ерекше челлендж\n"
        "🦄 /premium_mode — эксклюзивті режим\n"
        "📈 /premium_stats — кеңейтілген статистика\n\n"
        "😉 Қолданып көр! Жазылумен мүмкіндіктер көбірек 💜"
    ),
    "kg": (
        "✨ Мына нерселерди кыла алам:\n\n"
        "💬 Жөн эле мага кабар жаз — жооп берем.\n"
        "🧠 Мен сүйлөшүүнү эстеп калам (тазалоого болот).\n\n"
        "📎 Негизги буйруктар:\n"
        "🚀 /start — саламдашуу\n"
        "🔄 /reset — тарыхты тазалоо\n"
        "🆘 /help — ушул билдирүүнү көрсөтүү\n"
        "ℹ️ /about — мен жөнүндө\n"
        "🎭 /mode — сүйлөшүү стилин өзгөртүү\n"
        "🎯 /goal — максат коюу\n"
        "🏆 /goals — максаттар тизмеси\n"
        "🌱 /habit — көнүмүш кошуу\n"
        "📋 /habits — көнүмүштөр тизмеси\n"
        "📌 /task — күндүн тапшырмасы\n"
        "✉️ /feedback — пикир жөнөтүү\n"
        "⏰ /remind — максат жөнүндө эскертүү\n"
        "✅ /done — максатты аткарылган деп белгилөө\n"
        "🧩 /mytask — жеке тапшырма\n"
        "🎭 /test_mood — маанайды текшерүү\n\n"
        "🌐 /language — тил тандоо\n\n"
        "🌍 /timezone  — эскертүүлөр үчүн убакыт зонасын өзгөртүү\n"
        "👫 /invite — дос чакыруу\n"
        "💎 /premium_days — Mindra+ канча калды\n\n"
        "💎 Mindra+ мүмкүнчүлүктөрү:\n"
        "📊 /premium_report — жеке отчет\n"
        "🏅 /premium_challenge — өзгөчө тапшырма\n"
        "🦄 /premium_mode — эксклюзивдүү режим\n"
        "📈 /premium_stats — кеңейтилген статистика\n\n"
        "😉 Байкап көр! Жазылуу менен мүмкүнчүлүктөр көбөйөт 💜"
    ),
    "hy": (
        "✨ Ահա, թե ինչ կարող եմ անել․\n\n"
        "💬 Просто գրիր ինձ — ես կպատասխանեմ։\n"
        "🧠 Ես հիշում եմ զրույցի պատմությունը (կարող ես վերականգնել)։\n\n"
        "📎 Հիմնական հրամաններ․\n"
        "🚀 /start — ողջույն\n"
        "🔄 /reset — զրույցի պատմությունը մաքրել\n"
        "🆘 /help — ցույց տալ այս հաղորդագրությունը\n"
        "ℹ️ /about — իմ մասին\n"
        "🎭 /mode — փոխել շփման ոճը\n"
        "🎯 /goal — դնել նպատակ\n"
        "🏆 /goals — նպատակների ցուցակ\n"
        "🌱 /habit — ավելացնել սովորություն\n"
        "📋 /habits — սովորությունների ցուցակ\n"
        "📌 /task — օրվա առաջադրանք\n"
        "✉️ /feedback — ուղարկել արձագանք\n"
        "⏰ /remind — հիշեցնել նպատակը\n"
        "✅ /done — նշել նպատակը կատարված\n"
        "🧩 /mytask — անհատական առաջադրանք\n"
        "🎭 /test_mood — ստուգել տրամադրությունը\n\n"
        "🌐 /language — ընտրել լեզուն\n\n"
        "🌍 /timezone  — փոխել ժամանակային գոտին հիշեցումների համար\n"
        "👫 /invite — հրավիրել ընկերոջը\n"
        "💎 /premium_days — Mindra+-ի որքան է մնացել\n\n"
        "💎 Mindra+ հնարավորություններ․\n"
        "📊 /premium_report — անձնական հաշվետվություն\n"
        "🏅 /premium_challenge — բացառիկ մարտահրավեր\n"
        "🦄 /premium_mode — բացառիկ ռեժիմ\n"
        "📈 /premium_stats — ընդլայնված վիճակագրություն\n\n"
        "😉 Փորձիր! Բաժանորդագրությամբ հնարավորությունները ավելի շատ են 💜"
    ),
    "ce": (
        "✨ Цхьа хьоьшу болу:\n\n"
        "💬 ДӀайазде ма кхоллараллин — са йаьлла.\n"
        "🧠 Са гӀирса тарих йац (цхьа мацахь йаьлла).\n\n"
        "📎 Нохчи командеш:\n"
        "🚀 /start — салам алам\n"
        "🔄 /reset — тарих лелош\n"
        "🆘 /help — кхета хийцам\n"
        "ℹ️ /about — са йац\n"
        "🎭 /mode — стили тӀетохьа\n"
        "🎯 /goal — мацахь кхоллар\n"
        "🏆 /goals — мацахьер список\n"
        "🌱 /habit — йоцу привычка\n"
        "📋 /habits — привычкаш список\n"
        "📌 /task — тахана дӀаязде\n"
        "✉️ /feedback — йа дӀайазде отзыв\n"
        "⏰ /remind — мацахьер дӀадела\n"
        "✅ /done — мацахьер дӀанисса\n"
        "🧩 /mytask — персонал дӀаязде\n"
        "🎭 /test_mood — хьовса теста\n\n"
        "🌐 /language — моттиг дахьа\n\n"
        "🌍 /timezone  — напоминание хийцна лаьцна хийцара\n"
        "👫 /invite — дика чакхара\n"
        "💎 /premium_days — Mindra+ чохь дика остал\n\n"
        "💎 Mindra+ функцеш:\n"
        "📊 /premium_report — личный отчет\n"
        "🏅 /premium_challenge — эксклюзивный челлендж\n"
        "🦄 /premium_mode — эксклюзивный режим\n"
        "📈 /premium_stats — статистика\n\n"
        "😉 Хьажа хьоьшу! Подписка йолуш, функцеш къобал болу 💜"
    ),
    "md": (
        "✨ Iată ce pot face:\n\n"
        "💬 Scrie-mi un mesaj — îți voi răspunde.\n"
        "🧠 Îmi amintesc istoricul conversației (poți reseta).\n\n"
        "📎 Comenzi principale:\n"
        "🚀 /start — salut\n"
        "🔄 /reset — resetează istoricul\n"
        "🆘 /help — arată acest mesaj\n"
        "ℹ️ /about — despre mine\n"
        "🎭 /mode — schimbă stilul de comunicare\n"
        "🎯 /goal — setează un obiectiv\n"
        "🏆 /goals — lista obiectivelor\n"
        "🌱 /habit — adaugă un obicei\n"
        "📋 /habits — lista obiceiurilor\n"
        "📌 /task — sarcina zilei\n"
        "✉️ /feedback — trimite feedback\n"
        "⏰ /remind — amintește de un obiectiv\n"
        "✅ /done — marchează obiectivul îndeplinit\n"
        "🧩 /mytask — sarcină personalizată\n"
        "🎭 /test_mood — testează starea\n\n"
        "🌐 /language — alege limba\n\n"
        "🌍 /timezone  — schimbă fusul orar pentru mementouri\n"
        "👫 /invite — invită un prieten\n"
        "💎 /premium_days — câte zile de Mindra+ rămase\n\n"
        "💎 Funcții Mindra+:\n"
        "📊 /premium_report — raport personal\n"
        "🏅 /premium_challenge — provocare unică\n"
        "🦄 /premium_mode — mod exclusiv\n"
        "📈 /premium_stats — statistici avansate\n\n"
        "😉 Încearcă! Cu abonament ai mai multe opțiuni 💜"
    ),
    "ka": (
        "✨ აი, რას ვაკეთებ:\n\n"
        "💬 უბრალოდ მომწერე და გიპასუხებ.\n"
        "🧠 ვიმახსოვრებ დიალოგის ისტორიას (შეგიძლია გაასუფთავო).\n\n"
        "📎 ძირითადი ბრძანებები:\n"
        "🚀 /start — მისალმება\n"
        "🔄 /reset — ისტორიის გასუფთავება\n"
        "🆘 /help — ამ შეტყობინების ჩვენება\n"
        "ℹ️ /about — ჩემს შესახებ\n"
        "🎭 /mode — კომუნიკაციის სტილის შეცვლა\n"
        "🎯 /goal — მიზნის დაყენება\n"
        "🏆 /goals — შენი მიზნების სია\n"
        "🌱 /habit — ჩვევის დამატება\n"
        "📋 /habits — ჩვევების სია\n"
        "📌 /task — დღევანდელი დავალება\n"
        "✉️ /feedback — გამოგზავნე გამოხმაურება\n"
        "⏰ /remind — შეგახსენო მიზანი\n"
        "✅ /done — დააფიქსირე მიზნის შესრულება\n"
        "🧩 /mytask — პერსონალური დავალება\n"
        "🎭 /test_mood — ტესტი განწყობაზე\n\n"
        "🌐 /language — აირჩიე ენა\n\n"
        "🌍 /timezone  — დროის სარტყელის შეცვლა შეხსენებებისთვის\n"
        "👫 /invite — მეგობრის მიწვევა\n"
        "💎 /premium_days — Mindra+-ის დარჩენილი დრო\n\n"
        "💎 Mindra+ ფუნქციები:\n"
        "📊 /premium_report — პირადი ანგარიში\n"
        "🏅 /premium_challenge — უნიკალური გამოწვევა\n"
        "🦄 /premium_mode — ექსკლუზიური რეჟიმი\n"
        "📈 /premium_stats — გაფართოებული სტატისტიკა\n\n"
        "😉 სცადე! გამოწერით შესაძლებლობები მეტია 💜"
    ),
    "en": (
        "✨ Here’s what I can do:\n\n"
        "💬 Just write me a message — I’ll reply.\n"
        "🧠 I remember the chat history (you can reset it).\n\n"
        "📎 Main commands:\n"
        "🚀 /start — greeting\n"
        "🔄 /reset — reset chat history\n"
        "🆘 /help — show this message\n"
        "ℹ️ /about — about me\n"
        "🎭 /mode — change chat style\n"
        "🎯 /goal — set a goal\n"
        "🏆 /goals — list your goals\n"
        "🌱 /habit — add a habit\n"
        "📋 /habits — list your habits\n"
        "📌 /task — daily task\n"
        "✉️ /feedback — send feedback\n"
        "⏰ /remind — remind about a goal\n"
        "✅ /done — mark a goal as done\n"
        "🧩 /mytask — personalized task\n"
        "🎭 /test_mood — test your mood\n\n"
        "🌐 /language — choose language\n\n"
        "🌍 /timezone  — change your timezone for reminders\n"
        "👫 /invite — invite a friend\n"
        "💎 /premium_days — how many Mindra+ days left\n\n"
        "💎 Mindra+ features:\n"
        "📊 /premium_report — personal progress report\n"
        "🏅 /premium_challenge — unique challenge\n"
        "🦄 /premium_mode — exclusive mode\n"
        "📈 /premium_stats — extended statistics\n\n"
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
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # Получаем текст help и кнопки
    help_text = help_texts.get(lang, help_texts["ru"])
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
