# web_api/core.py
import os
from collections import defaultdict, deque
from typing import Deque, Dict, List, AsyncGenerator

from openai import AsyncOpenAI

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# per-session история (in-memory)
_history: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=20))

SYSTEM_PROMPT = (
    "You are Mindra, a warm, supportive assistant. "
    "Be concise, friendly, and helpful. "
    "If user speaks Russian, reply in Russian; otherwise reply in the user's language."
)

def _pack_messages(key: str, user_text: str):
    h = _history[key]
    messages: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += list(h)
    messages.append({"role": "user", "content": user_text})
    return messages, h

async def generate_reply(user_id: str, session_id: str, text: str) -> str:
    """Нестримо­вый ответ (для старого эндпоинта)."""
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text)

    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
    )
    reply = (resp.choices[0].message.content or "").strip() or "…"

    # обновим историю
    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": reply})
    return reply

async def generate_reply_stream(user_id: str, session_id: str, text: str) -> AsyncGenerator[str, None]:
    """
    Стрим по токенам: выдаёт маленькие кусочки текста (строки).
    Готов к прокидке через SSE.
    """
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text)

    stream = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
        stream=True,
    )

    full: List[str] = []
    async for event in stream:
        for choice in event.choices:
            delta = getattr(choice, "delta", None)
            if delta and delta.content:
                full.append(delta.content)
                yield delta.content

    # сохраним историю по завершении
    final_text = "".join(full).strip() or "…"
    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": final_text})

