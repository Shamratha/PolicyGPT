import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from app.database import get_db
from app.utils.auth_utils import get_current_user_claims
from app.repositories.user_repo import user_repository
from app.repositories.survey_repo import survey_repository
from app.schemas.survey import SurveyCreate, SurveyResponse, SurveyStatsResponse
from app.services.report_service import report_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/surveys", tags=["Policy Research surveys"])

@router.post("/submit", response_model=SurveyResponse)
def submit_research_survey(
    payload: SurveyCreate,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """
    Submits a user survey containing feedback on scheme awareness and access bottlenecks.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not synced.")

    survey_data = payload.model_dump()
    survey_data["user_id"] = user.id

    try:
        survey = survey_repository.create(db, survey_data)
        logger.info(f"User {user.id} submitted survey for scheme ID: {payload.scheme_id}")
        return survey
    except Exception as e:
        logger.error(f"Error saving survey: {e}")
        raise HTTPException(status_code=500, detail="Failed to save survey feedback.")

@router.get("/stats", response_model=SurveyStatsResponse)
def get_survey_statistics(db: Session = Depends(get_db)):
    """
    Compiles policy awareness metrics, bottleneck statistics, and demographic success rates.
    """
    try:
        stats = survey_repository.get_analytics_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error compiling survey stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to aggregate stats.")

@router.get("/report")
def download_policy_access_report(db: Session = Depends(get_db)):
    """
    Compiles research metrics and returns a downloadable PDF report.
    """
    try:
        stats = survey_repository.get_analytics_stats(db)
        pdf_bytes = report_service.generate_pdf_report(stats)
        
        # Stream response back
        headers = {
            "Content-Disposition": "attachment; filename=Policy_Access_Report.pdf",
            "Content-Type": "application/pdf"
        }
        return Response(content=pdf_bytes, headers=headers, media_type="application/pdf")
    except Exception as e:
        logger.error(f"Error compiling PDF report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF access report.")
