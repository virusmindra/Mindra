# web_api/app.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import asyncio

from core import generate_reply, generate_reply_stream
from goals_api import router as goals_router   # <--- НОВОЕ
from habits_api import router as habits_router 

app = FastAPI(title="Mindra Web API", version="1.0.0")

# зарегистрировать роутер целей
app.include_router(goals_router)
app.include_router(habits_router)

class ChatIn(BaseModel):
    userId: str | None = None
    sessionId: str | None = None
    input: str
    feature: str | None = "default"   # 👈

@app.post("/api/web-chat", response_model=ChatOut)
async def web_chat(payload: ChatIn, request: Request):
    ...
    feature = (payload.feature or "default").strip()
    ...
    reply = await generate_reply(user_id, session_id, text, feature=feature)  # 👈
    return {"reply": reply}

class ChatOut(BaseModel):
    reply: str


@app.get("/")
async def health():
    return {"ok": True, "service": "mindra-web-api"}


# обычный нестриминговый эндпоинт (как был)
@app.post("/api/web-chat", response_model=ChatOut)
async def web_chat(payload: ChatIn, request: Request):
    try:
        user_id = payload.userId or "web"
        session_id = payload.sessionId or "default"
        text = (payload.input or "").strip()
        feature = payload.feature or "default"
        source = payload.source or "web"

        if not text:
            return {"reply": "Пустое сообщение."}

        reply = await generate_reply(
            user_id=user_id,
            session_id=session_id,
            text=text,
            feature=feature,
            source=source,
        )
        return {"reply": reply}
    except Exception as e:
        print("web_chat error:", repr(e))
        # 200, чтобы фронт получал текст, а не падал по CORS
        return JSONResponse({"reply": "Извини, сервер сейчас недоступен."}, status_code=200)


# НОВОЕ: SSE-стрим
@app.post("/api/web-chat-stream")
async def web_chat_stream(payload: ChatIn):
    user_id = payload.userId or "web"
    session_id = payload.sessionId or "default"
    text = (payload.input or "").strip()
    feature = payload.feature or "default"
    source = payload.source or "web"

    async def token_generator():
        try:
            async for chunk in generate_reply_stream(
                user_id=user_id,
                session_id=session_id,
                text=text,
                feature=feature,
                source=source,
            ):
                # SSE кадры
                yield f"data:{chunk}\n\n"
                await asyncio.sleep(0)
            yield "event:end\ndata:[DONE]\n\n"
        except Exception as e:
            # отправим ошибку как SSE, чтобы клиент корректно завершился
            yield f"event:error\ndata:{repr(e)}\n\n"
            yield "event:end\ndata:[DONE]\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")

