# web_api/habits_api.py
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# ЗАМЕНИ ИМПОРТЫ НИЖЕ НА СВОИ
# откуда ты сейчас берёшь эти функции в боте
from handlers import (
    add_habit,
    get_habits,
    mark_habit_done,
    delete_habit,
)

from stats import (
    add_points,
    tracker_can_add,
)

router = APIRouter(prefix="/api/habits", tags=["habits"])


class HabitCreateIn(BaseModel):
    text: str


class HabitOut(BaseModel):
    index: int
    text: str
    done: bool = False


class HabitsListOut(BaseModel):
    habits: List[HabitOut]


def _normalize_habit(habit_raw, index: int) -> HabitOut:
    if isinstance(habit_raw, dict):
        text = habit_raw.get("text") or habit_raw.get("name") or "Без названия"
        done = bool(habit_raw.get("done", False))
    else:
        text = str(habit_raw)
        done = False

    return HabitOut(index=index, text=text, done=done)


def _get_uid_from_token() -> str:
    """
    Как и в goals_api: пока просто 'web-anon'.
    Потом сюда можно завести реальный user_id из JWT/кук.
    """
    return "web-anon"


@router.get("/", response_model=HabitsListOut)
async def api_list_habits(uid: str = Depends(_get_uid_from_token)):
    raw_habits = get_habits(uid) or []
    habits = [_normalize_habit(h, idx) for idx, h in enumerate(raw_habits)]
    return {"habits": habits}


@router.post("/", response_model=HabitOut, status_code=201)
async def api_create_habit(payload: HabitCreateIn, uid: str = Depends(_get_uid_from_token)):
    can, limit, cnt = tracker_can_add(uid, "habit")
    if not can:
        msg = f"Habit limit reached: {cnt}/{limit if limit is not None else '∞'}"
        raise HTTPException(status_code=403, detail=msg)

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty habit text")

    add_habit(uid, text)
    add_points(uid, 1)

    raw_habits = get_habits(uid) or []
    index = len(raw_habits) - 1 if raw_habits else 0
    habit_raw = raw_habits[index] if raw_habits else {"text": text}

    return _normalize_habit(habit_raw, index=index)


@router.post("/{index}/done", response_model=HabitOut)
async def api_mark_habit_done(index: int, uid: str = Depends(_get_uid_from_token)):
    raw_habits = get_habits(uid) or []
    if not (0 <= index < len(raw_habits)):
        raise HTTPException(status_code=404, detail="Habit not found")

    ok = mark_habit_done(uid, index)
    if not ok:
        raise HTTPException(status_code=500, detail="Could not mark habit as done")

    raw_habits = get_habits(uid) or []
    habit_raw = raw_habits[index]
    add_points(uid, 5)

    return _normalize_habit(habit_raw, index=index)


@router.delete("/{index}", response_model=HabitOut)
async def api_delete_habit(index: int, uid: str = Depends(_get_uid_from_token)):
    raw_habits = get_habits(uid) or []
    if not (0 <= index < len(raw_habits)):
        raise HTTPException(status_code=404, detail="Habit not found")

    habit_raw = raw_habits[index]
    ok = delete_habit(uid, index)
    if not ok:
        raise HTTPException(status_code=500, detail="Could not delete habit")

    return _normalize_habit(habit_raw, index=index)
