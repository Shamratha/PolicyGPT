import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from collections import Counter
from app.database import get_db
from app.models.user import User
from app.models.scheme import Scheme, SearchHistory
from app.models.profile import Profile
from app.models.analytics import AnalyticsEvent
from app.schemas.analytics import AnalyticsSummaryResponse, PopularScheme, StateUsage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Impact Analytics"])

@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Retrieves system metrics for administrative dashboards.
    """
    try:
        users_count = db.query(User).count()
        schemes_count = db.query(Scheme).count()
        searches_count = db.query(SearchHistory).count()

        # Fetch eligibility check events to compute scheme popularity and success rate
        events = db.query(AnalyticsEvent).filter(AnalyticsEvent.event_type == "eligibility_check").all()
        
        # Aggregate popularity in python to maintain cross-database compatibility
        scheme_counter = Counter()
        scheme_titles = {}
        success_count = 0
        total_checks = len(events)

        for e in events:
            details = e.details or {}
            s_id = details.get("scheme_id")
            s_title = details.get("scheme_title")
            status = details.get("result_status")

            if s_id and s_title:
                scheme_counter[s_id] += 1
                scheme_titles[s_id] = s_title

            if status in ["Eligible", "Potentially Eligible"]:
                success_count += 1

        most_requested = [
            PopularScheme(scheme_id=s_id, scheme_title=scheme_titles[s_id], count=cnt)
            for s_id, cnt in scheme_counter.most_common(5)
        ]

        # Calculate eligibility success rate
        success_rate = (success_count / total_checks * 100.0) if total_checks > 0 else 0.0

        # State-wise usage stats
        state_usage_query = db.query(
            func.coalesce(Profile.state, 'Unknown').label('state'),
            func.count(AnalyticsEvent.id).label('event_count')
        ).select_from(AnalyticsEvent).join(
            Profile, AnalyticsEvent.user_id == Profile.user_id, isouter=True
        ).group_by(
            func.coalesce(Profile.state, 'Unknown')
        ).all()

        state_usage = [
            StateUsage(state=row[0] or "Unknown", count=row[1] or 0)
            for row in state_usage_query
        ]

        return AnalyticsSummaryResponse(
            users_served=users_count,
            schemes_indexed=schemes_count,
            searches_performed=searches_count,
            most_requested_schemes=most_requested,
            state_wise_usage=state_usage,
            eligibility_success_rate=round(success_rate, 2)
        )
    except Exception as e:
        logger.error(f"Error compiling analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics aggregates.")
