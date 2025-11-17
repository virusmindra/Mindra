# web_api/app.py (самые первые строки)
import os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))      # /.../src/web_api
PARENT = os.path.dirname(ROOT)                          # /.../src
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# локальные импорты из пакета web_api
from web_api.goals_api import router as goals_router
from web_api.habits_api import router as habits_router
from web_api.core import generate_reply, generate_reply_stream  # сигнатура с feature/source поддерживается

# ---------- Pydantic-схемы (объявляем ДО использования) ----------
class ChatIn(BaseModel):
    userId: str | None = None
    sessionId: str | None = None
    input: str
    feature: str | None = None
    source: str | None = None

class ChatOut(BaseModel):
    reply: str

# ---------- Приложение ----------
app = FastAPI(title="Mindra Web API", version="1.0.0")

@app.get("/")
async def health():
    return {"ok": True, "service": "mindra-web-api"}

# Нестримо­вый чат
@app.post("/api/web-chat", response_model=ChatOut)
async def web_chat(payload: ChatIn, req: Request):
    try:
        user_id = payload.userId or "web"
        session_id = payload.sessionId or "default"
        text = (payload.input or "").strip()
        feature = payload.feature or "default"
        source = payload.source or "web"

        if not text:
            return {"reply": "Пустое сообщение."}

        reply = await generate_reply(user_id, session_id, text, feature=feature, source=source)
        return {"reply": reply}

    except Exception as e:
        # 👇 ВРЕМЕННЫЙ дебаг
        print("WEB_CHAT ERROR:", repr(e))
        return JSONResponse(
            {"reply": f"Ошибка сервера: {e!r}"},
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
