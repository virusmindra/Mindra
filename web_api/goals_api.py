# web_api/goals_api.py
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# ВАЖНО: тут импортируй СВОИ реальные функции/модули
# Ниже - пример, заменишь пути на свои.
from some_module import add_goal, get_goals, mark_goal_done, add_points, tracker_can_add

router = APIRouter(prefix="/api/goals", tags=["goals"])


# --- Модели для API --- #

class GoalCreateIn(BaseModel):
    text: str
    deadline: Optional[str] = None  # 'YYYY-MM-DD' или None
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
    """
    Приводим структуру твоей цели (dict/строка) к GoalOut.
    """
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
    """
    Заглушка для аутентификации.
    Сейчас просто возвращаем 'web-anon'.
    Потом сюда можно будет завести реальный user_id из JWT/кук.
    """
    return "web-anon"


# --- Эндпоинты --- #

@router.get("/", response_model=GoalsListOut)
async def api_list_goals(uid: str = Depends(_get_uid_from_token)):
    """
    Список целей текущего пользователя.
    """
    raw_goals = get_goals(uid) or []
    goals = [_normalize_goal(g, idx) for idx, g in enumerate(raw_goals)]
    return {"goals": goals}


@router.post("/", response_model=GoalOut, status_code=201)
async def api_create_goal(payload: GoalCreateIn, uid: str = Depends(_get_uid_from_token)):
    """
    Создать цель. Учитываем лимит по тарифу (как в /goal).
    """
    can, limit, cnt = tracker_can_add(uid, "goal")
    if not can:
        # 403 с понятным текстом — UI сам покажет перевод.
        msg = f"Goal limit reached: {cnt}/{limit if limit is not None else '∞'}"
        raise HTTPException(status_code=403, detail=msg)

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty goal text")

    # создаём через твою функцию
    add_goal(uid, text, deadline=payload.deadline, remind=payload.remind)
    add_points(uid, 1)

    # берём актуальный список и берём последнюю цель как только что добавленную
    raw_goals = get_goals(uid) or []
    index = len(raw_goals) - 1 if raw_goals else 0
    goal_raw = raw_goals[index] if raw_goals else {"text": text, "deadline": payload.deadline, "remind": payload.remind}

    return _normalize_goal(goal_raw, index=index)


@router.post("/{index}/done", response_model=GoalOut)
async def api_mark_goal_done(index: int, uid: str = Depends(_get_uid_from_token)):
    """
    Отметить цель выполненной по её индексу.
    """
    raw_goals = get_goals(uid) or []

    if not (0 <= index < len(raw_goals)):
        raise HTTPException(status_code=404, detail="Goal not found")

    ok = mark_goal_done(uid, index)
    if not ok:
        raise HTTPException(status_code=500, detail="Could not mark goal as done")

    # после изменения перечитаем
    raw_goals = get_goals(uid) or []
    goal_raw = raw_goals[index]
    add_points(uid, 5)

    return _normalize_goal(goal_raw, index=index)

