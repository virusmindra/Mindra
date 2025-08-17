import os
import sqlite3
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
import textwrap
import uuid
import asyncio
import pytz
import shutil
from elevenlabs import ElevenLabs 
from collections import defaultdict
from texts import (
    VOICE_TEXTS_BY_LANG,
    STORY_INTENT,
    VOICE_PRESETS,
    VOICE_UI_TEXTS,
    BGM_PRESETS,
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
from stats import load_stats, save_stats, get_premium_until, set_premium_until, is_premium, got_trial, set_trial, add_referral, add_points, get_user_stats, get_stats, OWNER_ID, ADMIN_USER_IDS, _collect_activity_dates, get_user_points, get_next_title_info, build_titles_ladder, get_user_title
from telegram.error import BadRequest
global user_timezones
from zoneinfo import ZoneInfo
from collections import defaultdict

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
user_voice_mode = {}  # {user_id: bool}
user_voice_prefs = {}

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

# Храним всё в sqlite
REMIND_DB_PATH = os.getenv("REMIND_DB_PATH", "reminders.sqlite3")

# Тихие часы по локальному времени пользователя
QUIET_START = 22  # не тревожить с 22:00
QUIET_END   = 9   # до 09:00

def _vm_i18n(uid:str)->dict:
    return VOICE_MODE_TEXTS.get(user_languages.get(uid,"ru"), VOICE_TEXTS["ru"])

def _v_ui_i18n(uid: str) -> dict:
    lang = user_languages.get(uid, "ru")
    return VOICE_UI_TEXTS.get(lang, VOICE_UI_TEXTS["ru"])
    
def _gh_i18n(uid: str) -> dict:
    return GH_TEXTS.get(user_languages.get(uid, "ru"), GH_TEXTS["ru"])

def _p_i18n(uid: str) -> dict:
    return P_TEXTS.get(user_languages.get(uid, "ru"), P_TEXTS["ru"])

def _tts_lang(lang: str) -> str:
    return LANG_TO_TTS.get(lang, "ru")

def _s_i18n(uid: str) -> dict:
    return STORY_TEXTS.get(user_languages.get(uid, "ru"), STORY_TEXTS["ru"])

def _has_eleven():
    return bool(os.getenv("ELEVEN_API_KEY"))
    
def _looks_like_story_intent(text: str, lang: str) -> bool:
    pats = STORY_INTENT.get(lang, STORY_INTENT["ru"])
    low = text.lower()
    return any(re.search(p, low) for p in pats)

# утилита безопасного обновления текста/клавы
async def _voice_refresh(q, uid: str, tab: str):
    text = _voice_menu_text(uid)
    kb = _voice_kb(uid, tab)
    try:
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # если ничего не изменилось — просто обновим клаву
            try:
                await q.edit_message_reply_markup(reply_markup=kb)
            except BadRequest:
                pass
        else:
            raise

def _voice_menu_text(uid: str) -> str:
    t = _v_ui_i18n(uid)
    p = _vp(uid)
    eng = t["engine_eleven"] if p["engine"].lower().startswith("eleven") else t["engine_gtts"]

    voice = "—"
    presets = VOICE_PRESETS.get(user_languages.get(uid, "ru"), VOICE_PRESETS["ru"])
    for name, eng_k, vid in presets:
        if vid and vid == p.get("voice_id") and eng_k.lower() == p["engine"].lower():
            voice = name
            break
    if voice == "—" and p.get("voice_id"):
        voice = p["voice_id"]

    bg = BGM_PRESETS.get(p["bgm_kind"], {"label": "—"})["label"]
    return (
        f"*{t['title']}*\n\n"
        f"{t['engine'].format(engine=eng)}\n"
        f"{t['voice'].format(voice=voice)}\n"
        f"{t['speed'].format(speed=p['speed'])}\n"
        f"{t['voice_only'].format(v=t['on'] if p['voice_only'] else t['off'])}\n"
        f"{t['auto_story'].format(v=t['on'] if p['auto_story_voice'] else t['off'])}\n"
        f"{t['bgm'].format(bg=bg, db=p['bgm_gain_db'])}\n"
        + (f"\n{t['no_eleven_key']}" if not _has_eleven() else "")
    )
    
def _voice_kb(uid: str, tab: str = "engine") -> InlineKeyboardMarkup:
    t = _v_ui_i18n(uid)
    p = _vp(uid)
    rows = []

    if tab == "engine":
        rows.append([
            InlineKeyboardButton(("✅ " if p["engine"] == "eleven" else "") + t["engine_eleven"], callback_data="v:engine:eleven"),
            InlineKeyboardButton(("✅ " if p["engine"] == "gTTS"   else "") + t["engine_gtts"],   callback_data="v:engine:gTTS"),
        ])
    elif tab == "voice":
        presets = VOICE_PRESETS.get(user_languages.get(uid, "ru"), VOICE_PRESETS["ru"])
        for i, (name, eng_k, vid) in enumerate(presets):
            if eng_k.lower() == "eleven" and not _has_eleven():
                continue
            rows.append([InlineKeyboardButton(name, callback_data=f"v:voice:{i}")])
    elif tab == "speed":
        rows.append([
            InlineKeyboardButton("➖ 0.9x", callback_data="v:speed:0.9"),
            InlineKeyboardButton("1.0x",    callback_data="v:speed:1.0"),
            InlineKeyboardButton("➕ 1.1x", callback_data="v:speed:1.1"),
        ])
    elif tab == "beh":
        rows.append([InlineKeyboardButton(("✅ " if p["voice_only"] else "❌ ") + "Voice only", callback_data="v:beh:voiceonly")])
        rows.append([InlineKeyboardButton(("✅ " if p["auto_story_voice"] else "❌ ") + "Auto story voice", callback_data="v:beh:autostory")])
    elif tab == "bg":
        for key, meta in BGM_PRESETS.items():
            mark = "✅ " if p["bgm_kind"] == key else ""
            rows.append([InlineKeyboardButton(mark + meta["label"], callback_data=f"v:bg:set:{key}")])
        rows.append([
            InlineKeyboardButton("-30dB", callback_data="v:bg:gain:-30"),
            InlineKeyboardButton("-25",   callback_data="v:bg:gain:-25"),
            InlineKeyboardButton("-22",   callback_data="v:bg:gain:-22"),
            InlineKeyboardButton("-20",   callback_data="v:bg:gain:-20"),
            InlineKeyboardButton("-18",   callback_data="v:bg:gain:-18"),
        ])

    rows.append([
        InlineKeyboardButton(t["btn_engine"], callback_data="v:tab:engine"),
        InlineKeyboardButton(t["btn_voice"],  callback_data="v:tab:voice"),
        InlineKeyboardButton(t["btn_speed"],  callback_data="v:tab:speed"),
        InlineKeyboardButton(t["btn_beh"],    callback_data="v:tab:beh"),
        InlineKeyboardButton(t["btn_bg"],     callback_data="v:tab:bg"),
    ])
    return InlineKeyboardMarkup(rows)
    
# === /voice_settings ===
async def voice_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await update.message.reply_text(
        _voice_menu_text(uid),
        parse_mode="Markdown",
        reply_markup=_voice_kb(uid, "engine")
    )


# === Callback ===
async def voice_settings_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data.startswith("v:"):
        return
    await q.answer()

    uid = str(q.from_user.id)
    p = _vp(uid)
    t = _v_ui_i18n(uid)  # i18n для подсказок
    parts = q.data.split(":")
    kind = parts[1]

    # Переход между вкладками — просто рендерим нужную
    if kind == "tab":
        tab = parts[2]
        return await _voice_refresh(q, uid, tab)

    # по умолчанию: какая вкладка «активна» после действия
    current_tab_map = {"engine": "engine", "voice": "voice", "speed": "speed", "beh": "beh", "bg": "bg"}
    current_tab = current_tab_map.get(kind, "engine")

    if kind == "engine":
        new_engine = parts[2]   # "eleven" | "gTTS"
        if new_engine == "eleven" and not _has_eleven():
            await q.answer(t["no_eleven_key"], show_alert=True)
        else:
            if p["engine"] != new_engine:
                p["engine"] = new_engine
                if p["engine"] == "gTTS":
                    # у gTTS нет voice_id — сбросим
                    p["voice_id"] = ""

    elif kind == "voice":
        # выбор пресета голоса
        try:
            idx = int(parts[2])
        except:
            idx = -1
        presets = VOICE_PRESETS.get(user_languages.get(uid, "ru"), VOICE_PRESETS["ru"])
        if 0 <= idx < len(presets):
            name, eng_k, vid = presets[idx]
            if eng_k.lower() == "eleven" and not _has_eleven():
                await q.answer(t["no_eleven_key"], show_alert=True)
            else:
                p["engine"] = "eleven" if eng_k.lower() == "eleven" else "gTTS"
                p["voice_id"] = vid or ""
                if p["engine"] == "gTTS":
                    p["voice_id"] = ""

    elif kind == "speed":
        try:
            p["speed"] = float(parts[2])
        except:
            pass

    elif kind == "beh":
        sub = parts[2]
        if sub == "voiceonly":
            p["voice_only"] = not p["voice_only"]
        elif sub == "autostory":
            p["auto_story_voice"] = not p["auto_story_voice"]

    elif kind == "bg":
        sub = parts[2]
        if sub == "set":
            p["bgm_kind"] = parts[3]
        elif sub == "gain":
            try:
                p["bgm_gain_db"] = int(parts[3])
            except:
                pass

    # безопасно перерисуем текущую вкладку
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

def _mix_with_bgm(voice_ogg: str, bg_path: str, bg_gain_db: int=-20) -> str:
    if not bg_path or not os.path.exists(bg_path) or not shutil.which("ffmpeg"):
        return voice_ogg
    out_path = f"/tmp/{uuid.uuid4().hex}.ogg"
    cmd = [
        "ffmpeg","-y",
        "-i", voice_ogg,
        "-stream_loop","-1","-i", bg_path,
        "-filter_complex",
        f"[1:a]volume={bg_gain_db}dB[a1];"
        f"[0:a][a1]amix=inputs=2:duration=first:dropout_transition=0,"
        f"loudnorm=I=-19:LRA=7:TP=-1.5",
        "-c:a","libopus","-b:a","48k","-ar","48000","-ac","1",
        out_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try: os.remove(voice_ogg)
        except: pass
        return out_path
    except Exception as e:
        logging.exception(f"ffmpeg mix failed: {e}")
        return voice_ogg

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
    p = _vp(uid)
    text = _expressive(text, lang)
    try:
        if p.get("engine") == "eleven" and p.get("voice_id") and os.getenv("ELEVEN_API_KEY"):
            return _tts_elevenlabs_to_ogg(text, p["voice_id"], p.get("speed",1.0))
        # можно добавить Azure при необходимости
        return _tts_gtts_to_ogg(text, lang, tld=p.get("accent","com"), speed=p.get("speed",1.0))
    except Exception as e:
        logging.exception(f"TTS primary failed ({p.get('engine')}), fallback to gTTS: {e}")
        return _tts_gtts_to_ogg(text, lang, tld=p.get("accent","com"), speed=p.get("speed",1.0))


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


async def story_cmd(update, context):
    uid = str(update.effective_user.id)
    if not is_premium(uid):
        tpay = _p_i18n(uid)
        return await update.message.reply_text(f"*{tpay['upsell_title']}*\n\n{tpay['upsell_body']}",
                                               parse_mode="Markdown", reply_markup=_premium_kb(uid))
    t = _s_i18n(uid)
    lang = user_languages.get(uid, "ru")

    if not context.args:
        return await update.message.reply_text(f"{t['title']}\n\n{t['usage']}", parse_mode="Markdown")

    raw = " ".join(context.args)
    args = _parse_story_args(raw)

    await update.message.reply_text(t["making"])
    text = await generate_story_text(uid, lang, args["topic"], args["name"], args["length"])

    context.chat_data[f"story_last_{uid}"] = {"text": text, "lang": lang, "topic": args["topic"]}

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_more"],  callback_data="st:new")],
        [InlineKeyboardButton(t["btn_voice"], callback_data="st:voice")],
        [InlineKeyboardButton(t["btn_close"], callback_data="st:close")],
    ])
    await update.message.reply_text(f"*{t['title']}*\n\n{text}", parse_mode="Markdown", reply_markup=kb)

    # 🔊 Авто-озвучка для премиума (если пользователь не просил voice в аргументах)
    if not args.get("voice") and is_premium(uid) and _vp(uid).get("auto_story_voice", True):
        bg_override = None
        prefs = _vp(uid)
        if prefs.get("auto_bgm_for_stories", True) and prefs.get("bgm_kind", "off") == "off":
            bg_override = "ocean"  # мягкий фон по умолчанию
        try:
            await send_voice_response(context, int(uid), text, lang, bgm_kind_override=bg_override)
        except Exception:
            logging.exception("Auto story TTS failed in story_cmd")

    # Если просили голосом явно — озвучим
    if args.get("voice"):
        await send_voice_response(context, int(uid), text, lang)

async def story_callback(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("st:"):
        return
    await q.answer()
    uid = str(q.from_user.id)
    lang = user_languages.get(uid, "ru")
    t = _s_i18n(uid)

    parts = q.data.split(":")
    action = parts[1]

    if action == "confirm":
        topic = context.chat_data.get(f"story_pending_{uid}", "")
        await q.edit_message_text(t["making"])
        text = await generate_story_text(uid, lang, topic, None, "short")
        context.chat_data[f"story_last_{uid}"] = {"text": text, "lang": lang, "topic": topic}

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["btn_more"],  callback_data="st:new")],
            [InlineKeyboardButton(t["btn_voice"], callback_data="st:voice")],
            [InlineKeyboardButton(t["btn_close"], callback_data="st:close")],
        ])
        await context.bot.send_message(chat_id=int(uid),
                                       text=f"*{t['title']}*\n\n{text}",
                                       parse_mode="Markdown",
                                       reply_markup=kb)

        # 🔊 Авто-озвучка для премиума
        if is_premium(uid) and _vp(uid).get("auto_story_voice", True):
            bg_override = None
            prefs = _vp(uid)
            if prefs.get("auto_bgm_for_stories", True) and prefs.get("bgm_kind","off") == "off":
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

        try:
            await q.edit_message_text(f"*{t['title']}*\n\n{text}",
                                      parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(t["btn_more"],  callback_data="st:new")],
                                          [InlineKeyboardButton(t["btn_voice"], callback_data="st:voice")],
                                          [InlineKeyboardButton(t["btn_close"], callback_data="st:close")],
                                      ]))
        except:
            await context.bot.send_message(chat_id=int(uid),
                                           text=f"*{t['title']}*\n\n{text}",
                                           parse_mode="Markdown")

        # 🔊 Авто-озвучка для премиума
        if is_premium(uid) and _vp(uid).get("auto_story_voice", True):
            bg_override = None
            prefs = _vp(uid)
            if prefs.get("auto_bgm_for_stories", True) and prefs.get("bgm_kind","off") == "off":
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

    if action == "close":
        try: await q.edit_message_text(t["ready"])
        except: pass
        return

def _tts_synthesize_to_ogg(text: str, lang: str) -> str:
    """Возвращает путь к .ogg (opus) для sendVoice. Требует gTTS + ffmpeg."""
    try:
        from gtts import gTTS  # ленивый импорт, чтобы без пакета не падал весь модуль
    except Exception as e:
        raise RuntimeError("gTTS not installed") from e

    mp3_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    ogg_path = f"/tmp/{uuid.uuid4().hex}.ogg"

    safe_text = textwrap.shorten(text, width=4000, placeholder="…")
    gTTS(text=safe_text, lang=_tts_lang(lang)).save(mp3_path)

    # mp3 -> ogg(opus) 48k mono
    subprocess.run(
        ["ffmpeg","-y","-i", mp3_path, "-ac","1","-ar","48000","-c:a","libopus", ogg_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    try: os.remove(mp3_path)
    except Exception: pass
    return ogg_path

async def send_voice_response(context, chat_id: int, text: str, lang: str, bgm_kind_override: str | None = None):
    uid = str(chat_id)
    try:
        ogg_path = synthesize_to_ogg(text, lang, uid)  # ElevenLabs → gTTS (фолбэк) внутри
        # 🎧 Подмешиваем фон, если выбран
        p = _vp(uid)
        kind = bgm_kind_override if bgm_kind_override is not None else p.get("bgm_kind", "off")
        if kind != "off":
            bg = BGM_PRESETS.get(kind, {}).get("path")
            ogg_path = _mix_with_bgm(ogg_path, bg, p.get("bgm_gain_db", -20))

        with open(ogg_path, "rb") as f:
            await context.bot.send_voice(chat_id=chat_id, voice=f)
    except Exception as e:
        logging.exception(f"TTS failed for chat_id={chat_id}: {e}")
        # ничего не шлём текстом, чтобы не дублировать уже отправленный ответ
    finally:
        try:
            os.remove(ogg_path)  # почистим временный файл, если был
        except Exception:
            pass

def require_premium_message(update, context, uid):
    t = _p_i18n(uid)
    return update.message.reply_text(
        f"*{t['upsell_title']}*\n\n{t['upsell_body']}",
        parse_mode="Markdown",
        reply_markup=_premium_kb(uid)
    )

async def voice_mode_cmd(update, context):
    uid = str(update.effective_user.id)
    t = _v_i18n(uid)
    if not is_premium(uid):
        return await require_premium_message(update, context, uid)
    if not context.args:
        return await update.message.reply_text(t["help"])
    arg = context.args[0].lower()
    if arg not in ("on","off"):
        return await update.message.reply_text(t["err"])
    user_voice_mode[uid] = (arg=="on")
    await update.message.reply_text(t["on"] if user_voice_mode[uid] else t["off"])

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

async def premium_challenge_callback(update, context):
    q = update.callback_query
    if not q or not q.data.startswith("pch:"):
        return
    await q.answer()
    uid = str(q.from_user.id)
    t = _p_i18n(uid)
    parts = q.data.split(":")
    action = parts[1]

    ensure_premium_db()

    if action == "new":
        # принудительно выдаём новый текст на текущую неделю (переписываем)
        tz = _user_tz(uid)
        week_iso = _week_start_iso(datetime.now(tz))
        lang = user_languages.get(uid, "ru")
        new_text = random.choice(CHALLENGE_BANK.get(lang, CHALLENGE_BANK["ru"]))
        with sqlite3.connect("mindra.db") as db:
            db.execute("UPDATE premium_challenges SET text=?, done=0 WHERE user_id=? AND week_start=?;",
                       (new_text, uid, week_iso))
            db.commit()
        await q.edit_message_text(f"*{t['challenge_title']}*\n\n{t['challenge_cta'].format(text=new_text)}",
                                  parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton(t["btn_done"], callback_data=f"pch:done:0")],
                                      [InlineKeyboardButton(t["btn_new"],  callback_data="pch:new")],
                                  ]))
        return

    if action == "done" and len(parts) >= 3:
        # отметим выполненным любую текущую запись пользователя
        with sqlite3.connect("mindra.db") as db:
            db.execute("UPDATE premium_challenges SET done=1 WHERE user_id=?;",
                       (uid,))
            db.commit()
        await q.edit_message_text(t["challenge_done"])
        return

def ensure_premium_db():
    with sqlite3.connect("mindra.db") as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS premium_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            week_start TEXT NOT NULL,   -- ISO date (YYYY-MM-DD) понедельник
            text TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        """)
        db.commit()

def _week_start_iso(dt: datetime) -> str:
    # понедельник этой недели в локальном времени пользователя
    monday = dt - timedelta(days=dt.weekday())
    return monday.date().isoformat()

def _premium_kb(uid: str) -> InlineKeyboardMarkup:
    t = _p_i18n(uid)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_get"],  callback_data="plus:buy")],
        [InlineKeyboardButton(t["btn_code"], callback_data="plus:code")],
    ])

def require_premium(func):
    async def wrapper(update, context, *args, **kwargs):
        uid = str(update.effective_user.id)
        if not is_premium(uid):
            t = _p_i18n(uid)
            msg = f"*{t['upsell_title']}*\n\n{t['upsell_body']}"
            await update.message.reply_text(msg, reply_markup=_premium_kb(uid), parse_mode="Markdown")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
    
def _gh_menu_keyboard(t: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_add_goal"],   callback_data="gh:new_goal")],
        [InlineKeyboardButton(t["btn_list_goals"], callback_data="gh:list_goals")],
        [InlineKeyboardButton(t["btn_add_habit"],  callback_data="gh:new_habit")],
        [InlineKeyboardButton(t["btn_list_habits"],callback_data="gh:list_habits")],
    ])

async def tracker_menu_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    t = _gh_i18n(uid)
    await update.message.reply_text(
        t["menu_title"],
        reply_markup=_gh_menu_keyboard(t)
    )

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

# /premium_report — отчёт 7д
@require_premium
async def premium_report_cmd(update, context):
    uid = str(update.effective_user.id)
    t = _p_i18n(uid)
    # цели: просто считаем done
    try:
        goals = get_goals(uid)
        goals_done = sum(1 for g in goals if isinstance(g, dict) and g.get("done"))
    except Exception:
        goals_done = 0
    # привычки: сколько отметок (если нет дат — берём количество записей)
    try:
        habits = get_habits(uid)
        habits_marked = len(habits)
    except Exception:
        habits_marked = 0
    # напоминания: fired за 7д (если нет статусов — 0)
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
    # активные дни — грубая метрика: дни с любой активностью (по last_seen логике не считаем, просто ~мин)
    active_30 = 0
    try:
        # если есть user_message_count или логи — подставь. Иначе ноль.
        active_30 = 0
    except Exception:
        pass

    text = (
        f"*{t['report_title']}*\n\n"
        f"{t['report_goals'].format(n=goals_done)}\n"
        f"{t['report_habits'].format(n=habits_marked)}\n"
        f"{t['report_rems'].format(n=rems_7)}\n"
        f"{t['report_streak'].format(n=active_30)}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# /premium_challenge — показать/создать челлендж недели
@require_premium
async def premium_challenge_cmd(update, context):
    ensure_premium_db()
    uid = str(update.effective_user.id)
    lang = user_languages.get(uid, "ru")
    t = _p_i18n(uid)

    # неделя по локальному времени пользователя
    tz = _user_tz(uid)
    week_iso = _week_start_iso(datetime.now(tz))

    with sqlite3.connect("mindra.db") as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
                         (uid, week_iso)).fetchone()
        if not row:
            # создаём челлендж
            text = random.choice(CHALLENGE_BANK.get(lang, CHALLENGE_BANK["ru"]))
            db.execute("INSERT INTO premium_challenges (user_id, week_start, text, done, created_at) "
                       "VALUES (?, ?, ?, 0, ?);",
                       (uid, week_iso, text, _to_epoch(_utcnow())))
            db.commit()
            row = db.execute("SELECT * FROM premium_challenges WHERE user_id=? AND week_start=?;",
                             (uid, week_iso)).fetchone()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_done"], callback_data=f"pch:done:{row['id']}")],
        [InlineKeyboardButton(t["btn_new"],  callback_data="pch:new")],
    ])
    await update.message.reply_text(
        f"*{t['challenge_title']}*\n\n{t['challenge_cta'].format(text=row['text'])}",
        parse_mode="Markdown", reply_markup=kb
    )

# /premium_mode — включает эксклюзивный промпт
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

# /premium_stats — расширенная статистика
@require_premium
async def premium_stats_cmd(update, context):
    uid = str(update.effective_user.id)
    t = _p_i18n(uid)

    # простые агрегаты
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

    active_30 = 0  # при желании сюда можно подвести real metric

    text = (
        f"*{t['stats_title']}*\n\n"
        f"{t['stats_goals_done'].format(n=total_goals_done)}\n"
        f"{t['stats_habit_days'].format(n=habit_days)}\n"
        f"{t['stats_active_days'].format(n=active_30)}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def gh_callback(update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data or not q.data.startswith("gh:"):
        return
    await q.answer()

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



def _i18n(uid: str) -> dict:
    return REMIND_TEXTS.get(user_languages.get(uid, "ru"), REMIND_TEXTS["ru"])

# ========== DB ==========

async def reminders_menu_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    t = _i18n(uid)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_add_rem"],  callback_data="rem:new")],
        [InlineKeyboardButton(t["btn_list_rem"], callback_data="rem:list")],
    ])
    # Покажем компактный заголовок-меню
    await update.message.reply_text(t["menu_title"], reply_markup=kb)
    
def remind_db() -> sqlite3.Connection:
    conn = sqlite3.connect(REMIND_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_remind_db():
    with remind_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            due_utc INTEGER NOT NULL,   -- epoch seconds (UTC)
            tz TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled', -- scheduled|fired|canceled
            created_at INTEGER NOT NULL
        );
        """)
        db.commit()

# ========== Time helpers ==========
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _user_tz(uid: str) -> ZoneInfo:
    tz = user_timezones.get(uid, "Europe/Kyiv")
    try:
        return ZoneInfo(tz)
    except Exception:
        return ZoneInfo("Europe/Kyiv")

def _to_epoch(dt_aware: datetime) -> int:
    return int(dt_aware.timestamp())

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

def _tz_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=f"tz:{code}") for (text, code) in row]
        for row in TZ_KEYBOARD_ROWS
    ])
    
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
    """Обработчик нажатий на инлайн-кнопки tz:..."""
    q = update.callback_query
    if not q or not q.data or not q.data.startswith("tz:"):
        return
    await q.answer()

    uid = str(q.from_user.id)
    lang = _get_lang(uid)
    t = TZ_TEXTS.get(lang, TZ_TEXTS["ru"])

    tz = q.data.split(":", 1)[1]
    try:
        _ = ZoneInfo(tz)
    except Exception:
        await q.edit_message_text(t["unknown"])
        return

    user_timezones[uid] = tz
    local_str = _format_local_time_now(tz, lang)
    try:
        await q.edit_message_text(
            t["saved"].format(tz=tz, local_time=local_str),
            parse_mode="Markdown"
        )
    except Exception:
        await context.bot.send_message(
            chat_id=int(uid),
            text=t["saved"].format(tz=tz, local_time=local_str),
            parse_mode="Markdown"
        )

    # === ФИНАЛ ОНБОРДИНГА: делаем только если ещё НЕ выдавали триал ===
    try:
        if not got_trial(uid):
            # 1) Реферал (если в /start был payload)
            ref_bonus_given = False
            ref_code = user_ref_args.pop(uid, None)   # ты сохраняешь это в /start
            referrer_id = _parse_referrer_id(ref_code)
            if referrer_id and referrer_id != uid:
                try:
                    ref_bonus_given = handle_referral(uid, referrer_id)  # твоя функция
                except Exception as e:
                    logging.warning(f"handle_referral error: {e}")
                if ref_bonus_given:
                    bonus_text = REFERRAL_BONUS_TEXT.get(lang, REFERRAL_BONUS_TEXT["ru"])
                    await context.bot.send_message(chat_id=int(uid), text=bonus_text, parse_mode="Markdown")
                    # уведомим пригласившего
                    try:
                        await context.bot.send_message(
                            chat_id=int(referrer_id),
                            text="🎉 Твой друг зарегистрировался по твоей ссылке! Вам обоим начислено +7 дней Mindra+ 🎉"
                        )
                    except Exception as e:
                        logging.warning(f"referrer notify failed: {e}")

            # 2) Если не реферал — выдаём триал
            if not ref_bonus_given:
                try:
                    trial_given = give_trial_if_needed(uid)  # твоя функция
                except Exception as e:
                    logging.warning(f"trial error: {e}")
                    trial_given = False
                if trial_given:
                    trial_info = TRIAL_INFO_TEXT.get(lang, TRIAL_INFO_TEXT["ru"])
                    await context.bot.send_message(chat_id=int(uid), text=trial_info, parse_mode="Markdown")

            # 3) Инициализируем системный промпт/историю (как у тебя было в language_callback)
            try:
                mode = "support"
                lang_prompt = LANG_PROMPTS.get(lang, LANG_PROMPTS["ru"])
                mode_prompt = MODES[mode].get(lang, MODES[mode]['ru'])
                system_prompt = f"{lang_prompt}\n\n{mode_prompt}"
                conversation_history[uid] = [{"role": "system", "content": system_prompt}]
                save_history(conversation_history)
            except Exception as e:
                logging.warning(f"history init failed: {e}")

            # 4) Welcome в самом конце
            first_name = q.from_user.first_name or {"ru":"друг","uk":"друже","en":"friend"}.get(lang, "друг")
            welcome_text = WELCOME_TEXTS.get(lang, WELCOME_TEXTS["ru"]).format(first_name=first_name)
            await context.bot.send_message(chat_id=int(uid), text=welcome_text, parse_mode="Markdown")
    except Exception as e:
        logging.exception(f"onboarding finalize error: {e}")

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    points = get_user_points(user_id)
    title = get_user_title(points, lang)

    # было: _, next_title, to_next = get_next_title_info(points, lang)
    next_title, to_next = get_next_title_info(points, lang)  # ← так правильно

    ladder = build_titles_ladder(lang)

    text = POINTS_HELP_TEXTS.get(lang, POINTS_HELP_TEXTS["ru"]).format(
        points=points,
        title=title,
        next_title=next_title,
        to_next=to_next,
        ladder=ladder,
    )
    await update.message.reply_text(text, parse_mode="Markdown")

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
    await query.answer()

    user_id = str(query.from_user.id)
    lang_code = query.data.replace("lang_", "")
    valid = {"ru","uk","md","be","kk","kg","hy","ka","ce","en"}
    if lang_code not in valid:
        lang_code = "ru"

    user_languages[user_id] = lang_code
    logging.info(f"🌐 Пользователь {user_id} выбрал язык: {lang_code}")

    # Показываем выбор таймзоны (тексты берём из TZ_TEXTS)
    t = TZ_TEXTS.get(lang_code, TZ_TEXTS["ru"])
    prompt = f"{t['title']}\n\n{t['hint']}"
    try:
        await query.edit_message_text(prompt, reply_markup=_tz_keyboard(), parse_mode="Markdown")
    except Exception:
        await context.bot.send_message(chat_id=int(user_id), text=prompt, reply_markup=_tz_keyboard(), parse_mode="Markdown")

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

    # ✅ фикс: исключаем владельца и админов из лимита
    if (user_id_int not in ADMIN_USER_IDS) and (user_id_int != OWNER_ID):
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

    # ——— Story intent suggest ———
    if _looks_like_story_intent(user_input, lang_code):
        if not is_premium(user_id):
            tpay = _p_i18n(user_id)
            await update.message.reply_text(
                f"*{tpay['upsell_title']}*\n\n{tpay['upsell_body']}",
                parse_mode="Markdown",
                reply_markup=_premium_kb(user_id)
            )
            return
    t = _s_i18n(user_id)
    topic_guess = user_input

    # Сохраняем тему в chat_data, НЕ в callback_data
    context.chat_data[f"story_pending_{user_id}"] = topic_guess

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ OK",  callback_data="st:confirm"),
         InlineKeyboardButton("❌ Нет", callback_data="st:close")]
    ])
    await update.message.reply_text(t["suggest"], reply_markup=kb)
    return


    lang_prompt = LANG_PROMPTS.get(lang_code, LANG_PROMPTS["ru"])

    # 📋 Определяем режим
    mode = user_modes.get(user_id, "support")
    # ВАЖНО: режим теперь словарь, берём под язык
    mode_prompt = MODES.get(mode, MODES["support"]).get(lang_code, MODES["support"]["ru"])

    system_prompt = f"{lang_prompt}\n\n{mode_prompt}"

    # 💾 Создаём/обновляем историю
    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": system_prompt}]
    else:
        conversation_history[user_id][0] = {"role": "system", "content": system_prompt}

    # Добавляем сообщение пользователя
    conversation_history[user_id].append({"role": "user", "content": user_input})
    trimmed_history = trim_history(conversation_history[user_id])

    try:
        # ✨ "печатает..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

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

        # 📝 Текстом
        await update.message.reply_text(reply, reply_markup=generate_post_response_buttons())

        # 🔊 Дополнительно — голосом для Mindra+ при включённом voice mode
        if is_premium(user_id) and user_voice_mode.get(user_id, False):
            await send_voice_response(context, user_id_int, reply, lang_code)

    except Exception as e:
        logging.error(f"❌ Ошибка в chat(): {e}")
        await update.message.reply_text(ERROR_MESSAGES_BY_LANG.get(lang_code, ERROR_MESSAGES_BY_LANG["ru"]))

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
    CommandHandler("settings", settings_command),
    CallbackQueryHandler(settings_language_callback, pattern=r"^setlang_"),
    CallbackQueryHandler(settings_tz_callback, pattern=r"^settz:"),
    
    # --- Цели и привычки
    CommandHandler("goal", goal),
    CommandHandler("goals", show_goals),
    CommandHandler("habit", habit),
    CommandHandler("habits", habits_list),
    CommandHandler("delete", delete_goal_command),
    CommandHandler("tracker_menu", tracker_menu_cmd),
    CallbackQueryHandler(gh_callback, pattern=r"^gh:"),

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
    CommandHandler("remind", remind_command),
    CommandHandler("reminders", reminders_list),
    CallbackQueryHandler(remind_callback, pattern=r"^rem:"),
    CommandHandler("reminders_menu", reminders_menu_cmd),
    # --- Статистика и очки
    CommandHandler("stats", stats_command),
    CommandHandler("mypoints", mypoints_command),
    CommandHandler("mystats", my_stats_command),
    

    # --- Премиум и челленджи
    CallbackQueryHandler(premium_challenge_callback, pattern=r"^pch:"),
    CallbackQueryHandler(plus_callback, pattern=r"^plus:"),
    CommandHandler("premium_stats", premium_stats_cmd),
    CommandHandler("premium_mode", premium_mode_cmd),
    CommandHandler("premium", premium_cmd),
    CommandHandler("premium_report", premium_report_cmd),
    CommandHandler("premium_challenge", premium_challenge_cmd),
    
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
    CommandHandler("points", points_command),
    CallbackQueryHandler(tz_callback, pattern=r"^tz:"),
    
    # --- Кнопки реакции и добавления цели
    CallbackQueryHandler(handle_reaction_button, pattern="^react_"),
    CallbackQueryHandler(handle_add_goal_callback, pattern="^add_goal\\|"),
    CallbackQueryHandler(handle_mark_habit_done_choose, pattern=r"^mark_habit_done_choose$"),
    CallbackQueryHandler(handle_done_habit_callback,    pattern=r"^done_habit\|\d+$"),
    
    # --- Чаты и голос
    CommandHandler("voice_mode", voice_mode_cmd),
    CommandHandler("story", story_cmd),
    CallbackQueryHandler(story_callback, pattern=r"^st:"),
    CommandHandler("voice_settings", voice_settings),
    CallbackQueryHandler(voice_settings_cb, pattern=r"^v:"),

    
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
