# storage.py — единый источник правды для целей (файл data/goals.json)
from pathlib import Path
import json

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

GOALS_FILE = DATA_DIR / "goals.json"

# ---------- low-level ----------
def load_goals():
    if GOALS_FILE.exists():
        with GOALS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_goals(data: dict):
    with GOALS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- high-level ----------
def get_goals(user_id):
    """Вернуть список целей пользователя (список dict)."""
    user_id = str(user_id)
    all_goals = load_goals() or {}
    # нормализуем ключи на строковые
    if user_id not in all_goals:
        all_goals = {str(k): v for k, v in all_goals.items()}
    return all_goals.get(user_id, [])

def add_goal(user_id, text, deadline=None, remind=False, extra: dict | None = None):
    """Добавить цель (единый формат dict). Совместимо со старым add_goal_for_user."""
    user_id = str(user_id)
    all_goals = load_goals() or {}
    items = all_goals.get(user_id, [])
    goal = {"text": str(text), "done": False}
    if deadline is not None:
        goal["deadline"] = deadline
    if remind is not False:
        goal["remind"] = bool(remind)
    if extra:
        goal.update(extra)

    items.append(goal)
    all_goals[user_id] = items
    save_goals(all_goals)
    return goal

def mark_goal_done(user_id, index: int):
    """Отметить цель по ИНДЕКСУ (из списка get_goals) выполненной."""
    user_id = str(user_id)
    all_goals = load_goals() or {}

    # нормализуем ключи
    if user_id not in all_goals:
        all_goals = {str(k): v for k, v in all_goals.items()}

    items = all_goals.get(user_id, [])
    if not (0 <= index < len(items)):
        return False

    item = items[index]
    if isinstance(item, dict):
        item["done"] = True
    else:
        # на случай старого формата (строка)
        item = {"text": str(item), "done": True}
        items[index] = item

    all_goals[user_id] = items
    save_goals(all_goals)
    return True

# ---------- совместимость со старым кодом ----------
def add_goal_for_user(user_id, goal_text):
    """Alias для старых вызовов."""
    return add_goal(user_id, goal_text)

def get_goals_for_user(user_id):
    """Вернуть тексты НЕвыполненных целей (как раньше ожидал старый код)."""
    items = get_goals(user_id)
    out = []
    for g in items:
        if isinstance(g, dict):
            if not g.get("done"):
                out.append(g.get("text") or "Без названия")
        else:
            # строковый формат
            out.append(str(g))
    return out
