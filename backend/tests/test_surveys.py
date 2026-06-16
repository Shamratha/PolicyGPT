import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.profile import Profile
from app.models.scheme import Scheme, EligibilityRule, SavedScheme, SearchHistory
from app.models.application import Application
from app.models.survey import Survey
from app.models.analytics import AnalyticsEvent
from app.repositories.survey_repo import survey_repository
from app.services.report_service import report_service

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_survey_repository_empty(db_session):
    stats = survey_repository.get_analytics_stats(db_session)
    assert stats["total_submissions"] == 0
    assert stats["awareness_rate"] == 0.0
    assert stats["average_difficulty"] == 0.0
    assert len(stats["bottlenecks"]) == 0

def test_survey_repository_aggregation(db_session):
    # Setup mock user & profiles
    u1 = User(id="user-1", clerk_id="clerk-1")
    u2 = User(id="user-2", clerk_id="clerk-2")
    db_session.add_all([u1, u2])
    db_session.flush()

    p1 = Profile(user_id="user-1", state="Karnataka", gender="Female", occupation="Student")
    p2 = Profile(user_id="user-2", state="Karnataka", gender="Male", occupation="Farmer")
    db_session.add_all([p1, p2])
    db_session.flush()

    # Setup mock scheme
    scheme = Scheme(id="scheme-1", name="pmegp", title="PMEGP", description="Prime Minister Employment Generation Programme guidelines.")
    db_session.add(scheme)
    db_session.flush()

    # Add surveys
    s1 = Survey(
        user_id="user-1",
        scheme_id="scheme-1",
        aware_of_scheme=True,
        applied_for_scheme=True,
        difficulty_rating=4,
        application_status="Approved",
        bottleneck_reason="Complex documentation"
    )
    s2 = Survey(
        user_id="user-2",
        scheme_id="scheme-1",
        aware_of_scheme=False,
        applied_for_scheme=False,
        difficulty_rating=None,
        application_status="Not Applied",
        bottleneck_reason=None
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    # Run analytical check
    stats = survey_repository.get_analytics_stats(db_session)
    
    assert stats["total_submissions"] == 2
    assert stats["awareness_rate"] == 50.0 # 1 out of 2
    assert stats["application_rate"] == 50.0 # 1 out of 2
    assert stats["average_difficulty"] == 4.0
    assert stats["bottlenecks"]["Complex documentation"] == 1
    
    # State awareness: Karnataka should be grouped
    state_karnataka = next(item for item in stats["state_awareness"] if item["state"] == "Karnataka")
    assert state_karnataka["submissions_count"] == 2
    assert state_karnataka["awareness_rate"] == 50.0

def test_report_service_pdf_generation():
    mock_stats = {
        "total_submissions": 5,
        "awareness_rate": 80.0,
        "application_rate": 60.0,
        "average_difficulty": 3.4,
        "bottlenecks": {"Complex documentation": 3, "Online portal broken": 2},
        "status_distribution": {"Approved": 2, "In Progress": 3},
        "state_awareness": [
            {"state": "Karnataka", "awareness_rate": 85.0, "submissions_count": 3},
            {"state": "Maharashtra", "awareness_rate": 70.0, "submissions_count": 2}
        ],
        "underserved_demographics": [
            {"demographic": "Female - Student", "match_rate": 90.0, "volume": 3},
            {"demographic": "Male - Farmer", "match_rate": 50.0, "volume": 2}
        ]
    }
    
    pdf_bytes = report_service.generate_pdf_report(mock_stats)
    assert len(pdf_bytes) > 1000 # Check that a valid non-empty byte buffer is compiled
    assert pdf_bytes.startswith(b"%PDF") # PDF header identification
