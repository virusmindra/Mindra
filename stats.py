import json
import os
from datetime import datetime, timedelta

STATS_FILE = "data/stats.json"
GOALS_FILE = "goals.json"
HABITS_FILE = "habits.json"

def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

# ==== PREMIUM/TRIAL/REFERRAL ====

def get_premium_until(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    return user.get("premium_until", None)

def set_premium_until(user_id, until_dt):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    user["premium_until"] = until_dt.isoformat()
    stats[str(user_id)] = user
    save_stats(stats)

def is_premium(user_id):
    until = get_premium_until(user_id)
    if until:
        try:
            return datetime.fromisoformat(until) > datetime.utcnow()
        except:
            return False
    return False

def got_trial(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    return user.get("got_trial", False)

def set_trial(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    user["got_trial"] = True
    stats[str(user_id)] = user
    save_stats(stats)

def add_referral(user_id, referrer_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    referrals = user.get("referrals", [])
    if referrer_id not in referrals:
        referrals.append(referrer_id)
    user["referrals"] = referrals
    stats[str(user_id)] = user
    save_stats(stats)

# ==== USER PROGRESS ====

def add_points(user_id: str, amount: int = 1):
    stats = load_stats()
    user_id = str(user_id)
    user = stats.get(user_id, {})
    user["points"] = user.get("points", 0) + amount
    stats[user_id] = user
    save_stats(stats)
    return user["points"]

def get_user_stats(user_id: str):
    from goals import get_goals
    from habits import get_habits

    goals = get_goals(user_id)
    total_goals = len(goals)
    completed_goals = len([g for g in goals if g.get("done")])

    habits = get_habits(user_id)
    total_habits = len(habits)

    stats = load_stats()
    user = stats.get(str(user_id), {})
    points = user.get("points", 0)

    return {
        "points": points,
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "habits": total_habits
    }
    
def get_user_title(points: int, lang: str = "ru") -> str:
    TITLES = {
        "ru": [
            (50,  "🌱 Новичок"),
            (100, "✨ Мотиватор"),
            (250, "🔥 Уверенный"),
            (500, "💎 Наставник"),
            (float('inf'), "🌟 Легенда")
        ],
        "uk": [
            (50,  "🌱 Новачок"),
            (100, "✨ Мотиватор"),
            (250, "🔥 Впевнений"),
            (500, "💎 Наставник"),
            (float('inf'), "🌟 Легенда")
        ],
        "be": [
            (50,  "🌱 Пачатковец"),
            (100, "✨ Матыватар"),
            (250, "🔥 Упэўнены"),
            (500, "💎 Настаўнік"),
            (float('inf'), "🌟 Легенда")
        ],
        "kk": [
            (50,  "🌱 Бастаушы"),
            (100, "✨ Мотивация беруші"),
            (250, "🔥 Сенімді"),
            (500, "💎 Ұстаз"),
            (float('inf'), "🌟 Аңыз")
        ],
        "kg": [
            (50,  "🌱 Жаңы келген"),
            (100, "✨ Мотивациячы"),
            (250, "🔥 Ишенимдүү"),
            (500, "💎 Наcатчы"),
            (float('inf'), "🌟 Легенда")
        ],
        "hy": [
            (50,  "🌱 Նորեկ"),
            (100, "✨ Մոտիվատոր"),
            (250, "🔥 Վստահ"),
            (500, "💎 Խորհրդատու"),
            (float('inf'), "🌟 Լեգենդ")
        ],
        "ce": [
            (50,  "🌱 Дика хьалхар"),
            (100, "✨ Мотивация кхетар"),
            (250, "🔥 Дукха ву"),
            (500, "💎 Къастийна"),
            (float('inf'), "🌟 Легенда")
        ],
        "md": [
            (50,  "🌱 Începător"),
            (100, "✨ Motivator"),
            (250, "🔥 Încrezător"),
            (500, "💎 Mentor"),
            (float('inf'), "🌟 Legenda")
        ],
        "ka": [
            (50,  "🌱 დამწყები"),
            (100, "✨ მოტივატორი"),
            (250, "🔥 დარწმუნებული"),
            (500, "💎 მენტორი"),
            (float('inf'), "🌟 ლეგენდა")
        ],
        "en": [
            (50,  "🌱 Newbie"),
            (100, "✨ Motivator"),
            (250, "🔥 Confident"),
            (500, "💎 Mentor"),
            (float('inf'), "🌟 Legend")
        ],
    }
    lang_titles = TITLES.get(lang, TITLES["ru"])
    for threshold, title in lang_titles:
        if points < threshold:
            return title
    return lang_titles[-1][1]

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

def add_points(user_id: str, amount: int = 1):
    stats = load_stats()
    user_id = str(user_id)
    if user_id not in stats:
        stats[user_id] = {"points": 0, "goals_completed": 0}
    stats[user_id]["points"] += amount
    save_stats(stats)
    return stats[user_id]["points"]

