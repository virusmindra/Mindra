import os
import sqlite3
import json
import random
import re
import math
import logging
import openai
import tempfile
import aiohttp
import subprocess
import ffmpeg
import traceback
import textwrap
import uuid
import asyncio
import pytz
import telegram
import shutil
from elevenlabs import ElevenLabs 
from collections import defaultdict
from texts import (
    VOICE_TEXTS_BY_LANG,
    STORY_INTENT,
    MENU_TEXTS,
    FEATURE_MATRIX,
    PLAN_FREE,
    PLAN_PLUS,
    PLAN_PRO,
    PLAN_LABEL,
    UPSELL_TEXTS,
    ALL_PLANS,
    PLAN_LABELS,
    QUOTAS,
    SLEEP_UI_TEXTS,
    VOICE_PRESETS,
    VOICE_UI_TEXTS,
    BGM_PRESETS,
    BGM_GAIN_CHOICES,
    STORY_TEXTS,
    LANG_TO_TTS,
    VOICE_MODE_TEXTS,
    CHALLENGE_BANK,
    GH_TEXTS,
    SETTINGS_TEXTS,
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
    POINTS_HELP_TEXTS,
    TIMEZONE_ALIASES,
    TZ_KEYBOARD_ROWS,
    TZ_TEXTS,
    P_TEXTS
)
from datetime import datetime, timedelta, timezone, date
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from telegram.constants import ChatAction, ParseMode
from config import client, TELEGRAM_BOT_TOKEN, ELEVEN_API_KEY, BASE_DIR, DATA_DIR, PREMIUM_DB_PATH, REMIND_DB_PATH
from history import load_history, save_history, trim_history
from goals import  is_goal_like, goal_keywords_by_lang, REACTIONS_GOAL_DONE, DELETE_MESSAGES
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from storage import delete_goal, load_goals, save_goals, add_goal, get_goals, get_goals_for_user, mark_goal_done, load_habits, save_habits, add_habit, get_habits, mark_habit_done, delete_habit
from random import randint, choice
from stats import (
    # --- constants ---
    ADMIN_USER_IDS, OWNER_ID,
    STATS_FILE, GOALS_FILE, HABITS_FILE,
    DATA_DIR, REMIND_DB_PATH, PREMIUM_DB_PATH,

    # --- reminders DB ---
    ensure_remind_db, remind_db, premium_db,

    # --- premium/subscription ---
    ensure_premium_db, migrate_premium_from_stats, ensure_premium_challenges,
    get_premium_until, set_premium_until, set_premium_until_dt, extend_premium_days,
    is_premium_db, _parse_any_dt,

    # --- trials & referrals ---
    grant_trial_if_eligible, process_referral,
    got_trial, set_trial,
    got_referral, set_referral, add_referral,

    # --- points & titles ---
    add_points, get_user_points,
    get_user_title, get_next_title_info, build_titles_ladder,

    # --- user stats ---
    load_stats, save_stats, get_stats, get_user_stats, _collect_activity_dates,
)
from telegram.error import BadRequest
global user_timezones
from zoneinfo import ZoneInfo
from collections import defaultdict
from functools import wraps

# Глобальные переменные
user_last_seen = {}
user_last_prompted = {}
user_reminders = {}
user_points = {}
user_message_count = {}
user_goal_count = {}
user_languages = {}  # {user_id: 'ru'/'uk'/'md'/'be'/'kk'/'kg'/'hy'/'ka'/'ce'}
user_ref_args: dict[str, str] = {}
user_last_polled = {}
user_last_report_sent = {}  # user_id: date (ISO)
user_last_daily_sent = {}  # user_id: date (iso)
user_timezones = {}
user_voice_mode = {}  # {user_id: bool}
user_voice_prefs = {}
waiting_feedback: set[str] = set()
_last_action = {}

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

REMIND_I18N = REMIND_TEXTS
# --- ДОБАВКА ДЛЯ SUPPORT ---
user_last_support: dict[str, datetime] = {}
user_support_daily_date: dict[str, str] = {}     # YYYY-MM-DD (UTC)
user_support_daily_count: dict[str, int] = defaultdict(int)

SUPPORT_MIN_HOURS_BETWEEN = 4     # не чаще 1 раза в 4 часа
SUPPORT_MAX_PER_DAY = 2           # не более 2 раз в сутки
SUPPORT_RANDOM_CHANCE = 0.7       # шанс отправить (как у POLL_RANDOM_CHANCE)

# Окно времени для «поддерживающих» сообщений — используем твои idle‑границы по Киеву
SUPPORT_TIME_START = IDLE_TIME_START   # 10
SUPPORT_TIME_END = IDLE_TIME_END       # 22
VOICE_TEXTS = VOICE_UI_TEXTS 


# Тихие часы по локальному времени пользователя
QUIET_START = 22  # не тревожить с 22:00
QUIET_END   = 9   # до 09:00
STORY_COOLDOWN_HOURS = 4 

_story_last_suggest: dict[str, datetime] = {}   # uid -> utc time
_story_optout_until: dict[str, datetime] = {}   # uid -> utc time

DEFAULT_ELEVEN_FEMALE = "21m00Tcm4TlvDq8ikWAM"
DEFAULT_ELEVEN_MALE = "JBFqnCBsd6RMkjVDRZzb" 
STORY_INTEN = STORY_INTENT

# Базовая папка проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Где хранить файлы БД (по умолчанию ./data, можно переопределить через ENV)
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# Полные пути к БД (можно переопределить через ENV)
PREMIUM_DB_PATH = os.getenv("PREMIUM_DB_PATH", os.path.join(DATA_DIR, "premium.sqlite3"))
REMIND_DB_PATH  = os.getenv("REMIND_DB_PATH",  os.path.join(DATA_DIR, "reminders.sqlite3"))

UI_MSG_KEY = "ui_msg_id"

# URL страницы оплаты — замени на свою
PREMIUM_URL = "https://example.com/pay"

# ==== Sleep (ambient only) ====
_sleep_prefs: dict[str, dict] = {}
CB = "ui:"
CHALLENGE_POINTS = int(os.getenv("CHALLENGE_POINTS", 25)) 


def _kb_home(uid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data="m:nav:home")]
    ])

    
def once_per_message(handler_name: str):
    def deco(fn):
        async def wrapper(update, context, *args, **kwargs):
            mid = getattr(getattr(update, "effective_message", None), "message_id", None)
            key = f"_once_{handler_name}_{mid}"
            if mid is not None and context.chat_data.get(key):
                return
            if mid is not None:
                context.chat_data[key] = True
            return await fn(update, context, *args, **kwargs)
        return wrapper
    return deco

def once_per_callback(handler_name: str):
    def deco(fn):
        async def wrapper(update, context, *args, **kwargs):
            q = getattr(update, "callback_query", None)
            cid = getattr(q, "id", None)
            key = f"_once_{handler_name}_{cid}"
            if cid is not None and context.chat_data.get(key):
                return
            if cid is not None:
                context.chat_data[key] = True
            return await fn(update, context, *args, **kwargs)
        return wrapper
    return deco


def _debounce(uid: str, key: str, ms: int = 800) -> bool:
    """True = надо игнорировать (слишком рано повтор)."""
    now = datetime.now(timezone.utc)
    k = (uid, key)
    t = _last_action.get(k)
    if t and (now - t) < timedelta(milliseconds=ms):
        return True
    _last_action[k] = now
    return False
    
async def _dbg_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except Exception:
        pass
    logging.debug(f"[DBG] unhandled callback: {q.data if q else None}")
    # ничего не отправляем
        
async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = _menu_header_text(uid)
    kb = _menu_kb_home(uid)

    chat_id = update.effective_chat.id
    ui_id = context.user_data.get(UI_MSG_KEY)

    if ui_id:
        # Пытаемся отредактировать существующее UI-сообщение
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=ui_id,
                text=text,
                reply_markup=kb,
                parse_mode="Markdown",
            )
            return
        except Exception:
            # если сообщение нельзя отредактировать (удалено/протухло) — пошлём новое ниже
            pass

    # UI-сообщения ещё нет — шлём новое и запоминаем id
    sent = await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    context.user_data[UI_MSG_KEY] = sent.message_id

async def _safe_answer(q):
    try:
        await q.answer()
    except BadRequest as e:
        s = str(e)
        if "query is too old" in s or "query ID is invalid" in s:
            pass
        else:
            raise
            
# универсальный «шим», чтобы любой командный хендлер можно было вызвать из callback
def _shim_update_for_cb(q: CallbackQuery, context) -> "object":
    chat_id = q.message.chat.id
    user = q.from_user
    bot = context.bot

    class _Msg:
        async def reply_text(self, text, **kw):
            await bot.send_message(chat_id=chat_id, text=text, **kw)

    class _Upd:
        pass

    u = _Upd()
    u.effective_user = user
    u.effective_chat = q.message.chat
    u.message = _Msg()
    return u


async def show_main_menu(msg):
    uid = str(msg.chat.id)
    t = _menu_i18n(uid)  # тексты по текущему языку

    # Заголовок + (если нужно) статус премиума
    lines = [t.get("title", "🏠 Main menu")]  # подстраховка от KeyError

    text = "\n".join(lines)

    await msg.edit_text(
        text,
        reply_markup=_menu_kb_home(uid),  # существующая клавиатура главного меню
        parse_mode="Markdown",
    )

async def _try_call(names, update, context) -> bool:
    """Пробует вызвать ПЕРВУЮ найденную функцию из списка names. Возвращает True при успехе."""
    import inspect, sys
    g = globals()
    for name in names:
        fn = g.get(name)
        if callable(fn):
            try:
                if inspect.iscoroutinefunction(fn):
                    await fn(update, context)
                else:
                    # синхронное — завернём
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, lambda: fn(update, context))
                return True
            except Exception as e:
                logging.warning("call %s failed: %s", name, e)
                return False
    return False
    
async def menu_cb(update, context):
    q = update.callback_query
    if not q or not q.data or not q.data.startswith("m:"):
        return
    await _safe_answer(q)
    context.user_data[UI_MSG_KEY] = q.message.message_id  # работаем в одном UI-сообщении

    uid = str(q.from_user.id)
    t = _menu_i18n(uid)

    # ---------- Навигация ----------
    if q.data == "m:nav:home":
        try:
            await q.edit_message_text(_menu_home_text(uid), reply_markup=_menu_kb_home(uid), parse_mode="Markdown")
        except Exception:
            await context.bot.send_message(chat_id=q.message.chat.id, text=_menu_home_text(uid),
                                           reply_markup=_menu_kb_home(uid), parse_mode="Markdown")
        return

    if q.data == "m:nav:features":
        return await q.edit_message_text(f"*{t['feat_title']}*\n{t['feat_body']}",
                                         parse_mode="Markdown", reply_markup=_menu_kb_features(uid))

    if q.data == "m:nav:plus":
        return await q.edit_message_text(f"*{t['plus_title']}*\n{t['plus_body']}",
                                         parse_mode="Markdown", reply_markup=_menu_kb_plus(uid))

    if q.data == "m:nav:premium":
        return await q.edit_message_text(f"*{t['prem_title']}*",
                                         parse_mode="Markdown", reply_markup=_menu_kb_premium(uid))

    if q.data == "m:nav:settings":
        return await q.edit_message_text(f"*{t['set_title']}*\n{t['set_body']}",
                                         parse_mode="Markdown", reply_markup=_menu_kb_settings(uid))

    if q.data == "m:nav:close":
        try:
            await q.delete_message()
        except Exception:
            pass
        return

    # ---------- Обычные функции (через вызов внешних хендлеров) ----------
    u = _shim_update_for_cb(q, context)
    ok = None  # важно: чтобы не было UnboundLocalError

    if q.data == "m:feat:tracker":
        ok = await _try_call(["tracker_menu_cmd", "tracker_menu"], u, context)

    elif q.data == "m:feat:mode":
        ok = await _try_call(["mode", "mode_cmd"], u, context)

    elif q.data == "m:feat:reminders":
        ok = await _try_call(["reminders_menu_cmd", "reminders_menu"], u, context)

    elif q.data == "m:feat:points":
        ok = await _try_call(["points_command", "points", "mypoints_command"], u, context)

    elif q.data == "m:feat:mood":
        ok = await _try_call(["test_mood", "test_mood_cmd"], u, context)

    # ---------- Премиум-функции ----------
    elif q.data == "m:plus:voice":
        ok = await _try_call(["voice_settings", "voice_settings_cmd"], u, context)

    elif q.data == "m:plus:sleep":
        ok = await _try_call(["sleep_cmd", "sleep"], u, context)

    elif q.data == "m:plus:story":
        ok = await _try_call(["story_cmd", "story_menu_cmd"], u, context)

    elif q.data == "m:plus:pmode":
        ok = await _try_call(["premium_mode_cmd", "premium_mode"], u, context)

    elif q.data == "m:plus:pstats":
        ok = await _try_call(["premium_stats_cmd", "premium_stats", "premium_status"], u, context)

    elif q.data == "m:plus:preport":
        ok = await _try_call(["premium_report_cmd", "premium_report"], u, context)

    elif q.data == "m:plus:pchallenge":
        ok = await _try_call(["premium_challenge_cmd", "premium_challenge"], u, context)

    # ---------- Премиум раздел ----------
    elif q.data == "m:premium:days":
        ok = await _try_call(["premium_days_cmd", "premium_days"], u, context)

    elif q.data == "m:premium:invite":
        ok = await _try_call(["invite", "invite_cmd"], u, context)

    # ---------- Настройки ----------
    elif q.data == "m:set:lang":
        # только выбор ЯЗЫКА (без таймзоны)
        # берём текст из твоего SETTINGS_TEXTS
        try:
            st = SETTINGS_TEXTS.get(user_languages.get(uid, "ru"), SETTINGS_TEXTS["ru"])
            title = st.get("choose_lang", "🌐 Выбери язык интерфейса:")
        except Exception:
            title = "🌐 Выбери язык интерфейса:"

        kb = [
            [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
             InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_uk")],
            [InlineKeyboardButton("Moldovenească 🇲🇩", callback_data="lang_md"),
             InlineKeyboardButton("Беларуская 🇧🇾", callback_data="lang_be")],
            [InlineKeyboardButton("Қазақша 🇰🇿", callback_data="lang_kk"),
             InlineKeyboardButton("Кыргызча 🇰🇬", callback_data="lang_kg")],
            [InlineKeyboardButton("Հայերեն 🇦🇲", callback_data="lang_hy"),
             InlineKeyboardButton("ქართული 🇬🇪", callback_data="lang_ka")],
            [InlineKeyboardButton("Нохчийн мотт 🇷🇺", callback_data="lang_ce"),
             InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
            [InlineKeyboardButton(t["back"], callback_data="m:nav:settings")],
        ]
        await q.edit_message_text(title, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(kb))
        return  # ← ранний выход, чтобы не упасть на "if not ok"

    elif q.data == "m:set:tz":
        return await show_timezone_menu(q.message, origin="settings")

    elif q.data == "m:set:feedback":
        await q.edit_message_text(t["feedback_ask"],
                                  parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t["back"], callback_data="m:nav:settings")]]))
        waiting_feedback.add(uid)
        return

    # ---------- общий результат ----------
    if ok is False:
        await context.bot.send_message(q.message.chat.id, "Команда недоступна.")
    return

async def ui_show_from_command(update: Update,
                               context: ContextTypes.DEFAULT_TYPE,
                               text: str,
                               reply_markup=None,
                               parse_mode: str | None = "Markdown"):
    chat_id = update.effective_chat.id
    ui_id = context.user_data.get(UI_MSG_KEY)

    if ui_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=ui_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return
        except BadRequest as e:
            # если текст/клава те же — просто выходим, не создавая новое сообщение
            if "message is not modified" in str(e).lower():
                return
            # другие BadRequest обрабатываем ниже (пошлём новое сообщение)
        except Exception:
            pass  # сообщение могло быть удалено / слишком старое — пошлём новое ниже

    sent = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    context.user_data[UI_MSG_KEY] = sent.message_id

def _kb_back_home(uid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data="m:nav:home")]])
    
def _menu_i18n(uid: str) -> dict:
    lang = user_languages.get(uid, "ru")
    return MENU_TEXTS.get(lang, MENU_TEXTS["ru"])

def _menu_header_text(uid: str) -> str:
    t = _menu_i18n(uid)
    until = get_premium_until(uid)
    if not until:
        return f"*{t['title']}*\n{t['premium_none']}"
    try:
        dt = datetime.fromisoformat(until)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        until_str = dt.astimezone(timezone.utc).isoformat()
    except Exception:
        until_str = until
    return f"*{t['title']}*\n{t['premium_until'].format(until=until_str)}"

def _engine_label(uid: str) -> str:
    eng = _vp(uid).get("engine", "gTTS")
    return "ElevenLabs" if str(eng).lower() == "eleven" else "gTTS"

def _sleep_summary(uid: str) -> tuple[str, int, int]:
    try:
        p = _sleep_p(uid)  # твоя новая prefs-функция
    except Exception:
        p = {"kind": "rain", "duration_min": 15, "gain_db": -20}
    kind = p.get("kind", "rain")
    meta = BGM_PRESETS.get(kind, {})
    label = meta.get("label", kind)
    return label, int(p.get("duration_min", 15)), int(p.get("gain_db", -20))

def _premium_summary(uid: str, t: dict) -> tuple[str, str]:
    has = is_premium(uid)
    until_iso = get_premium_until(uid)
    if not has:
        return (t["premium_no"], "")
    dt_str = ""
    try:
        if until_iso:
            dt = datetime.fromisoformat(until_iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_str = t["until_fmt"].format(dt=dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    except Exception:
        dt_str = ""
    return (t["premium_yes"], dt_str)

def _menu_home_text(uid: str) -> str:
    t = _menu_i18n(uid)
    until = get_premium_until(uid)
    if until:
        return f"*{t['title']}*\n\n" + t["premium_until"].format(until=until)
    else:
        return f"*{t['title']}*\n\n" + t["premium_none"]

def _menu_kb_home(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["features"],       callback_data="m:nav:features")],
        [InlineKeyboardButton(t["plus_features"],  callback_data="m:nav:plus")],
        [InlineKeyboardButton(t["premium"],        callback_data="m:nav:premium")],
        [InlineKeyboardButton(t["settings"],       callback_data="m:nav:settings")],
        [InlineKeyboardButton(t["close"],          callback_data="m:nav:close")],
    ]
    return InlineKeyboardMarkup(rows)


def _menu_kb_plus(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["plus_voice"],      callback_data="m:plus:voice")],
        [InlineKeyboardButton(t["plus_sleep"],      callback_data="m:plus:sleep")],
        [InlineKeyboardButton(t["plus_story"],      callback_data="m:plus:story")],
        [InlineKeyboardButton(t["plus_pmode"],      callback_data="m:plus:pmode")],
        [InlineKeyboardButton(t["plus_pstats"],     callback_data="m:plus:pstats")],
        [InlineKeyboardButton(t["plus_preport"],    callback_data="m:plus:preport")],
        [InlineKeyboardButton(t["plus_pchallenge"], callback_data="m:plus:pchallenge")],
        [InlineKeyboardButton(t["back"],            callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)

def _menu_kb_premium(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["premium_days"], callback_data="m:premium:days")],
        [InlineKeyboardButton(t["invite"],       callback_data="m:premium:invite")],
        # Заменишь URL на свою страницу оплаты
        [InlineKeyboardButton(t["premium_buy"],  url="https://example.com/pay")],
        [InlineKeyboardButton(t["back"],         callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)

def _menu_kb_settings(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["set_lang"],     callback_data="m:set:lang")],
        [InlineKeyboardButton(t["set_tz"],       callback_data="m:set:tz")],
        [InlineKeyboardButton(t["set_feedback"], callback_data="m:set:feedback")],
        [InlineKeyboardButton(t["back"],         callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)

def _menu_kb_features(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["feat_tracker"],   callback_data="m:feat:tracker")],
        [InlineKeyboardButton(t["features_mode"],  callback_data="m:feat:mode")],
        [InlineKeyboardButton(t["feat_reminders"], callback_data="m:feat:reminders")],
        [InlineKeyboardButton(t["feat_points"],    callback_data="m:feat:points")],
        [InlineKeyboardButton(t["feat_mood"],      callback_data="m:feat:mood")],
        [InlineKeyboardButton(t["back"],           callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)

def _features_text(uid: str) -> str:
    t = _menu_i18n(uid)
    return f"*{t['feat_title']}*\n{t['feat_body']}"

def _plus_features_text(uid: str) -> str:
    t = _menu_i18n(uid)
    return f"*{t['plus_title']}*\n{t['plus_body']}"

def _premium_text(uid: str) -> str:
    t = _menu_i18n(uid)
    # шапку «премиум до…» возьмём из общего заголовка
    return _menu_header_text(uid).replace(t["title"], t["prem_title"])


def _profile_kb(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["lang"], callback_data="m:nav:lang"),
         InlineKeyboardButton(t["tz"],   callback_data="m:nav:tz")],
        [InlineKeyboardButton(t["back"], callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)
    
def _sleep_p(uid: str) -> dict:
    p = _sleep_prefs.get(uid)
    if not p:
        p = {"kind": "rain", "duration_min": 20, "gain_db": -20}
        _sleep_prefs[uid] = p
    return p

def _sleep_i18n(uid: str) -> dict:
    lang = user_languages.get(uid, "ru")
    return SLEEP_UI_TEXTS.get(lang, SLEEP_UI_TEXTS["ru"])

    
def _v_i18n(uid: str) -> dict:
    """Короткие тексты для /voice_mode (on/off/help)."""
    lang = user_languages.get(uid, "ru")
    return VOICE_MODE_TEXTS.get(lang, VOICE_MODE_TEXTS["ru"])

def _vm_i18n(uid: str) -> dict:
    """Полное меню для /voice_settings."""
    lang = user_languages.get(uid, "ru")
    return VOICE_UI_TEXTS.get(lang, VOICE_UI_TEXTS["ru"])

def is_premium(user_id) -> bool:
    # админы — всегда премиум
    if str(user_id) in ADMIN_USER_IDS:
        return True
    return is_premium_db(user_id)
    
# Обратная совместимость: где-то могли звать _v_ui_i18n
def _v_ui_i18n(uid: str) -> dict:
    return _vm_i18n(uid)
    
def _gh_i18n(uid: str) -> dict:
    return GH_TEXTS.get(user_languages.get(uid, "ru"), GH_TEXTS["ru"])

def _p_i18n(uid: str) -> dict:
    return P_TEXTS.get(user_languages.get(uid, "ru"), P_TEXTS["ru"])

def _tts_lang(lang: str) -> str:
    return LANG_TO_TTS.get(lang, "ru")

def _s_i18n(uid: str) -> dict:
    return STORY_TEXTS.get(user_languages.get(uid, "ru"), STORY_TEXTS["ru"])

def _has_eleven() -> bool:
    return bool(ELEVEN_API_KEY)

# Иконки-флаги по коду (опционально)
FLAG_BY_CODE = {
    "ru":"🇷🇺","uk":"🇺🇦","en":"🇬🇧","md":"🇲🇩","be":"🇧🇾",
    "kk":"🇰🇿","kg":"🇰🇬","hy":"🇦🇲","ka":"🇬🇪","ce":"🏴"
}

# Порядок отображения
LANG_ORDER = ["ru","uk","en","md","be","kk","kg","hy","ka","ce"]

def _settings_i18n(uid: str) -> dict:
    lang = user_languages.get(uid, "ru")
    return SETTINGS_TEXTS.get(lang, SETTINGS_TEXTS["ru"])

def _lang_native_name(code: str) -> str:
    # Берём «родное» имя языка из твоего словаря (там уже хорошо заполнено)
    return SETTINGS_TEXTS["ru"]["lang_name"].get(code, code)

def _lang_menu_text(uid: str) -> str:
    t = _settings_i18n(uid)
    return f"*{t.get('choose_lang','🌐 Выбери язык интерфейса:')}*"

def _lang_kb(uid: str) -> InlineKeyboardMarkup:
    names = SETTINGS_TEXTS["ru"]["lang_name"]  # источник кодов
    # берём только те коды, что есть в словаре, и в заданном порядке
    codes = [c for c in LANG_ORDER if c in names]

    rows = []
    for i in range(0, len(codes), 2):
        chunk = codes[i:i+2]
        btns = []
        for code in chunk:
            label = f"{FLAG_BY_CODE.get(code,'')} {_lang_native_name(code)}".strip()
            btns.append(InlineKeyboardButton(label, callback_data=f"lang:{code}"))
        rows.append(btns)

    rows.append([InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data="m:nav:settings")])
    return InlineKeyboardMarkup(rows)

async def show_language_menu(msg):
    uid = str(msg.chat.id)
    await msg.edit_text(_lang_menu_text(uid), reply_markup=_lang_kb(uid), parse_mode="Markdown")

async def settings_router(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("m:set:"):
        return
    await q.answer()
    context.user_data[UI_MSG_KEY] = q.message.message_id

    uid = str(q.from_user.id)
    msg = q.message
    act = q.data.split(":", 2)[2]  # lang | tz | feedback

    if act == "lang":
        return await show_language_menu(msg)

    if act == "tz":
        # сюда — ТОЛЬКО таймзона, отдельный экран
        return await show_timezone_menu(msg)

    if act == "feedback":
        t = _menu_i18n(uid)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t["back"], callback_data="m:nav:settings")]])
        return await msg.edit_text(t.get("feedback_ask","💌 Напишите отзыв"), reply_markup=kb, parse_mode="Markdown")


async def language_cb(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("lang:"):
        return
    await q.answer()
    context.user_data[UI_MSG_KEY] = q.message.message_id

    uid = str(q.from_user.id)
    code = q.data.split(":", 1)[1]
    user_languages[uid] = code  # сохраняем язык

    # тост с подтверждением
    try:
        await q.answer(f"✅ {_lang_native_name(code)}", show_alert=False)
    except Exception:
        pass

    # возвращаемся в экран «Настройки» (или сразу домой — как тебе нужно)
    t = _menu_i18n(uid)
    return await q.message.edit_text(t.get("set_title", t["settings"]),
                                     reply_markup=_menu_kb_settings(uid),
                                     parse_mode="Markdown")


def upsell_fmt(uid_lang: str, key: str, **kw) -> str:
    t = UPSELL_TEXTS.get(uid_lang, UPSELL_TEXTS["ru"])
    s = t.get(key, "")
    return s.format(plus=PLAN_LABEL["plus"], pro=PLAN_LABEL["pro"], **kw)

def _plan_lang(uid: str):
    return user_languages.get(uid, "ru")

def _plan_label(uid: str, plan: str) -> str:
    return PLAN_LABELS.get(_plan_lang(uid), PLAN_LABELS["ru"]).get(plan, plan)

def upsell_for(uid: str, feature_key: str, extra: dict | None = None) -> tuple[str, str]:
    """Возвращает (title, body) локализованно для конкретной фичи."""
    lang = _plan_lang(uid)
    t = UPSELL_TEXTS.get(lang, UPSELL_TEXTS["ru"])
    plus = _plan_label(uid, PLAN_PLUS)
    pro  = _plan_label(uid, PLAN_PRO)
    e = {"plus": plus, "pro": pro}
    if extra:
        e.update(extra)
    body = t.get(feature_key, t["feature_quota_msg"]).format(**e)
    return (t["title"], body + f"\n\n{t['cta']}")


def current_plan(uid: str) -> str:
    try:
        db = sqlite3.connect(DB_PATH)
        row = db.execute("SELECT plan, expires_utc FROM subscriptions WHERE user_id=?",
                         (uid,)).fetchone()
        db.close()
        if not row:
            return PLAN_FREE
        plan, exp = row
        if plan in (PLAN_PLUS, PLAN_PRO) and exp:
            try:
                if datetime.fromisoformat(exp) < datetime.now(timezone.utc):
                    return PLAN_FREE
            except Exception:
                pass
        return plan if plan in ALL_PLANS else PLAN_FREE
    except Exception:
        return PLAN_FREE

def set_plan(uid: str, plan: str, days: int | None = None):
    plan = plan if plan in ALL_PLANS else PLAN_FREE
    exp = None
    if plan in (PLAN_PLUS, PLAN_PRO) and days:
        exp = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        INSERT INTO subscriptions(user_id, plan, expires_utc, updated_at)
        VALUES(?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET plan=excluded.plan, expires_utc=excluded.expires_utc, updated_at=excluded.updated_at
    """, (uid, plan, exp, now))
    db.commit()
    db.close()

def has_feature(uid: str, feature: str) -> bool:
    return FEATURE_MATRIX.get(current_plan(uid), {}).get(feature, False)

def quota(uid: str, key: str) -> int:
    return QUOTAS.get(current_plan(uid), {}).get(key, 0)
    

def _resolve_asset_path(rel_path: str | None) -> str | None:
    """Преобразует относительный путь из BGM_PRESETS в абсолютный (на всякий)."""
    if not rel_path:
        return None
    # пробуем относительно текущего файла
    base = os.path.dirname(os.path.abspath(__file__))
    p1 = os.path.normpath(os.path.join(base, rel_path))
    if os.path.exists(p1):
        return p1
    # и относительно CWD (если запускается из корня проекта)
    p2 = os.path.normpath(os.path.join(os.getcwd(), rel_path))
    if os.path.exists(p2):
        return p2
    return rel_path  # вернём как есть — дальше всё равно проверим exists
    
def _render_sleep_ogg(kind: str, minutes: int, gain_db: int = -20) -> str:
    if kind == "off":
        raise ValueError("Sleep sound 'off' — нечего играть")

    meta = BGM_PRESETS.get(kind, {})
    src_rel = meta.get("path")
    src = _resolve_asset_path(src_rel) if ' _resolve_asset_path' in globals() else (src_rel or "")
    if not src or not os.path.exists(src):
        raise FileNotFoundError(f"Sleep BGM not found: {src_rel}")

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found")

    minutes = max(1, min(int(minutes or 1), 240))
    total = minutes * 60

    cache_dir = os.path.join(tempfile.gettempdir(), "sleep_cache")
    os.makedirs(cache_dir, exist_ok=True)
    gain_tag = str(gain_db).replace("-", "m").replace("+", "p")
    key = f"{kind}_{minutes}_{gain_tag}"
    out_path = os.path.join(cache_dir, f"{key}.ogg")

    if os.path.exists(out_path):
        return out_path

    fade_in = 3
    fade_out = 5
    ff_cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-t", str(total + fade_out + 1), "-i", src,
        "-filter_complex",
        (
            f"[0:a]volume={gain_db}dB,"
            f"afade=t=in:st=0:d={fade_in},"
            f"atrim=duration={total},"
            f"afade=t=out:st={max(0, total - fade_out)}:d={fade_out},"
            f"aresample=48000[a]"
        ),
        "-map", "[a]",
        "-ac", "1",
        "-c:a", "libopus", "-b:a", "48k", "-ar", "48000",
        out_path
    ]
    subprocess.run(ff_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path

def _sleep_menu_text(uid: str) -> str:
    p = _sleep_p(uid)
    t = _sleep_i18n(uid)
    meta = BGM_PRESETS.get(p["kind"], {"label": p["kind"]})
    return (
        f"*{t['title']}*\n\n"
        f"{t['sound'].format(sound=meta['label'])}\n"
        f"{t['duration'].format(min=p['duration_min'])}\n"
        f"{t['gain'].format(db=p['gain_db'])}"
    )

def _kb_equal(a, b) -> bool:
    try:
        return (a or InlineKeyboardMarkup([])).to_dict() == (b or InlineKeyboardMarkup([])).to_dict()
    except Exception:
        return False

async def _sleep_refresh(q: CallbackQuery, uid: str, tab: str):
    try:
        await q.edit_message_text(
            _sleep_menu_text(uid),
            parse_mode="Markdown",
            reply_markup=_sleep_kb(uid, tab),
        )
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            try:
                await q.edit_message_reply_markup(reply_markup=_sleep_kb(uid, tab))
            except Exception:
                pass

def _sleep_kb(uid: str, tab: str = "kind", back_to: str = "plus") -> InlineKeyboardMarkup:
    p = _sleep_p(uid)
    t = _sleep_i18n(uid)

    rows: list[list[InlineKeyboardButton]] = []
    if tab == "kind":
        for key, meta in BGM_PRESETS.items():
            if key == "off":
                continue
            mark = "✅ " if p["kind"] == key else ""
            rows.append([InlineKeyboardButton(f"{mark}{meta['label']}", callback_data=f"sleep:kind:{key}")])

    elif tab == "dur":
        for row in ((5,10,15),(20,30,45),(60,90,120)):
            rows.append([InlineKeyboardButton(f"{m}m", callback_data=f"sleep:dur:{m}") for m in row])

    elif tab == "gain":
        for row in ((-30,-25,-20),(-15,-10,-5),(0,5,10)):
            rows.append([InlineKeyboardButton(f"{g} dB", callback_data=f"sleep:gain:{g}") for g in row])

    # нижняя панель
    rows.append([
        InlineKeyboardButton("▶️", callback_data="sleep:act:start"),
        InlineKeyboardButton("⏹", callback_data="sleep:act:stop"),
    ])
    rows.append([
        InlineKeyboardButton(f"🎵 {t['pick_sound']}",    callback_data="sleep:tab:kind"),
        InlineKeyboardButton(f"⏱ {t['pick_duration']}", callback_data="sleep:tab:dur"),
        InlineKeyboardButton(f"🔉 {t['pick_gain']}",     callback_data="sleep:tab:gain"),
    ])

    # ⬅️ Назад (в экран Премиум-функций или в корень)
    back_cb = "m:nav:plus" if back_to == "plus" else "m:nav:home"
    rows.append([InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data=back_cb)])

    return InlineKeyboardMarkup(rows)
    
# /sleep — открыть меню
async def sleep_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ui_show_from_command(
        update, context,
        _sleep_menu_text(uid),
        reply_markup=_sleep_kb(uid, "kind"),
        parse_mode="Markdown",
    )


async def show_sleep_menu(msg):
    uid = str(msg.chat.id)
    await msg.edit_text(
        _sleep_menu_text(uid),
        parse_mode="Markdown",
        reply_markup=_sleep_kb(uid, "kind"),
    )

# Колбэк "sl:*"

async def sleep_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data.startswith("sleep:"):
        return
    await q.answer()  # чтобы не висел "loading…"
    context.user_data[UI_MSG_KEY] = q.message.message_id  # работаем в одном сообщении

    uid = str(q.from_user.id)
    p = _sleep_p(uid)

    parts = q.data.split(":")
    kind = parts[1]
    current_tab = "kind"

    try:
        if kind == "tab":
            current_tab = parts[2]

        elif kind == "kind":
            new_kind = parts[2]
            if new_kind in BGM_PRESETS:
                p["kind"] = new_kind
            current_tab = "kind"

        elif kind == "dur":
            p["duration_min"] = max(1, min(int(parts[2]), 240))
            current_tab = "dur"

        elif kind == "gain":
            p["gain_db"] = int(parts[2])
            current_tab = "gain"

        elif kind == "act":
            action = parts[2]
            t = _sleep_i18n(uid)
            if action == "start":
                try:
                    ogg_path = _render_sleep_ogg(p["kind"], p["duration_min"], p["gain_db"])
                except FileNotFoundError:
                    return await q.answer(t["err_missing"], show_alert=True)
                except RuntimeError:
                    return await q.answer(t["err_ffmpeg"], show_alert=True)

                # шлём ВОЙС отдельным сообщением (это нормально)
                with open(ogg_path, "rb") as f:
                    await context.bot.send_voice(chat_id=int(uid), voice=f)

                meta = BGM_PRESETS.get(p["kind"], {"label": p["kind"]})
                await q.answer(t["started"].format(sound=meta["label"], min=p["duration_min"]), show_alert=True)

            elif action == "stop":
                await q.answer(t["stopped"], show_alert=True)

        # обновим экран
        await _sleep_refresh(q, uid, current_tab)

    except Exception as e:
        logging.exception("sleep_cb failed: %s", e)
        try:
            await q.answer("Oops, try again", show_alert=True)
        except Exception:
            pass
            
def _current_voice_name(uid: str) -> str:
    lang = user_languages.get(uid, "ru")
    p = _vp(uid)
    presets = VOICE_PRESETS.get(lang, VOICE_PRESETS["ru"])
    for name, eng, vid in presets:
        if p.get("engine","").lower() == eng.lower() and p.get("voice_id","") == vid:
            return name
    # если кастомный/пустой
    if p.get("engine","").lower() == "eleven" and p.get("voice_id"):
        return "Eleven (custom)"
    if p.get("engine","").lower() == "gTTS":
        return "gTTS"
    return "—"

ENGINE_ELEVEN = "eleven"
ENGINE_GTTS   = "gtts"

# профайл пользователя
def _vp(uid: str):
    if uid not in user_voice_prefs:
        user_voice_prefs[uid] = {
            "engine": ENGINE_ELEVEN if _has_eleven() else ENGINE_GTTS,
            "voice_id": DEFAULT_ELEVEN_FEMALE if _has_eleven() else "",
            "voice_name": "Female (Eleven)" if _has_eleven() else "gTTS",
            "speed": 1.0,
            "voice_only": False,
            "auto_story_voice": True,
            "accent": "com",
            "bgm_kind": "off",
            "bgm_gain_db": -20,
            "auto_bgm_for_stories": True,
        }
    return user_voice_prefs[uid]
    

def _build_story_patterns(words_dict: dict[str, list[str]]) -> dict[str, re.Pattern]:
    patterns: dict[str, re.Pattern] = {}
    for lang, items in words_dict.items():
        alts = []
        for kw in items:
            kw = kw.strip()
            if not kw:
                continue
            # экранируем + позволяем любые пробелы внутри фразы
            escaped = re.escape(kw).replace(r"\ ", r"\s+")
            # границы, чтобы не ловить куски внутри слов
            alts.append(rf"(?<!\w){escaped}(?!\w)")
        patterns[lang] = re.compile("|".join(alts), re.I) if alts else re.compile(r"$a")
    return patterns

STORY_INTENT = _build_story_patterns(STORY_INTENT)

def _looks_like_story_intent(text: str, lang: str, uid: str) -> bool:
    if not text:
        return False

    now = datetime.now(timezone.utc)

    # «Попросил не предлагать» недавно
    until = _story_optout_until.get(uid)
    if until and now < until:
        return False

    # Кулдаун, чтобы не спамить
    last = _story_last_suggest.get(uid)
    if last and (now - last) < timedelta(hours=STORY_COOLDOWN_HOURS):
        return False

    # Слишком длинные сообщения считаем обычным чатом
    if len(text.split()) > 20:
        return False

    patt = STORY_INTENT.get(lang, STORY_INTENT["ru"])
    return bool(patt.search(text))
    
async def _voice_refresh(q: CallbackQuery, uid: str, tab: str):
    new_text = _voice_menu_text(uid) or "🎙"
    new_kb = _voice_kb(uid, tab)

    cur = q.message
    same_text = (cur.text or "") == (new_text or "")
    same_kb = (cur.reply_markup and cur.reply_markup.to_dict()) == (new_kb and new_kb.to_dict())

    if same_text and same_kb:
        # нечего менять — просто выходим
        return

    try:
        await q.edit_message_text(new_text, parse_mode="Markdown", reply_markup=new_kb)
    except BadRequest as e:
        # на всякий случай перехватим edge-кейс
        if "message is not modified" in str(e).lower():
            return
        # если вдруг был другой баг — пробуем хотя бы разнести на новое сообщение
        try:
            await q.message.reply_text(new_text, parse_mode="Markdown", reply_markup=new_kb)
        except Exception:
            raise
            
def _voice_menu_text(uid: str) -> str:
    t = _vm_i18n(uid)     # оставляю твой i18n
    p = _vp(uid)
    eng_label = t["engine_eleven"] if str(p.get("engine")).lower() == "eleven" else t["engine_gtts"]
    vname = p.get("voice_name") or ( "Female (Eleven)" if str(p.get("engine")).lower()=="eleven" else "gTTS" )
    speed = p.get("speed", 1.0)
    bg_cfg = BGM_PRESETS.get(p.get("bgm_kind","off"), {"label":"Off"})
    bg_label = bg_cfg["label"]
    bg_db = p.get("bgm_gain_db", -20)

    return (
        f"*{t['title']}*\n\n"
        f"{t['engine'].format(engine=eng_label)}\n"
        f"{t['voice'].format(voice=vname)}\n"
        f"{t['speed'].format(speed=speed)}\n"
        f"{t['bgm'].format(bg=bg_label, db=bg_db)}"
    )
    
def _voice_kb(uid: str, tab: str = "engine", back_to: str = "plus") -> InlineKeyboardMarkup:
    t = _v_ui_i18n(uid)          # оставляю твой i18n
    p = _vp(uid)
    rows: list[list[InlineKeyboardButton]] = []
    can_eleven = has_feature(uid, "eleven_tts")

    # ⬇️ новый первый ряд — тумблер и «в меню»
    state = user_voice_mode.get(uid, False)
    on_lbl  = t.get("mode_on_btn",  "🔊 Включить")
    off_lbl = t.get("mode_off_btn", "🔇 Выключить")
    back_lbl = _menu_i18n(uid)["back"]
    rows.append([
        InlineKeyboardButton(("✅ " if state else "") + on_lbl,  callback_data="v:mode:on"),
        InlineKeyboardButton(("✅ " if not state else "") + off_lbl, callback_data="v:mode:off"),
        InlineKeyboardButton(back_lbl, callback_data="m:nav:plus"),
    ])    
    # ↓↓↓ унифицируем название эффективного движка: 'eleven' | 'gtts'
    try:
        eff_engine = _effective_tts_engine(uid).lower()
    except Exception:
        eff_engine = (
            "eleven"
            if (str(p.get("engine", "gtts")).lower() == "eleven"
                and _has_eleven() and bool(p.get("voice_id")) and can_eleven)
            else "gtts"
        )

    def _check(mark: bool) -> str: return "✅ " if mark else ""

    if tab == "engine":
        row = []
        if can_eleven:
            row.append(InlineKeyboardButton(
                _check(p.get("engine","").lower() == "eleven") + t["engine_eleven"],
                callback_data="v:engine:eleven"
            ))
        row.append(InlineKeyboardButton(
            _check(eff_engine == "gtts") + t["engine_gtts"],
            callback_data="v:engine:gTTS"             # callback оставляю как у тебя
        ))
        rows.append(row)

    elif tab == "voice":
        presets = VOICE_PRESETS.get(user_languages.get(uid, "ru"), VOICE_PRESETS["ru"])
        cur_engine = (p.get("engine") or "").lower()
        cur_voice  = p.get("voice_id", "")
        for i, (name, eng_k, vid) in enumerate(presets):
            if eng_k.lower() == "eleven" and (not can_eleven or not _has_eleven()):
                continue
            selected = (eng_k.lower() == cur_engine) and ((vid == cur_voice) or (eng_k.lower() == "gtts"))
            rows.append([InlineKeyboardButton(_check(selected) + name, callback_data=f"v:voice:{i}")])

    elif tab == "speed":
        speeds = [0.8, 0.9, 1.0, 1.1, 1.2]
        row = []
        for s in speeds:
            sel = abs(p.get("speed", 1.0) - s) < 1e-6
            label = f"{'➖ ' if s < 1.0 else ('➕ ' if s > 1.0 else '')}{s:.1f}x"
            row.append(InlineKeyboardButton(_check(sel) + label, callback_data=f"v:speed:{s:.1f}"))
        rows.append(row)

    elif tab == "beh":
        rows += [
            [InlineKeyboardButton((_check(p.get("voice_only", False)) + t.get("label_voice_only","Voice only")),
                                  callback_data="v:beh:voiceonly")],
            [InlineKeyboardButton((_check(p.get("auto_story_voice", True)) + t.get("label_auto_story","Auto story voice")),
                                  callback_data="v:beh:autostory")],
        ]

    elif tab == "bg":
        kinds_order = ["off", "rain", "fire", "ocean", "lofi"]
        present = [k for k in kinds_order if k in BGM_PRESETS] or list(BGM_PRESETS.keys())
        row = []
        for k in present:
            meta = BGM_PRESETS.get(k, {})
            label = meta.get("label", k)
            row.append(InlineKeyboardButton(_check(p.get("bgm_kind") == k) + label, callback_data=f"v:bg:set:{k}"))
        rows.append(row)

        gains = globals().get("BGM_GAIN_CHOICES", [-25, -20, -15, -10, -5, 0, 5])
        cur_gain = int(p.get("bgm_gain_db", -20))
        for i in range(0, len(gains), 4):
            chunk = gains[i:i+4]
            rows.append([
                InlineKeyboardButton(("✅ " if g == cur_gain else "") + f"{g:+} dB",
                                     callback_data=f"v:bg:gain:{g}") for g in chunk
            ])

    # Навигация по вкладкам
    rows.append([
        InlineKeyboardButton(t["btn_engine"], callback_data="v:tab:engine"),
        InlineKeyboardButton(t["btn_voice"],  callback_data="v:tab:voice"),
        InlineKeyboardButton(t["btn_speed"],  callback_data="v:tab:speed"),
        InlineKeyboardButton(t["btn_beh"],    callback_data="v:tab:beh"),
        InlineKeyboardButton(t["btn_bg"],     callback_data="v:tab:bg"),
    ])

    # ⬅️ Назад
    back_cb = "m:nav:plus" if back_to == "plus" else "m:nav:home"
    rows.append([InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data=back_cb)])

    return InlineKeyboardMarkup(rows)

# === /voice_settings ===
async def voice_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ui_show_from_command(
        update, context,
        _voice_menu_text(uid),
        reply_markup=_voice_kb(uid, "engine", back_to="plus"),
        parse_mode="Markdown"
    )

# === Callback ===
async def voice_settings_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data.startswith("v:"):
        return
    await q.answer()
    context.user_data[UI_MSG_KEY] = q.message.message_id   # <<< важно для единого сообщения

    uid = str(q.from_user.id)
    p = _vp(uid)
    parts = q.data.split(":")
    kind = parts[1]
    current_tab = "engine"

    if kind == "tab":
        return await _voice_refresh(q, uid, parts[2])

    # ←← ДОБАВЛЕННЫЙ БЛОК ДЛЯ /voice_mode (кнопки v:mode:on|off)
    elif kind == "mode":
        desired = (parts[2] or "").lower()   # "on" | "off"
        if not is_premium(uid):
            try:
                title, _ = upsell_for(uid, "feature_voice_mode")
                await q.answer(title, show_alert=True)
            except Exception:
                pass
            return await _voice_refresh(q, uid, "engine")

        user_voice_mode[uid] = (desired == "on")
        t_mode = _vmode_i18n(uid)
        toast = t_mode.get("on") if user_voice_mode[uid] else t_mode.get("off")
        try:
            await q.answer(f"✅ {toast}" if toast else "✅", show_alert=False)
        except Exception:
            pass
        return await _voice_refresh(q, uid, "engine")

    elif kind == "engine":
        new_engine = parts[2]
        if new_engine.lower() == "eleven":
            if not has_feature(uid, "eleven_tts"):
                try:
                    title, _ = upsell_for(uid, "feature_eleven")
                    await q.answer(title, show_alert=True)
                except Exception:
                    pass
                return await _voice_refresh(q, uid, "engine")
            if not _has_eleven():
                await q.answer(_v_ui_i18n(uid).get("no_eleven_key","ElevenLabs key not set"), show_alert=True)
                return await _voice_refresh(q, uid, "engine")
        p["engine"] = new_engine
        current_tab = "engine"

    elif kind == "voice":
        idx = int(parts[2])
        presets = VOICE_PRESETS.get(user_languages.get(uid, "ru"), VOICE_PRESETS["ru"])
        if 0 <= idx < len(presets):
            name, eng_k, vid = presets[idx]
            if eng_k.lower() == "eleven":
                if not has_feature(uid, "eleven_tts") or not _has_eleven():
                    await q.answer(_v_ui_i18n(uid).get("no_eleven_key","ElevenLabs not available"), show_alert=True)
                    return await _voice_refresh(q, uid, "engine")
            p["engine"] = eng_k
            p["voice_id"] = vid or p.get("voice_id","")
            p["voice_name"] = name
        current_tab = "engine"

    elif kind == "speed":
        try:
            p["speed"] = float(parts[2])
        except Exception:
            pass
        current_tab = "speed"

    elif kind == "beh":
        sub = parts[2]
        if sub == "voiceonly":
            p["voice_only"] = not p.get("voice_only", False)
        elif sub == "autostory":
            p["auto_story_voice"] = not p.get("auto_story_voice", True)
        current_tab = "beh"

    elif kind == "bg":
        sub = parts[2]
        if sub == "set":
            p["bgm_kind"] = parts[3]
        elif sub == "gain":
            try:
                p["bgm_gain_db"] = int(parts[3])
            except Exception:
                pass
        current_tab = "bg"

    await _voice_refresh(q, uid, current_tab)

def _expressive(text: str, lang: str) -> str:
    s = text.replace("...", "…")
    # [sigh] / (вздох)
    if lang in ("ru","uk","md","be","kk","kg","hy","ka","ce"):
        s = re.sub(r"\[(sigh|вздох)\]", "эх… ", s, flags=re.I)
        s = re.sub(r"\((вздох)\)", "эх… ", s, flags=re.I)
    else:
        s = re.sub(r"\[(sigh)\]", "ugh… ", s, flags=re.I)
    # Паузы: [pause300], [pause1000]
    def _pause(m):
        ms = int(m.group(1))
        dots = "…" * (1 if ms<=600 else 2 if ms<=1200 else 3)
        return f"{dots} "
    s = re.sub(r"\[pause(\d{2,4})\]", _pause, s, flags=re.I)
    # Whisper
    if lang in ("ru","uk","md","be","kk","kg","hy","ka","ce"):
        s = re.sub(r"\[whisper:(.+?)\]", r"(шёпотом) \1", s, flags=re.I)
    else:
        s = re.sub(r"\[whisper:(.+?)\]", r"(whispering) \1", s, flags=re.I)
    return s

def _to_ogg_from_mp3(mp3_path: str, speed: float=1.0) -> str:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    atempo = max(0.5, min(2.0, speed))
    out_path = f"/tmp/{uuid.uuid4().hex}.ogg"
    cmd = [
        "ffmpeg","-y","-i", mp3_path,
        "-filter:a", f"atempo={atempo}",
        "-c:a","libopus","-b:a","48k","-ar","48000","-ac","1",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try: os.remove(mp3_path)
    except: pass
    return out_path


def _mix_with_bgm(voice_ogg_path: str, bg_path: str | None, gain_db: int = -20) -> str:
    """
    Миксуем голос (OGG/Opus) + фон (MP3/WAV) с нормализацией.
    Возвращаем путь к новому OGG. При сбое — исходный путь.
    """
    try:
        if not bg_path or not os.path.exists(bg_path):
            logging.warning(f"BGM: file not found: {bg_path}")
            return voice_ogg_path

        if shutil.which("ffmpeg") is None:
            logging.warning("BGM: ffmpeg not found, skip mix")
            return voice_ogg_path

        out_path = os.path.join(tempfile.gettempdir(), f"voice_mix_{uuid.uuid4().hex}.ogg")

        # Голос первым входом → длительность берём у него (duration=first).
        # Фон лупим бесконечно и делаем тише в dB. Чуть выравниваем уровни dynaudnorm.
        cmd = [
            "ffmpeg", "-y",
            "-i", voice_ogg_path,
            "-stream_loop", "-1", "-i", bg_path,
            "-filter_complex",
            f"[1:a]volume={gain_db}dB[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0, dynaudnorm",
            "-c:a", "libopus", "-b:a", "48k", "-ar", "48000",
            out_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logging.error(f"FFmpeg mix failed: {res.stderr[:500]}")
            return voice_ogg_path

        return out_path

    except Exception as e:
        logging.exception(f"BGM mix failed: {e}")
        return voice_ogg_path
        
def _tts_elevenlabs_to_ogg(text: str, voice_id: str, speed: float=1.0) -> str:
    api_key = os.getenv("ELEVEN_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVEN_API_KEY not set")
    client = ElevenLabs(api_key=api_key)

    voice_settings = {
        "stability": 0.35,
        "similarity_boost": 0.7,
        "style": 0.6,
        "use_speaker_boost": True,
    }

    mp3_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM",  # любой дефолт
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        text=text,
        voice_settings=voice_settings,
    )
    with open(mp3_path, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)
    return _to_ogg_from_mp3(mp3_path, speed)

def _tts_gtts_to_ogg(text: str, lang: str, tld: str="com", speed: float=1.0) -> str:
    from gtts import gTTS
    mp3_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    gTTS(text=text, lang=lang if lang in ("ru","uk","en") else "ru", tld=tld).save(mp3_path)
    return _to_ogg_from_mp3(mp3_path, speed)

def synthesize_to_ogg(text: str, lang: str, uid: str) -> str:
    """
    Синтезирует речь в OGG (opus).
    - Если выбран Eleven и он доступен (ключ, voice_id, фича), используем ElevenLabs.
    - Иначе — gTTS.
    В любом фейле падаем в gTTS.
    """
    p = _vp(uid)
    text = _expressive(text, lang)

    try:
        use_eleven = (
            str(p.get("engine", "gTTS")).lower() == "eleven"
            and _has_eleven()                      # есть ELEVEN_API_KEY
            and bool(p.get("voice_id"))            # выбран голос
            and has_feature(uid, "eleven_tts")     # у тарифа есть право на Eleven
        )

        if use_eleven:
            # speed из профиля: 0.8..1.2 ок; твоя реализация _tts_elevenlabs_to_ogg уже есть
            return _tts_elevenlabs_to_ogg(
                text,
                p["voice_id"],
                p.get("speed", 1.0)
            )

        # gTTS (акцент по tld, скорость если поддержана в твоей _tts_gtts_to_ogg)
        return _tts_gtts_to_ogg(
            text,
            lang,
            tld=p.get("accent", "com"),
            speed=p.get("speed", 1.0),
        )

    except Exception as e:
        logging.exception(f"TTS primary failed ({p.get('engine')}), fallback to gTTS: {e}")
        # надёжный фолбэк
        return _tts_gtts_to_ogg(
            text,
            lang,
            tld=p.get("accent", "com"),
            speed=p.get("speed", 1.0),
        )


async def generate_story_text(uid: str, lang: str, topic: str, name: str|None, length: str="short") -> str:
    # длина → ориентир по абзацам
    target_paras = {"short": 5, "medium": 8, "long": 12}.get(length, 5)
    system = {
        "ru": "Ты пишешь тёплые короткие сказки для детей. Простой язык, добрый тон, 3–6 предложений в абзаце.",
        "uk": "Ти пишеш теплі короткі казки для дітей. Проста мова, добрий тон.",
        "en": "You write warm, short children’s bedtime stories. Simple language, kind tone."
    }.get(lang, "Ты пишешь тёплые короткие сказки для детей.")
    user = f"Тема: {topic or 'любая'}.\nИмя героя: {name or 'нет'}.\nАбзацев: {target_paras}.\nЗаверши на позитивной ноте."
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}]
        )
        text = resp.choices[0].message.content.strip()
        return text
    except Exception as e:
        logging.warning(f"Story LLM failed: {e}")
        # запасной простой шаблон
        base = f"Сказка про {'героя ' + name if name else 'маленького героя'} на тему «{topic or 'добро'}». "
        return (base + "Однажды герой отправился навстречу чуду. "
                "Дорога была добра и светла, и каждый шаг учил его смелости и дружбе. "
                "В конце пути герой понял: главное чудо — в его сердце. И с этой теплотой он вернулся домой.")

def _parse_story_args(raw: str) -> dict:
    d = {"topic": "", "name": None, "length": "short", "voice": False}
    d["topic"] = raw
    # name=
    m = re.search(r"(имя|name)\s*=\s*([^\|\n]+)", raw, flags=re.I)
    if m: d["name"] = m.group(2).strip()
    # length=
    if re.search(r"(длинн|long)", raw, flags=re.I): d["length"]="long"
    elif re.search(r"(средн|medium)", raw, flags=re.I): d["length"]="medium"
    elif re.search(r"(корот|short)", raw, flags=re.I): d["length"]="short"
    # voice=
    if re.search(r"(голос|voice)\s*=\s*(on|да|yes)", raw, flags=re.I): d["voice"]=True
    # topic cleanup
    d["topic"] = re.sub(r"(имя|name|длина|length|голос|voice)\s*=\s*[^\|\n]+","", d["topic"], flags=re.I).replace("|"," ").strip()
    return d

async def story_help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ui_show_from_command(update, context, _story_help(uid), parse_mode="Markdown")

def _story_help(uid: str) -> str:
    lang = user_languages.get(uid, "ru")
    return STORY_TEXTS.get(lang, STORY_TEXTS["ru"])

async def story_cmd(update, context):
    uid = str(update.effective_user.id)

    # 🔐 Тарифный гейт на саму команду /story
    if not has_feature(uid, "story_cmd"):
        title, body = upsell_for(uid, "feature_story_long")  # общий месседж про сказки
        return await update.message.reply_text(
            f"*{title}*\n\n{body}",
            parse_mode="Markdown",
            reply_markup=_premium_kb(uid),
        )

    t = _s_i18n(uid)
    lang = user_languages.get(uid, "ru")

    # без аргументов — показать usage
    if not context.args:
        return await update.message.reply_text(
            f"{t['title']}\n\n{t['usage']}",
            parse_mode="Markdown"
        )

    raw = " ".join(context.args)
    args = _parse_story_args(raw)  # ожидаем keys: topic, name, length, voice(bool)

    # 🧱 Квоты/фичи по длине
    target_paras = {"short": 5, "medium": 8, "long": 12}.get(args.get("length"), 5)
    max_paras = quota(uid, "story_max_paras")  # например: free=5, plus=8, pro=12
    if target_paras > max_paras or (
        args.get("length") in ("medium", "long") and not has_feature(uid, "story_medium_long")
    ):
        title, body = upsell_for(uid, "feature_story_long")
        return await update.message.reply_text(
            f"*{title}*\n\n{body}",
            parse_mode="Markdown",
            reply_markup=_premium_kb(uid),
        )

    # 🔊 Явная озвучка через аргумент — только если есть фича story_voice
    if args.get("voice") and not has_feature(uid, "story_voice"):
        title, body = upsell_for(uid, "feature_story_voice")
        await update.message.reply_text(
            f"*{title}*\n\n{body}",
            parse_mode="Markdown",
            reply_markup=_premium_kb(uid),
        )
        args["voice"] = False  # выключаем озвучку для этого вызова

    # ✍️ Генерация текста сказки
    await update.message.reply_text(t["making"])
    text = await generate_story_text(uid, lang, args.get("topic"), args.get("name"), args.get("length"))

    # запомним последнюю историю
    context.chat_data[f"story_last_{uid}"] = {"text": text, "lang": lang, "topic": args.get("topic")}

    # показать текст + кнопки
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_more"],  callback_data="st:new")],
        [InlineKeyboardButton(t["btn_voice"], callback_data="st:voice")],
        [InlineKeyboardButton(t["btn_close"], callback_data="st:close")],
    ])
    await update.message.reply_text(
        f"*{t['title']}*\n\n{text}",
        parse_mode="Markdown",
        reply_markup=kb
    )

    # 🔊 Авто-озвучка (если фича доступна) — только если НЕ просили voice аргументом
    if not args.get("voice") and has_feature(uid, "story_voice"):
        prefs = _vp(uid)
        if prefs.get("auto_story_voice", True):
            bg_override = None
            # подмешаем «океан» по умолчанию, если пользователь сам фон не выбрал
            if prefs.get("auto_bgm_for_stories", True) and prefs.get("bgm_kind", "off") == "off":
                bg_override = "ocean"
            try:
                await send_voice_response(context, int(uid), text, lang, bgm_kind_override=bg_override)
            except Exception:
                logging.exception("Auto story TTS failed in story_cmd")

    # 🔊 Явный запрос голосом — озвучиваем один раз (если фича есть)
    if args.get("voice") and has_feature(uid, "story_voice"):
        await send_voice_response(context, int(uid), text, lang)

async def story_callback(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("st:"):
        return
    await q.answer()
    context.user_data[UI_MSG_KEY] = q.message.message_id  # работаем в одном сообщении

    uid = str(q.from_user.id)
    lang = user_languages.get(uid, "ru")
    t = _s_i18n(uid)

    parts = q.data.split(":")
    action = parts[1]

    if action == "confirm":
        topic = context.chat_data.get(f"story_pending_{uid}", "")
        # показываем «делаю…» в ТОМ ЖЕ сообщении
        try:
            await q.edit_message_text(t["making"])
        except Exception:
            pass

        text = await generate_story_text(uid, lang, topic, None, "short")
        context.chat_data[f"story_last_{uid}"] = {"text": text, "lang": lang, "topic": topic}

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["btn_more"],  callback_data="st:new")],
            [InlineKeyboardButton(t["btn_voice"], callback_data="st:voice")],
            [InlineKeyboardButton(t["btn_close"], callback_data="st:close")],
        ])
        try:
            await q.edit_message_text(
                f"*{t['title']}*\n\n{text}",
                parse_mode="Markdown",
                reply_markup=kb,
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise

        # авто-озвучка (доп. сообщение только с voice — это нормально)
        if is_premium(uid) and _vp(uid).get("auto_story_voice", True):
            bg_override = None
            prefs = _vp(uid)
            if prefs.get("auto_bgm_for_stories", True) and prefs.get("bgm_kind", "off") == "off":
                bg_override = "ocean"
            try:
                await send_voice_response(context, int(uid), text, lang, bgm_kind_override=bg_override)
            except Exception:
                logging.exception("Auto story TTS failed in story_callback:confirm")
        return

    if action == "new":
        last = context.chat_data.get(f"story_last_{uid}")
        topic = last["topic"] if last else ""
        text = await generate_story_text(uid, lang, topic, None, "short")
        context.chat_data[f"story_last_{uid}"] = {"text": text, "lang": lang, "topic": topic}

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["btn_more"],  callback_data="st:new")],
            [InlineKeyboardButton(t["btn_voice"], callback_data="st:voice")],
            [InlineKeyboardButton(t["btn_close"], callback_data="st:close")],
        ])
        try:
            await q.edit_message_text(
                f"*{t['title']}*\n\n{text}",
                parse_mode="Markdown",
                reply_markup=kb,
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise

        if is_premium(uid) and _vp(uid).get("auto_story_voice", True):
            bg_override = None
            prefs = _vp(uid)
            if prefs.get("auto_bgm_for_stories", True) and prefs.get("bgm_kind", "off") == "off":
                bg_override = "ocean"
            try:
                await send_voice_response(context, int(uid), text, lang, bgm_kind_override=bg_override)
            except Exception:
                logging.exception("Auto story TTS failed in story_callback:new")
        return

    if action == "voice":
        last = context.chat_data.get(f"story_last_{uid}")
        if last:
            await send_voice_response(context, int(uid), last["text"], last["lang"])
        return

    elif action == "close":
        # ставим кулдаун и редактируем это же сообщение
        _story_optout_until[uid] = datetime.now(timezone.utc) + timedelta(hours=STORY_COOLDOWN_HOURS)
        try:
            await q.edit_message_text(t["ready"], parse_mode="Markdown")
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
        return

async def send_voice_response(context, chat_id: int, text: str, lang: str, bgm_kind_override: str | None = None):
    uid = str(chat_id)
    ogg_path = None
    mixed_path = None
    try:
        # синтез (внутри synthesize_to_ogg можно читать speed/voice из _vp(uid))
        ogg_path = synthesize_to_ogg(text, lang, uid)  # ElevenLabs → gTTS фолбэк внутри
        path_to_send = ogg_path

        # 🎧 фон (если выбран) — только для тарифов с фичей voice_bgm_mix
        p = _vp(uid)
        kind = (bgm_kind_override if bgm_kind_override is not None else p.get("bgm_kind", "off")) or "off"
        if kind != "off" and has_feature(uid, "voice_bgm_mix"):
            bg = BGM_PRESETS.get(kind, {}).get("path")
            if bg and os.path.exists(bg):
                try:
                    mixed_path = _mix_with_bgm(ogg_path, bg, p.get("bgm_gain_db", -20))
                    if mixed_path:
                        path_to_send = mixed_path
                except Exception as mix_e:
                    # не роняем ответ, просто шлём без фона
                    logging.warning(f"BGM mix failed ({kind}): {mix_e}")
        # если фича недоступна — просто отправим без фона (молча)

        # отправка с 1 ретраем на таймаут
        try:
            with open(path_to_send, "rb") as f:
                await context.bot.send_voice(chat_id=chat_id, voice=f)
        except TimedOut:
            await asyncio.sleep(1.5)
            with open(path_to_send, "rb") as f:
                await context.bot.send_voice(chat_id=chat_id, voice=f)

    except Exception as e:
        logging.exception(f"TTS failed for chat_id={chat_id}: {e}")
        # Ничего не дублируем текстом: текст уже отправлен выше в chat()

    finally:
        # чистим оба файла (если второй был создан)
        for pth in (mixed_path, ogg_path):
            try:
                if pth and os.path.exists(pth):
                    os.remove(pth)
            except Exception:
                pass

                

@wraps
def _noop(f):  # just to silence linters if needed
    return f

async def require_premium_message(update, context, uid: str | None):
    t = _p_i18n(uid or "ru")
    msg = f"*{t['upsell_title']}*\n\n{t['upsell_body']}"
    kb = _premium_kb(uid or "0")

    q = getattr(update, "callback_query", None)
    if q:
        try:
            await q.answer("💎 Mindra+", show_alert=False)
        except Exception:
            pass
        # Пытаемся редактировать текущее UI-сообщение
        try:
            return await q.message.edit_text(msg, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            # Фолбэк — отправим новым сообщением
            return await context.bot.send_message(chat_id=q.message.chat.id, text=msg, reply_markup=kb, parse_mode="Markdown")

    # Командный вызов (/...):
    if getattr(update, "message", None):
        return await update.message.reply_text(msg, reply_markup=kb, parse_mode="Markdown")

    # Самый последний фолбэк
    return await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=kb, parse_mode="Markdown")


# ---- helpers ----
def _engine_label_for(uid: str, engine_key: str) -> str:
    """Красивое имя движка с локализацией из _v_i18n."""
    t = _v_i18n(uid)
    k = (engine_key or "").strip().lower()
    if k == "eleven":
        return t.get("engine_eleven", "ElevenLabs")
    if k in ("gtts", "gtts"):
        return t.get("engine_gtts", "gTTS")
    return engine_key or "gTTS"


# ---- /voice_mode ----
# Хелпер для красивого названия текущего TTS-движка
def _engine_label(uid: str) -> str:
    p = _vp(uid)  # в нём лежит p["engine"]
    eng = (p.get("engine") or "gTTS").strip()
    key = eng.lower()
    # если выбран eleven, но ключа нет — фактически используем gTTS
    if key == "eleven" and not _has_eleven():
        key = "gtts"

    labels = {
        "eleven": "ElevenLabs",
        "gtts": "Google TTS",
        "g_t_t_s": "Google TTS",  # на всякий случай, если где-то сохранилось криво
        "google": "Google TTS",
    }
    return labels.get(key, eng)

# ---- /voice_mode ----
@require_premium
async def voice_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    t = _v_i18n(uid)  # берёт VOICE_MODE_TEXTS[lang]

    # без аргументов — показать текущее состояние
    if not context.args:
        state = user_voice_mode.get(uid, False)
        eng = _engine_label(uid)
        base = t["on"] if state else t["off"]
        return await ui_show_from_command(update, context, f"{base}\n🎛 Движок: {eng}", parse_mode="Markdown")

    arg = (context.args[0] or "").lower()
    if arg not in ("on", "off"):
        return await ui_show_from_command(update, context, f"{t['err']}\n\n{t['help']}", parse_mode="Markdown")

    user_voice_mode[uid] = (arg == "on")
    eng = _engine_label(uid)
    base = t["on"] if user_voice_mode[uid] else t["off"]
    await ui_show_from_command(update, context, f"{base}\n🎛 Движок: {eng}", parse_mode="Markdown")
    
async def plus_callback(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("plus:"):
        return
    await q.answer()
    uid = str(q.from_user.id)
    t = _p_i18n(uid)
    action = q.data.split(":",1)[1]
    if action == "buy":
        await q.edit_message_text(f"*{t['upsell_title']}*\n\n{t['upsell_body']}\n\n(Покупка через Telegram Payments — скоро)",
                                  parse_mode="Markdown")
    elif action == "code":
        await q.edit_message_text("🔑 Введи код в формате: `/redeem ABCDEF`", parse_mode="Markdown")

async def premium_challenge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data or not q.data.startswith("pch:"):
        return

    # быстрый ack (иначе "query is too old")
    try:
        await q.answer()
    except Exception:
        pass

    uid = str(q.from_user.id)

    # антидубль
    try:
        if _debounce(uid, "pch_cb"):
            return
    except Exception:
        pass

    lang = user_languages.get(uid, "ru")
    t = _p_i18n(uid)

    # pch:ACTION[:ID]
    parts = q.data.split(":", 2)
    action = parts[1] if len(parts) > 1 else ""
    cb_id = parts[2] if len(parts) > 2 else None

    # неделя по локальному времени пользователя
    try:
        tz = _user_tz(uid)
        now_local = datetime.now(tz)
    except Exception:
        now_local = datetime.now()
    week_iso = _week_start_iso(now_local)

    # гарантируем таблицу
    try:
        ensure_premium_challenges()
    except Exception as e:
        logging.warning("ensure_premium_challenges failed: %s", e)

    def _kb(done_flag: bool, row_id: int) -> InlineKeyboardMarkup:
        if done_flag:
            return InlineKeyboardMarkup([[InlineKeyboardButton(t["btn_new"], callback_data="pch:new")]])
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(t["btn_done"], callback_data=f"pch:done:{row_id}")],
            [InlineKeyboardButton(t["btn_new"],  callback_data="pch:new")],
        ])

    def _render(text: str, row_id: int, done_flag: bool, prefix: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
        title = t.get("challenge_title", "🏆 Weekly challenge")
        cta   = t.get("challenge_cta", "Your challenge this week:\n\n“{text}”").format(text=text)
        header = [prefix] if prefix else []
        body = "\n".join([*(header + ["", f"*{title}*", "", cta])]) if header else "\n".join([f"*{title}*", "", cta])
        return body, _kb(done_flag, row_id)

    try:
        with sqlite3.connect(PREMIUM_DB_PATH) as db:
            db.row_factory = sqlite3.Row

            # базовая строка недели (если нет — создаём)
            row = db.execute(
                "SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
                (uid, week_iso)
            ).fetchone()

            if not row:
                text = random.choice(CHALLENGE_BANK.get(lang, CHALLENGE_BANK["ru"]))
                db.execute(
                    "INSERT INTO premium_challenges (user_id, week_start, text, done, created_at) VALUES (?, ?, ?, 0, ?);",
                    (uid, week_iso, text, _to_epoch(_utcnow()))
                )
                db.commit()
                row = db.execute(
                    "SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
                    (uid, week_iso)
                ).fetchone()

            row_id   = int(row["id"])
            row_text = row["text"]
            row_done = bool(row["done"])

            if action == "done":
                # если в callback пришёл id — удостоверимся, что работаем по нему и этой же неделе
                try:
                    target_id = int(cb_id) if cb_id else None
                except Exception:
                    target_id = None

                if target_id and target_id != row_id:
                    r2 = db.execute(
                        "SELECT * FROM premium_challenges WHERE id=? AND user_id=? AND week_start=?;",
                        (target_id, uid, week_iso)
                    ).fetchone()
                    if r2:
                        row = r2
                        row_id   = int(row["id"])
                        row_text = row["text"]
                        row_done = bool(row["done"])

                if row_done:
                    body, kb = _render(row_text, row_id, True, prefix=t.get("done_ok", "✅ Done"))
                    return await q.edit_message_text(body, parse_mode="Markdown", reply_markup=kb)

                db.execute("UPDATE premium_challenges SET done=1 WHERE id=? AND user_id=?;", (row_id, uid))
                db.commit()

                # очки за неделю — 1 раз
                try:
                    add_points(uid, CHALLENGE_POINTS, reason="premium_challenge_done")
                except Exception as e:
                    logging.warning("add_points failed: %s", e)

                # тост ⭐️ +N
                try:
                    await q.answer(text=f"⭐️ +{CHALLENGE_POINTS}")
                except Exception:
                    pass

                body, kb = _render(row_text, row_id, True, prefix=t.get("done_ok", "✅ Done"))
                return await q.edit_message_text(body, parse_mode="Markdown", reply_markup=kb)

            if action == "new":
                new_text = random.choice(CHALLENGE_BANK.get(lang, CHALLENGE_BANK["ru"]))
                if row_done:
                    db.execute("UPDATE premium_challenges SET text=? WHERE id=? AND user_id=?;", (new_text, row_id, uid))
                    db.commit()
                    body, kb = _render(new_text, row_id, True, prefix=t.get("changed_ok", "🔄 Updated"))
                else:
                    db.execute("UPDATE premium_challenges SET text=?, done=0 WHERE id=? AND user_id=?;", (new_text, row_id, uid))
                    db.commit()
                    body, kb = _render(new_text, row_id, False, prefix=t.get("changed_ok", "🔄 Updated"))
                return await q.edit_message_text(body, parse_mode="Markdown", reply_markup=kb)

            # неизвестное действие → просто перерисуем текущее
            body, kb = _render(row_text, row_id, row_done)
            return await q.edit_message_text(body, parse_mode="Markdown", reply_markup=kb)

    except sqlite3.OperationalError as e:
        if "no such table: premium_challenges" in str(e):
            logging.warning("challenge table missing; creating and retrying…")
            ensure_premium_challenges()
            return await premium_challenge_callback(update, context)
        logging.exception("premium_challenge_callback op-error: %s", e)
        try:
            await context.bot.send_message(chat_id=q.message.chat.id, text="⚠️ Ошибка. Попробуй ещё раз.")
        except Exception:
            pass
    except Exception as e:
        logging.exception("premium_challenge_callback failed: %s", e)
        try:
            await context.bot.send_message(chat_id=q.message.chat.id, text="⚠️ Ошибка. Попробуй ещё раз.")
        except Exception:
            pass
            
    def _ensure_and_get(db: sqlite3.Connection) -> sqlite3.Row:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
            (uid, week_iso)
        ).fetchone()
        if not row:
            text = random.choice(CHALLENGE_BANK.get(lang, CHALLENGE_BANK["ru"]))
            db.execute(
                "INSERT INTO premium_challenges (user_id, week_start, text, done, created_at) "
                "VALUES (?, ?, ?, 0, ?);",
                (uid, week_iso, text, _to_epoch(_utcnow()))
            )
            db.commit()
            row = db.execute(
                "SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
                (uid, week_iso)
            ).fetchone()
        return row

    def _handle(db: sqlite3.Connection):
        # получаем текущую строку
        row = _ensure_and_get(db)

        # если в callback есть id — предпочитаем его (на случай гонок)
        if cb_id:
            try:
                rid = int(cb_id)
                got = db.execute(
                    "SELECT * FROM premium_challenges WHERE id=? AND user_id=? AND week_start=?;",
                    (rid, uid, week_iso)
                ).fetchone()
                if got:
                    row = got
            except Exception:
                pass

        if action == "done":
            db.execute("UPDATE premium_challenges SET done=1 WHERE id=? AND user_id=?;", (row["id"], uid))
            db.commit()
            body, kb = _render(row["text"], row["id"], prefix=f"✅ {t['done_ok']}")
            return body, kb

        if action == "new":
            new_text = random.choice(CHALLENGE_BANK.get(lang, CHALLENGE_BANK["ru"]))
            db.execute("UPDATE premium_challenges SET text=?, done=0 WHERE id=? AND user_id=?;",
                       (new_text, row["id"], uid))
            db.commit()
            body, kb = _render(new_text, row["id"], prefix=f"🔄 {t['changed_ok']}")
            return body, kb

        # по умолчанию просто показать текущий
        body, kb = _render(row["text"], row["id"])
        return body, kb

    try:
        with sqlite3.connect(PREMIUM_DB_PATH) as db:
            body, kb = _handle(db)
    except sqlite3.OperationalError as e:
        # если таблицы нет — создаём и повторяем один раз
        if "no such table: premium_challenges" in str(e):
            try:
                ensure_premium_challenges()
                with sqlite3.connect(PREMIUM_DB_PATH) as db:
                    body, kb = _handle(db)
            except Exception as ee:
                logging.exception("premium_challenge_callback retry failed: %s", ee)
                return
        else:
            logging.exception("premium_challenge_callback failed: %s", e)
            return

    try:
        await q.edit_message_text(body, parse_mode="Markdown", reply_markup=kb)
    except Exception as e:
        # если исходное сообщение нельзя редактировать — шлём новое
        logging.warning("edit_message_text failed, sending new: %s", e)
        await context.bot.send_message(chat_id=int(uid), text=body, parse_mode="Markdown", reply_markup=kb)

def _week_start_iso(dt):
    """ISO даты понедельника текущей недели в локальном времени."""
    if isinstance(dt, datetime):
        base = dt
    else:
        base = datetime.now(timezone.utc)
    monday = base - timedelta(days=base.weekday())
    return monday.date().isoformat()

def _menu_main_kb(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["features"],       callback_data="m:feat:open"),
         InlineKeyboardButton(t["plus_features"],  callback_data="m:plus:open")],
        [InlineKeyboardButton(t["premium"],        callback_data="m:prem:open")],
        [InlineKeyboardButton(t["close"],          callback_data="m:nav:close")],
    ]
    return InlineKeyboardMarkup(rows)

def _features_kb(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["feat_goals"],     callback_data="m:feat:goals")],
        [InlineKeyboardButton(t["feat_habits"],    callback_data="m:feat:habits")],
        [InlineKeyboardButton(t["feat_reminders"], callback_data="m:feat:reminders")],
        [InlineKeyboardButton(t["feat_points"],    callback_data="m:feat:points")],
        [InlineKeyboardButton(t["feat_mood"],      callback_data="m:feat:mood")],
        [InlineKeyboardButton(t["back"],           callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)

def _plus_features_kb(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["plus_voice"], callback_data="m:plus:voice")],
        [InlineKeyboardButton(t["plus_sleep"], callback_data="m:plus:sleep")],
        [InlineKeyboardButton(t["plus_story"], callback_data="m:plus:story")],
        [InlineKeyboardButton(t["back"],       callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)

def _premium_kb(uid: str) -> InlineKeyboardMarkup:
    t = _menu_i18n(uid)
    rows = [
        [InlineKeyboardButton(t["premium_days"], callback_data="m:premium:days")],
        [InlineKeyboardButton(t["invite"],       callback_data="m:premium:invite")],
        [InlineKeyboardButton(t["premium_buy"],  url=PREMIUM_URL)],
        [InlineKeyboardButton(t["back"],         callback_data="m:nav:home")],
    ]
    return InlineKeyboardMarkup(rows)
    
def _gh_menu_keyboard(t: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_add_goal"],   callback_data="gh:new_goal")],
        [InlineKeyboardButton(t["btn_list_goals"], callback_data="gh:list_goals")],
        [InlineKeyboardButton(t["btn_add_habit"],  callback_data="gh:new_habit")],
        [InlineKeyboardButton(t["btn_list_habits"],callback_data="gh:list_habits")],
        [InlineKeyboardButton(t["back"],            callback_data="gh:back")],
    ])

async def tracker_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    t = _gh_i18n(uid)
    await ui_show_from_command(update, context, t["menu_title"], reply_markup=_gh_menu_keyboard(t))

# /premium — апселл/статус
async def premium_cmd(update, context):
    uid = str(update.effective_user.id)
    t = _p_i18n(uid)
    if is_premium(uid):
        # посчитаем дни
        until = get_premium_until(uid)
        days = 0
        if until:
            try:
                u = until.strip()
                if u.endswith("Z"): u = u[:-1] + "+00:00"
                dt = datetime.fromisoformat(u)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                days = max(0, (dt - datetime.now(timezone.utc)).days)
            except Exception:
                pass
        await update.message.reply_text(t["days_left"].format(days=days), parse_mode="Markdown")
    else:
        await update.message.reply_text(f"*{t['upsell_title']}*\n\n{t['upsell_body']}",
                                        reply_markup=_premium_kb(uid), parse_mode="Markdown")


@require_premium
async def premium_report_cmd(update, context):
    uid = str(update.effective_user.id)
    t = _p_i18n(uid)

    try:
        goals = get_goals(uid)
        goals_done = sum(1 for g in goals if isinstance(g, dict) and g.get("done"))
    except Exception:
        goals_done = 0
    try:
        habits = get_habits(uid)
        habits_marked = len(habits)
    except Exception:
        habits_marked = 0

    rems_7 = 0
    try:
        with remind_db() as db:
            since = _to_epoch(datetime.now(timezone.utc) - timedelta(days=7))
            rems_7 = db.execute(
                "SELECT COUNT(*) FROM reminders WHERE user_id=? AND status='fired' AND due_utc>=?;",
                (uid, since)
            ).fetchone()[0]
    except Exception:
        pass

    active_30 = 0  # заглушка

    text = (
        f"*{t['report_title']}*\n\n"
        f"{t['report_goals'].format(n=goals_done)}\n"
        f"{t['report_habits'].format(n=habits_marked)}\n"
        f"{t['report_rems'].format(n=rems_7)}\n"
        f"{t['report_streak'].format(n=active_30)}"
    )
    await ui_show_from_command(update, context, text, reply_markup=_kb_home(uid), parse_mode="Markdown")
    
async def premium_challenge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if _debounce(uid, "pch_cmd"):  # антидубль
        return

    try:
        ensure_premium_challenges()
    except Exception as e:
        logging.warning("ensure_premium_challenges failed: %s", e)

    lang = user_languages.get(uid, "ru")
    t = _p_i18n(uid)

    # неделя по локальному времени (если у тебя есть _user_tz)
    try:
        tz = _user_tz(uid)
        now_local = datetime.now(tz)
    except Exception:
        now_local = datetime.now()
    week_iso = _week_start_iso(now_local)

    # достаём/создаём челлендж
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
            (uid, week_iso)
        ).fetchone()

        if not row:
            # возьми свой банк задач (CHALLENGE_BANK[lang])
            text = random.choice(CHALLENGE_BANK.get(lang, CHALLENGE_BANK["ru"]))
            db.execute(
                "INSERT INTO premium_challenges (user_id, week_start, text, done, created_at) VALUES (?, ?, ?, 0, ?);",
                (uid, week_iso, text, _to_epoch(_utcnow()))
            )
            db.commit()
            row = db.execute(
                "SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
                (uid, week_iso)
            ).fetchone()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_done"], callback_data=f"pch:done:{row['id']}")],
        [InlineKeyboardButton(t["btn_new"],  callback_data="pch:new")],
    ])

    await update.message.reply_text(
        f"*{t['challenge_title']}*\n\n{t['challenge_cta'].format(text=row['text'])}",
        parse_mode="Markdown",
        reply_markup=kb
    )

@require_premium
async def premium_mode_cmd(update, context):
    uid = str(update.effective_user.id)
    t = _p_i18n(uid)
    lang_code = user_languages.get(uid, "ru")

    # минимальный системный промпт для премиум-коуча
    coach_prompt = {
        "ru": "Ты — Mindra+ коуч. Кратко, по делу, с поддержкой, с фокусом на прогресс и привычки.",
        "uk": "Ти — Mindra+ коуч. Коротко, по суті, з підтримкою та фокусом на прогрес.",
        "en": "You are a Mindra+ coach. Be concise, supportive, progress-oriented.",
    }.get(lang_code, "Ты — Mindra+ коуч.")
    conversation_history[uid] = [{"role": "system", "content": coach_prompt}]
    save_history(conversation_history)

    await update.message.reply_text(f"*{t['mode_title']}*\n\n{t['mode_set']}", parse_mode="Markdown")

@require_premium
async def premium_stats_cmd(update, context):
    uid = str(update.effective_user.id)
    t = _p_i18n(uid)

    try:
        goals = get_goals(uid)
        total_goals_done = sum(1 for g in goals if isinstance(g, dict) and g.get("done"))
    except Exception:
        total_goals_done = 0
    try:
        habits = get_habits(uid)
        habit_days = len(habits)
    except Exception:
        habit_days = 0
    active_30 = 0

    text = (
        f"*{t['stats_title']}*\n\n"
        f"{t['stats_goals_done'].format(n=total_goals_done)}\n"
        f"{t['stats_habit_days'].format(n=habit_days)}\n"
        f"{t['stats_active_days'].format(n=active_30)}"
    )
    await ui_show_from_command(update, context, text, reply_markup=_kb_home(uid), parse_mode="Markdown")

async def gh_callback(update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data or not q.data.startswith("gh:"):
        return
    await q.answer()

    msg = q.message 
    uid = str(q.from_user.id)
    t = _gh_i18n(uid)
    action = q.data.split(":", 1)[1]

    # Вернуть меню
    if action == "menu":
        try:
            await q.edit_message_text(t["menu_title"], reply_markup=_gh_menu_keyboard(t))
        except Exception:
            await context.bot.send_message(chat_id=int(uid), text=t["menu_title"], reply_markup=_gh_menu_keyboard(t))
        return

    # Создание: просто показываем подсказку (как мы делали для reminders)
    if action == "new_goal":
        await context.bot.send_message(chat_id=int(uid), text=t["goal_usage"], parse_mode="Markdown")
        return
    if action == "new_habit":
        await context.bot.send_message(chat_id=int(uid), text=t["habit_usage"], parse_mode="Markdown")
        return

    # Списки: берём данные напрямую
    if action == "list_goals":
        try:
            goals = get_goals(uid)  # уже есть в твоём коде
        except Exception:
            goals = []
        if not goals:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(t["btn_add_goal"], callback_data="gh:new_goal")],
                                       [InlineKeyboardButton(t["back"], callback_data="gh:menu")]])
            await q.edit_message_text(t["goals_empty"], reply_markup=kb)
            return

        lines = []
        # аккуратно достаём поля
        for i, g in enumerate(goals, 1):
            title = g.get("title") or g.get("name") or g.get("text") or str(g)
            title = str(title).strip()
            done = g.get("done")
            mark = "✅" if done else "▫️"
            lines.append(f"{mark} {i}. {title}")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["btn_add_goal"], callback_data="gh:new_goal")],
            [InlineKeyboardButton(t["back"], callback_data="gh:menu")],
        ])
        await q.edit_message_text(t["goals_title"] + "\n\n" + "\n".join(lines), reply_markup=kb)
        return

    if action == "list_habits":
        try:
            habits = get_habits(uid)  # уже есть в твоём коде
        except Exception:
            habits = []
        if not habits:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(t["btn_add_habit"], callback_data="gh:new_habit")],
                                       [InlineKeyboardButton(t["back"], callback_data="gh:menu")]])
            await q.edit_message_text(t["habits_empty"], reply_markup=kb)
            return

        lines = []
        for i, h in enumerate(habits, 1):
            name = (isinstance(h, dict) and (h.get("name") or h.get("title") or h.get("text"))) or str(h)
            name = str(name).strip()
            # если у привычки есть «done» за сегодня — поставим галочку
            done = isinstance(h, dict) and h.get("done")
            mark = "✅" if done else "▫️"
            lines.append(f"{mark} {i}. {name}")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["btn_add_habit"], callback_data="gh:new_habit")],
            [InlineKeyboardButton(t["back"], callback_data="gh:menu")],
        ])
        await q.edit_message_text(t["habits_title"] + "\n\n" + "\n".join(lines), reply_markup=kb)
        return

    elif action == "back":
        return await show_main_menu(q.message)

def _i18n(uid: str) -> dict:
    return REMIND_TEXTS.get(user_languages.get(uid, "ru"), REMIND_TEXTS["ru"])

# ========== DB ==========

async def reminders_menu_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(_i18n(str(q.from_user.id))["menu_title"],
                              reply_markup=_reminders_kb(str(q.from_user.id)))

def _reminders_kb(uid: str) -> InlineKeyboardMarkup:
    t = _i18n(uid)          # тексты блока напоминаний
    t_menu = _menu_i18n(uid)  # чтобы взять локализованный "Назад"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_add_rem"],  callback_data="rem:new")],
        [InlineKeyboardButton(t["btn_list_rem"], callback_data="rem:list")],
        [InlineKeyboardButton(t_menu["back"],    callback_data="m:nav:home")],  # ⬅️ назад в Гл. меню
    ])

async def reminders_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    t = _i18n(uid)
    await ui_show_from_command(update, context, t["menu_title"], reply_markup=_reminders_kb(uid))

# ========== Time helpers ==========
def _utcnow():
    return datetime.now(timezone.utc)

def _user_tz(uid: str) -> ZoneInfo:
    tz = user_timezones.get(uid, "Europe/Kyiv")
    try:
        return ZoneInfo(tz)
    except Exception:
        return ZoneInfo("Europe/Kyiv")

def _to_epoch(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def _from_epoch(sec: int) -> datetime:
    return datetime.fromtimestamp(sec, tz=timezone.utc)

def _apply_quiet_hours(local_dt: datetime) -> datetime:
    """Если внутри тихих часов — переносим на ближайшие 09:00 локально."""
    hour = local_dt.hour
    if QUIET_START <= hour or hour < QUIET_END:
        if hour >= QUIET_START:
            return (local_dt + timedelta(days=1)).replace(hour=QUIET_END, minute=0, second=0, microsecond=0)
        return local_dt.replace(hour=QUIET_END, minute=0, second=0, microsecond=0)
    return local_dt

def _fmt_local(dt_local: datetime, lang: str) -> str:
    if lang == "en":
        return dt_local.strftime("%-I:%M %p, %Y-%m-%d")
    return dt_local.strftime("%H:%M, %Y-%m-%d")

# ========== Natural language parsing (ru/uk/en) ==========
WEEKDAYS_RU = {"пн":0,"пон":0,"понедельник":0,"вт":1,"ср":2,"чт":3,"чтврг":3,"пт":4,"птн":4,"пятница":4,"сб":5,"суббота":5,"вс":6,"вск":6}
WEEKDAYS_UK = {"пн":0,"вт":1,"ср":2,"чт":3,"пт":4,"сб":5,"нд":6,"нед":6}
WEEKDAYS_EN = {"mon":0,"monday":0,"tue":1,"tues":1,"tuesday":1,"wed":2,"wednesday":2,"thu":3,"thurs":3,"fr":4,"fri":4,"friday":4,"sat":5,"saturday":5,"sun":6,"sunday":6}

def _next_weekday(base_local: datetime, target_wd: int) -> datetime:
    delta = (target_wd - base_local.weekday()) % 7
    if delta == 0:
        delta = 7
    return base_local + timedelta(days=delta)

# ==== РОУТЕР ГЛАВНОГО МЕНЮ ====
async def menu_router(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("m:nav:"):
        return
    await q.answer()

    uid = str(q.from_user.id)
    t = _menu_i18n(uid)
    msg = q.message
    act = q.data.split(":", 2)[2]

    if act == "features":
        text = f'{t.get("feat_title", t["features"])}\n{t.get("feat_body", "")}'
        return await msg.edit_text(text, reply_markup=_menu_kb_features(uid), parse_mode="Markdown")

    elif act == "plus":
        return await msg.edit_text(t.get("plus_title", t["plus_features"]),
                                   reply_markup=_menu_kb_plus(uid), parse_mode="Markdown")

    elif act == "premium":
        return await msg.edit_text(t.get("prem_title", t["premium"]),
                                   reply_markup=_menu_kb_premium(uid), parse_mode="Markdown")

    elif act == "settings":
        return await msg.edit_text(t.get("set_title", t["settings"]),
                                   reply_markup=_menu_kb_settings(uid), parse_mode="Markdown")

    elif act == "home":
        return await show_main_menu(msg)

    elif act == "close":
        try:
            return await msg.delete()
        except Exception:
            return await show_main_menu(msg)

# m:plus:* — экраны внутри "Премиум-функции"
async def plus_router(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("m:plus:"):
        return
    await q.answer()
    context.user_data[UI_MSG_KEY] = q.message.message_id  # работаем в одном сообщении

    uid = str(q.from_user.id)
    msg = q.message
    parts = q.data.split(":")            # ["m","plus", ...]
    action = parts[2] if len(parts) >= 3 else ""

    # --- Озвучка
    if action == "voice":
        return await show_voice_menu(msg)  # edit того же сообщения

    # --- Звуки для сна
    if action == "sleep":
        if len(parts) == 3:
            return await show_sleep_menu(msg)
        sub = parts[3]
        p = _vp(uid)
        if sub == "set" and len(parts) >= 5:
            p["bgm_kind"] = parts[4]
            return await show_sleep_menu(msg)
        if sub == "gain" and len(parts) >= 5:
            try:
                p["bgm_gain_db"] = int(parts[4])
            except Exception:
                pass
            return await show_sleep_menu(msg)

    # --- Сказка: просто показать инструкцию, БЕЗ клавиатуры
    if action == "story":
        text = _story_help(uid)
        try:
            try:
                await q.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
            await q.edit_message_text(
                text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
        return

    # --- Premium-mode
    if action == "pmode":
        if len(parts) == 3:
            return await msg.edit_text(_pmode_text(uid), reply_markup=_pmode_kb(uid), parse_mode="Markdown")
        if len(parts) >= 4 and parts[3] == "toggle":
            user_premium_mode[uid] = not user_premium_mode.get(uid, False)
            return await msg.edit_text(_pmode_text(uid), reply_markup=_pmode_kb(uid), parse_mode="Markdown")

    # --- Premium-stats
    if action == "pstats":
        return await msg.edit_text(
            _simple_text("📊 Premium-stats", "Раздел в разработке. Тут будут расширенные графики и метрики."),
            reply_markup=_simple_kb_back(uid), parse_mode="Markdown"
        )

    # --- Premium-report
    if action == "preport":
        return await msg.edit_text(
            _simple_text("📝 Premium-report", "Еженедельный отчёт с персональными инсайтами — скоро."),
            reply_markup=_simple_kb_back(uid), parse_mode="Markdown"
        )

    # --- Premium-challenge
    if action == "pchallenge":
        return await msg.edit_text(
            _simple_text("🏆 Premium-challenge", "Ежемесячные челленджи с прогрессом и наградами — скоро."),
            reply_markup=_simple_kb_back(uid), parse_mode="Markdown"
        )

async def feat_router(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("m:feat:"):
        return
    await q.answer()

    uid = str(q.from_user.id)
    msg = q.message
    action = q.data.split(":", 2)[2]  # tracker | mode | reminders | points | mood

    if action == "tracker":
        # экран трекера
        t_p = _p_i18n(uid)  # тексты трекера (у тебя уже есть)
        return await msg.edit_text(t_p["menu_title"], reply_markup=_gh_menu_keyboard(t_p))

    elif action == "mode":
        # экран выбора режима
        return await show_mode_menu(msg)  # мы уже делали эту функцию

    elif action == "reminders":
        # экран напоминаний
        return await show_reminders_menu(msg)  # функция из блока reminders

    elif action == "points":
        # заглушка/экран очков — подставь свою функцию, если есть
        kb_back = InlineKeyboardMarkup([[InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data="m:nav:home")]])
        return await msg.edit_text("⭐️ Очки/Титул (скоро)", reply_markup=kb_back)

    elif action == "mood":
        kb_back = InlineKeyboardMarkup([[InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data="m:nav:home")]])
        return await msg.edit_text("🧪 Тест настроения (скоро)", reply_markup=kb_back)

def parse_natural_time(text: str, lang: str, user_tz: ZoneInfo) -> datetime | None:
    """
    Возвращает AWARE local datetime (в таймзоне пользователя) или None.
    Поддержка:
      RU/UK: «через 15 мин/час/день», «сегодня в 18:30», «завтра в 9», «в пт в 19»
      EN:    “in 30 min/hour/day”, “today at 6:30pm”, “tomorrow at 9”, “on fri at 7”
    """
    s = re.sub(r"\s+", " ", text.lower().strip())
    now_local = datetime.now(user_tz)

    # EN: in X ...
    m = re.search(r"\bin\s+(\d+)\s*(min|mins|minutes|hour|hours|day|days)\b", s)
    if m:
        n = int(m.group(1)); unit = m.group(2)
        if "min" in unit:  return now_local + timedelta(minutes=n)
        if "hour" in unit: return now_local + timedelta(hours=n)
        if "day" in unit:  return now_local + timedelta(days=n)

    # RU/UK: через X ...
    m = re.search(r"через\s+(\d+)\s*(мин|минут|хв|хвилин|час|часа|часов|годин|день|дня|дней|дн)\b", s)
    if m:
        n = int(m.group(1)); unit = m.group(2)
        if unit.startswith(("мин","хв")): return now_local + timedelta(minutes=n)
        if unit.startswith(("час","годин")): return now_local + timedelta(hours=n)
        if unit.startswith(("д","дн")): return now_local + timedelta(days=n)

    # today / сегодня / сьогодні
    if "today" in s or "сегодня" in s or "сьогодні" in s:
        base = now_local
        tm = re.search(r"\bв\s*(\d{1,2})(?::(\d{2}))?|\bat\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", s)
        if tm:
            h = int(tm.group(1) or tm.group(3)); mnt = int((tm.group(2) or tm.group(4) or "0"))
            ampm = (tm.group(5) or "").lower()
            if ampm == "pm" and h < 12: h += 12
            return base.replace(hour=h, minute=mnt, second=0, microsecond=0)
        return now_local + timedelta(hours=1)

    # tomorrow / завтра
    if "tomorrow" in s or "завтра" in s:
        base = now_local + timedelta(days=1)
        tm = re.search(r"\bв\s*(\d{1,2})(?::(\d{2}))?|\bat\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", s)
        if tm:
            h = int(tm.group(1) or tm.group(3)); mnt = int((tm.group(2) or tm.group(4) or "0"))
            ampm = (tm.group(5) or "").lower()
            if ampm == "pm" and h < 12: h += 12
            return base.replace(hour=h, minute=mnt, second=0, microsecond=0)
        return base.replace(hour=9, minute=0, second=0, microsecond=0)

    # weekday (ru/uk/en) [+ time]
    wd_map = WEEKDAYS_EN | WEEKDAYS_RU | WEEKDAYS_UK
    for name, idx in wd_map.items():
        if re.search(rf"\b(в|на|on)\s*{name}\b", s):
            base = _next_weekday(now_local, idx)
            tm = re.search(r"\bв\s*(\d{1,2})(?::(\d{2}))?|\bat\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", s)
            if tm:
                h = int(tm.group(1) or tm.group(3)); mnt = int((tm.group(2) or tm.group(4) or "0"))
                ampm = (tm.group(5) or "").lower()
                if ampm == "pm" and h < 12: h += 12
                return base.replace(hour=h, minute=mnt, second=0, microsecond=0)
            return base.replace(hour=9, minute=0, second=0, microsecond=0)

    # bare "в 18:30" / "at 6:30pm"
    tm = re.search(r"\bв\s*(\d{1,2})(?::(\d{2}))?|\bat\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", s)
    if tm:
        h = int(tm.group(1) or tm.group(3)); mnt = int((tm.group(2) or tm.group(4) or "0"))
        ampm = (tm.group(5) or "").lower()
        if ampm == "pm" and h < 12: h += 12
        cand = now_local.replace(hour=h, minute=mnt, second=0, microsecond=0)
        if cand <= now_local:
            cand += timedelta(days=1)
        return cand

    return None

# ========== UI (кнопки) ==========
def _btn_labels(uid: str) -> dict:
    t = _i18n(uid)
    return {
        "plus15": t["btn_plus15"],
        "plus1h":  t["btn_plus1h"],
        "tomorrow":t["btn_tomorrow"],
        "delete":  t["btn_delete"],
    }

def remind_keyboard(rem_id: int, uid: str) -> InlineKeyboardMarkup:
    b = _btn_labels(uid)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(b["plus15"], callback_data=f"rem:snooze:{rem_id}:15m"),
        InlineKeyboardButton(b["plus1h"],  callback_data=f"rem:snooze:{rem_id}:1h"),
        InlineKeyboardButton(b["tomorrow"], callback_data=f"rem:snooze:{rem_id}:tomorrow"),
        InlineKeyboardButton(b["delete"],   callback_data=f"rem:del:{rem_id}"),
    ]])

# ========== Планирование ==========
async def _schedule_job_on(job_queue, row: sqlite3.Row):
    """Создаёт JobQueue-задачу для напоминания."""
    if row["status"] != "scheduled":
        return
    due_dt_utc = _from_epoch(row["due_utc"])  # aware UTC
    when = due_dt_utc if due_dt_utc > _utcnow() else _utcnow() + timedelta(seconds=3)
    jname = f"rem#{row['id']}"
    for j in job_queue.get_jobs_by_name(jname):
        j.schedule_removal()
    job_queue.run_once(reminder_fire, when=when, name=jname, data={"id": row["id"]})

async def _schedule_job_for_reminder(context: ContextTypes.DEFAULT_TYPE, row: sqlite3.Row):
    await _schedule_job_on(context.job_queue, row)

# ========== Джоба: срабатывание ==========
async def reminder_fire(context: ContextTypes.DEFAULT_TYPE):
    rem_id = context.job.data["id"]
    with remind_db() as db:
        row = db.execute("SELECT * FROM reminders WHERE id=?;", (rem_id,)).fetchone()
        if not row or row["status"] != "scheduled":
            return

        uid = row["user_id"]
        lang = user_languages.get(uid, "ru")
        tdict = _i18n(uid)
        tz = ZoneInfo(row["tz"])
        now_local = datetime.now(tz)

        # Тихие часы → переносим
        if QUIET_START <= now_local.hour or now_local.hour < QUIET_END:
            new_local = _apply_quiet_hours(now_local)
            new_utc = new_local.astimezone(timezone.utc)
            db.execute("UPDATE reminders SET due_utc=? WHERE id=?;", (_to_epoch(new_utc), rem_id))
            db.commit()
            row = db.execute("SELECT * FROM reminders WHERE id=?;", (rem_id,)).fetchone()
            await _schedule_job_for_reminder(context, row)
            return

        # Отправляем
        local_dt = _from_epoch(row["due_utc"]).astimezone(tz)
        time_str = _fmt_local(local_dt, lang)
        text = row["text"]
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=tdict["fired"].format(text=text, time=time_str),
                reply_markup=remind_keyboard(rem_id, uid)
            )
        except Exception:
            pass

        db.execute("UPDATE reminders SET status='fired' WHERE id=?;", (rem_id,))
        db.commit()

# ========== Команды ==========
async def remind_command(update, context: ContextTypes.DEFAULT_TYPE):
    ensure_remind_db()
    uid = str(update.effective_user.id)
    lang = user_languages.get(uid, "ru")
    t = REMIND_TEXTS.get(lang, REMIND_TEXTS["ru"])
    tz = _user_tz(uid)

    # нет аргументов → подсказка (и старый usage тоже покажем)
    if not context.args:
        msg = "⏰ " + t["create_help"] + "\n\n" + t["usage"]
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    raw = " ".join(context.args).strip()

    # БЕСПЛАТНЫЙ ЛИМИТ: 1 активное напоминание
    if not is_premium(uid):
        with remind_db() as db:
            cnt = db.execute(
                "SELECT COUNT(*) AS c FROM reminders WHERE user_id=? AND status='scheduled';",
                (uid,)
            ).fetchone()[0]
        if cnt >= 1:
            await update.message.reply_text(t["limit"] + "\n\n" + t["usage"], parse_mode="Markdown")
            return

    # 1) Сначала пробуем СТАРЫЙ формат: HH:MM(.|:) + пробел + текст
    #    Поддержим и '19.30' на всякий.
    m = re.match(r"^\s*(\d{1,2})[:.](\d{2})\s+(.+)$", raw)
    dt_local = None
    text = raw
    now_local = datetime.now(tz)

    if m:
        h = int(m.group(1)); mnt = int(m.group(2))
        text = m.group(3).strip()
        dt_local = now_local.replace(hour=h, minute=mnt, second=0, microsecond=0)
        # Если время уже прошло — переносим на завтра
        if dt_local <= now_local:
            dt_local += timedelta(days=1)
    else:
        # 2) Новый парсер естественного языка (ru/uk/en)
        dt_local = parse_natural_time(raw, lang, tz)
        text = re.sub(r"\s+", " ", raw).strip()

    if not dt_local:
        await update.message.reply_text(t["not_understood"] + "\n\n" + t["usage"], parse_mode="Markdown")
        return

    # Тихие часы
    dt_local = _apply_quiet_hours(dt_local)
    dt_utc = dt_local.astimezone(timezone.utc)

    # Сохраняем в БД и планируем
    with remind_db() as db:
        cur = db.execute(
            "INSERT INTO reminders (user_id, text, due_utc, tz, status, created_at) "
            "VALUES (?, ?, ?, ?, 'scheduled', ?)",
            (uid, text, _to_epoch(dt_utc), str(tz.key), _to_epoch(_utcnow()))
        )
        rem_id = cur.lastrowid
        db.commit()
        row = db.execute("SELECT * FROM reminders WHERE id=?;", (rem_id,)).fetchone()

    await _schedule_job_for_reminder(context, row)

    # Ответ пользователю
    local_str = _fmt_local(dt_local, lang)
    await update.message.reply_text(
        t["created"].format(time=local_str, text=text),
        reply_markup=remind_keyboard(rem_id, uid)
    )

async def reminders_list(update, context: ContextTypes.DEFAULT_TYPE):
    ensure_remind_db()
    uid = str(update.effective_user.id)
    t = _i18n(uid)
    tz = _user_tz(uid)

    with remind_db() as db:
        rows = db.execute(
            "SELECT * FROM reminders WHERE user_id=? AND status='scheduled' ORDER BY due_utc ASC LIMIT 50;",
            (uid,)
        ).fetchall()

    # Если нет напоминаний — покажем кнопку "Добавить"
    if not rows:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t["btn_new"], callback_data="rem:new")]])
        await update.message.reply_text(t["list_empty"], reply_markup=kb)
        return

    # Текст-список
    lines = []
    for r in rows:
        local = _from_epoch(r["due_utc"]).astimezone(tz)
        lines.append(f"• #{r['id']} — {_fmt_local(local, user_languages.get(uid,'ru'))} — {r['text']}")

    # Клавиатура: по строке «Удалить #id» на каждый пункт + внизу «Добавить»
    kb_rows = []
    for r in rows:
        kb_rows.append([
            InlineKeyboardButton(f"{t['btn_delete']} #{r['id']}", callback_data=f"rem:del:{r['id']}")
        ])
    kb_rows.append([InlineKeyboardButton(t["btn_new"], callback_data="rem:new")])

    await update.message.reply_text(
        t["list_title"] + "\n\n" + "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(kb_rows)
    )
    
# ========== Callbacks (snooze / delete) ==========

async def remind_callback(update, context: ContextTypes.DEFAULT_TYPE):
    # ✅ гарантируем схему БД перед любыми SELECT/UPDATE
    ensure_remind_db()

    q = update.callback_query
    if not q or not q.data or not q.data.startswith("rem:"):
        return
    await q.answer()

    parts = q.data.split(":")
    action = parts[1] if len(parts) > 1 else None

    # ---- Меню: Создать новое напоминание
    if action == "new":
        uid = str(q.from_user.id)
        t = _i18n(uid)
        await context.bot.send_message(
            chat_id=int(uid),
            text="⏰ " + t["create_help"] + "\n\n" + t["usage"],
            parse_mode="Markdown",
        )
        return

    # ---- Меню: Показать список
    if action == "list":
        uid = str(q.from_user.id)
        tdict = _i18n(uid)
        tz_user = _user_tz(uid)
        try:
            with remind_db() as db:
                rows = db.execute(
                    "SELECT * FROM reminders WHERE user_id=? AND status='scheduled' "
                    "ORDER BY due_utc ASC LIMIT 50;",
                    (uid,)
                ).fetchall()
        except sqlite3.OperationalError:
            # на всякий случай пересоздадим схему и повторим запрос
            ensure_remind_db()
            with remind_db() as db:
                rows = db.execute(
                    "SELECT * FROM reminders WHERE user_id=? AND status='scheduled' "
                    "ORDER BY due_utc ASC LIMIT 50;",
                    (uid,)
                ).fetchall()

        if not rows:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(tdict["btn_add_rem"], callback_data="rem:new")]])
            await q.edit_message_text(tdict["list_empty"], reply_markup=kb)
            return

        u_lang = user_languages.get(uid, "ru")
        lines, kb_rows = [], []
        for r in rows:
            local = _from_epoch(r["due_utc"]).astimezone(tz_user)
            lines.append(f"• #{r['id']} — {_fmt_local(local, u_lang)} — {r['text']}")
            kb_rows.append([InlineKeyboardButton(f"{tdict['btn_delete']} #{r['id']}", callback_data=f"rem:del:{r['id']}")])
        kb_rows.append([InlineKeyboardButton(tdict["btn_add_rem"], callback_data="rem:new")])

        await q.edit_message_text(
            tdict["list_title"] + "\n\n" + "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(kb_rows)
        )
        return

    # ---- Ниже нужны rem_id (для del/snooze)
    if len(parts) < 3 or not parts[2].isdigit():
        return
    rem_id = int(parts[2])

    # --- Работаем с конкретным напоминанием
    with remind_db() as db:
        row = db.execute("SELECT * FROM reminders WHERE id=?;", (rem_id,)).fetchone()
        if not row:
            try:
                await q.edit_message_text("⚠️ Reminder not found.")
            except Exception:
                pass
            return

        uid = row["user_id"]
        tz = ZoneInfo(row["tz"])
        tdict = _i18n(uid)

        if action == "del":
            db.execute("UPDATE reminders SET status='canceled' WHERE id=?;", (rem_id,))
            db.commit()

            # Перерисуем список после удаления
            rows = db.execute(
                "SELECT * FROM reminders WHERE user_id=? AND status='scheduled' ORDER BY due_utc ASC LIMIT 50;",
                (uid,)
            ).fetchall()

            try:
                if rows:
                    tz_user = _user_tz(uid)
                    u_lang = user_languages.get(uid, "ru")
                    lines, kb_rows = [], []
                    for r in rows:
                        local = _from_epoch(r["due_utc"]).astimezone(tz_user)
                        lines.append(f"• #{r['id']} — {_fmt_local(local, u_lang)} — {r['text']}")
                        kb_rows.append([InlineKeyboardButton(f"{tdict['btn_delete']} #{r['id']}", callback_data=f"rem:del:{r['id']}")])
                    kb_rows.append([InlineKeyboardButton(tdict["btn_add_rem"], callback_data="rem:new")])
                    await q.edit_message_text(
                        tdict["list_title"] + "\n\n" + "\n".join(lines),
                        reply_markup=InlineKeyboardMarkup(kb_rows)
                    )
                else:
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton(tdict["btn_add_rem"], callback_data="rem:new")]])
                    await q.edit_message_text(tdict["list_empty"], reply_markup=kb)
            except Exception:
                await context.bot.send_message(chat_id=int(uid), text=tdict["deleted"])
            return

        if action == "snooze":
            kind = parts[3] if len(parts) > 3 else "15m"
            base_local = datetime.now(tz)
            if kind == "15m":
                new_local = base_local + timedelta(minutes=15)
            elif kind == "1h":
                new_local = base_local + timedelta(hours=1)
            elif kind == "tomorrow":
                due_local = _from_epoch(row["due_utc"]).astimezone(tz)
                hh, mm = due_local.hour, due_local.minute
                new_local = (base_local + timedelta(days=1)).replace(hour=hh or 9, minute=mm or 0, second=0, microsecond=0)
            else:
                new_local = base_local + timedelta(minutes=15)

            new_local = _apply_quiet_hours(new_local)
            new_utc = new_local.astimezone(timezone.utc)
            db.execute("UPDATE reminders SET due_utc=?, status='scheduled' WHERE id=?;", (_to_epoch(new_utc), rem_id))
            db.commit()
            row = db.execute("SELECT * FROM reminders WHERE id=?;", (rem_id,)).fetchone()

    # Пересоздаём джобу и отвечаем (для snooze)
    if action == "snooze":
        await _schedule_job_for_reminder(context, row)
        loc_str = _fmt_local(_from_epoch(row["due_utc"]).astimezone(ZoneInfo(row["tz"])), user_languages.get(uid, "ru"))
        try:
            await q.edit_message_text(
                _i18n(uid)["snoozed"].format(time=loc_str, text=row["text"]),
                reply_markup=remind_keyboard(rem_id, uid)
            )
        except Exception:
            await context.bot.send_message(
                chat_id=int(uid),
                text=_i18n(uid)["snoozed"].format(time=loc_str, text=row["text"]),
                reply_markup=remind_keyboard(rem_id, uid)
            )
            
# ========== Восстановление задач при старте ==========
async def restore_reminder_jobs(job_queue):
    ensure_remind_db()
    with remind_db() as db:
        rows = db.execute("SELECT * FROM reminders WHERE status='scheduled';").fetchall()
    for r in rows:
        await _schedule_job_on(job_queue, r)
        
def _settings_lang_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [("Русский 🇷🇺","setlang_ru"),("Українська 🇺🇦","setlang_uk"),("English 🇬🇧","setlang_en")],
        [("Moldovenească 🇲🇩","setlang_md"),("Беларуская 🇧🇾","setlang_be"),("Қазақша 🇰🇿","setlang_kk")],
        [("Кыргызча 🇰🇬","setlang_kg"),("Հայերեն 🇦🇲","setlang_hy"),("ქართული 🇬🇪","setlang_ka")],
        [("Нохчийн мотт 🇷🇺","setlang_ce")],
    ]
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=cb) for t, cb in row] for row in rows])

# Если у тебя уже есть TZ_KEYBOARD_ROWS и _tz_keyboard(), лучше сделать префиксную версию,
# чтобы не пересекаться с твоим онбордингом (где используется "tz:")
def _tz_keyboard_with_prefix(prefix: str = "settz") -> InlineKeyboardMarkup:
    # Требуются твои TZ_KEYBOARD_ROWS: [[("🇺🇦 Kyiv","Europe/Kyiv"), ...], ...]
    try:
        rows = [
            [InlineKeyboardButton(text, callback_data=f"{prefix}:{code}") for (text, code) in row]
            for row in TZ_KEYBOARD_ROWS
        ]
        return InlineKeyboardMarkup(rows)
    except NameError:
        # fallback: простая клавиатура
        fallback = [
            [("🇺🇦 Kyiv","Europe/Kyiv"),("🇷🇺 Moscow","Europe/Moscow")],
            [("🇺🇸 New York","America/New_York"),("🇺🇸 Los Angeles","America/Los_Angeles")],
            [("🌐 UTC","UTC")],
        ]
        return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=f"{prefix}:{c}") for t,c in r] for r in fallback])

def _get_lang(uid: str) -> str:
    return user_languages.get(uid, "ru")

def _format_local_time_now(tz_name: str, lang: str) -> str:
    now_local = datetime.now(ZoneInfo(tz_name))
    return now_local.strftime("%-I:%M %p, %Y-%m-%d") if lang == "en" else now_local.strftime("%H:%M, %Y-%m-%d")

# /settings — шаг 1: выбрать язык
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    lang = _get_lang(uid)
    t = SETTINGS_TEXTS.get(lang, SETTINGS_TEXTS["ru"])
    await update.message.reply_text(t["choose_lang"], reply_markup=_settings_lang_keyboard())

# settings: язык выбран → шаг 2: показать клавиатуру TZ с другим префиксом
async def settings_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data.startswith("setlang_"):
        return
    await q.answer()

    uid = str(q.from_user.id)
    lang = q.data.split("_", 1)[1]
    valid = {"ru","uk","md","be","kk","kg","hy","ka","ce","en"}
    if lang not in valid:
        lang = "ru"
    user_languages[uid] = lang
    logging.info(f"⚙️ /settings: set language {uid} -> {lang}")

    t = SETTINGS_TEXTS.get(lang, SETTINGS_TEXTS["ru"])
    # Переходим к выбору TZ (префикс settz)
    try:
        await q.edit_message_text(t["choose_tz"], reply_markup=_tz_keyboard_with_prefix("settz"))
    except Exception:
        await context.bot.send_message(chat_id=int(uid), text=t["choose_tz"], reply_markup=_tz_keyboard_with_prefix("settz"))

# settings: выбран TZ → применяем и показываем «готово»
async def settings_tz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data.startswith("settz:"):
        return
    await q.answer()

    uid = str(q.from_user.id)
    lang = _get_lang(uid)
    t = SETTINGS_TEXTS.get(lang, SETTINGS_TEXTS["ru"])

    tz = q.data.split(":", 1)[1]
    try:
        _ = ZoneInfo(tz)
    except Exception:
        # если пришло что-то странное — оставим прежний или дефолт
        tz = user_timezones.get(uid, "Europe/Kyiv")

    user_timezones[uid] = tz

    # Резюме
    lang_name = t["lang_name"].get(lang, "Русский")
    local_str = _format_local_time_now(tz, lang)
    text_done = t["done"].format(lang_name=lang_name, tz=tz, local_time=local_str)

    try:
        await q.edit_message_text(text_done, parse_mode="Markdown")
    except Exception:
        await context.bot.send_message(chat_id=int(uid), text=text_done, parse_mode="Markdown")
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _get_user_tz(user_id: str) -> ZoneInfo:
    tz_name = user_timezones.get(user_id, "Europe/Kyiv")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Europe/Kyiv")

def _local_now_for(user_id: str) -> datetime:
    return _now_utc().astimezone(_get_user_tz(user_id))

def _to_dt_aware_utc(val) -> datetime | None:
    """Принимает datetime (наивный/aware) или ISO-строку — возвращает aware UTC datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            # считаем, что это UTC-наивный
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
    return None

def _hours_since(ts_any, now_utc: datetime) -> float:
    ts = _to_dt_aware_utc(ts_any)
    if not ts:
        return 1e9
    return (now_utc - ts).total_seconds() / 3600.0
    
def get_mode_prompt(mode, lang):
    return MODES.get(mode, MODES["default"]).get(lang, MODES["default"]["ru"])

openai.api_key = os.getenv("OPENAI_API_KEY")

GOALS_FILE = Path("user_goals.json")

YOUR_ID = "7775321566"  # твой ID

def _tz_keyboard(prefix: str = "tz:", include_back: bool = False, uid: str | None = None) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text, callback_data=f"{prefix}{code}") for (text, code) in row]
        for row in TZ_KEYBOARD_ROWS
    ]
    if include_back and uid is not None:
        rows.append([InlineKeyboardButton(_menu_i18n(uid)["back"], callback_data="m:nav:settings")])
    return InlineKeyboardMarkup(rows)
    
    
def _get_lang(uid: str) -> str:
    return user_languages.get(uid, "ru")

def _format_local_time_now(tz_name: str, lang: str) -> str:
    now_local = datetime.now(ZoneInfo(tz_name))
    # en → 12h, остальные → 24h
    if lang == "en":
        return now_local.strftime("%-I:%M %p, %Y-%m-%d")
    return now_local.strftime("%H:%M, %Y-%m-%d")

def _resolve_tz(arg: str) -> str | None:
    s = arg.strip().lower().replace(" ", "").replace("-", "").replace(".", "")
    if s in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[s]
    # если пользователь ввёл уже IANA (Europe/Kyiv и т.п.)
    try:
        _ = ZoneInfo(arg)
        return arg
    except Exception:
        return None

async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    lang = _get_lang(uid)
    t = TZ_TEXTS.get(lang, TZ_TEXTS["ru"])

    # без аргумента — показать клавиатуру + подсказку
    if not context.args:
        await update.message.reply_text(
            f"{t['title']}\n\n{t['hint']}",
            reply_markup=_tz_keyboard(),
            parse_mode="Markdown"
        )
        return

    tz = _resolve_tz(context.args[0])
    if not tz:
        await update.message.reply_text(
            f"{t['unknown']}\n\n{t['hint']}",
            reply_markup=_tz_keyboard(),
            parse_mode="Markdown"
        )
        return

    user_timezones[uid] = tz
    local_str = _format_local_time_now(tz, lang)
    await update.message.reply_text(
        t["saved"].format(tz=tz, local_time=local_str),
        parse_mode="Markdown"
    )

def _parse_referrer_id(ref_code: str | None) -> str | None:
    if not ref_code:
        return None
    # Поддержим 'ref123', 'ref_123', 'ref-123' и т.п. — просто достанем цифры
    digits = "".join(ch for ch in ref_code if ch.isdigit())
    return digits or None

async def tz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data:
        return
    if not (q.data.startswith("tz:") or q.data.startswith("onb:tz:")):
        return
    await q.answer()

    uid = str(q.from_user.id)
    lang = _get_lang(uid)
    t = TZ_TEXTS.get(lang, TZ_TEXTS["ru"])
    t_menu = _menu_i18n(uid)

    data = q.data
    is_onboarding = data.startswith("onb:tz:")
    # tz:<Area/City>            → ["tz", "<Area/City>"]
    # onb:tz:<Area/City>        → ["onb", "tz", "<Area/City>"]
    tz = data.split(":", 2)[2] if is_onboarding else data.split(":", 1)[1]

    # валидация
    try:
        _ = ZoneInfo(tz)
    except Exception:
        if is_onboarding:
            return await q.edit_message_text(t.get("unknown", "Unknown timezone"))
        else:
            try:
                await q.answer(t.get("unknown", "Unknown timezone"), show_alert=True)
            except Exception:
                pass
            return await show_timezone_menu(q.message, origin="settings")

    # сохраняем
    user_timezones[uid] = tz
    local_str = _format_local_time_now(tz, lang)

    if not is_onboarding:
        # ==== ВАРИАНТ: НАСТРОЙКИ (без языка и без бонусов)
        try:
            await q.answer(f"✅ {tz} · {local_str}", show_alert=False)
        except Exception:
            pass
        return await q.message.edit_text(
            t_menu.get("set_title", t_menu["settings"]),
            reply_markup=_menu_kb_settings(uid),
            parse_mode="Markdown",
        )

    # ==== ВАРИАНТ: ОНБОРДИНГ (с бонусами/рефералом/приветствием)
    try:
        try:
            await q.edit_message_text(
                t["saved"].format(tz=tz, local_time=local_str),
                parse_mode="Markdown"
            )
        except BadRequest:
            await context.bot.send_message(
                chat_id=int(uid),
                text=t["saved"].format(tz=tz, local_time=local_str),
                parse_mode="Markdown"
            )

        # 1) Реферал
        referrer_id = user_ref_args.pop(uid, None)
        if referrer_id and referrer_id != uid:
            try:
                if process_referral(referrer_id, uid, days=7):
                    bonus_text = REFERRAL_BONUS_TEXT.get(lang, REFERRAL_BONUS_TEXT["ru"])
                    await context.bot.send_message(chat_id=int(uid), text=bonus_text, parse_mode="Markdown")
                    try:
                        await context.bot.send_message(
                            chat_id=int(referrer_id),
                            text=REFERRER_NOTIFY_TEXT.get(lang, REFERRER_NOTIFY_TEXT["ru"]),
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
            except Exception as e:
                logging.warning("process_referral failed: %s", e)

        # 2) Триал
        try:
            granted_until_iso = grant_trial_if_eligible(uid, days=3)
            if granted_until_iso:
                txt = TRIAL_INFO_TEXT.get(lang, TRIAL_INFO_TEXT["ru"]).format(until=granted_until_iso)
                await context.bot.send_message(chat_id=int(uid), text=txt, parse_mode="Markdown")
        except Exception as e:
            logging.warning("Trial grant failed: %s", e)

        # 3) Инициализация system prompt/истории
        try:
            mode = "support"
            lang_prompt = LANG_PROMPTS.get(lang, LANG_PROMPTS["ru"])
            mode_prompt = MODES[mode].get(lang, MODES[mode]['ru'])
            system_prompt = f"{lang_prompt}\n\n{mode_prompt}"
            conversation_history[uid] = [{"role": "system", "content": system_prompt}]
            save_history(conversation_history)
        except Exception as e:
            logging.warning("history init failed: %s", e)

        # 4) Welcome
        first_name = q.from_user.first_name or {"ru":"друг","uk":"друже","en":"friend"}.get(lang, "друг")
        welcome_text = WELCOME_TEXTS.get(lang, WELCOME_TEXTS["ru"]).format(first_name=first_name)
        await context.bot.send_message(chat_id=int(uid), text=welcome_text, parse_mode="Markdown")

    except Exception as e:
        logging.exception(f"onboarding finalize error: {e}")

async def show_timezone_menu(msg, origin: str = "settings"):
    uid = str(msg.chat.id)
    t = SETTINGS_TEXTS.get(user_languages.get(uid, "ru"), SETTINGS_TEXTS["ru"])
    prefix = "onb:tz:" if origin == "onboarding" else "tz:"
    include_back = (origin == "settings")
    await msg.edit_text(
        t.get("choose_tz", "🌍 Укажи свой часовой пояс:"),
        reply_markup=_tz_keyboard(prefix=prefix, include_back=include_back, uid=uid),
        parse_mode="Markdown",
    )

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = str(update.effective_user.id)
    lang = user_languages.get(uid, "ru")

    points = get_user_points(uid)
    title  = get_user_title(points, lang)
    next_title, to_next = get_next_title_info(points, lang)  # ← как ты и писал
    ladder = build_titles_ladder(lang)

    text = POINTS_HELP_TEXTS.get(lang, POINTS_HELP_TEXTS["ru"]).format(
        points=points,
        title=title,
        next_title=next_title,
        to_next=to_next,
        ladder=ladder,
    )
    await ui_show_from_command(update, context, text, reply_markup=_kb_back_home(uid), parse_mode="Markdown")

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

async def language_callback(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("lang_"):
        return
    await q.answer()
    context.user_data[UI_MSG_KEY] = q.message.message_id

    uid = str(q.from_user.id)
    code = q.data.split("_", 1)[1]
    user_languages[uid] = code

    # тост
    name = SETTINGS_TEXTS["ru"]["lang_name"].get(code, code)
    try:
        await q.answer(f"✅ {name}", show_alert=False)
    except Exception:
        pass

    # 🔹 онбординг: сразу перейти к выбору таймзоны (кнопки onb:tz:...)
    if context.user_data.pop("onb_waiting_lang", None):
        return await show_timezone_menu(q.message, origin="onboarding")

    # 🔹 обычные настройки: вернуться в экран «Настройки»
    t = _menu_i18n(uid)
    return await q.message.edit_text(
        t.get("set_title", t["settings"]),
        reply_markup=_menu_kb_settings(uid),
        parse_mode="Markdown",
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

    now_utc = _now_utc()
    logging.info("⏰ Проверка неактивных пользователей...")

    for user_id, last_seen_any in list(user_last_seen.items()):
        uid = str(user_id)
        local_now = _local_now_for(uid)

        # 1) Интервал между idle‑напоминаниями
        last_prompted_any = user_last_prompted.get(uid)
        if _hours_since(last_prompted_any, now_utc) < MIN_IDLE_HOURS:
            continue

        # 2) Неактивен минимум 6 часов
        if _hours_since(last_seen_any, now_utc) < 6:
            continue

        # 3) Дневное окно
        if not (IDLE_TIME_START <= local_now.hour < IDLE_TIME_END):
            continue

        try:
            lang = user_languages.get(uid, "ru")
            idle_messages = IDLE_MESSAGES.get(lang, IDLE_MESSAGES["ru"])
            message = random.choice(idle_messages)
            await app.bot.send_message(chat_id=int(uid), text=message)
            user_last_prompted[uid] = now_utc.isoformat()
            logging.info(f"📨 Idle-напоминание отправлено {uid} ({lang})")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке idle-сообщения {uid}: {e}")

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
    now_utc = _now_utc()

    for user_id in list(user_last_seen.keys()):
        uid = str(user_id)
        local_now = _local_now_for(uid)

        # Утреннее окно
        if not (DAILY_MIN_HOUR <= local_now.hour < DAILY_MAX_HOUR):
            continue

        # Уже отправляли сегодня?
        if user_last_daily_sent.get(uid) == local_now.date().isoformat():
            continue

        # Не отправлять, если активен в последние 8 часов
        if _hours_since(user_last_seen.get(uid), now_utc) < 8:
            continue

        try:
            lang = user_languages.get(uid, "ru")
            greeting = random.choice(MORNING_MESSAGES_BY_LANG.get(lang, MORNING_MESSAGES_BY_LANG["ru"]))
            task = random.choice(DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG["ru"]))
            text = f"{greeting}\n\n🎯 {task}"

            await context.bot.send_message(chat_id=int(uid), text=text)
            user_last_daily_sent[uid] = local_now.date().isoformat()
            logging.info(f"✅ Утреннее задание отправлено {uid} ({lang})")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке утреннего задания {uid}: {e}")

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
    uid = str(update.effective_user.id)
    logging.info(f"/start: user_id={uid}, args={context.args}, text={update.message.text}")

    # 1) Сохраняем реф-пейлоад из deep-link (/start ref_XXXX)
    ref_payload = None
    if context.args:
        a0 = context.args[0]
        if isinstance(a0, str):
            if a0.startswith("ref_"):
                ref_payload = a0[4:]
            elif a0.startswith("ref"):
                ref_payload = a0[3:]
    if ref_payload:
        # используем позже в tz_callback (только для on-boarding)
        user_ref_args[uid] = ref_payload

    # 2) Если язык ещё не выбран — показываем выбор ЯЗЫКА и выходим
    if uid not in user_languages:
        context.user_data["onb_waiting_lang"] = True  # флаг онбординга для language_callback
        keyboard = [
            [InlineKeyboardButton("Русский 🇷🇺",       callback_data="lang_ru"),
             InlineKeyboardButton("Українська 🇺🇦",    callback_data="lang_uk")],
            [InlineKeyboardButton("Moldovenească 🇲🇩", callback_data="lang_md"),
             InlineKeyboardButton("Беларуская 🇧🇾",    callback_data="lang_be")],
            [InlineKeyboardButton("Қазақша 🇰🇿",       callback_data="lang_kk"),
             InlineKeyboardButton("Кыргызча 🇰🇬",      callback_data="lang_kg")],
            [InlineKeyboardButton("Հայերեն 🇦🇲",       callback_data="lang_hy"),
             InlineKeyboardButton("ქართული 🇬🇪",       callback_data="lang_ka")],
            [InlineKeyboardButton("Нохчийн мотт 🏴",   callback_data="lang_ce"),
             InlineKeyboardButton("English 🇬🇧",       callback_data="lang_en")],
        ]
        # текст берём из твоих SETTINGS_TEXTS (если есть), иначе дефолт
        choose_lang = SETTINGS_TEXTS.get("ru", {}).get(
            "choose_lang", "🌐 Please select the language of communication:"
        )
        sent = await update.message.reply_text(
            choose_lang,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        context.user_data[UI_MSG_KEY] = sent.message_id  # дальше будем редачить это сообщение
        return

    # 3) Если язык выбран, но TZ ещё нет — открываем TZ в режиме онбординга
    if uid not in user_timezones:
        # покажем экран таймзоны, кнопки с префиксом onb:tz:...
        context.user_data["onb_waiting_tz"] = True
        # эта функция должна внутри вызвать _tz_keyboard(prefix="onb:tz:", include_back=False)
        return await show_timezone_menu(update.message, origin="onboarding")

    # 4) Оба параметра уже есть → показываем главное меню в одном UI-сообщении
    await ui_show_from_command(
        update, context,
        _menu_home_text(uid),
        reply_markup=_menu_kb_home(uid),
        parse_mode="Markdown",
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    if user_id in conversation_history:
        del conversation_history[user_id]
        save_history(conversation_history)
    await update.message.reply_text(RESET_TEXTS.get(lang, RESET_TEXTS["ru"]))

async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    lang = user_languages.get(uid, "ru")
    t = MODE_TEXTS.get(lang, MODE_TEXTS["ru"])
    await ui_show_from_command(update, context, t["text"], reply_markup=_mode_keyboard(uid))


def _mode_keyboard(uid: str) -> InlineKeyboardMarkup:
    lang = user_languages.get(uid, "ru")
    t_mode = MODE_TEXTS.get(lang, MODE_TEXTS["ru"])
    t_menu = MENU_TEXTS.get(lang, MENU_TEXTS["ru"])  # чтобы взять локализованный "Назад"

    keyboard = [
        [InlineKeyboardButton(t_mode["support"],    callback_data="mode_support")],
        [InlineKeyboardButton(t_mode["motivation"], callback_data="mode_motivation")],
        [InlineKeyboardButton(t_mode["philosophy"], callback_data="mode_philosophy")],
        [InlineKeyboardButton(t_mode["humor"],      callback_data="mode_humor")],
        [InlineKeyboardButton(t_menu["back"],       callback_data="m:nav:home")],  # ⬅️ Назад в главное меню
    ]
    return InlineKeyboardMarkup(keyboard)

async def mode_menu_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    msg = q.message
    uid = str(q.from_user.id)
    lang = user_languages.get(uid, "ru")
    t = MODE_TEXTS.get(lang, MODE_TEXTS["ru"])
    await msg.edit_text(t["text"], reply_markup=_mode_keyboard(uid))

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

    # 🕒 активность
    user_last_seen[user_id_int] = datetime.now(timezone.utc)
    logging.info(f"✅ user_last_seen обновлён в chat для {user_id_int}")

    # 🔥 дневной учёт сообщений (сброс по дню)
    today = str(date.today())
    if user_id not in user_message_count:
        user_message_count[user_id] = {"date": today, "count": 0}
    elif user_message_count[user_id]["date"] != today:
        user_message_count[user_id] = {"date": today, "count": 0}

    # 📈 динамический лимит по тарифу
    try:
        cap = quota(user_id, "daily_messages")
    except Exception:
        cap = 10  # безопасный дефолт

    # ⛔ блок, если не владелец/админ и лимит достигнут
    if (user_id_int not in ADMIN_USER_IDS) and (user_id_int != OWNER_ID):
        if user_message_count[user_id]["count"] >= cap:
            try:
                title, body = upsell_for(user_id, "feature_quota_msg", {"n": cap})
                await update.message.reply_text(f"*{title}*\n\n{body}", parse_mode="Markdown")
            except Exception:
                # фолбэк, если upsell_for ещё не подключён
                lang = user_languages.get(user_id, "ru")
                lock_msg = LOCK_MESSAGES_BY_LANG.get(lang, LOCK_MESSAGES_BY_LANG["ru"])
                try:
                    await update.message.reply_text(lock_msg.format(n=cap))
                except Exception:
                    await update.message.reply_text(lock_msg)
            return

    # +1 к счётчику (после проверки лимита)
    user_message_count[user_id]["count"] += 1

    # 📌 текст пользователя
    user_input = (update.message.text or "").strip()
    if not user_input:
        return

    # 🌐 язык и режим
    lang_code = user_languages.get(user_id, "ru")

    # ——— РАННИЙ ПЕРЕХВАТ ЗАПРОСА СКАЗКИ ———
    try:
        if _looks_like_story_intent(user_input, lang_code, user_id):
            if is_premium(user_id):
                topic_guess = user_input
                context.chat_data[f"story_pending_{user_id}"] = topic_guess[:200]
                t = _s_i18n(user_id)
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(t["btn_ok"],  callback_data="st:confirm"),
                    InlineKeyboardButton(t["btn_no"],  callback_data="st:close"),
                ]])
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=t["suggest"],
                    reply_markup=kb
                )
            else:
                tpay = _p_i18n(user_id)
                await update.message.reply_text(
                    f"*{tpay['upsell_title']}*\n\n{tpay['upsell_body']}",
                    parse_mode="Markdown",
                    reply_markup=_premium_kb(user_id)
                )
            return  # 👈 не уходим в LLM, чтобы он не написал сказку сам
    except Exception as e:
        logging.warning(f"Story intercept failed: {e}")

    # ——— Обычный ответ ассистента ———
    lang_prompt = LANG_PROMPTS.get(lang_code, LANG_PROMPTS["ru"])
    mode = user_modes.get(user_id, "support")
    mode_prompt = MODES.get(mode, MODES["support"]).get(lang_code, MODES["support"]["ru"])

    guard = {
        "ru": "Если пользователь просит сказку/историю на ночь — не пиши сам рассказ в этом режиме. Ответь коротко и предложи кнопки «Сказка».",
        "uk": "Якщо користувач просить казку — не пиши сам текст у цьому режимі. Коротко відповідай і запропонуй кнопку «Казка».",
        "en": "If the user asks for a bedtime story, do not write the full story here. Reply briefly and suggest the Story button."
    }.get(lang_code, "Если пользователь просит сказку — не пиши её здесь; предложи кнопки «Сказка».")
    system_prompt = f"{lang_prompt}\n\n{mode_prompt}\n\n{guard}"

    # 💾 история
    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": system_prompt}]
    else:
        conversation_history[user_id][0] = {"role": "system", "content": system_prompt}

    conversation_history[user_id].append({"role": "user", "content": user_input})
    trimmed_history = trim_history(conversation_history[user_id])

    try:
        # ✨ “печатает…”
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        # 🤖 LLM-ответ
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=trimmed_history
        )
        reply = (resp.choices[0].message.content or "").strip() or "…"

        # сохранить в историю
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        save_history(conversation_history)

        # 💜 эмпатичный префикс
        reaction = detect_emotion_reaction(user_input, lang_code) + detect_topic_and_react(user_input, lang_code)
        final_text = reaction + reply

        # 📝 ответ текстом
        await update.message.reply_text(
            final_text,
            reply_markup=generate_post_response_buttons()
        )

        # 🔊 озвучка (premium + включён voice_mode)
        if is_premium(user_id) and user_voice_mode.get(user_id, False):
            await send_voice_response(context, user_id_int, final_text, lang_code)

    except Exception as e:
        logging.error(f"❌ Ошибка в chat(): {e}")
        await update.message.reply_text(
            ERROR_MESSAGES_BY_LANG.get(lang_code, ERROR_MESSAGES_BY_LANG["ru"])
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    help_text = help_texts.get(lang, help_texts["ru"])
    b = buttons_text.get(lang, buttons_text["ru"])

    keyboard = [
        [InlineKeyboardButton(b[0], callback_data="create_goal")],
        [InlineKeyboardButton(b[1], callback_data="show_goals")],
        [InlineKeyboardButton(b[2], callback_data="create_habit")],
        [InlineKeyboardButton(b[3], callback_data="show_habits")],
        [InlineKeyboardButton(b[4], url="https://t.me/talktomindra_bot")],
    ]
    await update.message.reply_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard))

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

async def send_evening_checkin(context: ContextTypes.DEFAULT_TYPE):
    now_utc = _now_utc()

    for user_id in list(user_last_seen.keys()):
        uid = str(user_id)
        local_now = _local_now_for(uid)

        # Окно «вечер»: например, 18–22 по локальному (можешь вынести в константы)
        if not (18 <= local_now.hour < 22):
            continue

        # Не писать тем, кто активен последние 3 часа
        if _hours_since(user_last_seen.get(uid), now_utc) < 3:
            continue

        # Одно сообщение в сутки
        last_evening = user_last_evening.get(uid)
        if _hours_since(last_evening, now_utc) < 24 and last_evening and \
           last_evening.astimezone(_get_user_tz(uid)).date() == local_now.date():
            continue

        # Рандомизация
        if random.random() > 0.7:
            continue

        try:
            lang = user_languages.get(uid, "ru")
            msg = random.choice(EVENING_MESSAGES_BY_LANG.get(lang, EVENING_MESSAGES_BY_LANG["ru"]))
            await context.bot.send_message(chat_id=int(uid), text=msg)
            user_last_evening[uid] = now_utc
        except Exception as e:
            logging.error(f"❌ Не удалось отправить вечернее сообщение {uid}: {e}")


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

async def send_random_support(context: ContextTypes.DEFAULT_TYPE):
    global user_last_support, user_support_daily_count, user_support_daily_date
    global user_last_seen, user_languages, user_timezones

    now_utc = _now_utc()

    # Кого знаем — тем и шлём (подставь свой источник, если у тебя иначе)
    candidate_user_ids = list(user_last_seen.keys())

    for user_id in candidate_user_ids:
        # 0) не трогаем, если был активен последние N часов
        last_seen = user_last_seen.get(user_id)
        if _hours_since(last_seen, now_utc) < MIN_HOURS_SINCE_ACTIVE:
            continue

        # 1) локальное окно времени
        local_now = _local_now_for(user_id)
        if not (SUPPORT_WINDOW_START <= local_now.hour < SUPPORT_WINDOW_END):
            continue

        # 2) дневной лимит по ЛОКАЛЬНОЙ дате пользователя
        local_date_str = local_now.date().isoformat()
        if user_support_daily_date.get(user_id) != local_date_str:
            user_support_daily_date[user_id] = local_date_str
            user_support_daily_count[user_id] = 0

        if user_support_daily_count[user_id] >= SUPPORT_MAX_PER_DAY:
            continue

        # 3) пауза между сообщениями (UTC-aware)
        last_support = user_last_support.get(user_id)
        if _hours_since(last_support, now_utc) < SUPPORT_MIN_HOURS_BETWEEN:
            continue

        # 4) рандом (смягчаем частоту)
        if random.random() > SUPPORT_RANDOM_CHANCE:
            continue

        # 5) отправка
        try:
            lang = user_languages.get(user_id, "ru")
            msg = random.choice(SUPPORT_MESSAGES_BY_LANG.get(lang, SUPPORT_MESSAGES_BY_LANG["ru"]))
            await context.bot.send_message(chat_id=int(user_id), text=msg)

            user_last_support[user_id] = now_utc         # сохраняем aware UTC
            user_support_daily_count[user_id] += 1

            logging.info(f"✅ Support sent to {user_id} ({lang}) at {local_now.isoformat()}")
        except Exception as e:
            logging.exception(f"❌ Support send failed for {user_id}: {e}")

async def send_random_poll(context: ContextTypes.DEFAULT_TYPE):
    now_utc = _now_utc()

    for user_id in list(user_last_seen.keys()):
        uid = str(user_id)

        # Не спамим часто
        if _hours_since(user_last_polled.get(uid), now_utc) < MIN_HOURS_SINCE_LAST_POLL:
            continue

        # Не трогаем активных за последние N часов
        if _hours_since(user_last_seen.get(uid), now_utc) < MIN_HOURS_SINCE_ACTIVE:
            continue

        # Рандом
        if random.random() > POLL_RANDOM_CHANCE:
            continue

        try:
            lang = user_languages.get(uid, "ru")
            poll = random.choice(POLL_MESSAGES_BY_LANG.get(lang, POLL_MESSAGES_BY_LANG["ru"]))
            await context.bot.send_message(chat_id=int(uid), text=poll)
            user_last_polled[uid] = now_utc
            logging.info(f"✅ Опрос отправлен {uid}")
        except Exception as e:
            logging.error(f"❌ Ошибка отправки опроса {uid}: {e}")

async def send_daily_task(context: ContextTypes.DEFAULT_TYPE):
    now_utc = _now_utc()

    for user_id in list(user_last_seen.keys()):
        uid = str(user_id)
        local_now = _local_now_for(uid)

        # окно утром (используем существующие DAILY_MIN_HOUR/DAILY_MAX_HOUR)
        if not (DAILY_MIN_HOUR <= local_now.hour < DAILY_MAX_HOUR):
            continue

        # Не чаще, чем раз в MIN_HOURS_SINCE_LAST_MORNING_TASK
        last_prompted = user_last_prompted.get(f"{uid}_morning_task")
        if _hours_since(last_prompted, now_utc) < MIN_HOURS_SINCE_LAST_MORNING_TASK:
            continue

        # Не отправлять, если был активен последний час
        last_seen = user_last_seen.get(uid)
        if _hours_since(last_seen, now_utc) < 1:
            continue

        try:
            lang = user_languages.get(uid, "ru")
            greetings = MORNING_MESSAGES_BY_LANG.get(lang, MORNING_MESSAGES_BY_LANG["ru"])
            tasks = DAILY_TASKS_BY_LANG.get(lang, DAILY_TASKS_BY_LANG["ru"])
            text = f"{random.choice(greetings)}\n\n🎯 {random.choice(tasks)}"

            await context.bot.send_message(chat_id=int(uid), text=text)
            user_last_prompted[f"{uid}_morning_task"] = now_utc.isoformat()
            logging.info(f"✅ Утреннее задание отправлено {uid} ({lang})")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке утреннего задания {uid}: {e}")

async def mypoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = str(update.effective_user.id)
    lang = user_languages.get(uid, "ru")
    stats = get_user_stats(uid)
    points = stats.get("points", 0)
    completed = stats.get("goals_completed", 0)

    TEXTS = {
        "ru":  "🌟 *Твоя статистика:*\n\n✨ Очки: {p}\n🎯 Выполнено целей: {c}",
        "en":  "🌟 *Your Stats:*\n\n✨ Points: {p}\n🎯 Goals completed: {c}",
        "uk":  "🌟 *Твоя статистика:*\n\n✨ Бали: {p}\n🎯 Виконано цілей: {c}",
        "be":  "🌟 *Твая статыстыка:*\n\n✨ Балы: {p}\n🎯 Выканана мэт: {c}",
        "kk":  "🌟 *Сенің статистикаң:*\n\n✨ Ұпайлар: {p}\n🎯 Орындалған мақсаттар: {c}",
        "kg":  "🌟 *Сенин статистикаң:*\n\n✨ Упайлар: {p}\n🎯 Аткарылган максаттар: {c}",
        "hy":  "🌟 *Քո վիճակագրությունը:*\n\n✨ Միավորներ: {p}\n🎯 Կատարված նպատակներ: {c}",
        "ce":  "🌟 *Хьо статистика:*\n\n✨ Баллар: {p}\n🎯 Хийцар мацахь: {c}",
        "md":  "🌟 *Statistica ta:*\n\n✨ Puncte: {p}\n🎯 Obiective realizate: {c}",
        "ka":  "🌟 *შენი სტატისტიკა:*\n\n✨ ქულები: {p}\n🎯 შესრულებული მიზნები: {c}",
    }
    text = TEXTS.get(lang, TEXTS["ru"]).format(p=points, c=completed)
    await ui_show_from_command(update, context, text, reply_markup=_kb_back_home(uid), parse_mode="Markdown")


async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    # фильтр по Киеву
    now_kiev = _now_utc().astimezone(ZoneInfo("Europe/Kyiv"))
    if not (REPORT_MIN_HOUR <= now_kiev.hour < REPORT_MAX_HOUR):
        return

    for raw_uid in PREMIUM_USERS:
        uid = str(raw_uid)
        try:
            # Уже отправляли сегодня?
            if user_last_report_sent.get(uid) == now_kiev.date().isoformat():
                continue

            lang = user_languages.get(uid, "ru")
            report_texts = {  # (оставил как есть, только используем ниже)
                "ru": ("📊 *Твой недельный отчёт Mindra+* 💜\n\n"
                       "✅ Выполнено целей: *{goals}*\n"
                       "🌱 Отмечено привычек: *{habits}*\n\n"
                       "✨ Так держать! Я горжусь тобой 💪💜"),
                "uk": ("📊 *Твій тижневий звіт Mindra+* 💜\n\n"
                       "✅ Виконано цілей: *{goals}*\n"
                       "🌱 Відмічено звичок: *{habits}*\n\n"
                       "✨ Так тримати! Я пишаюсь тобою 💪💜"),
                "en": ("📊 *Your weekly Mindra+ report* 💜\n\n"
                       "✅ Goals completed: *{goals}*\n"
                       "🌱 Habits tracked: *{habits}*\n\n"
                       "✨ Keep it up! I'm proud of you 💪💜"),
                "be": ("📊 *Твой тыднёвы справаздача Mindra+* 💜\n\n"
                       "✅ Выканана мэт: *{goals}*\n"
                       "🌱 Адзначана звычак: *{habits}*\n\n"
                       "✨ Так трымаць! Я ганаруся табой 💪💜"),
                "kk": ("📊 *Сенің Mindra+ апталық есебің* 💜\n\n"
                       "✅ Орындалған мақсаттар: *{goals}*\n"
                       "🌱 Белгіленген әдеттер: *{habits}*\n\n"
                       "✨ Осылай жалғастыр! Мен сені мақтан тұтамын 💪💜"),
                "kg": ("📊 *Сенин Mindra+ апталык отчётуң* 💜\n\n"
                       "✅ Аткарылган максаттар: *{goals}*\n"
                       "🌱 Белгиленген адаттар: *{habits}*\n\n"
                       "✨ Ошентип улант! Мен сени сыймыктанам 💪💜"),
                "hy": ("📊 *Քո Mindra+ շաբաթական հաշվետվությունը* 💜\n\n"
                       "✅ Կատարված նպատակներ: *{goals}*\n"
                       "🌱 Նշված սովորություններ: *{habits}*\n\n"
                       "✨ Շարունակիր այսպես! Հպարտանում եմ քեզանով 💪💜"),
                "ce": ("📊 *ДогӀа Mindra+ нан неделю отчет* 💜\n\n"
                       "✅ Кхоллар мацахь: *{goals}*\n"
                       "🌱 Хийна хетам: *{habits}*\n\n"
                       "✨ Дехар цуьнан! Со цуьнан делла йойла хьо 💪💜"),
                "md": ("📊 *Raportul tău săptămânal Mindra+* 💜\n\n"
                       "✅ Obiective îndeplinite: *{goals}*\n"
                       "🌱 Obiceiuri marcate: *{habits}*\n\n"
                       "✨ Ține-o tot așa! Sunt mândru de tine 💪💜"),
                "ka": ("📊 *შენი Mindra+ ყოველკვირეული ანგარიში* 💜\n\n"
                       "✅ შესრულებული მიზნები: *{goals}*\n"
                       "🌱 მონიშნული ჩვევები: *{habits}*\n\n"
                       "✨ გააგრძელე ასე! მე ვამაყობ შენით 💪💜"),
            }

            goals = get_goals(uid)                        # твоя функция
            completed_goals = [g for g in goals if g.get("done")]
            try:
                habits = get_habits(uid)                  # твоя функция
                completed_habits = len(habits)
            except Exception:
                completed_habits = 0

            text = report_texts.get(lang, report_texts["ru"]).format(
                goals=len(completed_goals),
                habits=completed_habits
            )
            await context.bot.send_message(
                chat_id=int(uid),
                text=text,
                parse_mode="Markdown"
            )
            user_last_report_sent[uid] = now_kiev.date().isoformat()
            logging.info(f"✅ Еженедельный отчёт отправлен {uid}")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке отчёта {uid}: {e}")
        
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

def give_trial_if_needed(user_id: str | int, days: int = 3) -> str | None:
    """
    Выдаёт триал, если ещё не выдавали. Возвращает ISO until или None.
    Использует SQLite (extend_premium_days) + ваши got_trial/set_trial.
    """
    try:
        # если уже был триал — не выдаём повторно
        if got_trial(user_id):
            return None

        # продлеваем/назначаем премиум на days
        until_iso = extend_premium_days(user_id, days)

        # помечаем, что триал выдан (ваша старая функция/флаг)
        set_trial(user_id)

        logging.info(f"🎁 Trial: user {user_id} -> +{days} days (until {until_iso})")
        return until_iso
    except Exception as e:
        logging.exception(f"give_trial_if_needed failed: {e}")
        return None


def handle_referral(user_id: str | int, referrer_id: str | int, days: int = 7) -> bool:
    """
    Начисляет реферальный бонус +days дня обоим (использует SQLite).
    Возвращает True, если бонусы выданы.
    """
    try:
        u = str(user_id)
        r = str(referrer_id)

        # нельзя пригласить самого себя
        if not r or r == u:
            return False

        # если есть ваша защита от повторов — проверьте тут (опционально):
        # if already_referred(u): return False

        # оба получают +days (наращиваем к текущему, если уже есть)
        u_until = extend_premium_days(u, days)
        r_until = extend_premium_days(r, days)

        # триальный флаг (ок: отметим получателя; рефереру можно не ставить)
        try:
            if not got_trial(u):
                set_trial(u)
        except Exception:
            pass

        # ваша аналитика/лог
        try:
            add_referral(u, r)
        except Exception:
            pass

        logging.info(f"👥 Referral: {u} via {r} -> +{days} days each (u:{u_until}, r:{r_until})")
        return True
    except Exception as e:
        logging.exception(f"handle_referral failed: {e}")
        return False


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    lang = user_languages.get(uid, "ru")

    # Надёжно получаем username бота для диплинка
    try:
        me = await context.bot.get_me()
        username = me.username or "talktomindra_bot"
    except Exception:
        username = "talktomindra_bot"  # запасной вариант

    # Рекомендуемый формат payload: ref_<inviter_id>
    invite_link = f"https://t.me/{username}?start=ref_{uid}"

    # Шаблоны с плейсхолдером {link}, подставим ниже
    INVITE_TEMPLATES = {
        "ru": (
            "🎁 Пригласи друга и вы оба получите +7 дней Mindra+!\n\n"
            "1️⃣ Отправь эту ссылку другу в Telegram:\n"
            "{link}\n\n"
            "2️⃣ Как только он запустит бота по этой ссылке, вам обоим автоматически начислится +7 дней Mindra+! 🟣"
        ),
        "uk": (
            "🎁 Запроси друга — і ви обидва отримаєте +7 днів Mindra+!\n\n"
            "1️⃣ Надішли це посилання другові в Telegram:\n"
            "{link}\n\n"
            "2️⃣ Щойно він запустить бота за цим посиланням, вам обом автоматично нарахується +7 днів Mindra+! 🟣"
        ),
        "be": (
            "🎁 Запрасі сябра — і вы абодва атрымаеце +7 дзён Mindra+!\n\n"
            "1️⃣ Дашлі яму гэтую спасылку ў Telegram:\n"
            "{link}\n\n"
            "2️⃣ Калі ён запусціць бота па спасылцы, вам абодвум аўтаматычна налічыцца +7 дзён Mindra+! 🟣"
        ),
        "kk": (
            "🎁 Осы сілтемемен досыңды шақыр — екеуің де +7 күн Mindra+ аласыңдар!\n\n"
            "1️⃣ Telegram арқылы мына сілтемені жібер:\n"
            "{link}\n\n"
            "2️⃣ Ол ботты осы сілтеме арқылы іске қосқанда, екеуіңе де автоматты түрде +7 күн Mindra+ қосылады! 🟣"
        ),
        "kg": (
            "🎁 Бул шилтеме менен досуңду чакыр — экөөңөр тең +7 күн Mindra+ аласыңар!\n\n"
            "1️⃣ Бул шилтемени Telegram аркылуу жөнөт:\n"
            "{link}\n\n"
            "2️⃣ Досуң ушул шилтеме менен ботту иштетсе, экөөңөргө тең автоматтык түрдө +7 күн Mindra+ берилет! 🟣"
        ),
        "hy": (
            "🎁 Հրավիրիր ընկերոջդ այս հղումով և երկուսդ էլ կստանաք +7 օր Mindra+!\n\n"
            "1️⃣ Ուղարկիր այս հղումը ընկերոջդ Telegram-ով.\n"
            "{link}\n\n"
            "2️⃣ Երբ նա այս հղումով բացի բոտը, դուք երկուսդ էլ ավտոմատ կստանաք +7 օր Mindra+! 🟣"
        ),
        "ce": (
            "🎁 ДӀасан сылкъе йу ду цуьнан дош ю — тхо ахкаранна +7 берим Mindra+ дац!\n\n"
            "1️⃣ Сылкъе догхьа ду Telegram чураш:\n"
            "{link}\n\n"
            "2️⃣ Цуьнан бота хьалха йиш йолу цу сылкъе, тхо а автоматика йу +7 берим Mindra+ дац! 🟣"
        ),
        "md": (
            "🎁 Invită un prieten cu acest link și primiți amândoi +7 zile de Mindra+!\n\n"
            "1️⃣ Trimite-i acest link pe Telegram:\n"
            "{link}\n\n"
            "2️⃣ De îndată ce pornește botul cu acest link, amândoi primiți automat +7 zile de Mindra+! 🟣"
        ),
        "ka": (
            "🎁 მოიწვიე მეგობარი ამ ბმულით და ორივემ მიიღეთ +7 დღე Mindra+!\n\n"
            "1️⃣ გაუგზავნე ეს ბმული Telegram-ში:\n"
            "{link}\n\n"
            "2️⃣ როგორც კი ის ბოტს ამ ბმულით გახსნის, თქვენ ორსაც ავტომატურად დაერიცხებათ +7 დღე Mindra+! 🟣"
        ),
        "en": (
            "🎁 Invite a friend and you both get +7 days of Mindra+!\n\n"
            "1️⃣ Send this link to your friend on Telegram:\n"
            "{link}\n\n"
            "2️⃣ As soon as they start the bot via this link, you both automatically receive +7 days of Mindra+! 🟣"
        ),
    }

    text = INVITE_TEMPLATES.get(lang, INVITE_TEMPLATES["ru"]).format(link=invite_link)

    await update.message.reply_text(text, disable_web_page_preview=True)
    
def plural_ru(number, one, few, many):
    # Склонение для русского языка (можно добавить и для других, если нужно)
    n = abs(number)
    if n % 10 == 1 and n % 100 != 11:
        return one
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return few
    else:
        return many

async def premium_days(update, context):
    uid = str(update.effective_user.id)
    args = context.args or []

    def _is_admin() -> bool:
        return (update.effective_user.id in ADMIN_USER_IDS) or (update.effective_user.id == OWNER_ID)

    try:
        # /premium_days  — показать себе
        if len(args) == 0:
            until = get_premium_until(uid)
            if not until:
                return await update.message.reply_text("У тебя сейчас нет премиума.")
            try:
                dt = datetime.fromisoformat(until)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)
            left_days = max(0, int((dt - datetime.now(timezone.utc)).total_seconds() // 86400))
            return await update.message.reply_text(
                f"Премиум до: {dt.isoformat()}\nОсталось дней: {left_days}"
            )

        # /premium_days <days> — продлить СЕБЕ (только админ)
        elif len(args) == 1:
            if not _is_admin():
                return await update.message.reply_text("Команда доступна только админам.")
            days = int(args[0])
            new_until = extend_premium_days(uid, days)
            return await update.message.reply_text(f"Готово. Твой премиум продлён до {new_until}")

        # /premium_days <user_id> <days> — продлить КОМУ-ТО (только админ)
        else:
            if not _is_admin():
                return await update.message.reply_text("Команда доступна только админам.")
            target = args[0]
            days = int(args[1])
            new_until = extend_premium_days(target, days)
            return await update.message.reply_text(f"ОК. Пользователь {target} продлён до {new_until}")

    except Exception as e:
        logging.exception("premium_days_cmd failed: %s", e)
        return await update.message.reply_text(
            "Использование: /premium_days [days] или /premium_days <user_id> <days>"
        )
        
# Список всех команд/обработчиков для экспорта
handlers = [
    # --- Старт / Меню (сверху, чтобы всё меню ловилось первым)
    CommandHandler("start", start),
    CommandHandler("menu", menu_cmd),
    CallbackQueryHandler(menu_cb, pattern=r"^m:"),

    # --- Язык / Настройки
    CommandHandler("language", language_command),
    CallbackQueryHandler(language_callback, pattern=r"^lang_"),
    CommandHandler("settings", settings_command),
    CallbackQueryHandler(settings_language_callback, pattern=r"^setlang_"),
    CallbackQueryHandler(settings_tz_callback, pattern=r"^settz:"),
    CallbackQueryHandler(tz_callback, pattern=r"^(tz|onb:tz):"),
    CallbackQueryHandler(settings_router, pattern=r"^m:set:"),
    CallbackQueryHandler(language_cb,   pattern=r"^lang:"),
    CallbackQueryHandler(menu_router,   pattern=r"^m:nav:"),
    
    # --- Премиум и челленджи (подняты выше, чтобы команды не ловились чем-то ещё)
    CommandHandler("premium", premium_cmd),
    CommandHandler("premium_days", premium_days),              # твоя версия или premium_days_cmd
    CommandHandler("premium_mode", premium_mode_cmd),
    CommandHandler("premium_stats", premium_stats_cmd),
    CommandHandler("premium_report", premium_report_cmd),

    # Челлендж — отдельно и раньше всего остального
    CommandHandler("premium_challenge", premium_challenge_cmd, block=True),
    CallbackQueryHandler(premium_challenge_callback, pattern=r"^pch:", block=True),

    # --- Функции: трекер целей/привычек/напоминаний/очки/статистика
    CommandHandler("tracker_menu", tracker_menu_cmd),
    CallbackQueryHandler(gh_callback, pattern=r"^gh:"),
    CallbackQueryHandler(menu_router,        pattern=r"^m:nav:"),
    CommandHandler("goal", goal),
    CallbackQueryHandler(feat_router,    pattern=r"^m:feat:"),
    CommandHandler("goals", show_goals),
    CommandHandler("habit", habit),
    CommandHandler("habits", habits_list),
    CommandHandler("delete", delete_goal_command),

    # если у тебя кнопки напрямую зовут эти экраны
    CallbackQueryHandler(show_goals, pattern=r"^show_goals$"),
    CallbackQueryHandler(goal, pattern=r"^create_goal$"),
    CallbackQueryHandler(delete_goal_choose_handler,   pattern=r"^delete_goal_choose$"),
    CallbackQueryHandler(delete_goal_confirm_handler,  pattern=r"^delete_goal_\d+$"),
    CallbackQueryHandler(show_habits,                  pattern=r"^show_habits$"),
    CallbackQueryHandler(create_habit_handler,         pattern=r"^create_habit$"),
    CallbackQueryHandler(delete_habit_choose_handler,  pattern=r"^delete_habit_choose$"),
    CallbackQueryHandler(delete_habit_confirm_handler, pattern=r"^delete_habit_\d+$"),

    # Напоминания / задачи
    CommandHandler("task", task),
    CommandHandler("remind", remind_command),
    CommandHandler("reminders", reminders_menu_cmd),
    CommandHandler("reminders_menu", reminders_menu_cmd),
    CallbackQueryHandler(remind_callback, pattern=r"^rem:"),
    CallbackQueryHandler(reminders_menu_open, pattern=r"^rem:menu$"),
    
    # Статистика и очки
    CommandHandler("stats", stats_command),
    CommandHandler("mypoints", mypoints_command),
    CommandHandler("mystats", my_stats_command),
    CommandHandler("points", points_command),

    # --- Моды, голос, сказки, сон
    CommandHandler("mode", mode),
    CallbackQueryHandler(handle_mode_choice, pattern=r"^mode_"),
    CallbackQueryHandler(mode_menu_open, pattern=r"^mode:menu$"),
    
    CommandHandler("voice_mode", voice_mode_cmd),
    CommandHandler("voice_settings", voice_settings),
    CallbackQueryHandler(voice_settings_cb, pattern=r"^v:"),
    CallbackQueryHandler(plus_router, pattern=r"^m:plus:"),
    
    CommandHandler("story", story_cmd),
    CallbackQueryHandler(story_callback, pattern=r"^st:"),
    CommandHandler("story_help", story_help_cmd),
    
    CommandHandler("sleep", sleep_cmd),
    CallbackQueryHandler(sleep_cb, pattern=r"^sleep:"),

    # --- Разное
    CommandHandler("timezone", set_timezone),
    CommandHandler("feedback", feedback),
    CommandHandler("quote", quote),
    CommandHandler("invite", invite),
    CommandHandler("mytask", mytask_command),
    CommandHandler("reset", reset),
    CommandHandler("test_mood", test_mood),

    # Кнопки реакций и done
    CallbackQueryHandler(handle_reaction_button,          pattern=r"^react_"),
    CallbackQueryHandler(handle_add_goal_callback,        pattern=r"^add_goal\|"),
    CallbackQueryHandler(handle_mark_goal_done_choose,    pattern=r"^mark_goal_done_choose$"),
    CallbackQueryHandler(handle_done_goal_callback,       pattern=r"^done_goal\|\d+$"),
    CallbackQueryHandler(handle_mark_habit_done_choose,   pattern=r"^mark_habit_done_choose$"),
    CallbackQueryHandler(handle_done_habit_callback,      pattern=r"^done_habit\|\d+$"),

    # --- Диагностический ловец в самом конце и НЕ блокирующий
    CallbackQueryHandler(_dbg_cb, pattern=r".+", block=False),

    # --- Сообщения
    MessageHandler(filters.VOICE, handle_voice),
    MessageHandler(filters.TEXT & ~filters.COMMAND, chat),  # важно исключить команды!
    MessageHandler(filters.COMMAND, unknown_command),       # Unknown строго последним
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
