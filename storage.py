# storage.py

from collections import defaultdict
from storage_goals import get_goals as _get_goals_file
from storage_goals import mark_goal_done as _mark_goal_done_file
from storage_goals import load_goals, save_goals

# Временное хранилище в памяти
user_goals = defaultdict(list)


GOALS_FILE = Path("user_goals.json")

def load_goals():
    if GOALS_FILE.exists():
        with GOALS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_goals(data):
    with GOALS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_goal(user_id, goal_text, deadline=None, remind=False):
    user_id = str(user_id)
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

def get_goals(user_id):
    user_id = str(user_id)
    goals = load_goals()
    return goals.get(user_id, [])

def mark_goal_done(user_id, index):
    user_id = str(user_id)
    goals_all = load_goals() or {}

    if isinstance(goals_all, list):  # на всякий
        goals_all = {user_id: goals_all}

    # нормализуем ключи
    if user_id not in goals_all:
        goals_all = {str(k): v for k, v in goals_all.items()}

    items = goals_all.get(user_id, [])
    if not (0 <= index < len(items)):
        return False

    item = items[index]
    if isinstance(item, dict):
        item["done"] = True
    else:
        item = {"text": str(item), "done": True}
        items[index] = item

    goals_all[user_id] = items
    save_goals(goals_all)
    return True
