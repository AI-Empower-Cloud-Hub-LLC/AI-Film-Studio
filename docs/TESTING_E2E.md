# End-to-End Testing

Guide for running full-stack end-to-end tests against AI Film Studio using Docker Compose.

## Overview

End-to-end (E2E) tests exercise the entire stack: frontend, backend API, database, Redis, and Celery workers. They verify that the user-facing workflows work correctly when all services are running together.

## Prerequisites

- Docker and Docker Compose installed
- API keys configured in `backend/.env` (at minimum `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` for agent-based tests)

## Starting the Full Stack

```bash
# From repo root
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

docker-compose up -d
```

Services:

| Service | URL | Purpose |
|---|---|---|
| Frontend | http://localhost:3000 | Next.js UI |
| Backend API | http://localhost:8000 | FastAPI REST + WebSocket |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache and task broker |
| Celery Worker | &mdash; | Background job processing |

Verify all services are healthy:

```bash
docker-compose ps
curl http://localhost:8000/health
```

## Manual E2E Test Scenarios

### 1. Health Check

```bash
curl -s http://localhost:8000/ | python3 -m json.tool
# Expected: {"message": "Welcome to AI Film Studio", "version": "v1", "status": "running"}

curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: {"status": "healthy"}
```

### 2. User Registration and Login

```bash
# Register
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","username":"e2euser","password":"securepass123"}' \
  | python3 -m json.tool

# Login
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"securepass123"}' \
  | python3 -m json.tool

# Save the access_token from the response, then:
TOKEN="<paste-access-token>"

# Get current user
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

### 3. Project CRUD

```bash
# Create a project
curl -s -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"title":"E2E Test Film","description":"Testing end to end","format":"landscape"}' \
  | python3 -m json.tool

# List projects
curl -s http://localhost:8000/api/v1/projects/ | python3 -m json.tool
```

### 4. Autonomous Film Creation

```bash
# Create a film (requires valid ANTHROPIC_API_KEY)
curl -s -X POST http://localhost:8000/api/v1/autonomous/create-film \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A mysterious journey through an enchanted forest at twilight","style":"cinematic","duration":30}' \
  | python3 -m json.tool

# Check agent status
curl -s http://localhost:8000/api/v1/autonomous/agent-status | python3 -m json.tool

# List autonomous projects
curl -s http://localhost:8000/api/v1/autonomous/projects | python3 -m json.tool
```

### 5. WebSocket Real-Time Updates

Connect to the WebSocket endpoint to receive live progress updates during film creation:

```python
# test_ws.py
import asyncio
import websockets
import json

async def listen(project_id: str):
    uri = f"ws://localhost:8000/ws/{project_id}"
    async with websockets.connect(uri) as ws:
        print(f"Connected to {uri}")
        async for message in ws:
            data = json.loads(message)
            print(f"Update: {data}")

asyncio.run(listen("your-project-id"))
```

### 6. Frontend Smoke Test

1. Open http://localhost:3000 in a browser.
2. Verify the landing page loads with feature cards.
3. Navigate to `/create` and confirm the film creation form renders.
4. Navigate to `/dashboard` and confirm the project list loads.
5. Navigate to `/login` and `/register` and confirm auth forms render.

## Automated E2E with Playwright

To add browser-based E2E tests:

```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

Create `frontend/e2e/smoke.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

test('landing page loads', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page).toHaveTitle(/AI Film Studio/)
})

test('create page renders form', async ({ page }) => {
  await page.goto('http://localhost:3000/create')
  await expect(page.locator('form')).toBeVisible()
})

test('health endpoint responds', async ({ request }) => {
  const res = await request.get('http://localhost:8000/health')
  expect(res.ok()).toBeTruthy()
  const body = await res.json()
  expect(body.status).toBe('healthy')
})
```

Run:

```bash
npx playwright test
```

## Automated API E2E with pytest

Create `backend/tests/test_e2e.py` for full-flow API tests:

```python
"""
End-to-end API flow tests.
Run against the test database (via conftest.py fixtures).
"""
import pytest

def test_full_auth_flow(client):
    # Register
    reg = client.post("/api/v1/auth/register", json={
        "email": "flow@test.com",
        "username": "flowuser",
        "password": "securepass123",
    })
    assert reg.status_code == 201
    token = reg.json()["tokens"]["access_token"]

    # Access protected endpoint
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "flow@test.com"

    # Refresh
    refresh = reg.json()["tokens"]["refresh_token"]
    ref = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert ref.status_code == 200

def test_full_project_flow(client):
    # Create project
    create = client.post("/api/v1/projects/", json={
        "title": "E2E Project",
        "description": "Full flow test",
        "format": "landscape",
    })
    assert create.status_code == 200
    assert create.json()["title"] == "E2E Project"

    # List projects
    listing = client.get("/api/v1/projects/")
    assert listing.status_code == 200
    assert len(listing.json()) >= 1
```

## Tear Down

```bash
docker-compose down -v   # stop all services and remove volumes
```
