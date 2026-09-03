"""Visitor Statistics API Router."""
from fastapi import APIRouter
from server.services.stats import stats_service

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.post("/visit")
@router.get("/visit")
async def record_visit():
    """Increment and return the total visitor count for each page load."""
    total_visits = stats_service.record_visit()
    return {"total_visits": total_visits}


@router.get("/visits")
async def get_visits():
    """Get current visitor count without incrementing."""
    total_visits = stats_service.get_visit_count()
    return {"total_visits": total_visits}
