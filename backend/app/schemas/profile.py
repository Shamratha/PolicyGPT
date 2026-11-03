from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Gender = Literal["Male", "Female", "Other"]


class ProfileBase(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[Gender] = None
    state: Optional[str] = Field(None, max_length=60)
    education: Optional[str] = Field(None, max_length=60)
    occupation: Optional[str] = Field(None, max_length=60)
    income: Optional[float] = Field(None, ge=0.0, le=1_000_000_000)
    startup_status: Optional[bool] = False
    student_status: Optional[bool] = False

    @field_validator("name", "state", "education", "occupation", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v

    @field_validator("gender", mode="before")
    @classmethod
    def normalise_gender(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v.capitalize() if v else None
        return v


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    # Stored values are returned as-is (older rows may predate validation).
    gender: Optional[str] = None
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
