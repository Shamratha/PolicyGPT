import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True, nullable=False) # standard handle/slug
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    benefits = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    required_documents = Column(Text, nullable=True)
    application_steps = Column(Text, nullable=True)
    state = Column(String, default="Central") # e.g. "Central", "Karnataka"
    category = Column(String, nullable=True) # e.g. "Business", "Education", "Agriculture"
    ministry = Column(String, nullable=True)
    is_for_women = Column(Boolean, default=False)
    is_for_students = Column(Boolean, default=False)
    is_for_startups = Column(Boolean, default=False)
    is_for_farmers = Column(Boolean, default=False)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    rules = relationship("EligibilityRule", back_populates="scheme", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="scheme", cascade="all, delete-orphan")
    surveys = relationship("Survey", back_populates="scheme", cascade="all, delete-orphan")
    saved_by_users = relationship("SavedScheme", back_populates="scheme", cascade="all, delete-orphan")

class EligibilityRule(Base):
    __tablename__ = "eligibility_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String, nullable=False) # e.g. "age", "gender", "income", "state", "student_status", "startup_status"
    operator = Column(String, nullable=False) # e.g. ">=", "<=", "==", "in"
    expected_value = Column(String, nullable=False) # e.g. "18", "35", "female", "karnataka", "true"
    created_at = Column(DateTime, server_default=func.now())

    scheme = relationship("Scheme", back_populates="rules")

class SavedScheme(Base):
    __tablename__ = "saved_schemes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_id = Column(String, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="saved_schemes")
    scheme = relationship("Scheme", back_populates="saved_by_users")

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="search_history")
