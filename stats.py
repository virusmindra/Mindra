import json
from datetime import datetime

STATS_FILE = "data/stats.json"

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

def get_stats():
    stats = load_stats()
    return {
        "total_users": len(stats["users"]),
        "premium_users": len(stats["premium_users"]),
        "last_users": stats["users"],
        "last_premium": stats["premium_users"]
    }
