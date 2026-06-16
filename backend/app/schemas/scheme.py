from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class EligibilityRuleBase(BaseModel):
    field_name: str
    operator: str
    expected_value: str

class EligibilityRuleCreate(EligibilityRuleBase):
    pass

class EligibilityRuleResponse(EligibilityRuleBase):
    id: str
    scheme_id: str

    class Config:
        from_attributes = True

class SchemeBase(BaseModel):
    name: str
    title: str
    description: str
    benefits: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    required_documents: Optional[str] = None
    application_steps: Optional[str] = None
    state: str = "Central"
    category: Optional[str] = None
    ministry: Optional[str] = None
    is_for_women: bool = False
    is_for_students: bool = False
    is_for_startups: bool = False
    is_for_farmers: bool = False
    deadline: Optional[datetime] = None

class SchemeCreate(SchemeBase):
    rules: Optional[List[EligibilityRuleCreate]] = []

class SchemeResponse(SchemeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    rules: List[EligibilityRuleResponse] = []

    class Config:
        from_attributes = True

class EligibilityCheckResponse(BaseModel):
    scheme_id: str
    scheme_title: str
    status: str # "Eligible", "Potentially Eligible", "Not Eligible"
    reason: str
    benefits: Optional[str] = ""
    required_documents: List[str] = []
    application_steps: List[str] = []
    next_opportunities: List[str] = []

class SavedSchemeResponse(BaseModel):
    id: str
    scheme_id: str
    scheme: SchemeResponse
    created_at: datetime

    class Config:
        from_attributes = True

class SearchHistoryResponse(BaseModel):
    id: str
    query: str
    created_at: datetime

    class Config:
        from_attributes = True

class ScrapeRequest(BaseModel):
    url: str

