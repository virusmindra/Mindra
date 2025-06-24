# goals.py

import json
import os

GOALS_FILE = "goals.json"

# Загружаем цели
def load_goals():
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохраняем цели
def save_goals(data):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Добавляем новую цель
def add_goal(user_id, goal_text):
    goals = load_goals()
    if user_id not in goals:
        goals[user_id] = []
    goals[user_id].append({"text": goal_text, "done": False})
    save_goals(goals)
