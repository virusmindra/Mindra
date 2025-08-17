# config.py
import os
import openai

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "").strip()

openai.api_key = OPENAI_API_KEY  # Инициализируем ключ для OpenAI API

# Создаём клиента (для новых версий OpenAI, 1.x+)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

PREMIUM_USERS = {"7775321566"}
