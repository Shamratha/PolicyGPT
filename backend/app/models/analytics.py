import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String, nullable=False) # e.g. "search", "eligibility_check", "view_scheme", "chat_query"
    details = Column(JSON, default=dict) # Event-specific metadata
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
