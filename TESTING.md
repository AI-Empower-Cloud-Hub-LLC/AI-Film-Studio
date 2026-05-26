# Testing Guide

This document is the central reference for running and writing tests in AI Film Studio. It covers the full testing surface: backend unit/integration tests, frontend linting and builds, agent-specific testing, end-to-end workflows, and CI/CD.

## Quick Reference

```bash
# Backend tests (from repo root)
cd backend
source venv/bin/activate
pytest                              # all tests with coverage
pytest -m unit                      # unit tests only
pytest -m integration               # integration tests only
pytest -k test_auth                 # tests matching a keyword
pytest --cov=app --cov-report=html  # HTML coverage report

# Frontend checks (from repo root)
cd frontend
npm run lint                        # ESLint
npm run build                       # TypeScript compilation + Next.js build
```

## Test Categories

| Category | Location | Runner | Docs |
|---|---|---|---|
| Backend unit tests | `backend/tests/test_services.py` | pytest | [Backend Testing](docs/TESTING_BACKEND.md) |
| Backend API tests | `backend/tests/test_main.py`, `test_auth.py`, `test_projects.py` | pytest | [Backend Testing](docs/TESTING_BACKEND.md) |
| Agent tests | `backend/tests/` (agent-related) | pytest | [Agent Testing](docs/TESTING_AGENTS.md) |
| Frontend lint | `frontend/` | ESLint | [Frontend Testing](docs/TESTING_FRONTEND.md) |
| Frontend build | `frontend/` | Next.js | [Frontend Testing](docs/TESTING_FRONTEND.md) |
| End-to-end | Manual / Docker Compose | Browser + API | [E2E Testing](docs/TESTING_E2E.md) |
| CI/CD pipeline | `.github/workflows/ci.yml` | GitHub Actions | [CI Testing](docs/TESTING_CI.md) |

## Test Stack

### Backend

- **pytest** &mdash; test runner with markers (`unit`, `integration`, `slow`)
- **pytest-asyncio** &mdash; async test support for agent and service tests
- **pytest-cov** &mdash; coverage reporting (term-missing, HTML, XML)
- **httpx** &mdash; async HTTP client for testing
- **FastAPI TestClient** &mdash; synchronous API testing
- **SQLite in-memory** &mdash; isolated database per test function (see `conftest.py`)

### Frontend

- **ESLint** with `@typescript-eslint` and `@next/eslint-plugin-next` &mdash; static analysis
- **Next.js build** &mdash; type checking and compilation

## Configuration Files

| File | Purpose |
|---|---|
| `backend/pytest.ini` | pytest settings, markers, coverage options |
| `backend/tests/conftest.py` | Shared fixtures (`db_session`, `client`) |
| `frontend/eslint.config.mjs` | ESLint flat config with TypeScript and Next.js rules |
| `.github/workflows/ci.yml` | CI pipeline definition |

## Existing Test Files

| File | What it tests |
|---|---|
| `test_main.py` | Health and root endpoints (`/`, `/health`) |
| `test_auth.py` | Registration, login, JWT tokens, refresh, `/me` endpoint |
| `test_projects.py` | Project CRUD, autonomous endpoints, film creation validation |
| `test_services.py` | Password hashing, JWT encode/decode, prompt optimizer, WebSocket manager |

## Writing New Tests

1. Add your test file under `backend/tests/` following the `test_*.py` naming convention.
2. Use the `client` fixture for API tests and `db_session` for direct ORM tests.
3. Mark tests with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.slow`.
4. For async tests, use `@pytest.mark.asyncio`.
5. Keep tests isolated &mdash; each function gets a fresh in-memory SQLite database.

```python
# Example: testing a new endpoint
def test_my_endpoint(client):
    response = client.get("/api/v1/my-endpoint")
    assert response.status_code == 200
```

## Coverage

Coverage is collected automatically via `pytest.ini` defaults:

```ini
--cov=app
--cov-report=term-missing
--cov-report=html
--cov-report=xml
```

- **Terminal**: see uncovered lines in the console after each run.
- **HTML**: open `backend/htmlcov/index.html` in a browser for a detailed report.
- **XML**: `backend/coverage.xml` is uploaded to Codecov in CI.

## Detailed Guides

- [Backend Testing](docs/TESTING_BACKEND.md) &mdash; fixtures, API tests, service tests, database isolation
- [Frontend Testing](docs/TESTING_FRONTEND.md) &mdash; ESLint, build checks, adding component tests
- [Agent Testing](docs/TESTING_AGENTS.md) &mdash; testing autonomous agents, mocking LLM calls, orchestrator tests
- [E2E Testing](docs/TESTING_E2E.md) &mdash; end-to-end workflows with Docker Compose
- [CI/CD Testing](docs/TESTING_CI.md) &mdash; GitHub Actions pipeline, services, caching, coverage uploads
