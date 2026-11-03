import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.utils.auth_utils import get_current_user_claims
from app.repositories.user_repo import user_repository
from app.repositories.profile_repo import profile_repository
from app.repositories.scheme_repo import scheme_repository
from app.repositories.application_repo import application_repository
from app.schemas.scheme import ApplicationResponse, UpdateApplicationRequest
from app.services.eligibility_service import eligibility_service
from app.models.application import Application

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("")
@router.get("/", include_in_schema=False)
def get_user_dashboard_summary(
    db: Session = Depends(get_db), 
    claims: dict = Depends(get_current_user_claims)
):
    """
    Returns saved schemes, recent searches, application progress, and eligible schemes.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not synced.")

    profile = profile_repository.get_by_user_id(db, str(user.id))
    if not profile:
        profile = profile_repository.create(db, {"user_id": str(user.id)})

    # 1. Fetch saved schemes
    saved_models = scheme_repository.get_saved_schemes(db, str(user.id))
    saved_schemes = [
        {
            "id": sm.id,
            "scheme_id": sm.scheme_id,
            "title": sm.scheme.title,
            "name": sm.scheme.name,
            "category": sm.scheme.category,
            "state": sm.scheme.state
        } for sm in saved_models
    ]

    # 2. Fetch search history
    history_models = scheme_repository.get_search_history(db, str(user.id), limit=5)
    recent_searches = [{"id": hm.id, "query": hm.query, "created_at": hm.created_at} for hm in history_models]

    # 3. Fetch user applications progress
    app_models = application_repository.get_user_applications(db, str(user.id))
    applications = [
        {
            "id": am.id,
            "scheme_id": am.scheme_id,
            "scheme_title": am.scheme.title,
            "status": am.status,
            "progress": am.progress_percentage,
            "document_checklist": am.document_checklist
        } for am in app_models
    ]

    # 4. Compute matches: evaluate all schemes in database against user profile
    all_schemes = scheme_repository.get_multi(db, limit=100)
    matched_schemes = []
    
    # We do a fast evaluate
    for s in all_schemes:
        # Check if basic tags match user profile categories for relevance speedup
        # (e.g. if scheme is women-only and user is male, skip or mark not eligible)
        eval_res = eligibility_service.check_eligibility(db, profile, s)
        if eval_res.status in ["Eligible", "Potentially Eligible"]:
            matched_schemes.append({
                "scheme_id": s.id,
                "title": s.title,
                "status": eval_res.status,
                "reason": eval_res.reason,
                "category": s.category,
                "state": s.state
            })

    return {
        "saved_schemes": saved_schemes,
        "recent_searches": recent_searches,
        "applications": applications,
        "eligibility_matches": matched_schemes
    }

@router.post("/save/{scheme_id}")
def save_scheme(
    scheme_id: str, 
    db: Session = Depends(get_db), 
    claims: dict = Depends(get_current_user_claims)
):
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not synced.")

    scheme = scheme_repository.get(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    if scheme_repository.is_scheme_saved(db, str(user.id), scheme_id):
        return {"status": "already_saved"}

    scheme_repository.save_scheme(db, str(user.id), scheme_id)
    return {"status": "saved"}

@router.post("/unsave/{scheme_id}")
def unsave_scheme(
    scheme_id: str, 
    db: Session = Depends(get_db), 
    claims: dict = Depends(get_current_user_claims)
):
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not synced.")

    success = scheme_repository.unsave_scheme(db, str(user.id), scheme_id)
    return {"status": "unsaved" if success else "not_saved"}

@router.post("/applications/{scheme_id}/start", response_model=ApplicationResponse)
def start_application(
    scheme_id: str, 
    db: Session = Depends(get_db), 
    claims: dict = Depends(get_current_user_claims)
):
    """
    Starts an application, initializing the checklist of documents using the eligibility engine.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not synced.")

    scheme = scheme_repository.get(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")

    # Check if application already exists
    existing = application_repository.get_by_user_and_scheme(db, str(user.id), scheme_id)
    if existing:
        return existing

    profile = profile_repository.get_by_user_id(db, str(user.id))
    if not profile:
        profile = profile_repository.create(db, {"user_id": str(user.id)})

    # Generate document checklist using eligibility engine
    eval_res = eligibility_service.check_eligibility(db, profile, scheme)
    docs = eval_res.required_documents or ["Aadhaar Card", "Proof of Residency", "Income Certificate"]
    
    # Format document checklist as {"Aadhaar": False, ...}
    checklist = {doc: False for doc in docs}

    app = Application(
        user_id=user.id,
        scheme_id=scheme_id,
        status="Draft",
        document_checklist=checklist,
        progress_percentage=0
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

@router.post("/applications/{app_id}/update", response_model=ApplicationResponse)
def update_application(
    app_id: str,
    payload: UpdateApplicationRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """
    Update application checklist items and recalculate percentage progress.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not synced.")

    app = db.query(Application).filter(Application.id == app_id, Application.user_id == user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found.")

    # Update checklist
    app.document_checklist = payload.checklist  # type: ignore
    
    # Calculate progress percentage
    if payload.checklist:
        checked_count = sum(1 for checked in payload.checklist.values() if checked)
        total_count = len(payload.checklist)
        app.progress_percentage = int((checked_count / total_count) * 100)  # type: ignore
    else:
        app.progress_percentage = 0  # type: ignore

    app.status = payload.status  # type: ignore
    db.add(app)
    db.commit()
    db.refresh(app)
    return app
