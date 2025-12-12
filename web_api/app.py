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

router = APIRouter()

# ---------- Pydantic-схемы (объявляем ДО использования) ----------
class ChatIn(BaseModel):
    userId: str | None = None
    sessionId: str | None = None
    input: str
    feature: str | None = None
    source: str | None = None

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
    
# ---------- Приложение ----------
app = FastAPI(title="Mindra Web API", version="1.0.0")

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

        if not text:
            return {"reply": "Пустое сообщение.", "goal_suggestion": None}

        reply = await generate_reply(
            user_id,
            session_id,
            text,
            feature=feature,
            source=source,
        )

        goal_suggestion = None
        if feature == "goals":
            goal_suggestion = extract_goal_suggestion(reply)

        return {"reply": reply, "goal_suggestion": goal_suggestion}

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
