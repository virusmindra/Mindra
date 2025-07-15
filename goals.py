import json
import os
from stats import add_points  # добавь в начало goals.py

GOALS_FILE = "goals.json"

def mark_goal_done(user_id, index):
    goals = load_goals()
    if user_id in goals and 0 <= index < len(goals[user_id]):
        goals[user_id][index]["done"] = True
        save_goals(goals)
        add_points(user_id, 10)  # начисляем 10 баллов
        return True
    return False

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

# Добавляем новую цель (с дедлайном и напоминанием)
def add_goal(user_id, goal_text, deadline=None, remind=False):
    goals = load_goals()
    if user_id not in goals:
        goals[user_id] = []
    goals[user_id].append({
        "text": goal_text,
        "done": False,
        "deadline": deadline,
        "remind": remind
    })
    save_goals(goals)

# Получаем цели
def get_goals(user_id):
    goals = load_goals()
    return goals.get(user_id, [])

# Отметить цель как выполненную
def mark_goal_done(user_id, index):
    goals = load_goals()
    if user_id in goals and 0 <= index < len(goals[user_id]):
        goals[user_id][index]["done"] = True
        save_goals(goals)
        return True
    return False

# Удалить цель
def delete_goal(user_id, index):
    goals = load_goals()
    if user_id in goals and 0 <= index < len(goals[user_id]):
        goals[user_id].pop(index)
        save_goals(goals)
        return True
    return False
