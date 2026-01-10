# web_api/app.py (самые первые строки)
import os, sys, re
ROOT = os.path.dirname(os.path.abspath(__file__))      # /.../src/web_api
PARENT = os.path.dirname(ROOT)                          # /.../src
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import Optional
# локальные импорты из пакета web_api
from web_api.goals_api import router as goals_router
from web_api.habits_api import router as habits_router
from web_api.core import generate_reply, generate_reply_stream  # сигнатура с feature/source поддерживается
from elevenlabs.client import ElevenLabs

router = APIRouter()


# ---------- Pydantic-схемы (объявляем ДО использования) ----------
class ChatIn(BaseModel):
    userId: str | None = None
    sessionId: str | None = None
    input: str
    feature: str | None = None
    source: str | None = None

    # ✅ новые поля для web
    lang: str | None = "en"          # "en" | "es"
    wantVoice: bool | None = False   # premium voice (ElevenLabs)

class ChatOut(BaseModel):
    reply: str

class WebChatRequest(BaseModel):
    session_id: str
    text: str
    feature: Optional[str] = None
    source: Optional[str] = "web"


def extract_goal_suggestion(reply: str) -> dict | None:
    """
    Пытаемся достать цель из ответа, чтобы фронт мог показать кнопку:
    ➕ Сохранить как цель

    Возвращаем {"text": "..."} или None.
    """
    if not reply:
        return None

    text = reply.strip()

    # 1) Если в ответе есть строка "Цель: ...."
    m = re.search(r"(?:^|\n)\s*Цель\s*:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    if m:
        goal = m.group(1).strip().strip('"').strip("'")
        goal = re.sub(r"\s+", " ", goal)[:180]
        if len(goal) >= 6:
            return {"text": goal}

    # 2) Если модель пишет "Я сохранила/сохранил твою цель: ...."
    m2 = re.search(r"(?:цель|goal)\s*[:\-]\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    if m2:
        goal = m2.group(1).strip().strip('"').strip("'")
        goal = re.sub(r"\s+", " ", goal)[:180]
        if len(goal) >= 6:
            return {"text": goal}

    # 3) Fallback: берём первую строку (если она не супер длинная)
    first_line = text.split("\n", 1)[0].strip()
    first_line = re.sub(r"\s+", " ", first_line)
    if 10 <= len(first_line) <= 140:
        return {"text": first_line}

    return None

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "")  # поставь свою дефолтную voice id
ELEVEN_MODEL_ID = os.getenv("ELEVEN_MODEL_ID", "eleven_multilingual_v2")

_eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY) if ELEVEN_API_KEY else None

def estimate_seconds(text: str) -> int:
    # MVP оценка: 14 chars/sec
    t = (text or "").strip()
    return max(1, round(len(t) / 14)) if t else 1

def eleven_tts_to_mp3(text: str) -> tuple[str, int] | None:
    """
    Возвращает (path_to_mp3, seconds)
    """
    if not _eleven_client or not ELEVEN_VOICE_ID:
        return None

    seconds = estimate_seconds(text)

    out_path = f"/tmp/mindra_{uuid.uuid4().hex}.mp3"

    audio = _eleven_client.text_to_speech.convert(
        voice_id=ELEVEN_VOICE_ID,
        model_id=ELEVEN_MODEL_ID,
        text=text,
        output_format="mp3_44100_128",
    )

    with open(out_path, "wb") as f:
        # audio может быть генератором чанков
        if isinstance(audio, (bytes, bytearray)):
            f.write(audio)
        else:
            for chunk in audio:
                if chunk:
                    f.write(chunk)

    return out_path, seconds

# ---------- Приложение ----------
app = FastAPI(title="Mindra Web API", version="1.0.0")

import time
import uuid
from fastapi.responses import FileResponse

_AUDIO_STORE: dict[str, dict] = {}  # key -> {"path": str, "expires": float, "seconds": int}

def _audio_put(path: str, seconds: int, ttl_sec: int = 3600) -> str:
    key = uuid.uuid4().hex
    _AUDIO_STORE[key] = {"path": path, "expires": time.time() + ttl_sec, "seconds": int(seconds)}
    return key

def _audio_get(key: str):
    rec = _AUDIO_STORE.get(key)
    if not rec:
        return None
    if rec["expires"] < time.time():
        try:
            os.remove(rec["path"])
        except Exception:
            pass
        _AUDIO_STORE.pop(key, None)
        return None
    return rec

@app.get("/api/audio/{key}")
async def get_audio(key: str):
    rec = _audio_get(key)
    if not rec:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return FileResponse(rec["path"], media_type="audio/mpeg")

@app.get("/")
async def health():
    return {"ok": True, "service": "mindra-web-api"}

# Нестримо­вый чат
@app.post("/api/web-chat")
async def web_chat(payload: ChatIn, req: Request):
    try:
        user_id = payload.userId or "web"
        session_id = payload.sessionId or "default"
        text = (payload.input or "").strip()
        feature = payload.feature or "default"
        source = payload.source or "web"

        # ✅ безопасно читаем wantVoice даже если поля нет
        want_voice = bool(getattr(payload, "wantVoice", False))

        if not text:
            return {"reply": "Пустое сообщение.", "goal_suggestion": None}

        reply = await generate_reply(
        user_id,
        session_id,
        text,
        feature=feature,
        source=source,
        lang=payload.lang or "en",
    )

        goal_suggestion = None
        if feature == "goals":
            goal_suggestion = extract_goal_suggestion(reply)

        tts_block = None
want_voice = bool(payload.wantVoice)

if want_voice:
    try:
        tts_res = eleven_tts_to_mp3(reply)
        if tts_res:
            path, seconds = tts_res
            key = _audio_put(path, seconds, ttl_sec=3600)

            # audio url для сайта
            base = str(req.base_url).rstrip("/")  # например https://xxx.onrender.com
            audio_url = f"{base}/api/audio/{key}"

            tts_block = {
                "provider": "elevenlabs",
                "seconds": int(seconds),
                "audioUrl": audio_url,
            }
    except Exception as e:
        print("ELEVEN TTS ERROR:", repr(e))
        tts_block = None

        return {
        "reply": reply,
        "goal_suggestion": goal_suggestion,
        "tts": tts_block,  # ✅ вот это увидит Next.js и спишет секунды
    }

    except Exception as e:
        print("WEB_CHAT ERROR:", repr(e))
        return JSONResponse(
            {"reply": f"Ошибка сервера: {e!r}", "goal_suggestion": None},
            status_code=200,
        )
        
# SSE-стрим
@app.post("/api/web-chat-stream")
async def web_chat_stream(payload: ChatIn):
    user_id = payload.userId or "web"
    session_id = payload.sessionId or "default"
    text = (payload.input or "").strip()
    feature = payload.feature or "default"
    source = payload.source or "web"

    async def token_generator():
        try:
            async for chunk in generate_reply_stream(user_id, session_id, text, feature=feature, source=source):
                yield f"data:{chunk}\n\n"
                await asyncio.sleep(0)
            yield "event:end\ndata:[DONE]\n\n"
        except Exception as e:
            yield f"event:error\ndata:{repr(e)}\n\n"
            yield "event:end\ndata:[DONE]\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")

# Подключаем роутеры целей и привычек
app.include_router(goals_router)
app.include_router(habits_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или конкретный домен Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
