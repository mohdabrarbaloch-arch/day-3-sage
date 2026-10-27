import os
import sys
import uuid

# Use a fresh throwaway database per test run so fixed test emails never
# collide with a previous run's data on disk.
os.environ["DATABASE_URL"] = f"sqlite:////tmp/sage_test_{uuid.uuid4().hex}.db"
os.environ["SECRET_KEY"] = "test-secret-key-long-enough-for-hs256-signing"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _signup(email=None, password="password123", name="Test"):
    if email is None:
        email = f"{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/auth/signup",
        json={"email": email, "password": password, "full_name": name},
    )
    return r


def _auth_headers(token):
    return {"Authorization": "Bearer " + token}


def _upload(token, content, filename="notes.txt"):
    return client.post(
        "/api/documents",
        files={"file": (filename, content, "text/plain")},
        headers=_auth_headers(token),
    )
