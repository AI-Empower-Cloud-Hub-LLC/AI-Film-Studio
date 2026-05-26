# Testing Knowledge — AI Film Studio

This document captures the testing knowledge, conventions, and skills required to effectively test the Autonomous Agentic AI Film Studio.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI 0.109, SQLAlchemy 2.x, Celery |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| AI/ML | Anthropic Claude (Opus), OpenAI GPT-4, ElevenLabs, Replicate |
| Database | PostgreSQL 15+ (SQLite in-memory for tests) |
| Queue/Cache | Redis 7+ |
| Media | OpenCV, MoviePy, Pillow |
| Containers | Docker & Docker Compose |

## Project Structure (Test-Relevant)

```
AI-Film-Studio/
├── backend/
│   ├── app/
│   │   ├── agents/           # Autonomous agent logic
│   │   │   ├── base_agent.py          # Abstract base with Claude integration
│   │   │   ├── director_agent.py      # Creative vision & scene breakdown
│   │   │   ├── screenwriter_agent.py  # Script & dialogue generation
│   │   │   ├── cinematographer_agent.py
│   │   │   ├── sound_designer_agent.py
│   │   │   ├── editor_agent.py
│   │   │   └── orchestrator.py        # Full pipeline coordinator
│   │   ├── api/              # REST endpoints (routes/ and v1/)
│   │   ├── models/           # SQLAlchemy ORM (Project, Scene, Script)
│   │   ├── services/         # AI & media service wrappers
│   │   ├── core/config.py    # Pydantic settings (env vars)
│   │   └── db/session.py     # DB session factory
│   ├── tests/
│   │   ├── conftest.py       # Fixtures: db_session, client
│   │   ├── test_main.py      # Health / root endpoint tests
│   │   ├── api/              # API route tests
│   │   └── services/         # Service-layer tests
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router pages
│   └── components/           # React components
└── docker-compose.yml
```

## Running Tests

### Backend (pytest)

```bash
cd backend
source venv/bin/activate   # or use Docker
pytest                     # run all tests
pytest tests/test_main.py  # single file
pytest -v                  # verbose output
pytest -x                  # stop on first failure
pytest --tb=short          # shorter tracebacks
```

### Frontend (Next.js lint)

```bash
cd frontend
npm run lint               # ESLint checks
npm run build              # type-check + build verification
```

## Test Configuration

### Database Fixture (`conftest.py`)

Tests use an **in-memory SQLite** database so they are fast and isolated:

- `db_session` — creates fresh tables before each test, tears them down after.
- `client` — `TestClient` wired to the test DB via FastAPI dependency override on `get_db`.

```python
# Usage in a test file
def test_example(client):
    response = client.get("/health")
    assert response.status_code == 200
```

### Environment Variables

Backend configuration lives in `backend/app/core/config.py` (Pydantic `Settings`). Key variables for testing:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API access (required for agent tests hitting the real API) |
| `DATABASE_URL` | Overridden to `sqlite:///:memory:` in tests |
| `OPENAI_API_KEY` | GPT-4 integration |
| `ELEVENLABS_API_KEY` | Voice synthesis |
| `REPLICATE_API_TOKEN` | MusicGen / SVD models |

For unit tests that don't call external APIs, mock the relevant clients (see Mocking section below).

## Test Categories

### 1. Unit Tests — Agents

Each agent inherits from `BaseAgent` and implements an async `process(input_data)` method. The base class holds a `_ask_claude` helper that calls the Anthropic API.

**What to test:**
- `process()` returns the expected dictionary keys.
- Memory management (`add_to_memory`, `get_context`, `clear_memory`).
- Fallback behaviour when LLM output is malformed (e.g., Director's JSON parse fallback).

**Mocking pattern:**

```python
from unittest.mock import AsyncMock, patch

@patch.object(DirectorAgent, "_ask_claude", new_callable=AsyncMock)
async def test_director_process(mock_claude):
    mock_claude.side_effect = [
        "A noir-style vision statement...",              # _create_vision
        '[{"scene_number":1,"description":"Opening"}]',  # _break_down_scenes
    ]
    agent = DirectorAgent(anthropic_api_key="test-key")
    result = await agent.process({"prompt": "noir detective", "style": "cinematic", "duration": 30})
    assert "vision" in result
    assert "scenes" in result
    assert isinstance(result["scenes"], list)
```

### 2. Unit Tests — API Endpoints

Use the `client` fixture from `conftest.py`:

```python
def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()

def test_health_check(client):
    response = client.get("/health")
    assert response.json()["status"] == "healthy"
```

### 3. Integration Tests — Orchestrator Pipeline

The `AgentOrchestrator` chains all five agents sequentially:

1. **Director** → vision + scenes
2. **Screenwriter** → script scenes
3. **Cinematographer** → shot plans + visual prompts
4. **Sound Designer** → audio plan
5. **Editor** → final timeline

**Testing strategy:**
- Mock `_ask_claude` on `BaseAgent` to control every LLM call.
- Assert that each step receives output from the previous step.
- Verify error propagation: if any agent raises, the orchestrator returns `{"status": "error", ...}`.

```python
@patch.object(BaseAgent, "_ask_claude", new_callable=AsyncMock)
async def test_full_pipeline(mock_claude):
    mock_claude.return_value = '{"placeholder": true}'
    orch = AgentOrchestrator(anthropic_api_key="test-key")
    result = await orch.create_film("test prompt")
    assert result["status"] in ("success", "error")
```

### 4. Database / Model Tests

Models: `Project`, `Scene`, `Script` (in `backend/app/models/`).

```python
def test_create_project(db_session):
    from app.models.project import Project
    project = Project(title="Test Film", description="A test", status="draft")
    db_session.add(project)
    db_session.commit()
    assert project.id is not None
```

### 5. Service Tests

Services in `backend/app/services/` wrap external APIs (AI generation, video processing, storage). Always mock external calls:

```python
@patch("app.services.ai_services.openai_client")
def test_ai_service(mock_openai):
    mock_openai.chat.completions.create.return_value = mock_response
    result = generate_text("prompt")
    assert result is not None
```

### 6. Frontend Checks

```bash
cd frontend
npm run lint    # ESLint
npm run build   # TypeScript type-check + Next.js build
```

No dedicated test runner is currently configured for the frontend. Lint and build serve as the primary quality gates.

## Mocking Guidelines

| What to Mock | How |
|-------------|-----|
| Claude / Anthropic | `patch.object(BaseAgent, "_ask_claude")` or per-agent |
| OpenAI | `patch("app.services.ai_services.openai_client")` |
| ElevenLabs | `patch("app.services.audio_generator.elevenlabs_client")` |
| Replicate | `patch("app.services.video_generator.replicate_client")` |
| Database | Use `db_session` fixture (in-memory SQLite) |
| Redis / Celery | `patch` the task `.delay()` / `.apply_async()` calls |

## Key Testing Patterns

### Async Tests

Agent methods are `async`. Use `pytest-asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_agent():
    ...
```

### JSON Fallback Testing

The Director agent parses LLM output as JSON. Test the fallback path:

```python
@patch.object(DirectorAgent, "_ask_claude", new_callable=AsyncMock)
async def test_scene_breakdown_fallback(mock_claude):
    mock_claude.side_effect = [
        "valid vision text",
        "NOT VALID JSON",   # triggers fallback
    ]
    agent = DirectorAgent(anthropic_api_key="test-key")
    result = await agent.process({"prompt": "test", "duration": 30})
    assert len(result["scenes"]) == 3  # fallback produces duration // 10 scenes
```

### Memory Isolation

Agents accumulate state in `self.memory`. Always verify memory doesn't leak between tests:

```python
async def test_memory_isolation():
    agent = DirectorAgent(anthropic_api_key="test-key")
    agent.add_to_memory({"data": "test"})
    assert len(agent.memory) == 1
    agent.clear_memory()
    assert len(agent.memory) == 0
```

## CI / CD

GitHub Actions workflows live in `.github/workflows/`. The static frontend is deployed to GitHub Pages via CI.

Typical CI checks:
- `pytest` for backend
- `npm run lint` + `npm run build` for frontend
- Docker build verification

## Useful Commands Reference

```bash
# Backend
cd backend && source venv/bin/activate
pytest                          # all tests
pytest -k "test_director"       # filter by name
pytest --cov=app                # coverage report

# Frontend
cd frontend
npm run lint
npm run build

# Docker (full stack)
docker-compose up --build       # build and run
docker-compose run backend pytest  # tests inside container

# Quick health check
curl http://localhost:8000/health
curl http://localhost:8000/
```
