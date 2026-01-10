import os, uuid, shutil, subprocess
from typing import Tuple, Optional
from gtts import gTTS

# если уже есть _expressive — используем его
# def _expressive(text: str, lang: str) -> str: ...

def _to_mp3_with_speed(src_mp3: str, speed: float = 1.0) -> str:
    """
    Меняет скорость через ffmpeg atempo и возвращает новый mp3.
    """
    if abs(speed - 1.0) < 0.01:
        return src_mp3

    if not shutil.which("ffmpeg"):
        # если ffmpeg нет — просто вернём исходник
        return src_mp3

    atempo = max(0.5, min(2.0, float(speed)))
    out_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    cmd = [
        "ffmpeg", "-y",
        "-i", src_mp3,
        "-filter:a", f"atempo={atempo}",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        os.remove(src_mp3)
    except Exception:
        pass

    return out_path


def _tts_gtts_to_mp3(text: str, lang: str, tld: str = "com") -> str:
    mp3_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    # gTTS реально поддерживает ограниченный набор кодов
    safe_lang = lang if lang in ("en", "es", "ru", "uk") else "en"
    gTTS(text=text, lang=safe_lang, tld=tld).save(mp3_path)
    return mp3_path


def _tts_elevenlabs_to_mp3(text: str, voice_id: str) -> str:
    """
    Твой ElevenLabs mp3.
    Если у тебя уже есть eleven_tts_to_mp3(text) -> (path, seconds),
    можно его использовать вместо этой функции.
    """
    from elevenlabs import ElevenLabs
    api_key = os.getenv("ELEVEN_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVEN_API_KEY not set")
    client = ElevenLabs(api_key=api_key)

    mp3_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        text=text,
        voice_settings={
            "stability": 0.35,
            "similarity_boost": 0.7,
            "style": 0.6,
            "use_speaker_boost": True,
        },
    )
    with open(mp3_path, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)
    return mp3_path


def synthesize_to_mp3(text: str, lang: str, uid: str) -> str:
    """
    Web-TTS (MP3). Похож на synthesize_to_ogg, только для браузера.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")

    # эмоции/паузы (если хочешь)
    try:
        text = _expressive(text, lang)
    except Exception:
        pass

    # твой профиль (если хочешь reuse из telegram)
    try:
        p = _vp(uid)  # если есть
    except Exception:
        p = {}

    engine = str(p.get("engine", "eleven")).lower()
    speed = float(p.get("speed", 1.0) or 1.0)
    accent = p.get("accent", "com")
    voice_id = p.get("voice_id", "")

    # ⚡️Fast MVP: если есть eleven ключ — используем его, иначе gTTS
    use_eleven = False
    try:
        use_eleven = (
            engine == "eleven"
            and bool(os.getenv("ELEVEN_API_KEY"))
            and bool(voice_id)
            and has_feature(uid, "eleven_tts")  # если хочешь премиум-гейт
        )
    except Exception:
        # если has_feature/_vp нет в web-контексте — просто ориентируемся на ключ
        use_eleven = bool(os.getenv("ELEVEN_API_KEY"))

    mp3_path = None
    if use_eleven:
        mp3_path = _tts_elevenlabs_to_mp3(text[:600], voice_id)
    else:
        mp3_path = _tts_gtts_to_mp3(text[:600], lang=lang, tld=accent)

    mp3_path = _to_mp3_with_speed(mp3_path, speed=speed)
    return mp3_path

