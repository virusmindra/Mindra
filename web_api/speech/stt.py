import os, uuid, shutil, subprocess, tempfile
from openai import OpenAI

client = OpenAI()  # берет OPENAI_API_KEY из env

def _ensure_wav(input_path: str) -> str:
    """
    Whisper умеет много форматов, но для стабильности (webm/ogg) конвертим в wav.
    Возвращает путь к wav (или исходник если ffmpeg нет).
    """
    if not shutil.which("ffmpeg"):
        return input_path

    ext = os.path.splitext(input_path)[1].lower()
    if ext in (".wav", ".mp3", ".m4a"):
        return input_path

    out_path = os.path.join(tempfile.gettempdir(), f"stt_{uuid.uuid4().hex}.wav")
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path

async def transcribe_audio_to_text(path: str, lang: str = "en") -> str:
    """
    Speech → Text (STT) через OpenAI Whisper.
    """
    wav_path = None
    try:
        wav_path = _ensure_wav(path)
        with open(wav_path, "rb") as f:
            # язык можно подсказать, но whisper-1 и так часто угадывает
            res = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                # language=lang,  # можно включить если хочешь жестко
            )
        # res.text в новых версиях клиента
        text = getattr(res, "text", None) or (res.get("text") if isinstance(res, dict) else "")
        return (text or "").strip()
    finally:
        # удаляем wav если он был создан конвертацией
        try:
            if wav_path and wav_path != path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass
