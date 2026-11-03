from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    clerk_id: str

class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    clerk_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
