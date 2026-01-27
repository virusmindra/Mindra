# web_api/core.py
import os
import json
from collections import defaultdict, deque
from typing import Deque, Dict, List, AsyncGenerator, Optional, Any

from openai import AsyncOpenAI

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# per-session история (in-memory)
_history: Dict[str, Deque[dict]] = defaultdict(lambda: deque(maxlen=20))

SYSTEM_PROMPT_BASE = """
You are Mindra, a warm, supportive AI friend and gentle coach.

IMPORTANT LANGUAGE RULES:
- You must respond ONLY in {LANG_NAME}.
- If the user writes in another language, still respond ONLY in {LANG_NAME}.
- Never use Russian or any other language.
- Do not mix languages.

STYLE:
- Sound human, warm, caring, and a bit playful when appropriate.
- Keep it concise, friendly, and easy to read.
- Use emojis sometimes, not in every sentence.
- No markdown formatting. Do not use #, **, bullet lists with - or *.
- Use short paragraphs separated by a blank line (double line breaks).
- Do not use triple quotes.
- Do not mention being an AI model.
- Do not give medical advice, diagnoses, or treatment instructions. If the user asks medical questions, encourage contacting a professional and offer emotional support and general wellness-safe suggestions.

DIALOG FLOW (CRITICAL):
- Always end your message with ONE clear, natural question that helps the conversation continue.
- The question must be relevant to what the user just said.
- If the user expresses an emotion (sad, anxious, angry, lonely), first validate it gently, then offer 1–2 simple options or a small next step, then ask a question.

TRUTHFULNESS:
- If you are not sure, say you’re not fully sure and suggest a safe next step.

GOALS/HABITS:
- When talking about a goal or habit, write it without quotes like:
  Goal: go to the gym 3 times a week
- Keep goals realistic, focus on small next steps.
"""

def build_system_prompt(feature: Optional[str], source: Optional[str], lang: Optional[str] = "en") -> str:
    lang = (lang or "en").lower().strip()
    if lang.startswith("es"):
        lang_key = "es"
        lang_name = "Spanish"
    else:
        lang_key = "en"
        lang_name = "English"

    prompt = SYSTEM_PROMPT_BASE.replace("{LANG_NAME}", lang_name)

    if source == "web":
        prompt += """
WEB APP CONTEXT:
- The user is chatting in the Mindra web app.
- Do not mention Telegram commands, bots, slash-commands, or Telegram-specific UI.
- Keep replies optimized for web chat: short paragraphs, clear tone, quick empathy, light emojis.
"""
    elif source == "telegram":
        prompt += """
TELEGRAM CONTEXT:
- The user is chatting in Telegram.
- You may briefly mention buttons or simple commands ONLY if it clearly helps.
"""

    section_descriptions_en = {
        "goals": "Focus: goals. Help clarify goals, make them measurable, and suggest one small next step.",
        "habits": "Focus: habits. Help build routines, reduce friction, and support consistency gently.",
        "reminders": "Focus: reminders and check-ins. Help the user remember actions and plan follow-ups.",
        "challenges": "Focus: challenges. Motivate, celebrate progress, suggest one concrete task.",
        "sleep_sounds": "Focus: sleep and relaxation. Speak softly, suggest calming routines and wind-down ideas.",
        "bedtime_stories": "Focus: bedtime stories. Tell short cozy stories; avoid anything scary or stressful.",
        "daily_tasks": "Focus: daily tasks. Help pick 1–3 small realistic tasks for today.",
        "modes": "Focus: conversation modes. Help choose or adjust the style (flirty/friendly/coach).",
        "points": "Focus: points and titles. Celebrate achievements, keep it light and motivating.",
    }
    section_descriptions_es = {
        "goals": "Enfoque: metas. Ayuda a aclarar metas, hacerlas medibles y proponer un pequeño siguiente paso.",
        "habits": "Enfoque: hábitos. Ayuda a crear rutinas, bajar la fricción y apoyar la constancia con cariño.",
        "reminders": "Enfoque: recordatorios y check-ins. Ayuda a recordar acciones y planear seguimientos.",
        "challenges": "Enfoque: desafíos. Motiva, celebra el progreso y propone una tarea concreta.",
        "sleep_sounds": "Enfoque: sueño y relajación. Habla suave y sugiere rutinas calmantes.",
        "bedtime_stories": "Enfoque: cuentos para dormir. Cuenta historias cortas y acogedoras; nada estresante.",
        "daily_tasks": "Enfoque: tareas diarias. Ayuda a elegir 1–3 tareas pequeñas y realistas para hoy.",
        "modes": "Enfoque: modos de conversación. Ayuda a elegir o ajustar el estilo (coqueta/amigable/coach).",
        "points": "Enfoque: puntos y títulos. Celebra logros con energía suave y sin presión.",
    }

    if feature and feature != "default":
        if lang_key == "es":
            desc = section_descriptions_es.get(feature, "Estás en una sección específica. Adapta la respuesta a ese enfoque.")
        else:
            desc = section_descriptions_en.get(feature, "You are in a specific feature section. Tailor your answer to this focus.")
        prompt += "\n" + desc + "\n"

    # important guard
    prompt += """
IMPORTANT:
- Never say you cannot set reminders. In this web app, you can help the user set a reminder by confirming the text and time.
- If the user asks for a timer or reminder, respond as if you can help: propose the reminder text + time and ask to confirm.
"""

    return prompt


def _pack_messages(
    key: str,
    user_text: str,
    feature: Optional[str] = None,
    source: Optional[str] = None,
    lang: Optional[str] = "en",
):
    h = _history[key]
    system_prompt = build_system_prompt(feature, source, lang=lang)
    messages: List[dict] = [{"role": "system", "content": system_prompt}]
    messages += list(h)
    messages.append({"role": "user", "content": user_text})
    return messages, h


def _apply_memory_context(messages: List[dict], memory_context: Optional[dict], lang: Optional[str]) -> None:
    if not memory_context:
        return

    prof = (memory_context.get("profile") or {}) if isinstance(memory_context, dict) else {}
    mems = memory_context.get("memories") or [] if isinstance(memory_context, dict) else []

    picked: List[str] = []
    for m in mems[:10]:
        c = str((m or {}).get("content") or "").strip()
        if c:
            picked.append(c)
        if len(picked) >= 2:
            break

    if not (prof or picked):
        return

    extra = "\n\nMEMORY (use subtly, do not list):\n"
    if prof.get("name"):
        extra += f"- Name: {prof.get('name')}\n"
    if prof.get("about"):
        extra += f"- About: {prof.get('about')}\n"
    if prof.get("style"):
        extra += f"- Style: {prof.get('style')}\n"
    for c in picked:
        extra += f"- {c}\n"

    extra += "\nRULE: Sometimes (not always) naturally reference 1 memory as a human would. Keep it warm, not creepy.\n"

    messages[0]["content"] = (messages[0].get("content") or "").rstrip() + extra


async def extract_memory_updates(lang: str, user_text: str, assistant_text: str) -> dict:
    system = (
        "You are a memory extractor for a coaching companion app.\n"
        "Return STRICT JSON only.\n"
        "Goal: extract small stable facts worth remembering.\n"
        "Do NOT include sensitive medical/legal diagnoses.\n"
        "If nothing worth saving, return {\"profile\": null, \"memories\": []}.\n"
        "JSON schema:\n"
        "{\n"
        "  \"profile\": {\"name\": string|null, \"about\": string|null, \"style\": string|null} | null,\n"
        "  \"memories\": [\n"
        "     {\"kind\": \"goal\"|\"pref\"|\"bio\"|\"relationship\"|\"work\"|\"routine\"|\"note\", \"content\": string, \"salience\": 1|2|3}\n"
        "  ]\n"
        "}\n"
    )

    prompt = (
        f"LANG={lang}\n"
        f"USER:\n{user_text}\n\n"
        f"ASSISTANT:\n{assistant_text}\n\n"
        "Extract memory updates."
    )

    r = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    raw = (r.choices[0].message.content or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"profile": None, "memories": []}


async def generate_reply(
    user_id: str,
    session_id: str,
    text: str,
    feature: Optional[str] = None,
    source: Optional[str] = None,
    lang: Optional[str] = "en",
    memory_context: Optional[dict] = None,
) -> str:
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text, feature=feature, source=source, lang=lang)

    _apply_memory_context(messages, memory_context, lang)

    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
    )
    reply = (resp.choices[0].message.content or "").strip() or "…"

    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": reply})
    return reply


async def generate_reply_stream(
    user_id: str,
    session_id: str,
    text: str,
    feature: Optional[str] = None,
    source: Optional[str] = None,
    lang: Optional[str] = "en",
    memory_context: Optional[dict] = None,
) -> AsyncGenerator[str, None]:
    key = f"{user_id}:{session_id}"
    messages, h = _pack_messages(key, text, feature=feature, source=source, lang=lang)

    _apply_memory_context(messages, memory_context, lang)

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
            if delta and getattr(delta, "content", None):
                chunk = delta.content
                full.append(chunk)
                yield chunk

    final_text = "".join(full).strip() or "…"
    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": final_text})

