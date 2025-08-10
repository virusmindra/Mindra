import json
import os
from datetime import datetime, timedelta
from storage import get_goals, get_habits, load_goals, load_habits

STATS_FILE = "data/stats.json"
GOALS_FILE = "goals.json"
HABITS_FILE = "habits.json"

ADMIN_USER_IDS = ["7775321566"] 
OWNER_ID = "7775321566"
ADMIN_USER_IDS = [OWNER_ID]  # Можно расширять список

def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    # 🟣 Создаём директорию, если её нет
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

# ==== PREMIUM/TRIAL/REFERRAL ====

def get_premium_until(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    return user.get("premium_until", None)
    

def set_premium_until(user_id, until_dt, add_days=False):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    current_until = user.get("premium_until")
    now = datetime.utcnow()
    # Если есть текущая дата — сравниваем с новой
    if current_until:
        current_until_dt = datetime.fromisoformat(current_until)
        if add_days:
            # Если нужно добавить дни — прибавляем к текущей дате
            if current_until_dt > now:
                until_dt = current_until_dt + (until_dt - now)
            else:
                until_dt = now + (until_dt - now)
        else:
            # Обычная логика: берем максимальное значение
            if current_until_dt > until_dt:
                until_dt = current_until_dt
    user["premium_until"] = until_dt.isoformat()
    stats[str(user_id)] = user
    save_stats(stats)
    
def is_premium(user_id):
    if str(user_id) in ADMIN_USER_IDS:
        return True
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

def got_referral(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    return user.get("got_referral", False)

def set_referral(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    user["got_referral"] = True
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

def get_stats(user_id: str):
    user_id = str(user_id)

    goals_data = load_goals() or {}
    user_goals = goals_data.get(user_id, [])

    habits_data = load_habits() or {}
    user_habits = habits_data.get(user_id, [])

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    completed_goals = sum(1 for g in user_goals if isinstance(g, dict) and g.get("done"))
    completed_habits = sum(1 for h in user_habits if isinstance(h, dict) and h.get("done"))

    completed_goals_today = sum(1 for g in user_goals if isinstance(g, dict) and g.get("done_at") == today)
    completed_habits_today = sum(1 for h in user_habits if isinstance(h, dict) and h.get("done_at") == today)

    # Активные дни считаем по done_at (если нет — можно добавить логику по "date")
    days_active = len(
        set(
            [g.get("done_at") for g in user_goals if isinstance(g, dict) and g.get("done_at")]
            + [h.get("done_at") for h in user_habits if isinstance(h, dict) and h.get("done_at")]
        )
    )

    return {
        "completed_goals": completed_goals,
        "completed_habits": completed_habits,
        "completed_goals_today": completed_goals_today,
        "completed_habits_today": completed_habits_today,
        "days_active": days_active,
        "mood_entries": 0,  # если будет mood.json — посчитаем
    }


def get_user_stats(user_id: str):
    user_id = str(user_id)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    goals = get_goals(user_id)
    habits = get_habits(user_id)

    total_goals = len(goals)
    completed_goals = sum(1 for g in goals if isinstance(g, dict) and g.get("done"))
    completed_goals_today = sum(1 for g in goals if isinstance(g, dict) and g.get("done_at") == today)

    total_habits = len(habits)
    completed_habits = sum(1 for h in habits if isinstance(h, dict) and h.get("done"))
    completed_habits_today = sum(1 for h in habits if isinstance(h, dict) and h.get("done_at") == today)

    # Поинты: берём откуда есть, мягко
    points = 0
    try:
        from handlers import user_points  # если живёт там
        points = user_points.get(user_id, 0)
    except Exception:
        try:
            from stats import user_points  # если живёт тут
            points = user_points.get(user_id, 0)
        except Exception:
            points = 0

    return {
        "points": points,
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "completed_goals_today": completed_goals_today,
        "total_habits": total_habits,
        "completed_habits": completed_habits,
        "completed_habits_today": completed_habits_today,
    }
