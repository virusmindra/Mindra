# goals_store.py
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

DATA_DIR = os.getenv("MINDRA_DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

def _path(uid: str) -> str:
    safe = "".join(ch for ch in uid if ch.isalnum() or ch in ("-", "_"))
    return os.path.join(DATA_DIR, f"goals_{safe}.json")

def get_goals(uid: str) -> List[Dict[str, Any]]:
    p = _path(uid)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []

def _save(uid: str, items: List[Dict[str, Any]]) -> None:
    p = _path(uid)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def add_goal(uid: str, text: str, deadline: Optional[str] = None, remind: bool = False) -> str:
    items = get_goals(uid)
    goal_id = uuid.uuid4().hex
    items.append({
        "id": goal_id,
        "text": text,
        "done": False,
        "deadline": deadline,
        "remind": bool(remind),
        "createdAt": int(time.time()),
    })
    _save(uid, items)
    return goal_id

def mark_goal_done(uid: str, index: int) -> bool:
    items = get_goals(uid)
    if index < 0 or index >= len(items):
        return False
    items[index]["done"] = True
    _save(uid, items)
    return True

def delete_goal(uid: str, index: int) -> bool:
    items = get_goals(uid)
    if index < 0 or index >= len(items):
        return False
    items.pop(index)
    _save(uid, items)
    return True
