import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True) # e.g. "Male", "Female", "Other"
    state = Column(String, nullable=True) # e.g. "Karnataka", "Maharashtra", etc.
    education = Column(String, nullable=True) # e.g. "Graduate", "10th Pass", etc.
    occupation = Column(String, nullable=True) # e.g. "Student", "Unemployed", "Farmer"
    income = Column(Float, nullable=True) # Annual family income
    startup_status = Column(Boolean, default=False)
    student_status = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")
