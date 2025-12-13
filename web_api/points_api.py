from fastapi import APIRouter
from pydantic import BaseModel
from points_store import get_points

router = APIRouter(prefix="/api/points", tags=["points"])

class PointsOut(BaseModel):
    points: int

@router.get("", response_model=PointsOut)
def read_points(user_id: str = "web"):
    return {"points": get_points(user_id)}
