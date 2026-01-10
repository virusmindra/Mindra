# web_api/speech/stt.py

async def transcribe_audio_to_text(path: str, lang: str = "en") -> str:
    """
    Speech → Text (STT)

    TODO: подключи Whisper:
    - OpenAI Audio Transcription (рекомендую для MVP)
    - faster-whisper (локально, позже)
    """
    # пока заглушка
    return ""
