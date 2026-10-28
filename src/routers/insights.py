
from fastapi import APIRouter, HTTPException

from src.ai_insights import generate_ai_insights

router = APIRouter(tags=["AI Insights"])


@router.get("/api/insights")
def get_ai_insights():
    try:
        return generate_ai_insights()
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
