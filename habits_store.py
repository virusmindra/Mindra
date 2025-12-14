# habits_store.py
import json
import os
import time
from typing import Any, Dict, List
from uuid import uuid4

DATA_DIR = os.getenv("MINDRA_DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

def _path(uid: str) -> str:
    safe = "".join(ch for ch in str(uid) if ch.isalnum() or ch in ("-", "_"))
    return os.path.join(DATA_DIR, f"habits_{safe}.json")

def get_habits(uid: str) -> List[Dict[str, Any]]:
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

def add_habit(uid: str, text: str) -> str:
    items = get_habits(uid)
    habit_id = str(uuid4())
    now = int(time.time())

    items.append({
        "id": habit_id,
        "text": text,
        "createdAt": now,
        "updatedAt": now,
        "doneToday": False,
        "lastDoneAt": None,
    })

    _save(uid, items)
    return habit_id

def mark_habit_done(uid: str, habit_id: str) -> bool:
    items = get_habits(uid)
    hid = str(habit_id)
    now = int(time.time())

    for h in items:
        if str(h.get("id")) == hid:
            h["doneToday"] = True
            h["lastDoneAt"] = now
            h["updatedAt"] = now
            _save(uid, items)
            return True
    return False

def delete_habit(uid: str, habit_id: str) -> bool:
    items = get_habits(uid)
    hid = str(habit_id)

    new_items = [h for h in items if str(h.get("id")) != hid]
    if len(new_items) == len(items):
        return False

    _save(uid, new_items)
    return True
