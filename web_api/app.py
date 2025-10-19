# web_api/app.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

# --- FastAPI app ---
app = FastAPI(title="Mindra Web API", version="1.0.0")

# --- CORS (если фронт стучится напрямую) ---
# Можно настроить через переменную окружения ALLOW_ORIGINS
# пример: "https://mindra.group,https://mindra-site.vercel.app,http://localhost:3000"
origins_env = os.getenv("ALLOW_ORIGINS", "")
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
if allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["*"],
    )

# --- Временная заглушка бота (замени на реальную логику) ---
async def generate_reply(user_id: str, session_id: str, text: str) -> str:
    return f"Эхо: {text}"

# --- Схемы ---
class ChatIn(BaseModel):
    userId: str | None = None
    sessionId: str | None = None
    input: str

class ChatOut(BaseModel):
    reply: str

# --- Роуты ---
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
            return JSONResponse({"reply": "Пустое сообщение."}, status_code=200)

        reply = await generate_reply(user_id, session_id, text)
        return {"reply": reply}
    except Exception as e:
        print("web_chat error:", repr(e))
        return JSONResponse({"reply": "Извини, сервер сейчас недоступен."}, status_code=200)
