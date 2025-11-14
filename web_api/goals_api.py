# web_api/goals_api.py
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from handlers import add_goal, get_goals, mark_goal_done, delete_goal
from stats import add_points, tracker_can_add

router = APIRouter(prefix="/api/goals", tags=["goals"])


class GoalCreateIn(BaseModel):
  text: str
  deadline: Optional[str] = None
  remind: bool = False


class GoalOut(BaseModel):
  index: int
  text: str
  done: bool = False
  deadline: Optional[str] = None
  remind: bool = False


class GoalsListOut(BaseModel):
  goals: List[GoalOut]


def _normalize_goal(goal_raw, index: int) -> GoalOut:
  if isinstance(goal_raw, dict):
      text = goal_raw.get("text") or goal_raw.get("name") or goal_raw.get("title") or "Без названия"
      done = bool(goal_raw.get("done", False))
      deadline = goal_raw.get("deadline") or goal_raw.get("date")
      remind = bool(goal_raw.get("remind", False))
  else:
      text = str(goal_raw)
      done = False
      deadline = None
      remind = False

  return GoalOut(
      index=index,
      text=text,
      done=done,
      deadline=deadline,
      remind=remind,
  )


def _get_uid_from_token() -> str:
  return "web-anon"


@router.get("/", response_model=GoalsListOut)
async def api_list_goals(uid: str = Depends(_get_uid_from_token)):
  raw_goals = get_goals(uid) or []
  goals = [_normalize_goal(g, idx) for idx, g in enumerate(raw_goals)]
  return {"goals": goals}


@router.post("/", response_model=GoalOut, status_code=201)
async def api_create_goal(payload: GoalCreateIn, uid: str = Depends(_get_uid_from_token)):
  can, limit, cnt = tracker_can_add(uid, "goal")
  if not can:
      msg = f"Goal limit reached: {cnt}/{limit if limit is not None else '∞'}"
      raise HTTPException(status_code=403, detail=msg)

  text = payload.text.strip()
  if not text:
      raise HTTPException(status_code=400, detail="Empty goal text")

  add_goal(uid, text, deadline=payload.deadline, remind=payload.remind)
  add_points(uid, 1)

  raw_goals = get_goals(uid) or []
  index = len(raw_goals) - 1 if raw_goals else 0
  goal_raw = raw_goals[index] if raw_goals else {"text": text, "deadline": payload.deadline, "remind": payload.remind}

  return _normalize_goal(goal_raw, index=index)


@router.post("/{index}/done", response_model=GoalOut)
async def api_mark_goal_done(index: int, uid: str = Depends(_get_uid_from_token)):
  raw_goals = get_goals(uid) or []
  if not (0 <= index < len(raw_goals)):
      raise HTTPException(status_code=404, detail="Goal not found")

  ok = mark_goal_done(uid, index)
  if not ok:
      raise HTTPException(status_code=500, detail="Could not mark goal as done")

  raw_goals = get_goals(uid) or []
  goal_raw = raw_goals[index]
  add_points(uid, 5)

  return _normalize_goal(goal_raw, index=index)


@router.delete("/{index}", response_model=GoalOut)
async def api_delete_goal(index: int, uid: str = Depends(_get_uid_from_token)):
  """
  Удалить цель по индексу.
  """
  raw_goals = get_goals(uid) or []
  if not (0 <= index < len(raw_goals)):
      raise HTTPException(status_code=404, detail="Goal not found")

  goal_raw = raw_goals[index]

  ok = delete_goal(uid, index)
  if not ok:
      raise HTTPException(status_code=500, detail="Could not delete goal")

  return _normalize_goal(goal_raw, index=index)
