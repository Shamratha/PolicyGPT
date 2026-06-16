from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class AnalyticsEventCreate(BaseModel):
    event_type: str
    details: Dict[str, Any] = {}

class AnalyticsEventResponse(AnalyticsEventCreate):
    id: str
    user_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PopularScheme(BaseModel):
    scheme_id: str
    scheme_title: str
    count: int

class StateUsage(BaseModel):
    state: str
    count: int

class AnalyticsSummaryResponse(BaseModel):
    users_served: int
    schemes_indexed: int
    searches_performed: int
    most_requested_schemes: List[PopularScheme]
    state_wise_usage: List[StateUsage]
    eligibility_success_rate: float # Percentage of checks returning Eligible/Potentially Eligible
