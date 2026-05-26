"""
Tests for authentication endpoints.
"""


def test_register_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123",
        "full_name": "Test User",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["username"] == "testuser"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


def test_register_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "username": "user1",
        "password": "securepass123",
    }
    client.post("/api/v1/auth/register", json=payload)
    res = client.post("/api/v1/auth/register", json={**payload, "username": "user2"})
    assert res.status_code == 409


def test_register_duplicate_username(client):
    client.post("/api/v1/auth/register", json={
        "email": "a@example.com",
        "username": "sameuser",
        "password": "securepass123",
    })
    res = client.post("/api/v1/auth/register", json={
        "email": "b@example.com",
        "username": "sameuser",
        "password": "securepass123",
    })
    assert res.status_code == 409


def test_register_short_password(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "short@example.com",
        "username": "shortpw",
        "password": "abc",
    })
    assert res.status_code == 422


def test_login_success(client):
    client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "username": "loginuser",
        "password": "securepass123",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "securepass123",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == "login@example.com"
    assert "access_token" in data["tokens"]


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "username": "wrongpw",
        "password": "securepass123",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert res.status_code == 401


def test_me_authenticated(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "username": "meuser",
        "password": "securepass123",
    })
    token = reg.json()["tokens"]["access_token"]
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"


def test_me_unauthenticated(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_invalid_token(client):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert res.status_code == 401


def test_refresh_token(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "username": "refreshuser",
        "password": "securepass123",
    })
    refresh_token = reg.json()["tokens"]["refresh_token"]
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_refresh_invalid_token(client):
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
    assert res.status_code == 401
