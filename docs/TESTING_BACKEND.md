# Backend Testing

Detailed guide for writing and running backend tests for AI Film Studio.

## Prerequisites

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # includes pytest, pytest-asyncio, pytest-cov, httpx
```

## Running Tests

```bash
# All tests with verbose output and coverage
pytest

# Specific file
pytest tests/test_auth.py

# Specific test function
pytest tests/test_auth.py::test_login_success

# By marker
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Keyword filter
pytest -k "auth"

# Stop on first failure
pytest -x
```

## Configuration

`pytest.ini` is at `backend/pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

## Fixtures

All shared fixtures are defined in `backend/tests/conftest.py`.

### `db_session`

Creates a fresh in-memory SQLite database for each test function. All ORM models are created before the test and dropped after it, ensuring full isolation.

```python
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    # ... yields a SQLAlchemy Session ...
    Base.metadata.drop_all(bind=engine)
```

Use this fixture when you need direct database access:

```python
def test_create_user(db_session):
    user = User(email="a@b.com", username="testuser", hashed_password="...")
    db_session.add(user)
    db_session.commit()
    assert db_session.query(User).count() == 1
```

### `client`

A FastAPI `TestClient` wired to the test database. Depends on `db_session` so every API test automatically gets a clean database.

```python
def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
```

## Test Patterns

### API Endpoint Tests

Test HTTP methods, status codes, and response bodies:

```python
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
    assert "access_token" in data["tokens"]
```

### Authenticated Endpoint Tests

Register a user, extract the token, and pass it in the `Authorization` header:

```python
def test_me_authenticated(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "username": "meuser",
        "password": "securepass123",
    })
    token = reg.json()["tokens"]["access_token"]
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"
```

### Service Unit Tests

Import service functions directly and test them without HTTP:

```python
from app.services.auth_service import hash_password, verify_password

def test_password_hash_and_verify():
    hashed = hash_password("myP@ssw0rd")
    assert verify_password("myP@ssw0rd", hashed)
    assert not verify_password("wrong", hashed)
```

### Async Tests

Use the `asyncio` marker for async service or agent functions:

```python
import pytest

@pytest.mark.asyncio
async def test_prompt_optimizer_passthrough():
    from app.services.prompt_optimizer import PromptOptimizer
    optimizer = PromptOptimizer()
    result = await optimizer.optimize("A sunset over mountains", "cinematic", 30)
    assert result["was_optimized"] is False
```

### Validation Tests

Ensure Pydantic schema validation rejects bad input:

```python
def test_create_film_validation_short_prompt(client):
    res = client.post("/api/v1/autonomous/create-film", json={
        "prompt": "hi",          # too short (min 10 chars)
        "style": "cinematic",
        "duration": 30,
    })
    assert res.status_code == 422
```

## Database Isolation

Each test function gets its own SQLite in-memory database via the `db_session` fixture. This means:

- Tests cannot interfere with each other.
- No cleanup is needed between tests.
- Tests run in parallel safely (though pytest-xdist is not currently configured).

The test database uses `StaticPool` to keep the in-memory database alive for the duration of each test:

```python
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

## Coverage

After running tests, coverage reports are generated automatically:

| Format | Location | Purpose |
|---|---|---|
| Terminal | stdout | Quick check of uncovered lines |
| HTML | `backend/htmlcov/index.html` | Detailed interactive report |
| XML | `backend/coverage.xml` | CI upload to Codecov |

Source paths covered: everything under `app/`, excluding `tests/`, `venv/`, `__pycache__/`, and `migrations/`.

## Adding New Test Files

1. Create `backend/tests/test_<module>.py`.
2. Import fixtures implicitly from `conftest.py` (e.g. `client`, `db_session`).
3. Use descriptive function names: `test_<action>_<scenario>`.
4. Mark tests: `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.slow`.

```python
"""
Tests for the video compilation service.
"""
import pytest

@pytest.mark.integration
def test_compile_video_missing_scenes(client):
    res = client.post("/api/v1/videos/compile", json={"project_id": "nonexistent"})
    assert res.status_code == 404
```
