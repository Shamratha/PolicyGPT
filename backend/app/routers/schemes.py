import logging
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.config import settings
from app.utils.auth_utils import get_current_user_claims, require_admin
from app.repositories.user_repo import user_repository
from app.repositories.profile_repo import profile_repository
from app.repositories.scheme_repo import scheme_repository
from app.models.scheme import Scheme, EligibilityRule
from app.schemas.scheme import SchemeResponse, EligibilityCheckResponse, ScrapeRequest, SchemeCreateRequest
from app.services.eligibility_service import eligibility_service
from app.services.ai_service import ai_service
from app.services.scraper_service import scraper_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schemes", tags=["Schemes"])

@router.get("", response_model=List[SchemeResponse])
@router.get("/", response_model=List[SchemeResponse], include_in_schema=False)
def get_all_schemes(
    state: Optional[str] = None,
    category: Optional[str] = None,
    women: Optional[bool] = None,
    students: Optional[bool] = None,
    startups: Optional[bool] = None,
    farmers: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve government schemes with query filters.
    """
    query = db.query(Scheme)
    if state:
        query = query.filter(Scheme.state.ilike(f"%{state}%"))
    if category:
        query = query.filter(Scheme.category.ilike(f"%{category}%"))
    if women:
        query = query.filter(Scheme.is_for_women == True)
    if students:
        query = query.filter(Scheme.is_for_students == True)
    if startups:
        query = query.filter(Scheme.is_for_startups == True)
    if farmers:
        query = query.filter(Scheme.is_for_farmers == True)
    return query.all()

@router.post("", response_model=SchemeResponse, status_code=201)
@router.post("/", response_model=SchemeResponse, status_code=201, include_in_schema=False)
def create_scheme(
    payload: SchemeCreateRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_admin),
):
    """
    Add a new scheme or scholarship with optional rule-based eligibility criteria.
    The scheme is immediately searchable in the explorer, the AI assistant and eligibility checks.
    """
    if scheme_repository.get_by_name(db, str(payload.name)):
        raise HTTPException(status_code=409, detail=f"A scheme with the id '{payload.name}' already exists. Choose a different title or id.")

    data = payload.model_dump(exclude={"rules"})
    if payload.deadline:
        data["deadline"] = datetime.combine(payload.deadline, time(23, 59))
    scheme = Scheme(**data)
    try:
        db.add(scheme)
        db.flush()
        for rule in payload.rules:
            db.add(EligibilityRule(scheme_id=scheme.id, **rule.model_dump()))
        db.commit()
        db.refresh(scheme)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create scheme: {e}")
        raise HTTPException(status_code=500, detail="Could not save the scheme.")

    try:
        text = "\n".join(
            f"{label}: {value}" for label, value in (
                ("Title", scheme.title), ("Description", scheme.description), ("Benefits", scheme.benefits),
                ("Eligibility", scheme.eligibility_criteria), ("Documents", scheme.required_documents),
                ("How to apply", scheme.application_steps), ("State", scheme.state), ("Ministry", scheme.ministry),
            ) if value
        )
        ai_service.index_scheme_text(str(scheme.id), str(scheme.name), text)
    except Exception as e:  # search index is best-effort; the SQL record is the source of truth
        logger.warning(f"Scheme {scheme.name} saved but not indexed for AI search: {e}")

    logger.info(f"Scheme created by {claims.get('sub')}: {scheme.name}")
    return scheme


@router.delete("/{scheme_id}", status_code=204)
def delete_scheme(scheme_id: str, db: Session = Depends(get_db), claims: dict = Depends(require_admin)):
    """Remove a scheme (and its rules, saved bookmarks and applications)."""
    scheme = scheme_repository.get(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")
    db.delete(scheme)
    db.commit()
    try:
        if not settings.ai_offline:
            ai_service.collection.delete(where={"scheme_id": scheme_id})
    except Exception as e:
        logger.warning(f"Could not remove scheme {scheme_id} from the search index: {e}")
    logger.info(f"Scheme {scheme_id} deleted by {claims.get('sub')}")
    return Response(status_code=204)


@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme_by_id(scheme_id: str, db: Session = Depends(get_db)):
    """
    Get scheme details by its ID.
    """
    scheme = scheme_repository.get(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found.")
    return scheme

@router.get("/{scheme_id}/eligibility", response_model=EligibilityCheckResponse)
def evaluate_user_eligibility(
    scheme_id: str, 
    db: Session = Depends(get_db), 
    claims: dict = Depends(get_current_user_claims)
):
    """
    Evaluates profile against scheme criteria returning Eligible, Potentially Eligible, or Not Eligible.
    Also tracks this query event in Analytics.
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

    profile = profile_repository.get_by_user_id(db, str(user.id))
    if not profile:
        # Create blank profile for evaluation (causes missing fields triggers)
        profile = profile_repository.create(db, {"user_id": user.id})

    evaluation = eligibility_service.check_eligibility(db, profile, scheme)
    
    # Log analytics event
    from app.models.analytics import AnalyticsEvent
    event = AnalyticsEvent(
        user_id=user.id,
        event_type="eligibility_check",
        details={"scheme_id": scheme.id, "scheme_title": scheme.title, "result_status": evaluation.status}
    )
    db.add(event)
    db.commit()

    return evaluation

@router.post("/upload")
def upload_policy_document(
    scheme_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    claims: dict = Depends(require_admin),
):
    """
    Admin endpoint to upload guidelines PDF and index in ChromaDB.
    """
    scheme = scheme_repository.get(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found in SQL database.")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are accepted.")

    try:
        text = ai_service.extract_text_from_pdf(file.file)
    except Exception as e:
        logger.warning(f"Unreadable PDF upload {file.filename}: {e}")
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable PDF.")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from PDF.")

    try:
        # Chunk, embed, and store in ChromaDB
        ai_service.index_scheme_text(scheme_id, str(scheme.name), text)
        return {"status": "success", "message": f"Successfully indexed guidelines for {scheme.title}."}
    except Exception as e:
        logger.error(f"Error handling PDF upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process guidelines PDF: {str(e)}")

@router.post("/scrape", response_model=SchemeResponse)
def scrape_official_scheme(
    payload: ScrapeRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_admin)
):
    """
    Scrape an official government scheme guidelines webpage and register/index it.
    Only authenticated users (acting as admins) can scrape and add new schemes.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
        
    try:
        scheme = scraper_service.scrape_and_index_scheme(str(payload.url), db)
        return scheme
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run scrape pipeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to run scraping pipeline.")

