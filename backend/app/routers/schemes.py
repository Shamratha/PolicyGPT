import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.utils.auth_utils import get_current_user_claims
from app.repositories.user_repo import user_repository
from app.repositories.profile_repo import profile_repository
from app.repositories.scheme_repo import scheme_repository
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeResponse, EligibilityCheckResponse, ScrapeRequest
from app.services.eligibility_service import eligibility_service
from app.services.ai_service import ai_service
from app.services.scraper_service import scraper_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schemes", tags=["Schemes"])

@router.get("/", response_model=List[SchemeResponse])
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
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to upload guidelines PDF and index in ChromaDB.
    """
    scheme = scheme_repository.get(db, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found in SQL database.")

    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are accepted.")

    try:
        # Extract text from uploaded PDF
        text = ai_service.extract_text_from_pdf(file.file)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from PDF.")

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
    claims: dict = Depends(get_current_user_claims)
):
    """
    Scrape an official government scheme guidelines webpage and register/index it.
    Only authenticated users (acting as admins) can scrape and add new schemes.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
        
    try:
        scheme = scraper_service.scrape_and_index_scheme(payload.url, db)
        return scheme
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run scrape pipeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to run scraping pipeline.")

