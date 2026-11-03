from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ApplicationStatus = Literal["Completed", "In Progress", "Approved", "Rejected", "Not Applied"]


class SurveyCreate(BaseModel):
    scheme_id: Optional[str] = None
    aware_of_scheme: bool = True
    applied_for_scheme: bool = False
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)
    application_status: Optional[ApplicationStatus] = None
    bottleneck_reason: Optional[str] = Field(None, max_length=200)
    feedback_comments: Optional[str] = Field(None, max_length=2000)

    @field_validator("scheme_id", "bottleneck_reason", "feedback_comments", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v

    @model_validator(mode="after")
    def check_consistency(self):
        if self.applied_for_scheme and not self.aware_of_scheme:
            raise ValueError("You cannot have applied for a scheme you were not aware of.")
        if not self.applied_for_scheme:
            if self.application_status not in (None, "Not Applied"):
                raise ValueError("application_status must be 'Not Applied' when applied_for_scheme is false.")
            if self.difficulty_rating is not None:
                raise ValueError("difficulty_rating can only be given when applied_for_scheme is true.")
            self.application_status = "Not Applied"
        elif self.application_status == "Not Applied":
            raise ValueError("application_status cannot be 'Not Applied' when applied_for_scheme is true.")
        return self


class SurveyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    scheme_id: Optional[str] = None
    aware_of_scheme: bool
    applied_for_scheme: bool
    difficulty_rating: Optional[int] = None
    application_status: Optional[str] = None
    bottleneck_reason: Optional[str] = None
    feedback_comments: Optional[str] = None
    created_at: datetime


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
    awareness_rate: float  # 0 to 100
    application_rate: float  # 0 to 100
    average_difficulty: float  # 1.0 to 5.0
    bottlenecks: Dict[str, int]
    status_distribution: Dict[str, int]
    state_awareness: List[StateAwarenessStats]
    underserved_demographics: List[DemographicsStats]
