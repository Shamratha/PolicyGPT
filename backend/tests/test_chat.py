import pytest
from app.services.translation_service import translation_service
from app.services.ai_service import ai_service
from app.schemas.chat import CitationInfo
from app.models.user import User
from app.models.profile import Profile
from app.models.scheme import Scheme, EligibilityRule, SavedScheme, SearchHistory
from app.models.application import Application
from app.models.survey import Survey
from app.models.analytics import AnalyticsEvent

def test_translation_bypasses():
    # Bypasses English query translation
    assert translation_service.translate_to_english("What is PMEGP?", "en") == "What is PMEGP?"
    assert translation_service.translate_from_english("Hello", "en") == "Hello"

def test_mock_query_expansion():
    # Verify query expansions are generated
    queries = ai_service.expand_query("startup grant")
    assert len(queries) >= 1
    assert "startup grant" in queries

def test_synthesize_response_citations():
    # Verify citations are correctly formed from search queries
    db_schemes = [
        Scheme(
            id="test-scheme-uuid",
            name="pmegp",
            title="Prime Minister Employment Generation Programme",
            state="Central",
            category="Business",
            benefits="Subsidy"
        )
    ]
    
    # Mock Chroma search output
    mock_search = [
        {
            "id": "test-scheme-uuid_chunk_0",
            "metadata": {"scheme_id": "test-scheme-uuid", "scheme_name": "pmegp"},
            "document": "PMEGP guidelines. Apply for loans up to Rs. 20 Lakhs.",
            "distance": 0.1
        }
    ]

    # Run synthesis (which triggers mock keys checks)
    ans, citations, conf = ai_service.synthesize_response(
        query="business loan",
        search_results=mock_search,
        schemes_db=db_schemes
    )

    assert "grounded" in ans
    assert "Prime Minister Employment Generation Programme" in ans
    assert len(citations) == 1
    assert citations[0].scheme_name == "pmegp"
    assert citations[0].scheme_title == "Prime Minister Employment Generation Programme"
    assert conf > 0


def test_offline_answer_no_match_returns_no_citations():
    db_schemes = [Scheme(id="s1", name="pmegp", title="PMEGP", state="Central", category="Business", description="Loans")]
    ans, citations, conf = ai_service.synthesize_response(query="weather forecast", search_results=[], schemes_db=db_schemes)
    assert citations == []
    assert conf == 0
    assert "couldn't find" in ans
