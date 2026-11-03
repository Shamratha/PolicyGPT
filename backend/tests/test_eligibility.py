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
from app.services.eligibility_service import eligibility_service

# Setup in-memory SQLite for isolated test runs
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

def test_evaluate_gender_rule():
    # Pass rule: Gender must be Female
    rule = EligibilityRule(field_name="gender", operator="==", expected_value="female")
    
    female_profile = Profile(gender="Female")
    passed, msg = eligibility_service.evaluate_rule(rule, female_profile)
    assert passed is True
    
    male_profile = Profile(gender="Male")
    passed, msg = eligibility_service.evaluate_rule(rule, male_profile)
    assert passed is False

def test_evaluate_age_rule():
    # Pass rule: Age must be >= 18 and <= 55
    rule_min = EligibilityRule(field_name="age", operator=">=", expected_value="18")
    rule_max = EligibilityRule(field_name="age", operator="<=", expected_value="55")
    
    p_young = Profile(age=17)
    passed_min, _ = eligibility_service.evaluate_rule(rule_min, p_young)
    assert passed_min is False

    p_valid = Profile(age=25)
    passed_min, _ = eligibility_service.evaluate_rule(rule_min, p_valid)
    passed_max, _ = eligibility_service.evaluate_rule(rule_max, p_valid)
    assert passed_min is True
    assert passed_max is True

    p_old = Profile(age=60)
    passed_max, _ = eligibility_service.evaluate_rule(rule_max, p_old)
    assert passed_max is False

def test_check_eligibility_hybrid(db_session):
    # Setup mock scheme in test database
    scheme = Scheme(
        name="test_scheme",
        title="Test Scheme Title",
        description="Testing guidelines description details.",
        state="Karnataka",
        category="Education"
    )
    db_session.add(scheme)
    db_session.commit()
    db_session.refresh(scheme)

    # Add rules
    rule1 = EligibilityRule(scheme_id=scheme.id, field_name="state", operator="==", expected_value="karnataka")
    rule2 = EligibilityRule(scheme_id=scheme.id, field_name="income", operator="<=", expected_value="100000")
    db_session.add_all([rule1, rule2])
    db_session.commit()
    db_session.refresh(scheme)

    # 1. Test case: User passes all checks
    profile_eligible = Profile(state="Karnataka", income=50000.0)
    result = eligibility_service.check_eligibility(db_session, profile_eligible, scheme)
    # Since we are using mock openai keys during tests, the check completes using the fallback logic
    assert result.status in ["Eligible", "Potentially Eligible"]

    # 2. Test case: User fails a hard check (state)
    profile_failed = Profile(state="Maharashtra", income=50000.0)
    result = eligibility_service.check_eligibility(db_session, profile_failed, scheme)
    assert result.status == "Not Eligible"
    assert "State" in result.reason


def test_occupation_and_in_rules():
    farmer_rule = EligibilityRule(field_name="occupation", operator="==", expected_value="farmer")
    assert eligibility_service.evaluate_rule(farmer_rule, Profile(occupation="Farmer"))[0] is True
    assert eligibility_service.evaluate_rule(farmer_rule, Profile(occupation="Student"))[0] is False

    in_rule = EligibilityRule(field_name="state", operator="in", expected_value="karnataka, kerala")
    assert eligibility_service.evaluate_rule(in_rule, Profile(state="Kerala"))[0] is True
    assert eligibility_service.evaluate_rule(in_rule, Profile(state="Bihar"))[0] is False


def test_missing_profile_is_potentially_eligible(db_session):
    scheme = Scheme(name="s2", title="S2", description="desc", state="Central")
    db_session.add(scheme)
    db_session.flush()
    db_session.add(EligibilityRule(scheme_id=scheme.id, field_name="age", operator=">=", expected_value="18"))
    db_session.commit()
    db_session.refresh(scheme)
    result = eligibility_service.check_eligibility(db_session, None, scheme)
    assert result.status == "Potentially Eligible"
    assert "age" in result.reason
