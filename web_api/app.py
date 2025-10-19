# web_api/app.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
# web_api/app.py  (добавь сверху после app = FastAPI(...))
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mindra.group",              # твой домен
        "https://mindra-site.vercel.app",    # превью/верцел
        "http://localhost:3000",             # локалка
    ],
    allow_methods=["POST","GET","OPTIONS"],
    allow_headers=["*"],
)


app = FastAPI(title="Mindra Web API", version="1.0.0")

# TODO: импортируй реальную логику бота
# from handlers import generate_reply  # пример

async def generate_reply(user_id: str, session_id: str, text: str) -> str:
    # временный стаб
    return f"Эхо: {text}"

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
            return JSONResponse({"reply": "Пустое сообщение."})
        reply = await generate_reply(user_id, session_id, text)
        return {"reply": reply}
    except Exception as e:
        print("web_chat error:", repr(e))
        return JSONResponse({"reply": "Извини, сервер сейчас недоступен."}, status_code=200)
