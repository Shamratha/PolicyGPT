import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    scheme_id = Column(String, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=True)
    aware_of_scheme = Column(Boolean, default=True)
    applied_for_scheme = Column(Boolean, default=False)
    difficulty_rating = Column(Integer, nullable=True) # 1 to 5 scale
    application_status = Column(String, nullable=True) # e.g. "Completed", "In Progress", "Rejected", "Approved", "Not Applied"
    bottleneck_reason = Column(String, nullable=True) # e.g. "Complex documentation", "Online portal broken", etc.
    feedback_comments = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="surveys")
    scheme = relationship("Scheme", back_populates="surveys")
