from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile, os, uuid

@app.post("/api/call/turn")
async def call_turn(
    req: Request,
    audio: UploadFile = File(...),
    user_id: str = Form("web"),
    sessionId: str = Form("call"),
    feature: str = Form("call"),
    lang: str = Form("en"),
    wantVoice: str = Form("1"),  # "1"/"0"
):
    try:
        want_voice = wantVoice in ("1", "true", "True", "yes", "on")

        # 1) сохраняем файл
        suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
        in_path = os.path.join(tempfile.gettempdir(), f"call_{uuid.uuid4().hex}{suffix}")
        with open(in_path, "wb") as f:
            f.write(await audio.read())

        # 2) ТРАНСКРИПЦИЯ
        # ⚠️ тут вызови свой Whisper/ASR.
        # Ниже — пример через OpenAI (если у тебя уже подключено). Замени на свою реализацию.
        transcript = await transcribe_audio_to_text(in_path, lang=lang)  # <- сделай эту функцию

        transcript = (transcript or "").strip()
        if not transcript:
            return {"ok": True, "transcript": "", "reply": "I didn't catch that 🙈 Try again.", "tts": None}

        # 3) ответ модели (у тебя уже есть)
        reply = await generate_reply(
            user_id,
            sessionId,
            transcript,
            feature=feature,
            source="web_call",
            lang=lang,
        )

        # 4) голос
        voice_blocked = False
        voice_reason = None
        tts_block = None

        if want_voice:
            # залогин чек: если "web" — не даём
            if not user_id or user_id == "web":
                voice_blocked = True
                voice_reason = "login_required"
            else:
                try:
                    tts_text = (reply.split("\n\n", 1)[0] or reply).strip()[:600]
                    mp3_path = synthesize_to_mp3(tts_text, lang=lang, uid=user_id)
                    seconds = 0  # можно посчитать, но MVP ок без этого

                    key = _audio_put(mp3_path, seconds, ttl_sec=3600)
                    base = str(req.base_url).rstrip("/")
                    audio_url = f"{base}/api/audio/{key}"

                    tts_block = {
                        "provider": "mp3",
                        "seconds": seconds,
                        "audioUrl": audio_url,
                    }
                except Exception as e:
                    print("CALL TTS ERROR:", repr(e))
                    voice_blocked = True
                    voice_reason = "temporarily_unavailable"
                    tts_block = None

        # cleanup input file
        try:
            os.remove(in_path)
        except Exception:
            pass

        return {
            "ok": True,
            "transcript": transcript,
            "reply": reply,
            "tts": tts_block,
            "voiceBlocked": voice_blocked,
            "voiceReason": voice_reason,
        }

    except Exception as e:
        print("CALL TURN ERROR:", repr(e))
        return JSONResponse(
            {"ok": False, "error": "Server error 😕"},
            status_code=200
        )

