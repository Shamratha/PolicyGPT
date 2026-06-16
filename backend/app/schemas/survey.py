from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

class SurveyCreate(BaseModel):
    scheme_id: Optional[str] = None
    aware_of_scheme: bool = True
    applied_for_scheme: bool = False
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)
    application_status: Optional[str] = None # "Completed", "In Progress", "Rejected", "Approved", "Not Applied"
    bottleneck_reason: Optional[str] = None # e.g., "Complex documentation", "Online portal broken", etc.
    feedback_comments: Optional[str] = None

class SurveyResponse(SurveyCreate):
    id: str
    user_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DemographicsStats(BaseModel):
    demographic: str
    match_rate: float
    volume: int

class StateAwarenessStats(BaseModel):
    state: str
    awareness_rate: float
    submissions_count: int

class SurveyStatsResponse(BaseModel):
    total_submissions: int
    awareness_rate: float # 0 to 100
    application_rate: float # 0 to 100
    average_difficulty: float # 1.0 to 5.0
    bottlenecks: Dict[str, int]
    status_distribution: Dict[str, int]
    state_awareness: List[StateAwarenessStats]
    underserved_demographics: List[DemographicsStats]
