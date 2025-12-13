# web_api/goals_api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from goals_store import add_goal, get_goals, mark_goal_done, delete_goal
from plans import can_add
from points_store import add_points, get_points

router = APIRouter(prefix="/api/goals", tags=["goals"])

class GoalCreate(BaseModel):
    text: str
    deadline: Optional[str] = None
    remind: Optional[bool] = False
    user_id: Optional[str] = None

def _uid(payload_user_id: Optional[str]) -> str:
    return (payload_user_id or "web").strip() or "web"

@router.get("")
def list_goals(user_id: str = "web"):
    items = get_goals(user_id) or []
    return {"ok": True, "goals": items, "points": get_points(user_id)}

@router.post("")
def create_goal(payload: GoalCreate):
    uid = _uid(payload.user_id)
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Пустой текст цели.")

    current = get_goals(uid) or []
    ok, limit = can_add(uid, "goal", len(current))
    if not ok:
        raise HTTPException(status_code=403, detail=f"Лимит целей для плана. Лимит: {limit}")

    goal_id = add_goal(uid, text, deadline=payload.deadline, remind=bool(payload.remind))
    pts = add_points(uid, 1)  # +1 за создание цели

    return {"ok": True, "id": goal_id, "goals": get_goals(uid), "points": pts}

@router.post("/{goal_id}/done")
def done(goal_id: str, user_id: str = "web"):
    uid = (user_id or "web").strip() or "web"
    if not mark_goal_done(uid, goal_id):
        raise HTTPException(status_code=404, detail="Цель не найдена.")

    pts = add_points(uid, 5)  # +5 за выполнение
    return {"ok": True, "goals": get_goals(uid), "points": pts}

@router.delete("/{goal_id}")
def remove(goal_id: str, user_id: str = "web"):
    uid = (user_id or "web").strip() or "web"
    if not delete_goal(uid, goal_id):
        raise HTTPException(status_code=404, detail="Цель не найдена.")

    return {"ok": True, "goals": get_goals(uid), "points": get_points(uid)}

    items = get_goals(uid) or []
    return {"ok": True, "goals": [_normalize_goal(i, g) for i, g in enumerate(items)]}
