# web_api/core.py
import os
from collections import defaultdict, deque
from typing import Deque, Dict, List, AsyncGenerator

from openai import AsyncOpenAI

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# per-session история (in-memory)
_history: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=20))


SYSTEM_PROMPT = """
Ты — Mindra, тёплый поддерживающий AI-друг и коуч.
Помогаешь с целями, привычками, эмоциями и мотивацией.
Отвечай кратко, живо, по-дружески, с эмодзи, без диагнозов и медицины.
Не используй markdown-разметку (#, **, списки с - или *). Пиши обычный текст.
Разделяй абзацы пустой строкой (двойной перенос строки).
Не используй тройные кавычки и сложные конструкции, цель пиши без кавычек, например: Цель: ходить в зал 3 раза в неделю.
Если не знаешь, честно говори, что не уверена, и предлагай поддерживающий шаг.
"""


def build_system_prompt(feature: str | None, source: str | None) -> str:
    prompt = SYSTEM_PROMPT

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

# --- добавь рядом с SYSTEM_PROMPT ---

FEATURE_HINTS: dict[str, str] = {
    "default": "",
    "goals": (
        "РЕЖИМ: ЦЕЛИ И ПЛАНЫ.\n\n"
        "Когда пользователь просит помочь с целью (особенно про зал, тренировки, здоровье, похудение "
        "или набор массы), действуй по шагам.\n\n"
        "1) Помоги сформулировать 1–2 чёткие SMART-цели. Пиши без кавычек, например:\n"
        "   Цель: ходить в зал 3 раза в неделю (пн, ср, пт) в течение 2 месяцев, чтобы улучшить форму.\n\n"
        "2) Предложи конкретный план тренировок по дням недели: какие дни, какие группы мышц, по 4–6 упражнений "
        "с примерными подходами и повторами.\n\n"
        "3) Добавь короткие рекомендации по питанию и восстановлению: вода, сон 7–9 часов, больше белка, начинать мягко.\n\n"
        "4) В конце сделай мини-чек-лист в одну строку, например:\n"
        "   Чек-лист: записать цель, выбрать дни для зала, поставить напоминания, подготовить одежду.\n\n"
        "5) Заверши ответ тёплым вопросом вовлечения: хочешь, я сохраню это как цель и помогу следить за прогрессом?\n\n"
        "Пиши просто, по-дружески, с эмодзи, без медицинских терминов."
    ),
    "habits": (
        "User is in the Habits panel. Suggest small atomic daily/weekly habits, "
        "a simple cadence (e.g., daily/every other day), and short check-ins. "
        "Keep answers compact; prefer bullet points."
    ),
    "reminders": (
        "User is in the Reminders section. Talk about when and how to be reminded; "
        "propose practical schedules (morning/evening, weekdays) and short wording."
    ),
    "challenges": (
        "User is in Premium Challenges. Encourage participation, give clear rules, "
        "and propose a tiny step to start today."
    ),
    "sleep_sounds": (
        "User is in Sleep Sounds. Answer briefly with calm tone; any playback "
        "controls are handled by UI."
    ),
    "bedtime_stories": (
        "User is in Bedtime Stories. Tell short, cozy bedtime stories in 3–6 "
        "sentences unless asked for longer. Gentle, warm tone."
    ),
    "daily_tasks": (
        "User is in Daily Tasks. Suggest exactly one small actionable task for today."
    ),
    "modes": (
        "User is choosing conversation modes. Explain options briefly and help pick "
        "one based on their goal."
    ),
    "points": (
        "User is in Points/Titles. Celebrate progress, be encouraging; don't reveal "
        "internal scoring rules."
    ),
}

def _apply_feature_hint(messages: list[dict], feature: str | None, source: str | None) -> None:
    """Мягко модифицируем system-подсказку под выбранную фичу и источник."""
    # Берём уже построенный промпт (из build_system_prompt)
    base = messages[0].get("content") or SYSTEM_PROMPT

    # Дополнительно уточняем источник (если хочешь оставить это тут)
    if source:
        base += f" The request comes from the '{source}' client."

    hint = FEATURE_HINTS.get(feature or "default", "")
    if hint:
        messages[0]["content"] = base.rstrip() + "\n\n" + hint
    else:
        messages[0]["content"] = base


# --- обновленные функции ---

async def generate_reply(
    user_id: str,
    session_id: str,
    text: str,
    feature: str | None = None,
    source: str | None = None,
) -> str:
    """Нестримовый ответ."""
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text, feature=feature, source=source)

    # Подмешаем подсказку под режим
    _apply_feature_hint(messages, feature, source)

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
    """Стрим по токенам (SSE-совместимый)."""
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text, feature=feature, source=source)

    # Подмешаем подсказку под режим
    _apply_feature_hint(messages, feature, source)

    stream = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
        stream=True,
    )

    full: list[str] = []
    async for event in stream:
        for choice in event.choices:
            delta = getattr(choice, "delta", None)
            if delta and getattr(delta, "content", None):
                chunk = delta.content
                full.append(chunk)
                yield chunk

    final_text = "".join(full).strip() or "…"
    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": final_text})
