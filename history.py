import os
import json

HISTORY_FILE = "dialogues.json"

# Загрузка истории из файла
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохранение истории в файл
def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Ограничение длины истории (оставим последние 10 сообщений + system)
def trim_history(history, max_messages=10):
    system_prompt = history[0]  # system всегда остаётся
    trimmed = history[-max_messages:] if len(history) > max_messages else history[1:]
    return [system_prompt] + trimmed
