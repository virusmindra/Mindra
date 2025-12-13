# goals_store.py
import json
import os
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

DATA_DIR = os.getenv("MINDRA_DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)


def _path(uid: str) -> str:
    safe = "".join(ch for ch in str(uid) if ch.isalnum() or ch in ("-", "_"))
    return os.path.join(DATA_DIR, f"goals_{safe}.json")


def get_goals(uid: str) -> List[Dict[str, Any]]:
    p = _path(uid)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(uid: str, items: List[Dict[str, Any]]) -> None:
    p = _path(uid)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_goal(uid: str, text: str, deadline: Optional[str] = None, remind: bool = False) -> str:
    items = get_goals(uid)
    goal_id = str(uuid4())
    items.append(
        {
            "id": goal_id,
            "text": text,
            "done": False,
            "deadline": deadline,
            "remind": bool(remind),
            "createdAt": int(time.time()),
            "updatedAt": int(time.time()),
        }
    )
    _save(uid, items)
    return goal_id


def mark_goal_done(uid: str, goal_id: str) -> bool:
    items = get_goals(uid)
    gid = str(goal_id)

    for g in items:
        if str(g.get("id")) == gid:
            g["done"] = True
            g["updatedAt"] = int(time.time())
            _save(uid, items)
            return True
    return False


def delete_goal(uid: str, goal_id: str) -> bool:
    items = get_goals(uid)
    gid = str(goal_id)

    new_items = [g for g in items if str(g.get("id")) != gid]
    if len(new_items) == len(items):
        return False

    _save(uid, new_items)
    return True
