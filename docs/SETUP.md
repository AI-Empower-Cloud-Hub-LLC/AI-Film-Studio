# Setup & Deployment Guide

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose** (for containerised deployment)
- **PostgreSQL 15+** (production) or SQLite (development)
- **Redis 7+** (for Celery task queue)

## Quick Start (Development)

### 1. Clone & configure

```bash
git clone https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio.git
cd AI-Film-Studio
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Edit `backend/.env` and add your API keys:

```
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000` in your browser.

### 4. Run tests

```bash
cd backend
pytest tests/ -v
```

## Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Services:
| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js dashboard |
| backend | 8000 | FastAPI API |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Cache & task broker |
| celery-worker | — | Background task processor |

## Production Deployment

### Environment variables

Set these in your production environment:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Random 32+ char secret for JWT signing |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for AI agents |
| `OPENAI_API_KEY` | No | OpenAI API key for GPT features |
| `ELEVENLABS_API_KEY` | No | ElevenLabs API key for voiceovers |
| `REPLICATE_API_TOKEN` | No | Replicate API token for video generation |
| `APP_ENV` | No | `production` / `development` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |

### Health checks

- `GET /health` — returns `{"status": "healthy"}`
- `GET /` — returns API info with version

### WebSocket

Connect to `ws://HOST/ws/projects/{project_id}` for real-time updates during film creation.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────>│   Backend    │────>│  PostgreSQL   │
│  (Next.js)   │     │  (FastAPI)   │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                    ┌───────┴────────┐
                    │   AI Agents    │
                    │  (5 agents)    │
                    ├────────────────┤
                    │ Director       │
                    │ Screenwriter   │
                    │ Cinematographer│
                    │ Sound Designer │
                    │ Editor         │
                    └───────┬────────┘
                            │
                 ┌──────────┼──────────┐
                 │          │          │
          ┌──────┴───┐ ┌───┴────┐ ┌───┴──────┐
          │ Anthropic │ │ OpenAI │ │ElevenLabs│
          │ Claude    │ │ GPT-4  │ │ Voice    │
          └──────────┘ └────────┘ └──────────┘
```
