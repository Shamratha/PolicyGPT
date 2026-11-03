import re
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from typing import Dict, Literal, Optional, List
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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

class SearchHistoryResponse(BaseModel):
    id: str
    query: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScrapeRequest(BaseModel):
    url: HttpUrl


ApplicationStatus = Literal["Draft", "Submitted", "Approved", "Rejected"]


class UpdateApplicationRequest(BaseModel):
    checklist: Dict[str, bool] = Field(default_factory=dict, max_length=50)
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    scheme_id: str
    status: str
    document_checklist: Dict[str, bool] = {}
    progress_percentage: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None



# ---------------------------------------------------------------------------
# Creating schemes / scholarships (admin)
# ---------------------------------------------------------------------------
SchemeCategory = Literal[
    "Education", "Business", "Agriculture", "Healthcare", "Housing", "Employment",
    "Social Welfare", "Women & Child", "General",
]
RuleField = Literal["age", "income", "gender", "state", "occupation", "education", "student_status", "startup_status"]
RuleOperator = Literal[">=", "<=", "==", "!=", "in"]

_NUMERIC_FIELDS = {"age", "income"}
_BOOLEAN_FIELDS = {"student_status", "startup_status"}
_TRUE = {"true", "yes", "1"}
_FALSE = {"false", "no", "0"}


class EligibilityRuleIn(BaseModel):
    field_name: RuleField
    operator: RuleOperator
    expected_value: str = Field(..., min_length=1, max_length=200)

    @model_validator(mode="after")
    def check_rule(self):
        value = self.expected_value.strip()
        if not value:
            raise ValueError("Rule value cannot be empty.")
        field, op = self.field_name, self.operator
        if field in _NUMERIC_FIELDS:
            if op not in (">=", "<=", "=="):
                raise ValueError(f"'{field}' rules must use >=, <= or ==.")
            try:
                number = float(value)
            except ValueError:
                raise ValueError(f"'{field}' rule value must be a number.")
            if field == "age":
                if not number.is_integer() or not 0 <= number <= 120:
                    raise ValueError("Age rule value must be a whole number between 0 and 120.")
                value = str(int(number))
            else:
                if number < 0:
                    raise ValueError("Income rule value cannot be negative.")
                value = str(int(number)) if number.is_integer() else str(number)
        elif field in _BOOLEAN_FIELDS:
            if op != "==":
                raise ValueError(f"'{field}' rules must use ==.")
            low = value.lower()
            if low not in _TRUE | _FALSE:
                raise ValueError(f"'{field}' rule value must be true or false.")
            value = "true" if low in _TRUE else "false"
        else:
            if op not in ("==", "!=", "in"):
                raise ValueError(f"'{field}' rules must use ==, != or in.")
            value = ", ".join(v.strip().lower() for v in value.split(",") if v.strip()) if op == "in" else value.lower()
            if field == "gender":
                allowed = {"male", "female", "other"}
                if any(v.strip() not in allowed for v in value.split(",")):
                    raise ValueError("Gender rule value must be male, female or other.")
        self.expected_value = value
        return self


class SchemeCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    name: Optional[str] = Field(None, description="URL-friendly id; generated from the title when empty")
    description: str = Field(..., min_length=20, max_length=5000)
    benefits: Optional[str] = Field(None, max_length=3000)
    eligibility_criteria: Optional[str] = Field(None, max_length=3000)
    required_documents: Optional[str] = Field(None, max_length=3000)
    application_steps: Optional[str] = Field(None, max_length=3000)
    state: str = Field("Central", min_length=2, max_length=60)
    category: SchemeCategory = "General"
    ministry: Optional[str] = Field(None, max_length=200)
    is_for_women: bool = False
    is_for_students: bool = False
    is_for_startups: bool = False
    is_for_farmers: bool = False
    deadline: Optional[date] = None
    rules: List[EligibilityRuleIn] = Field(default_factory=list, max_length=20)

    @field_validator("title", "description", "state", mode="before")
    @classmethod
    def strip_required(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("name", "benefits", "eligibility_criteria", "required_documents", "application_steps", "ministry", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v

    @field_validator("name")
    @classmethod
    def check_slug(cls, v):
        if v is not None and not re.fullmatch(r"[a-z0-9_]{3,60}", v):
            raise ValueError("name may only contain lowercase letters, numbers and underscores (3-60 characters).")
        return v

    @field_validator("deadline")
    @classmethod
    def deadline_not_past(cls, v):
        if v is not None and v < date.today():
            raise ValueError("Deadline cannot be in the past.")
        return v

    @model_validator(mode="after")
    def check_consistency(self):
        if self.name is None:
            slug = re.sub(r"[^a-z0-9]+", "_", self.title.lower()).strip("_")[:60]
            self.name = slug if len(slug) >= 3 else f"scheme_{slug}".strip("_")
        ages_min = [int(r.expected_value) for r in self.rules if r.field_name == "age" and r.operator == ">="]
        ages_max = [int(r.expected_value) for r in self.rules if r.field_name == "age" and r.operator == "<="]
        if ages_min and ages_max and max(ages_min) > min(ages_max):
            raise ValueError("Minimum age rule is higher than the maximum age rule.")
        for r in self.rules:
            if r.field_name == "gender" and r.operator == "==" and r.expected_value != "female" and self.is_for_women:
                raise ValueError("A women-only scheme cannot have a gender rule for a different gender.")
        state_rules = [r for r in self.rules if r.field_name == "state" and r.operator == "=="]
        if self.state.lower() != "central" and state_rules and state_rules[0].expected_value != self.state.lower():
            raise ValueError("The state eligibility rule does not match the scheme's state.")
        keys = [(r.field_name, r.operator) for r in self.rules]
        if len(keys) != len(set(keys)):
            raise ValueError("Each field/operator combination can only appear once in the rules.")
        return self
