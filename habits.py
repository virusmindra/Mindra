# habits.py

import json, os

HABITS_FILE = "habits.json"

def load_habits():
    if os.path.exists(HABITS_FILE):
        with open(HABITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_habits(data):
    with open(HABITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_habit(user_id, text):
    habits = load_habits()
    if user_id not in habits:
        habits[user_id] = []
    habits[user_id].append({"text": text, "done": False})
    save_habits(habits)

def get_habits(user_id):
    return load_habits().get(user_id, [])

def mark_habit_done(user_id, index):
    habits = load_habits()
    if user_id in habits and 0 <= index < len(habits[user_id]):
        habits[user_id][index]["done"] = True
        save_habits(habits)
        return True
    return False

def delete_habit(user_id, index):
    habits = load_habits()
    if user_id in habits and 0 <= index < len(habits[user_id]):
        habits[user_id].pop(index)
        save_habits(habits)
        return True
    return False
