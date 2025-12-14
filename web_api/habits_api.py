# web_api/habits_api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from habits_store import add_habit, get_habits, mark_habit_done, delete_habit
from plans import can_add
from points_store import add_points, get_points

router = APIRouter(prefix="/api/habits", tags=["habits"])

class HabitCreate(BaseModel):
    text: str
    user_id: Optional[str] = None

def _uid(payload_user_id: Optional[str]) -> str:
    return (payload_user_id or "web").strip() or "web"

@router.get("")
def list_habits(user_id: str = "web"):
    items = get_habits(user_id) or []
    return {"habits": items, "points": get_points(user_id)}

@router.post("")
def create_habit(payload: HabitCreate):
    uid = _uid(payload.user_id)

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Пустой текст привычки.")

    current = get_habits(uid) or []
    ok, limit = can_add(uid, "habit", len(current))
    if not ok:
        raise HTTPException(status_code=403, detail=f"Лимит привычек для плана. Лимит: {limit}")

    habit_id = add_habit(uid, text)
    pts = add_points(uid, 1)  # +1 за создание привычки

    return {"ok": True, "id": habit_id, "habits": get_habits(uid), "points": pts}

@router.post("/{habit_id}/done")
def done_habit(habit_id: str, user_id: str = "web"):
    if not mark_habit_done(user_id, habit_id):
        raise HTTPException(status_code=404, detail="Привычка не найдена.")

    pts = add_points(user_id, 2)  # 🔁 привычка = +2
    return {"ok": True, "habits": get_habits(user_id), "points": pts}

@router.delete("/{habit_id}")
def remove_habit(habit_id: str, user_id: str = "web"):
    if not delete_habit(user_id, habit_id):
        raise HTTPException(status_code=404, detail="Привычка не найдена.")
    return {"ok": True, "habits": get_habits(user_id), "points": get_points(user_id)}

    items = get_habits(uid) or []
    return {"ok": True, "habits": [_normalize_habit(i, h) for i, h in enumerate(items)]}
