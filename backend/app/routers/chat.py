import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth_utils import get_current_user_claims
from app.repositories.user_repo import user_repository
from app.repositories.profile_repo import profile_repository
from app.repositories.scheme_repo import scheme_repository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import ai_service
from app.services.translation_service import translation_service
from app.models.analytics import AnalyticsEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["AI Policy Assistant"])

@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse, include_in_schema=False)
def converse_with_policy_ai(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """
    RAG chat assistant that supports translations, semantic search, and citation sources.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not synced.")

    user_profile = profile_repository.get_by_user_id(db, str(user.id))
    profile_dict = None
    if user_profile:
        profile_dict = {
            "name": user_profile.name,
            "age": user_profile.age,
            "gender": user_profile.gender,
            "state": user_profile.state,
            "education": user_profile.education,
            "occupation": user_profile.occupation,
            "income": user_profile.income,
            "startup_status": user_profile.startup_status,
            "student_status": user_profile.student_status
        }

    lang = payload.language
    original_message = payload.message

    # Step 1: Translate to English if query is in Kannada or Hindi
    english_query = translation_service.translate_to_english(original_message, lang)
    logger.info(f"Query translated from {lang}: '{original_message}' -> '{english_query}'")

    # Save to user's search history database
    scheme_repository.add_search_history(db, str(user.id), english_query)

    # Step 2: Query Expansion
    queries = ai_service.expand_query(english_query)

    # Step 3: Vector search matching documents in Chroma
    search_results = ai_service.vector_search(queries, limit=5)

    # Step 4: Fetch all schemes in SQL DB to resolve detailed metadata for citations
    all_schemes = scheme_repository.get_multi(db, limit=200)

    # Step 5: Synthesize grounded response using GPT-4o
    answer_en, citations, confidence = ai_service.synthesize_response(
        query=english_query,
        search_results=search_results,
        schemes_db=all_schemes,
        profile_dict=profile_dict,
        history=payload.history
    )

    # Step 6: Translate back to original query language (Hindi/Kannada) if needed
    final_answer = translation_service.translate_from_english(answer_en, lang)

    # Log chat analytics event
    event = AnalyticsEvent(
        user_id=user.id,
        event_type="chat_query",
        details={
            "query": original_message,
            "language": lang,
            "confidence_score": confidence,
            "citations_count": len(citations)
        }
    )
    db.add(event)
    db.commit()

    return ChatResponse(
        response=final_answer,
        citations=citations,
        confidence_score=confidence,
        language=lang
    )
