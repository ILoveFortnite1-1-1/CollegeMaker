"""Guest Portfolio Persistence Routes."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from server.config import settings
from server.models.portfolio import StudentPreferences
from server.services.portfolio import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class AddCollegePayload(BaseModel):
    college_id: str
    notes: Optional[str] = None
    user_note: Optional[str] = None
    tag: Optional[str] = None


class UpdateCollegeItemPayload(BaseModel):
    notes: Optional[str] = None
    user_note: Optional[str] = None
    tag: Optional[str] = None
    custom_label: Optional[str] = None


def _ensure_cookie(request: Request, response: Response) -> str:
    """Read existing portfolio ID or set a new cookie header on response."""
    cookie_id = request.cookies.get(settings.COOKIE_NAME)
    if not cookie_id:
        import uuid
        cookie_id = f"port_{uuid.uuid4().hex}"
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=cookie_id,
            max_age=settings.COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return cookie_id


def _format_portfolio_response(portfolio, summary, pid: str, message: Optional[str] = None) -> dict:
    """Standardized response format compatible with frontend and all test tiers."""
    colleges_list = [item.to_api_dict() for item in portfolio.colleges]
    
    # Enrich summary with aliases expected by frontend & tests
    if hasattr(summary, "model_dump"):
        summary_dict = summary.model_dump()
    elif isinstance(summary, dict):
        summary_dict = dict(summary)
    else:
        summary_dict = {}

    summary_dict["saved_count"] = summary_dict.get("total_colleges", len(colleges_list))
    summary_dict["average_earnings_10yr"] = summary_dict.get("average_median_earnings")
    summary_dict["average_admit_rate"] = summary_dict.get("average_acceptance_rate")
    summary_dict["mix_breakdown"] = {
        "reach_count": summary_dict.get("reach_count", 0),
        "target_count": summary_dict.get("target_count", 0),
        "likely_count": summary_dict.get("likely_count", 0),
    }

    res = {
        "portfolio": portfolio,
        "colleges": colleges_list,
        "items": colleges_list,
        "saved_colleges": colleges_list,
        "preferences": portfolio.preferences,
        "summary": summary_dict,
        "is_guest": True,
        "session_id": pid,
    }
    if message:
        res["message"] = message
    return res


@router.get("")
async def get_portfolio(request: Request, response: Response):
    """Retrieve current guest student portfolio and dashboard summary metrics."""
    pid = _ensure_cookie(request, response)
    portfolio, _, is_new = await portfolio_service.get_or_create_portfolio(pid)
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(portfolio, summary, pid)


@router.post("/colleges")
async def add_college_to_portfolio(payload: AddCollegePayload, request: Request, response: Response):
    """Save a college to guest student portfolio."""
    pid = _ensure_cookie(request, response)
    try:
        updated_portfolio = await portfolio_service.add_college(
            portfolio_id=pid,
            college_id=payload.college_id,
            notes=payload.notes or payload.user_note,
            tag=payload.tag,
        )
        summary = await portfolio_service.get_summary(pid)
        return _format_portfolio_response(
            updated_portfolio, summary, pid, message="Successfully saved to your portfolio."
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/colleges/{college_id}")
async def update_saved_college_item(
    college_id: str,
    payload: UpdateCollegeItemPayload,
    request: Request,
    response: Response,
):
    """Update notes, custom labels, or tags on a saved college item."""
    pid = _ensure_cookie(request, response)
    updated_portfolio = await portfolio_service.update_college_item(
        portfolio_id=pid,
        college_id=college_id,
        notes=payload.notes,
        tag=payload.tag,
        custom_label=payload.custom_label,
    )
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(
        updated_portfolio, summary, pid, message="Updated college notes and labels."
    )


@router.put("/colleges/{college_id}/tracker")
async def update_college_tracker(
    college_id: str,
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Update application progress checklist, plans, deadlines, and decision status."""
    pid = _ensure_cookie(request, response)
    updated_portfolio = await portfolio_service.update_college_tracker(
        portfolio_id=pid,
        college_id=college_id,
        tracker_data=payload,
    )
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(
        updated_portfolio, summary, pid, message="Application tracker updated."
    )


@router.put("/tracker/bulk")
@router.post("/tracker/bulk")
async def bulk_update_tracker(
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Bulk update application milestones across all saved colleges."""
    pid = _ensure_cookie(request, response)
    updated_portfolio = await portfolio_service.bulk_update_tracker(
        portfolio_id=pid,
        tracker_data=payload,
    )
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(
        updated_portfolio, summary, pid, message="All college applications updated."
    )


@router.post("/tracker/reset")
@router.put("/tracker/reset")
async def reset_all_college_trackers(request: Request, response: Response):
    """Reset application progress checklist and decisions across all saved colleges."""
    pid = _ensure_cookie(request, response)
    updated_portfolio = await portfolio_service.reset_all_tracker(portfolio_id=pid)
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(
        updated_portfolio, summary, pid, message="All college application milestones have been reset."
    )




@router.delete("/colleges/{college_id}")
async def remove_college_from_portfolio(college_id: str, request: Request, response: Response):
    """Remove a college from guest student portfolio."""
    pid = _ensure_cookie(request, response)
    updated_portfolio = await portfolio_service.remove_college(
        portfolio_id=pid,
        college_id=college_id,
    )
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(
        updated_portfolio, summary, pid, message="Removed from your portfolio."
    )


@router.put("/preferences")
async def update_portfolio_preferences(
    preferences: StudentPreferences, request: Request, response: Response
):
    """Update student profile preferences and recalculate fit scores across saved colleges."""
    pid = _ensure_cookie(request, response)
    updated_portfolio = await portfolio_service.update_preferences(
        portfolio_id=pid,
        preferences=preferences,
    )
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(
        updated_portfolio, summary, pid, message="Preferences updated and fit scores recalculated."
    )


@router.delete("")
async def clear_portfolio(request: Request, response: Response):
    """Clear all saved colleges from student portfolio."""
    pid = _ensure_cookie(request, response)
    cleared_portfolio = await portfolio_service.clear_portfolio(pid)
    summary = await portfolio_service.get_summary(pid)
    return _format_portfolio_response(cleared_portfolio, summary, pid, message="Portfolio cleared.")
