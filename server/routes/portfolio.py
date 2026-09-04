"""Guest Portfolio Persistence Routes."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ValidationError
from server.config import settings
from server.models.portfolio import (
    ChecklistItem,
    FinancialAidOffer,
    EssayEntry,
    ScenarioOverrideRequest,
    StudentPreferences,
)
from server.services.portfolio import portfolio_service
from server.services.portfolio_store import portfolio_store
from server.services.aid_service import aid_service
from server.services.calendar_service import calendar_service
from server.services.chances_service import chances_service
from server.services.scenario_service import scenario_service
from server.services.scorecard import scorecard_service


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


# -----------------------------------------------------------------------------
# R1: Financial Aid Offer Comparison
# -----------------------------------------------------------------------------
@router.post("/aid/{college_id}")
@router.put("/aid/{college_id}")
@router.post("/colleges/{college_id}/aid")
@router.put("/colleges/{college_id}/aid")
async def save_college_aid_offer(
    college_id: str,
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Save or update financial aid offer for a college in portfolio."""
    pid = _ensure_cookie(request, response)
    try:
        offer = await portfolio_store.save_aid_offer(pid, college_id, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "status": "success",
        "college_id": college_id,
        "offer": offer.model_dump(),
        "aid_offer": offer.model_dump(),
    }


@router.delete("/aid/{college_id}")
@router.delete("/colleges/{college_id}/aid")
async def delete_college_aid_offer(
    college_id: str,
    request: Request,
    response: Response,
):
    """Delete financial aid offer for a college in portfolio."""
    pid = _ensure_cookie(request, response)
    deleted = await portfolio_store.delete_aid_offer(pid, college_id)
    return {
        "status": "success",
        "college_id": college_id,
        "deleted": deleted,
    }


@router.get("/aid/comparison")
@router.get("/aid-comparison")
@router.get("/aid")
async def get_portfolio_aid_comparison(
    request: Request,
    response: Response,
):
    """Get side-by-side financial aid comparison across saved colleges."""
    pid = _ensure_cookie(request, response)
    portfolio, _, _ = await portfolio_service.get_or_create_portfolio(pid)
    comparison = await aid_service.get_portfolio_aid_comparison(portfolio)
    return comparison


# -----------------------------------------------------------------------------
# R2: Deadline Calendar
# -----------------------------------------------------------------------------
@router.get("/calendar")
@router.get("/deadlines")
async def get_portfolio_calendar(
    request: Request,
    response: Response,
    auto_populate: bool = True,
):
    """Aggregate all application, financial aid, and scholarship deadlines across saved colleges."""
    pid = _ensure_cookie(request, response)
    portfolio, _, _ = await portfolio_service.get_or_create_portfolio(pid)
    calendar_data = calendar_service.get_portfolio_calendar(portfolio, auto_populate_defaults=auto_populate)
    return calendar_data


# -----------------------------------------------------------------------------
# R3: Essay Tracker
# -----------------------------------------------------------------------------
@router.get("/essays")
async def list_portfolio_essays(
    request: Request,
    response: Response,
):
    """List all essay entries in the student's portfolio."""
    pid = _ensure_cookie(request, response)
    essays = await portfolio_store.get_essays(pid)
    essay_dicts = [e.to_dict() for e in essays]
    return {
        "essays": essay_dicts,
        "count": len(essay_dicts),
    }


@router.post("/essays")
async def create_portfolio_essay(
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Create a new essay entry."""
    pid = _ensure_cookie(request, response)
    try:
        essay = await portfolio_store.create_essay(pid, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return essay.to_dict()


@router.put("/essays/{essay_id}")
async def update_portfolio_essay(
    essay_id: str,
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Update an existing essay entry."""
    pid = _ensure_cookie(request, response)
    try:
        updated = await portfolio_store.update_essay(pid, essay_id, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Essay with ID '{essay_id}' not found.")
    return updated.to_dict()


@router.delete("/essays/{essay_id}")
async def delete_portfolio_essay(
    essay_id: str,
    request: Request,
    response: Response,
):
    """Delete an essay entry."""
    pid = _ensure_cookie(request, response)
    deleted = await portfolio_store.delete_essay(pid, essay_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Essay with ID '{essay_id}' not found.")
    return {"status": "success", "essay_id": essay_id, "deleted": True}


# -----------------------------------------------------------------------------
# R4: Admissions Chances Portfolio Summary
# -----------------------------------------------------------------------------
@router.get("/chances")
@router.get("/chances-summary")
async def get_portfolio_chances(
    request: Request,
    response: Response,
):
    """Get admissions chances evaluation across all saved colleges in portfolio."""
    pid = _ensure_cookie(request, response)
    portfolio, _, _ = await portfolio_service.get_or_create_portfolio(pid)
    chances_list = []
    counts = {"Reach": 0, "Target": 0, "Likely": 0, "Safety": 0}

    for item in portfolio.colleges:
        college = item.college or await scorecard_service.get_college_by_id(item.college_id)
        if college:
            est = chances_service.estimate_chances(college, portfolio.preferences)
            chances_list.append(est.model_dump())
            counts[est.classification] = counts.get(est.classification, 0) + 1

    return {
        "chances": chances_list,
        "items": chances_list,
        "distribution": counts,
        "reach_count": counts.get("Reach", 0),
        "target_count": counts.get("Target", 0),
        "likely_count": counts.get("Likely", 0),
        "safety_count": counts.get("Safety", 0),
        "total_colleges": len(chances_list),
    }


# -----------------------------------------------------------------------------
# R5: "What-If" Scenario Modeling
# -----------------------------------------------------------------------------
@router.post("/scenario")
@router.post("/scenarios/simulate")
async def simulate_scenario(
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Run in-memory what-if scenario simulation with temporary parameter overrides."""
    pid = _ensure_cookie(request, response)
    portfolio, _, _ = await portfolio_service.get_or_create_portfolio(pid)
    try:
        override_req = ScenarioOverrideRequest(**payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    result = await scenario_service.simulate_scenario(portfolio, override_req)
    return result


# -----------------------------------------------------------------------------
# R7: Per-School Requirements Checklist
# -----------------------------------------------------------------------------
@router.post("/tracker/{college_id}/checklist")
@router.post("/colleges/{college_id}/requirements")
async def add_college_checklist_item(
    college_id: str,
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Add a requirement checklist item to a saved college."""
    pid = _ensure_cookie(request, response)
    try:
        item = await portfolio_store.add_checklist_item(pid, college_id, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not item:
        raise HTTPException(status_code=404, detail=f"College '{college_id}' not found in portfolio.")
    return item.model_dump()


@router.put("/tracker/{college_id}/checklist/{item_id}")
@router.put("/colleges/{college_id}/requirements/{item_id}")
async def update_college_checklist_item(
    college_id: str,
    item_id: str,
    payload: Dict[str, Any],
    request: Request,
    response: Response,
):
    """Update or toggle a requirement checklist item."""
    pid = _ensure_cookie(request, response)
    try:
        item = await portfolio_store.update_checklist_item(pid, college_id, item_id, payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Checklist item '{item_id}' not found for college '{college_id}'.",
        )
    return item.model_dump()


@router.get("/tracker/{college_id}/checklist")
@router.get("/colleges/{college_id}/requirements")
async def get_college_checklist(
    college_id: str,
    request: Request,
    response: Response,
):
    """Get requirement checklist items for a saved college."""
    pid = _ensure_cookie(request, response)
    items = await portfolio_store.get_checklist(pid, college_id)
    item_dicts = [it.model_dump() for it in items]
    return {
        "items": item_dicts,
        "requirements": item_dicts,
        "count": len(item_dicts),
    }


@router.delete("/tracker/{college_id}/checklist/{item_id}")
@router.delete("/colleges/{college_id}/requirements/{item_id}")
async def delete_college_checklist_item(
    college_id: str,
    item_id: str,
    request: Request,
    response: Response,
):
    """Delete a checklist requirement item."""
    pid = _ensure_cookie(request, response)
    deleted = await portfolio_store.delete_checklist_item(pid, college_id, item_id)
    return {"status": "success", "deleted": deleted}


@router.get("/requirements-matrix")
async def get_requirements_matrix(
    request: Request,
    response: Response,
):
    """Get cross-school requirement checklist matrix."""
    pid = _ensure_cookie(request, response)
    matrix = await portfolio_store.get_requirements_matrix(pid)
    return matrix


class ToggleRequirementAllPayload(BaseModel):
    requirement_name: str
    completed: Optional[bool] = None


class ToggleEverythingPayload(BaseModel):
    completed: bool = True


@router.post("/requirements-matrix/toggle-all")
async def toggle_requirement_all(
    payload: ToggleRequirementAllPayload,
    request: Request,
    response: Response,
):
    """Mark a requirement as done (or incomplete) across all saved colleges in one click."""
    pid = _ensure_cookie(request, response)
    result = await portfolio_store.toggle_requirement_all(
        pid, payload.requirement_name, payload.completed
    )
    return result


@router.post("/requirements-matrix/toggle-everything")
async def toggle_everything(
    payload: ToggleEverythingPayload,
    request: Request,
    response: Response,
):
    """Mark all requirements across all saved colleges as done (or incomplete) in one click."""
    pid = _ensure_cookie(request, response)
    result = await portfolio_store.toggle_all_requirements(pid, payload.completed)
    return result


@router.post("/tracker/{college_id}/checklist/bulk")
async def toggle_college_checklist_bulk(
    college_id: str,
    payload: ToggleEverythingPayload,
    request: Request,
    response: Response,
):
    """Mark all requirements for a single college as done (or incomplete) in one click."""
    pid = _ensure_cookie(request, response)
    result = await portfolio_store.toggle_college_checklist_all(pid, college_id, payload.completed)
    return result


