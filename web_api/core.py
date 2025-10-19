# web_api/core.py
import os
from collections import defaultdict, deque
from typing import Deque, Dict, List
from openai import OpenAI

# -------- OpenAI клиент ----------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------- Память диалогов (in-memory) ----------
# Ключ = "{user_id}:{session_id}", значения — deque сообщений (role/content)
_history: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=20))

# -------- Мини i18n/режимы (можешь заменить своими) ----------
LANG_PROMPTS = {
    "ru": "Ты Mindra — тёплый поддерживающий ассистент. Пиши кратко, дружелюбно и по делу.",
    "en": "You are Mindra — a warm, supportive assistant. Be concise, friendly, and helpful.",
}

MODES = {
    "support": {
        "ru": "Режим поддержки: отвечай бережно, помогающе и структурно.",
        "en": "Support mode: be caring, helpful, and structured.",
    }
}

# Временные карты предпочтений; при желании можешь подменить своими
user_modes: Dict[str, str] = {}
user_languages: Dict[str, str] = {}

GUARD = {
    "ru": "Если пользователь просит сказку — не пиши её тут; предложи отдельный режим «Сказка».",
    "en": "If the user asks for a bedtime story, do not write it here; suggest a separate Story mode.",
}

def _guess_lang(text: str) -> str:
    # грубая авто-эвристика: если есть кириллица — ru, иначе en
    for ch in text:
        if "а" <= ch.lower() <= "я" or ch.lower() == "ё":
            return "ru"
    return "en"

def _system_prompt(lang: str, mode: str) -> str:
    lp = LANG_PROMPTS.get(lang, LANG_PROMPTS["en"])
    mp = MODES.get(mode, MODES["support"]).get(lang, MODES["support"]["en"])
    gd = GUARD.get(lang, GUARD["en"])
    return f"{lp}\n\n{mp}\n\n{gd}"

# ---- Можно подключить детект эмоций/тем и т.п. (заглушки оставлены) ----
def detect_emotion_reaction(_text: str, _lang: str) -> str:  # noqa: N802
    return ""

def detect_topic_and_react(_text: str, _lang: str) -> str:  # noqa: N802
    return ""

# -------- Основная функция ответа ----------
async def generate_reply(user_id: str, session_id: str, text: str) -> str:
    """
    Централизованный «мозг» для веб-чата.
    Держит короткую историю, собирает system prompt и обращается к OpenAI.
    """
    key = f"{user_id}:{session_id}"

    # язык и режим (можешь подменить/заполнять извне)
    lang = user_languages.get(user_id) or _guess_lang(text)
    mode = user_modes.get(user_id, "support")

    sys_prompt = _system_prompt(lang, mode)

    # соберём список сообщений для модели
    h = _history[key]
    messages: List[dict] = [{"role": "system", "content": sys_prompt}]
    messages += list(h)
    messages.append({"role": "user", "content": text})

    try:
        # Вызов OpenAI. (SDK синхронный; в рамках FastAPI/Render — норм для старта)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",   # при желании поменяй модель
            messages=messages,
            temperature=0.7,
        )
        reply = (resp.choices[0].message.content or "").strip() or "…"
    except Exception as e:
        # Лог ошибки и запасной ответ, чтобы фронт не ломался
        print("openai error:", repr(e))
        reply = "Извини, сейчас не получается ответить. Попробуй ещё раз."

    # лёгкая «эмпатическая» подсказка (если захочешь — развивай)
    reaction = detect_emotion_reaction(text, lang) + detect_topic_and_react(text, lang)
    final_text = (reaction + reply).strip()

    # Обновим историю
    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": final_text})

    return final_text
