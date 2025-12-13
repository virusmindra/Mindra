import os
from typing import Tuple

# Free=1 цель, Plus=5, Pro=∞
DEFAULT_PLAN = os.getenv("DEFAULT_PLAN", "free").lower()

LIMITS = {
    "free": {"goal": 1, "habit": 3, "reminder": 3},
    "plus": {"goal": 5, "habit": 10, "reminder": 10},
    "pro":  {"goal": 10_000_000, "habit": 10_000_000, "reminder": 10_000_000},
}

def get_user_plan(uid: str) -> str:
    # пока без платежей: всем free, либо можно руками в ENV поставить DEFAULT_PLAN=plus/pro
    return DEFAULT_PLAN if DEFAULT_PLAN in LIMITS else "free"

def can_add(uid: str, kind: str, current_count: int) -> Tuple[bool, int]:
    plan = get_user_plan(uid)
    limit = LIMITS[plan].get(kind, 0)
    if limit <= 0:
        return True, limit
    return current_count < limit, limit
