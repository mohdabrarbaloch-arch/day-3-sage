"""API integration tests for auth, documents, conversations, and summarization."""

from .conftest import _auth_headers, _signup, _upload, client


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["app"] == "Sage"


def test_signup_and_login():
    r = _signup(email="user@example.com", password="password123")
    assert r.status_code == 201
    token = r.json()["access_token"]
    assert token
    login = client.post(
        "/api/auth/login", json={"email": "user@example.com", "password": "password123"}
    )
    assert login.status_code == 200


def test_duplicate_signup_conflict():
    _signup(email="dup@example.com", password="password123")
    r = _signup(email="dup@example.com", password="password123")
    assert r.status_code == 409


def test_login_wrong_password():
    _signup(email="wrong@example.com", password="password123")
    r = client.post(
        "/api/auth/login", json={"email": "wrong@example.com", "password": "badpassword"}
    )
    assert r.status_code == 401


def test_upload_and_ask():
    token = _signup().json()["access_token"]
    up = _upload(token, "The capital of France is Paris. Paris has the Eiffel Tower.", "france.txt")
    assert up.status_code == 201
    doc_id = up.json()["id"]
    ask = client.post(
        "/api/conversations/ask",
        json={"question": "What is the capital of France?", "document_id": doc_id},
        headers=_auth_headers(token),
    )
    assert ask.status_code == 200
    body = ask.json()
    assert body["grounded"] is True
    assert "Paris" in body["answer"]


def test_ask_requires_auth():
    r = client.post("/api/conversations/ask", json={"question": "hi"})
    assert r.status_code == 401


def test_upload_rejects_bad_extension():
    token = _signup().json()["access_token"]
    r = client.post(
        "/api/documents",
        files={"file": ("bad.exe", b"binary", "application/octet-stream")},
        headers=_auth_headers(token),
    )
    assert r.status_code == 400


def test_summarize_endpoint():
    token = _signup().json()["access_token"]
    content = (
        "The sky is blue. Clouds are white. Rain falls from clouds. "
        "The sun is bright. Stars appear at night. The moon orbits Earth."
    )
    up = _upload(token, content, "sky.txt")
    doc_id = up.json()["id"]
    r = client.post(
        "/api/summarize",
        json={"document_id": doc_id, "ratio": 0.5, "max_sentences": 3},
        headers=_auth_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["summary"]


def test_document_not_found_404():
    token = _signup().json()["access_token"]
    r = client.get("/api/documents/nonexistent", headers=_auth_headers(token))
    assert r.status_code == 404
