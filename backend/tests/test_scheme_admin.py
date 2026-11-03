"""Tests for adding / deleting schemes and scholarships (admin feature)."""
from datetime import date, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def auth(sub: str, email: str = "") -> dict:
    token = jwt.encode({"sub": sub, "email": email or f"{sub}@example.com"}, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


ADMIN = auth("admin_user", "admin@policygpt.in")
CITIZEN = auth("citizen_user", "citizen@example.com")

VALID = {
    "title": "Karnataka Vidya Siri Scholarship",
    "description": "Food and accommodation support for backward-class students studying in Karnataka.",
    "benefits": "Rs. 1,500 per month for 10 months",
    "eligibility_criteria": "Karnataka students aged 17-30 with family income up to Rs. 2.5 lakh",
    "required_documents": "Aadhaar card, Income certificate, Caste certificate, College admission receipt",
    "application_steps": "1. Register on SSP portal. 2. Fill the post-matric form. 3. Submit documents to college.",
    "state": "Karnataka",
    "category": "Education",
    "ministry": "Backward Classes Welfare Department, Karnataka",
    "is_for_students": True,
    "deadline": (date.today() + timedelta(days=60)).isoformat(),
    "rules": [
        {"field_name": "state", "operator": "==", "expected_value": "Karnataka"},
        {"field_name": "student_status", "operator": "==", "expected_value": "yes"},
        {"field_name": "income", "operator": "<=", "expected_value": "250000"},
        {"field_name": "age", "operator": ">=", "expected_value": "17"},
        {"field_name": "age", "operator": "<=", "expected_value": "30"},
    ],
}


@pytest.fixture(scope="module", autouse=True)
def users():
    for h in (ADMIN, CITIZEN):
        client.post("/api/auth/sync-user", headers=h)
    # a student in Karnataka and a farmer in Bihar
    client.post("/api/profiles/me", headers=ADMIN, json={
        "age": 20, "gender": "Female", "state": "Karnataka", "income": 150000, "student_status": True,
    })
    client.post("/api/profiles/me", headers=CITIZEN, json={
        "age": 45, "gender": "Male", "state": "Bihar", "income": 90000, "occupation": "Farmer", "student_status": False,
    })


@pytest.fixture(scope="module")
def created():
    res = client.post("/api/schemes", headers=ADMIN, json=VALID)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_scheme_returns_full_record(created):
    assert created["name"] == "karnataka_vidya_siri_scholarship"  # generated from the title
    assert created["category"] == "Education" and created["is_for_students"] is True
    assert created["deadline"].startswith(VALID["deadline"])
    rules = {(r["field_name"], r["operator"], r["expected_value"]) for r in created["rules"]}
    assert ("state", "==", "karnataka") in rules
    assert ("student_status", "==", "true") in rules  # "yes" normalised


def test_new_scheme_is_listed_and_searchable(created):
    assert any(s["id"] == created["id"] for s in client.get("/api/schemes", params={"students": True}).json())
    assert client.get(f"/api/schemes/{created['id']}").status_code == 200
    chat = client.post("/api/chat", headers=ADMIN, json={"message": "Vidya Siri scholarship for students"}).json()
    assert created["name"] in [c["scheme_name"] for c in chat["citations"]]


def test_new_scheme_rules_drive_eligibility(created):
    ok = client.get(f"/api/schemes/{created['id']}/eligibility", headers=ADMIN).json()
    assert ok["status"] == "Eligible", ok
    assert "Aadhaar card" in ok["required_documents"]
    no = client.get(f"/api/schemes/{created['id']}/eligibility", headers=CITIZEN).json()
    assert no["status"] == "Not Eligible"


def test_duplicate_scheme_rejected(created):
    res = client.post("/api/schemes", headers=ADMIN, json=VALID)
    assert res.status_code == 409


def test_minimal_scheme_without_rules():
    res = client.post("/api/schemes", headers=ADMIN, json={
        "title": "PM Vishwakarma", "description": "Support for traditional artisans and craftspeople across India.",
    })
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["state"] == "Central" and body["category"] == "General" and body["rules"] == []


@pytest.mark.parametrize("override", [
    {"title": "ab"},
    {"title": "   "},
    {"description": "too short"},
    {"name": "Bad Name!"},
    {"category": "Fashion"},
    {"deadline": "2020-01-01"},
    {"deadline": "not-a-date"},
    {"is_for_students": "sometimes"},
    {"rules": [{"field_name": "age", "operator": ">=", "expected_value": "eighteen"}]},
    {"rules": [{"field_name": "age", "operator": "<=", "expected_value": "200"}]},
    {"rules": [{"field_name": "age", "operator": ">=", "expected_value": "40"}, {"field_name": "age", "operator": "<=", "expected_value": "30"}]},
    {"rules": [{"field_name": "income", "operator": "<=", "expected_value": "-1"}]},
    {"rules": [{"field_name": "student_status", "operator": ">=", "expected_value": "true"}]},
    {"rules": [{"field_name": "student_status", "operator": "==", "expected_value": "maybe"}]},
    {"rules": [{"field_name": "gender", "operator": "==", "expected_value": "robot"}]},
    {"rules": [{"field_name": "height", "operator": ">=", "expected_value": "150"}]},
    {"rules": [{"field_name": "age", "operator": "~", "expected_value": "18"}]},
    {"rules": [{"field_name": "state", "operator": "==", "expected_value": "Kerala"}]},
    {"rules": [{"field_name": "age", "operator": ">=", "expected_value": "18"}, {"field_name": "age", "operator": ">=", "expected_value": "20"}]},
    {"rules": [{"field_name": "age", "operator": ">=", "expected_value": ""}]},
    {"is_for_women": True, "rules": [{"field_name": "gender", "operator": "==", "expected_value": "male"}]},
])
def test_create_scheme_validation(override):
    payload = {**VALID, "title": "Validation Probe Scheme", **override}
    res = client.post("/api/schemes", headers=ADMIN, json=payload)
    assert res.status_code == 422, res.text


def test_create_scheme_requires_valid_login():
    res = client.post("/api/schemes", headers={"Authorization": "Bearer garbage"}, json=VALID)
    assert res.status_code == 401


def test_only_admins_can_manage_when_allow_list_set(monkeypatch, created):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@policygpt.in")
    payload = {**VALID, "title": "Citizen Attempt Scheme"}
    assert client.post("/api/schemes", headers=CITIZEN, json=payload).status_code == 403
    assert client.delete(f"/api/schemes/{created['id']}", headers=CITIZEN).status_code == 403
    assert client.post("/api/schemes/upload", headers=CITIZEN, data={"scheme_id": created["id"]},
                       files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")}).status_code == 403
    assert client.post("/api/schemes/scrape", headers=CITIZEN, json={"url": "https://example.com"}).status_code == 403
    res = client.post("/api/schemes", headers=ADMIN, json=payload)
    assert res.status_code == 201, res.text


def test_delete_scheme():
    res = client.post("/api/schemes", headers=ADMIN, json={
        "title": "Temporary Scheme To Delete", "description": "This scheme exists only to test deletion end to end.",
    })
    sid = res.json()["id"]
    client.post(f"/api/dashboard/save/{sid}", headers=ADMIN)
    assert client.delete(f"/api/schemes/{sid}", headers=ADMIN).status_code == 204
    assert client.get(f"/api/schemes/{sid}").status_code == 404
    assert client.delete(f"/api/schemes/{sid}", headers=ADMIN).status_code == 404
    dash = client.get("/api/dashboard", headers=ADMIN).json()
    assert all(s["scheme_id"] != sid for s in dash["saved_schemes"])
