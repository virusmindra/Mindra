import json
import os
from datetime import datetime

STATS_FILE = "data/stats.json"
GOALS_FILE = "goals.json"
HABITS_FILE = "habits.json"

# Хранилище очков пользователей
user_points = {}

def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}, "premium_users": {}}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def add_premium(user_id):
    stats = load_stats()
    stats["premium_users"][str(user_id)] = datetime.utcnow().isoformat()
    save_stats(stats)

def add_points(user_id, points):
    stats = load_stats()
    user_id = str(user_id)
    if user_id not in stats:
        stats[user_id] = {"points": 0, "goals_completed": 0}
    stats[user_id]["points"] += points
    stats[user_id]["goals_completed"] += 1
    save_stats(stats)

def get_user_stats(user_id: str):
    if os.path.exists("stats.json"):
        with open("stats.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(user_id, {"points": 0})
    return {"points": 0}

def get_user_title(points: int) -> str:
    if points < 50:
        return "🌱 Новичок"
    elif points < 100:
        return "✨ Мотиватор"
    elif points < 250:
        return "🔥 Уверенный"
    elif points < 500:
        return "💎 Наставник"
    else:
        return "🌟 Легенда"

def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_stats(user_id):
    goals_data = load_json_file(GOALS_FILE)
    user_goals = goals_data.get(user_id, [])
    completed_goals = sum(1 for goal in user_goals if goal.get("done"))

    habits_data = load_json_file(HABITS_FILE)
    user_habits = habits_data.get(user_id, [])
    completed_habits = sum(1 for habit in user_habits if habit.get("done"))

    days_active = len(set(g.get("date") for g in user_goals if g.get("date"))) if user_goals else 0
    mood_entries = 0  # если есть mood.json — добавь подсчёт

    return {
        "completed_goals": completed_goals,
        "completed_habits": completed_habits,
        "days_active": days_active,
        "mood_entries": mood_entries
    }

# 📊 Получение статистики пользователя
def get_user_stats(user_id: str):
    from goals import get_goals  # если нужно
    from habits import get_habits  # если нужно
    from handlers import user_points  # или если user_points у тебя в stats.py, то не нужно импортировать

    goals = get_goals(user_id)
    total_goals = len(goals)
    completed_goals = len([g for g in goals if g.get("done")])

    habits = get_habits(user_id)
    total_habits = len(habits)

    points = 0
    # если user_points хранится в stats.py, то:
    global user_points
    points = user_points.get(user_id, 0)

    return {
        "points": points,
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "habits": total_habits
    }

# 🏅 Получение титула по очкам
def get_user_title(points: int):
    if points < 10:
        return "Новичок 💫"
    elif points < 30:
        return "Уверенный 🌟"
    elif points < 60:
        return "Мастер 💎"
    else:
        return "Легенда 🔥"

def add_points(user_id: str, amount: int):
    """Начислить пользователю очки."""
    global user_points
    current = user_points.get(user_id, 0)
    user_points[user_id] = current + amount
    return user_points[user_id]
