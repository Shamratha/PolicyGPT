from pydantic import BaseModel, EmailStr
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

    class Config:
        from_attributes = True
