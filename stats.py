import json
import os
from datetime import datetime

STATS_FILE = "data/stats.json"
GOALS_FILE = "goals.json"
HABITS_FILE = "habits.json"

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

def get_stats():
    # Загружаем цели
    goals_data = load_json_file(GOALS_FILE)
    completed_goals = 0
    for user_goals in goals_data.values():
        for goal in user_goals:
            if goal.get("done"):
                completed_goals += 1

    # Загружаем привычки
    habits_data = load_json_file(HABITS_FILE)
    completed_habits = 0
    for user_habits in habits_data.values():
        for habit in user_habits:
            if habit.get("done"):  # если у тебя поле done
                completed_habits += 1

    # Дни активности можно считать по количеству уникальных пользователей
    total_users = len(goals_data.keys())

    return {
        "total_users": total_users,
        "completed_goals": completed_goals,
        "completed_habits": completed_habits,
        "days_active": 25,  # 👈 сюда можно добавить реальную логику
        "mood_entries": 14  # 👈 сюда тоже, если будешь хранить mood.json
    }
