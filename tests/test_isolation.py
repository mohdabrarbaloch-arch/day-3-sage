def test_cross_user_isolation():
    from .conftest import _auth_headers, _signup, _upload, client

    t1 = _signup(email="one@x.com", password="password123").json()["access_token"]
    t2 = _signup(email="two@x.com", password="password123").json()["access_token"]
    up = _upload(t1, "Secret content belonging to user one.", "secret.txt")
    doc_id = up.json()["id"]
    # User two must not see user one's document.
    r = client.get(f"/api/documents/{doc_id}", headers=_auth_headers(t2))
    assert r.status_code == 404
