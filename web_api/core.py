# web_api/core.py
from datetime import date
from typing import List, Dict, Any

# Импортируй то, что у тебя уже есть в боте:
# - client (OpenAI)
# - conversation_history, trim_history, save_history
# - detect_emotion_reaction, detect_topic_and_react
# - LANG_PROMPTS, MODES, user_modes, user_languages
# - is_premium / quota / has_feature (если надо) — можно убрать для первой версии

# from your_bot_module import (
#     client, conversation_history, trim_history, save_history,
#     detect_emotion_reaction, detect_topic_and_react,
#     LANG_PROMPTS, MODES, user_modes, user_languages
# )

# На первое время добавим простые дефолты, чтобы не падать, если чего-то нет:
try:
    from your_bot_module import client
except Exception:
    client = None  # замените на ваш клиент

LANG_PROMPTS = globals().get("LANG_PROMPTS", {"ru": "Ты заботливый ассистент.", "en": "You are a caring assistant."})
MODES = globals().get("MODES", {"support": {"ru": "Режим поддержки.", "en": "Support mode."}})
user_modes = globals().get("user_modes", {})
user_languages = globals().get("user_languages", {})

conversation_history: Dict[str, List[Dict[str, Any]]] = globals().get("conversation_history", {})

def trim_history(messages: List[Dict[str, Any]], max_tokens: int = 4000) -> List[Dict[str, Any]]:
    # заглушка: если у тебя уже есть своя – импортни её и убери эту
    return messages[-20:]

def save_history(_): 
    pass

def detect_emotion_reaction(text: str, lang: str) -> str:
    return ""

def detect_topic_and_react(text: str, lang: str) -> str:
    return ""

async def generate_reply(user_id: str, session_id: str, text: str) -> str:
    """
    Минимальный «ядро»-ответ без Telegram-обвязки: 
    строим system prompt, ведём историю, зовём LLM, возвращаем строку.
    """
    uid = user_id
    lang_code = user_languages.get(uid, "ru")

    lang_prompt = LANG_PROMPTS.get(lang_code, LANG_PROMPTS["ru"])
    mode = user_modes.get(uid, "support")
    mode_prompt = MODES.get(mode, MODES["support"]).get(lang_code, MODES["support"]["ru"])

    guard_map = {
        "ru": "Если пользователь просит сказку — не пиши её здесь; предложи отдельный режим «Сказка».",
        "uk": "Якщо користувач просить казку — не пиши її тут; запропонуй режим «Казка».",
        "en": "If the user asks for a bedtime story, do not write it here; suggest a separate Story mode.",
    }
    guard = guard_map.get(lang_code, guard_map["ru"])

    system_prompt = f"{lang_prompt}\n\n{mode_prompt}\n\n{guard}"

    # инициализируем историю для пользователя
    if uid not in conversation_history:
        conversation_history[uid] = [{"role": "system", "content": system_prompt}]
    else:
        # обновим system в начале
        conversation_history[uid][0] = {"role": "system", "content": system_prompt}

    conversation_history[uid].append({"role": "user", "content": text})
    messages = trim_history(conversation_history[uid])

    # Вызов LLM (замени на свой клиент)
    if client is None:
        # заглушка, пока нет клиента
        reply = f"Эхо: {text}"
    else:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply = (resp.choices[0].message.content or "").strip() or "…"

    reaction = detect_emotion_reaction(text, lang_code) + detect_topic_and_react(text, lang_code)
    final_text = (reaction + reply).strip()

    # сохранить в историю
    conversation_history[uid].append({"role": "assistant", "content": final_text})
    try:
        save_history(conversation_history)
    except Exception:
        pass

    return final_text
