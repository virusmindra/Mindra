# config.py
import os
import openai

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "").strip()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")

openai.api_key = OPENAI_API_KEY  # Инициализируем ключ для OpenAI API

# Создаём клиента (для новых версий OpenAI, 1.x+)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

PREMIUM_USERS = {"7775321566"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Папка для БД (можно переопределить через ENV)
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# Полные пути к БД (можно переопределить через ENV)
PREMIUM_DB_PATH = os.getenv("PREMIUM_DB_PATH", os.path.join(DATA_DIR, "premium.sqlite3"))
REMIND_DB_PATH  = os.getenv("REMIND_DB_PATH",  os.path.join(DATA_DIR, "reminders.sqlite3"))
