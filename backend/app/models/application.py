import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_id = Column(String, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="Draft") # e.g. "Draft", "Submitted", "Approved", "Rejected"
    document_checklist = Column(JSON, default=dict) # e.g. {"Aadhaar": true, "Income Cert": false}
    progress_percentage = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="applications")
    scheme = relationship("Scheme", back_populates="applications")
