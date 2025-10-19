# web_api/app.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from core import generate_reply  # <- твоя реальная логика

app = FastAPI(title="Mindra Web API", version="1.0.0")

class ChatIn(BaseModel):
    userId: str | None = None
    sessionId: str | None = None
    input: str

class ChatOut(BaseModel):
    reply: str

@app.get("/")
async def health():
    return {"ok": True, "service": "mindra-web-api"}

@app.post("/api/web-chat", response_model=ChatOut)
async def web_chat(payload: ChatIn, request: Request):
    try:
        user_id = payload.userId or "web"
        session_id = payload.sessionId or "default"
        text = (payload.input or "").strip()
        if not text:
            return {"reply": "Пустое сообщение."}
        reply = await generate_reply(user_id, session_id, text)
        return {"reply": reply}
    except Exception as e:
        print("web_chat error:", repr(e))
        return {"reply": "Извини, сервер сейчас недоступен."}
