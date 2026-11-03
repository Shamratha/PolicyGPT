"""
Robustness / "does it crash?" tests.

Every endpoint is hit with malformed, hostile and unusual input. The server must always answer
with a proper status code below 500 (validation error, not found, unauthorised, ...) and never crash.
"""
import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app

# raise_server_exceptions=False -> a server crash shows up as a 500 response we can assert on
client = TestClient(app, raise_server_exceptions=False)

H = {"Authorization": "Bearer " + jwt.encode({"sub": "robustness_user"}, "x", algorithm="HS256")}
client.post("/api/auth/sync-user", headers=H)

WEIRD_STRINGS = [
    "",
    " ",
    "a" * 10000,
    "'; DROP TABLE schemes; --",
    "\" OR 1=1 --",
    "<script>alert('x')</script>",
    "{{7*7}} ${7*7}",
    "../../../../etc/passwd",
    "\u0000\u0001\u0002",
    "😀🚀🔥" * 50,
    "नमस्ते ಕನ್ನಡ مرحبا 你好",
    "%00%ff%fe",
]
WEIRD_VALUES = [None, 0, -1, 10**18, 3.14, True, [], {}, [1, 2], {"a": {"b": "c"}}, "null", "NaN"]

JSON_ENDPOINTS = [
    ("POST", "/api/chat"),
    ("POST", "/api/profiles/me"),
    ("POST", "/api/surveys/submit"),
    ("POST", "/api/schemes"),
    ("POST", "/api/schemes/scrape"),
]


def ok(res):
    assert res.status_code < 500, f"{res.request.method} {res.request.url} -> {res.status_code}: {res.text[:300]}"


@pytest.mark.parametrize("method,url", JSON_ENDPOINTS)
@pytest.mark.parametrize("body", [None, "not json", "[]", "{", "null", "12345"])
def test_malformed_bodies(method, url, body):
    ok(client.request(method, url, headers={**H, "Content-Type": "application/json"}, content=body))


@pytest.mark.parametrize("method,url", JSON_ENDPOINTS)
@pytest.mark.parametrize("value", WEIRD_VALUES + WEIRD_STRINGS)
def test_every_field_with_weird_values(method, url, value):
    fields = {
        "/api/chat": ["message", "language", "history"],
        "/api/profiles/me": ["name", "age", "gender", "state", "income", "student_status"],
        "/api/surveys/submit": ["scheme_id", "aware_of_scheme", "difficulty_rating", "application_status", "feedback_comments"],
        "/api/schemes": ["title", "description", "category", "deadline", "rules", "is_for_women"],
        "/api/schemes/scrape": ["url"],
    }[url]
    for field in fields:
        ok(client.request(method, url, headers=H, json={field: value}))


@pytest.mark.parametrize("text", WEIRD_STRINGS[1:])
def test_chat_with_hostile_text(text):
    res = client.post("/api/chat", headers=H, json={"message": text[:2000] or "x", "language": "en"})
    ok(res)
    if res.status_code == 200:
        assert isinstance(res.json()["response"], str)


@pytest.mark.parametrize("weird_id", ["x", "' OR '1'='1", "..%2F..%2Fetc", "😀", "a" * 500, "null", "0", "-1"])
def test_weird_ids_in_urls(weird_id):
    for method, url in [
        ("GET", f"/api/schemes/{weird_id}"),
        ("GET", f"/api/schemes/{weird_id}/eligibility"),
        ("DELETE", f"/api/schemes/{weird_id}"),
        ("POST", f"/api/dashboard/save/{weird_id}"),
        ("POST", f"/api/dashboard/unsave/{weird_id}"),
        ("POST", f"/api/dashboard/applications/{weird_id}/start"),
    ]:
        ok(client.request(method, url, headers=H))
    ok(client.post(f"/api/dashboard/applications/{weird_id}/update", headers=H, json={"checklist": {}, "status": "Draft"}))


@pytest.mark.parametrize("params", [
    {"state": "'; DROP TABLE schemes; --"}, {"state": "%"}, {"state": "_"}, {"category": "a" * 5000},
    {"women": "yes"}, {"students": "1"}, {"farmers": "maybe"}, {"startups": ""},
])
def test_weird_query_parameters(params):
    ok(client.get("/api/schemes", params=params))


@pytest.mark.parametrize("token", ["", "Bearer", "Bearer ", "Basic abc", "Bearer a.b.c", "Bearer " + "x" * 5000])
def test_weird_auth_headers(token):
    ok(client.get("/api/profiles/me", headers={"Authorization": token}))
    ok(client.get("/api/dashboard", headers={"Authorization": token}))


def test_token_without_subject():
    t = "Bearer " + jwt.encode({"email": "nosub@example.com"}, "x", algorithm="HS256")
    for method, url in [("POST", "/api/auth/sync-user"), ("GET", "/api/profiles/me"), ("GET", "/api/dashboard")]:
        ok(client.request(method, url, headers={"Authorization": t}))


@pytest.mark.parametrize("filename,content,ctype", [
    ("empty.pdf", b"", "application/pdf"),
    ("huge-name-" + "a" * 300 + ".pdf", b"%PDF-1.4 broken", "application/pdf"),
    ("image.png", b"\x89PNG\r\n", "image/png"),
    ("no_extension", b"data", "application/octet-stream"),
])
def test_bad_uploads(filename, content, ctype):
    sid = client.get("/api/schemes").json()[0]["id"]
    ok(client.post("/api/schemes/upload", headers=H, data={"scheme_id": sid}, files={"file": (filename, content, ctype)}))


def test_wrong_http_methods():
    for method, url in [("PUT", "/api/chat"), ("DELETE", "/api/profiles/me"), ("PATCH", "/api/schemes"), ("GET", "/api/chat")]:
        ok(client.request(method, url, headers=H))


def test_many_requests_in_a_row_stay_healthy():
    for i in range(40):
        ok(client.post("/api/chat", headers=H, json={"message": f"scholarship question {i}"}))
    assert client.get("/health").json()["status"] == "ok"


def test_unknown_routes_return_404():
    assert client.get("/api/does-not-exist").status_code == 404
    assert client.get("/totally/unknown").status_code == 404
