import json, os
from typing import Dict

POINTS_PATH = os.getenv("POINTS_PATH", "data_points.json")
_points_cache: Dict[str, int] = {}

def _load():
    global _points_cache
    if _points_cache:
        return
    if os.path.exists(POINTS_PATH):
        try:
            with open(POINTS_PATH, "r", encoding="utf-8") as f:
                _points_cache = json.load(f) or {}
        except:
            _points_cache = {}

def _save():
    with open(POINTS_PATH, "w", encoding="utf-8") as f:
        json.dump(_points_cache, f, ensure_ascii=False, indent=2)

def get_points(uid: str) -> int:
    _load()
    return int(_points_cache.get(uid, 0))

def add_points(uid: str, n: int) -> int:
    _load()
    cur = int(_points_cache.get(uid, 0))
    cur += int(n)
    _points_cache[uid] = cur
    _save()
    return cur
