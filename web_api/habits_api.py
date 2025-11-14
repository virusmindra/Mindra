# web_api/habits_api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from handlers import add_habit, get_habits, mark_habit_done, delete_habit
from stats import add_points  # tracker_can_add — УБРАНО

router = APIRouter(prefix="/api/habits", tags=["habits"])

HABITS_LIMIT = int(os.getenv("HABITS_LIMIT", "0"))  # 0 = без лимита

class HabitCreate(BaseModel):
    text: str
    user_id: str | None = None

class HabitOut(BaseModel):
    index: int
    text: str
    done: bool

def _normalize_habit(idx: int, h: dict) -> HabitOut:
    return HabitOut(
        index=idx,
        text=h.get("text") or h.get("name") or "Без названия",
        done=bool(h.get("done")),
    )

@router.get("")
def list_habits():
    uid = "web"
    items = get_habits(uid) or []
    return {"habits": [_normalize_habit(i, h) for i, h in enumerate(items)]}

@router.post("")
def create_habit(payload: HabitCreate):
    uid = "web"
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Пустой текст привычки.")

    if HABITS_LIMIT > 0:
        current = get_habits(uid) or []
        if len(current) >= HABITS_LIMIT:
            raise HTTPException(status_code=403, detail="Достигнут лимит привычек для текущего плана.")

    add_habit(uid, payload.text.strip())
    try:
        add_points(uid, 1)
    except Exception:
        pass

    items = get_habits(uid) or []
    return {"ok": True, "habits": [_normalize_habit(i, h) for i, h in enumerate(items)]}

@router.post("/{index}/done")
def mark_done(index: int):
    uid = "web"
    if index < 0:
        raise HTTPException(status_code=400, detail="Некорректный индекс.")

    if not mark_habit_done(uid, index):
        raise HTTPException(status_code=404, detail="Привычка не найдена.")

    try:
        add_points(uid, 5)
    except Exception:
        pass

    items = get_habits(uid) or []
    return {"ok": True, "habits": [_normalize_habit(i, h) for i, h in enumerate(items)]}

@router.delete("/{index}")
def delete(index: int):
    uid = "web"
    if index < 0:
        raise HTTPException(status_code=400, detail="Некорректный индекс.")

    if not delete_habit(uid, index):
        raise HTTPException(status_code=404, detail="Привычка не найдена.")

    items = get_habits(uid) or []
    return {"ok": True, "habits": [_normalize_habit(i, h) for i, h in enumerate(items)]}
