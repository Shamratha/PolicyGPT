import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.scraper_service import scraper_service, extract_text_from_html
from app.models.scheme import Scheme, EligibilityRule

# Setup in-memory sqlite for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_html_text_extraction():
    html = """
    <html>
        <head><title>Ignore Head</title></head>
        <body>
            <header>Ignore Header</header>
            <nav>Ignore Nav</nav>
            <main>
                <h1>Scraped Title</h1>
                <p>This is the actual content of the page.</p>
            </main>
            <footer>Ignore Footer</footer>
            <script>console.log("Ignore Script");</script>
            <style>body { color: red; }</style>
        </body>
    </html>
    """
    cleaned = extract_text_from_html(html)
    assert "Ignore Head" not in cleaned
    assert "Ignore Header" not in cleaned
    assert "Ignore Nav" not in cleaned
    assert "Ignore Footer" not in cleaned
    assert "Ignore Script" not in cleaned
    assert "Scraped Title" in cleaned
    assert "This is the actual content of the page." in cleaned

@patch("httpx.Client.get")
@patch("app.services.ai_service.ai_service.index_scheme_text")
def test_scrape_and_index_pipeline(mock_index, mock_get, db_session):
    # Mock HTTTP response
    mock_resp = MagicMock()
    mock_resp.text = """
    <html>
        <body>
            <h1>Rajiv Gandhi Entrepreneurship Program</h1>
            <p>Guidelines for Karnataka tech startups. Funding up to 25,000 monthly.</p>
        </body>
    </html>
    """
    mock_resp.raise_for_status = MagicMock()
    
    # Configure mock client context manager
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_get.return_value = mock_resp
    
    # We patch httpx.Client constructor to return our mock client
    with patch("httpx.Client") as mock_client_class:
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Trigger scraping pipeline (offline mode extracts the record from the page with heuristics)
        scheme = scraper_service.scrape_and_index_scheme(
            url="https://eitbt.karnataka.gov.in/startup/rajiv-gandhi",
            db=db_session
        )
        
        # Verify database record creation
        assert scheme is not None
        assert str(scheme.name) == "rajiv_gandhi_entrepreneurship_program"
        assert str(scheme.title) == "Rajiv Gandhi Entrepreneurship Program"
        assert bool(scheme.is_for_startups) is True
        assert str(scheme.state) == "Karnataka"
        
        # Verify eligibility rules creation
        rules = db_session.query(EligibilityRule).filter(EligibilityRule.scheme_id == str(scheme.id)).all()
        assert {(r.field_name, r.expected_value) for r in rules} == {("state", "karnataka"), ("startup_status", "true")}
        state_rule = next(r for r in rules if r.field_name == "state")
        assert state_rule.operator == "=="
        assert state_rule.expected_value == "karnataka"
        
        # Verify vector DB indexing was triggered
        mock_index.assert_called_once()
        called_args = mock_index.call_args[0]
        assert called_args[0] == str(scheme.id)
        assert called_args[1] == "rajiv_gandhi_entrepreneurship_program"
        assert "Karnataka" in called_args[2]
