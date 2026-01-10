import os, uuid, shutil, subprocess
from typing import Tuple, Optional

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


def _trim_silence(src_mp3: str) -> str:
    if not shutil.which("ffmpeg"):
        return src_mp3

    out_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    cmd = [
        "ffmpeg", "-y",
        "-i", src_mp3,
        "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.2",
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
    from gtts import gTTS  # 👈 ленивый импорт
    mp3_path = f"/tmp/{uuid.uuid4().hex}.mp3"
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
    Всегда возвращает путь к mp3 или кидает исключение.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")

    # эмоции/паузы (optional)
    try:
        text = _expressive(text, lang)
    except Exception:
        pass

    # профиль (optional)
    try:
        p = _vp(uid)  # если есть
    except Exception:
        p = {}

    engine = str(p.get("engine", "eleven")).lower()
    speed = float(p.get("speed", 1.0) or 1.0)
    accent = p.get("accent", "com")
    voice_id = (
        (p.get("voice_id") or "").strip()
        or os.getenv("ELEVEN_VOICE_ID", "").strip()
        or "21m00Tcm4TlvDq8ikWAM"
    )

    mp3_path = None  # ✅ важно

    # 1) Пытаемся ElevenLabs если ключ есть и engine=eleven
    use_eleven = bool(os.getenv("ELEVEN_API_KEY")) and engine == "eleven"
    if use_eleven:
        try:
            mp3_path = _tts_elevenlabs_to_mp3(text[:600], voice_id)
        except Exception as e:
            print("TTS Eleven failed, fallback to gTTS:", repr(e))
            mp3_path = None

    # 2) Fallback на gTTS (если eleven не использовали или упал)
    if not mp3_path:
        mp3_path = _tts_gtts_to_mp3(text[:600], lang=lang, tld=accent)

    # 3) Пост-обработка
    try:
        mp3_path = _trim_silence(mp3_path)
    except Exception as e:
        print("TTS trim failed:", repr(e))

    try:
        mp3_path = _to_mp3_with_speed(mp3_path, speed=speed)
    except Exception as e:
        print("TTS speed failed:", repr(e))

    return mp3_path

