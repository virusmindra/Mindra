# web_api/goals_api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

# Бизнес-функции живут в handlers.py
from goals_store import add_goal, get_goals, mark_goal_done, delete_goal
from stats import add_points  # tracker_can_add — УБРАНО

router = APIRouter(prefix="/api/goals", tags=["goals"])

# Опциональный простой лимит из ENV (если не задан — без лимита)
GOALS_LIMIT = int(os.getenv("GOALS_LIMIT", "0"))  # 0 = без лимита

class GoalCreate(BaseModel):
    text: str
    deadline: str | None = None
    remind: bool | None = False
    user_id: str | None = None  # на будущее; пока можем игнорить

class GoalOut(BaseModel):
    index: int
    text: str
    done: bool
    deadline: str | None = None
    remind: bool | None = None

def _normalize_goal(idx: int, g: dict) -> GoalOut:
    return GoalOut(
        index=idx,
        text=g.get("text") or g.get("name") or g.get("title") or "Без названия",
        done=bool(g.get("done")),
        deadline=g.get("deadline"),
        remind=g.get("remind"),
    )

@router.get("")
def list_goals():
    uid = "web"  # если надо — подставим реального пользователя позже
    items = get_goals(uid) or []
    return {"goals": [_normalize_goal(i, g) for i, g in enumerate(items)]}

@router.post("")
def create_goal(payload: GoalCreate):
    uid = "web"
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Пустой текст цели.")

    # Простой лимит (если включили через ENV)
    if GOALS_LIMIT > 0:
        current = get_goals(uid) or []
        if len(current) >= GOALS_LIMIT:
            raise HTTPException(status_code=403, detail="Достигнут лимит целей для текущего плана.")

    add_goal(uid, payload.text.strip(), deadline=payload.deadline, remind=bool(payload.remind))
    try:
        add_points(uid, 1)
    except Exception:
        pass

    items = get_goals(uid) or []
    return {"ok": True, "goals": [_normalize_goal(i, g) for i, g in enumerate(items)]}

@router.post("/{index}/done")
def mark_done(index: int):
    uid = "web"
    if index < 0:
        raise HTTPException(status_code=400, detail="Некорректный индекс.")

    if not mark_goal_done(uid, index):
        raise HTTPException(status_code=404, detail="Цель не найдена.")

    try:
        add_points(uid, 5)
    except Exception:
        pass

    items = get_goals(uid) or []
    return {"ok": True, "goals": [_normalize_goal(i, g) for i, g in enumerate(items)]}

@router.delete("/{index}")
def delete(index: int):
    uid = "web"
    if index < 0:
        raise HTTPException(status_code=400, detail="Некорректный индекс.")

    if not delete_goal(uid, index):
        raise HTTPException(status_code=404, detail="Цель не найдена.")

    items = get_goals(uid) or []
    return {"ok": True, "goals": [_normalize_goal(i, g) for i, g in enumerate(items)]}
