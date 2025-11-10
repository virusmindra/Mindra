# web_api/core.py
import os
from collections import defaultdict, deque
from typing import Deque, Dict, List, AsyncGenerator

from openai import AsyncOpenAI

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# per-session история (in-memory)
_history: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=20))

SYSTEM_PROMPT_BASE = (
    "You are Mindra, a warm, supportive assistant. "
    "Be concise, friendly, and helpful. "
    "If user speaks Russian, reply in Russian; otherwise reply in the user's language."
)


def build_system_prompt(feature: str | None, source: str | None) -> str:
    prompt = SYSTEM_PROMPT_BASE

    # источник: сайт vs Telegram
    if source == "web":
        prompt += (
            " The user is chatting with you in the Mindra web app. "
            "Do not mention Telegram commands, bots, or slash-commands. "
            "Write answers that look good in a web chat UI: short paragraphs, emojis when appropriate."
        )
    elif source == "telegram":
        prompt += (
            " The user is chatting with you in Telegram. "
            "You may briefly mention buttons or commands that exist in the bot if it helps."
        )

    # фокус/раздел (feature)
    section_descriptions = {
        "goals": (
            "The current focus is goals. Help the user formulate, clarify and track personal goals. "
            "Encourage clear, measurable goals and small next steps."
        ),
        "habits": (
            "The current focus is habits. Help the user build and maintain healthy habits and routines. "
            "Think in terms of small daily actions and streaks."
        ),
        "reminders": (
            "The current focus is reminders and check-ins. Help the user remember important actions, "
            "review their day, and plan short follow-ups."
        ),
        "challenges": (
            "The current focus is premium challenges. Motivate the user to participate in challenges, "
            "celebrate their progress, and suggest concrete tasks."
        ),
        "sleep_sounds": (
            "The current focus is sleep and relaxation. Speak softly and calmly, suggest sounds or routines "
            "that help unwind and relax before sleep."
        ),
        "bedtime_stories": (
            "The current focus is bedtime stories. You can tell short, cozy stories that help the user relax "
            "and feel safe. Avoid horror or anything stressful."
        ),
        "daily_tasks": (
            "The current focus is daily tasks. Help the user choose 1–3 small tasks for today and keep them realistic."
        ),
        "modes": (
            "The current focus is conversation modes (e.g., flirty, friendly, coach, therapist-like). "
            "Help the user choose or adjust the style that feels best for them."
        ),
        "points": (
            "The current focus is points and titles, like a little game. Celebrate achievements, unlock titles, "
            "and motivate the user gently without pressure."
        ),
    }

    if feature and feature != "default":
        desc = section_descriptions.get(
            feature,
            "The user is in a specific feature section of the app. Tailor your answer to this focus.",
        )
        prompt += " " + desc

    return prompt


def _pack_messages(
    key: str,
    user_text: str,
    feature: str | None = None,
    source: str | None = None,
):
    h = _history[key]
    system_prompt = build_system_prompt(feature, source)
    messages: List[dict] = [{"role": "system", "content": system_prompt}]
    messages += list(h)
    messages.append({"role": "user", "content": user_text})
    return messages, h


async def generate_reply(
    user_id: str,
    session_id: str,
    text: str,
    feature: str | None = None,
    source: str | None = None,
) -> str:
    """Нестримо­вый ответ (для старого эндпоинта)."""
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text, feature=feature, source=source)

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


async def generate_reply_stream(
    user_id: str,
    session_id: str,
    text: str,
    feature: str | None = None,
    source: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Стрим по токенам: выдаёт маленькие кусочки текста (строки).
    Готов к прокидке через SSE.
    """
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text, feature=feature, source=source)

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
