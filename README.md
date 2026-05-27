# Autonomous Agentic AI Film Studio

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/next.js-16-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![CI/CD](https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio/actions/workflows/ci.yml)

**The world's first fully autonomous AI film studio powered by collaborative AI agents.** Describe a concept in plain language, and a crew of specialized agents — Director, Screenwriter, Cinematographer, Editor, Sound Designer, and VFX — collaborate to produce a complete film from script to final cut.

## Table of Contents

- [Agent Crew](#agent-crew)
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Development](#development)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Agent Crew

Six autonomous AI agents power the production pipeline. Each agent operates independently, makes creative decisions, and communicates with the others through an orchestration layer.

| Agent | Role | Autonomy |
|---|---|---|
| **Director** | Interprets the user's concept into a creative vision, coordinates all agents, and reviews final output | Highest |
| **Screenwriter** | Writes complete scripts with dialogue, character arcs, and scene descriptions | High |
| **Cinematographer** | Plans camera angles, shot composition, lighting, and visual continuity | High |
| **Editor** | Assembles scenes, determines pacing and rhythm, applies transitions | High |
| **Sound Designer** | Generates or selects background music and soundscapes, mixes audio | High |
| **VFX** | Applies visual effects, color grading, and CGI enhancements | High |

The **Agent Orchestrator** manages the sequential data flow between agents: Director vision &rarr; Screenwriter script &rarr; Cinematographer shot plan &rarr; Sound Designer audio &rarr; Editor assembly &rarr; VFX polish.

See [Agent Architecture](AGENT_ARCHITECTURE.md) for implementation details.

## Features

- **AI Scriptwriting** &mdash; Generate professional scripts using GPT-4 and Claude
- **Smart Storyboarding** &mdash; Automatic visual planning from scripts
- **Scene Generation** &mdash; AI-powered video scene creation via Replicate (Stable Video Diffusion)
- **Voice Synthesis** &mdash; Natural voiceovers in multiple languages via ElevenLabs
- **Music Generation** &mdash; Background scores via Replicate (MusicGen)
- **Auto Editing** &mdash; Intelligent video compilation with OpenCV and MoviePy
- **Multi-Format** &mdash; Landscape, portrait, and square output
- **Real-Time Updates** &mdash; WebSocket-based progress streaming during production
- **Authentication** &mdash; JWT-based auth with access and refresh tokens
- **Dashboard** &mdash; Project management UI for tracking productions

## Architecture Overview

```
                         +-----------+
  User Prompt  --------> | Frontend  |  (Next.js / TypeScript / Tailwind CSS)
                         +-----+-----+
                               |  REST + WebSocket
                         +-----v-----+
                         |  Backend   |  (FastAPI / Python)
                         +-----+-----+
                               |
              +----------------+----------------+
              |                |                |
        +-----v-----+   +-----v-----+   +-----v-----+
        |  Agents    |   |  Celery   |   |  Database  |
        | Orchestrator|   |  Workers  |   | PostgreSQL |
        +-----+-----+   +-----+-----+   +-----------+
              |                |
     +--------+--------+      +---- Redis (broker + cache)
     |  |  |  |  |  |  |
     D  S  C  SD E  VFX
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio.git
cd AI-Film-Studio

# Set up environment variables
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
# Edit backend/.env and add your API keys (see Environment Variables below)

# Start all services (PostgreSQL, Redis, backend, Celery worker, frontend)
docker-compose up -d

# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
```

### Using the Setup Script

```bash
git clone https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio.git
cd AI-Film-Studio

# Automated setup (installs backend & frontend dependencies, creates .env files)
./setup.sh

# Edit backend/.env and add your API keys

# Start both servers concurrently
npm run dev
```

### Manual Setup

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

## Development

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload          # API on http://localhost:8000
```

Key directories:

| Path | Purpose |
|---|---|
| `app/agents/` | Agent implementations and orchestrator |
| `app/api/` | REST endpoints (v1 router) |
| `app/models/` | SQLAlchemy ORM models (Project, Scene, Script, User) |
| `app/schemas/` | Pydantic request/response schemas |
| `app/services/` | AI integrations, auth, storage, WebSocket manager |
| `app/middleware/` | Logging and exception handling |
| `app/tasks/` | Celery background tasks |

### Frontend

```bash
cd frontend
npm install
npm run dev                        # Dev server on http://localhost:3000
npm run build                      # Production build
npm run lint                       # ESLint
```

Key directories:

| Path | Purpose |
|---|---|
| `app/` | Next.js App Router pages and layouts |
| `app/create/` | Film creation interface |
| `app/dashboard/` | Project management dashboard |
| `app/projects/` | Project detail views |
| `app/components/` | Shared React components |

## Project Structure

```
AI-Film-Studio/
├── backend/
│   ├── app/
│   │   ├── agents/           # Director, Screenwriter, Cinematographer, etc.
│   │   ├── api/              # REST API routes (v1)
│   │   ├── core/             # Settings and configuration
│   │   ├── middleware/        # Logging, error handling
│   │   ├── models/           # SQLAlchemy ORM (Project, Scene, Script, User)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # AI generation, auth, storage, WebSocket
│   │   ├── tasks/            # Celery background jobs
│   │   └── utils/            # Shared utilities
│   ├── tests/                # pytest suite
│   ├── main.py               # FastAPI entrypoint
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router
│   │   ├── create/           # New film creation
│   │   ├── dashboard/        # Project dashboard
│   │   ├── login/            # Authentication
│   │   ├── register/         # User registration
│   │   ├── projects/         # Project views
│   │   ├── scripts/          # Script management
│   │   ├── storyboards/      # Storyboard views
│   │   ├── scenes/           # Scene management
│   │   └── voiceovers/       # Voiceover management
│   └── components/           # Shared UI components
├── docs/                     # Extended documentation
├── .github/workflows/        # CI/CD pipelines
├── .devcontainer/            # GitHub Codespaces config
├── docker-compose.yml
├── setup.sh                  # Automated setup script
└── package.json              # Root scripts (dev, build, docker)
```

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/projects/` | Create a new project |
| `POST` | `/scripts/generate` | Generate a script from a prompt |
| `POST` | `/storyboards/generate` | Create a storyboard from a script |
| `POST` | `/scenes/generate` | Generate a video scene |
| `POST` | `/voiceovers/generate` | Synthesize a voiceover |
| `POST` | `/videos/compile` | Compile the final video |
| `WS` | `/ws/{project_id}` | Real-time production status updates |

Full interactive documentation is available at `http://localhost:8000/docs` after starting the backend.

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in the values:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI GPT-4 &mdash; [Get key](https://platform.openai.com) |
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude &mdash; [Get key](https://console.anthropic.com) |
| `ELEVENLABS_API_KEY` | No | ElevenLabs voice synthesis &mdash; [Get key](https://elevenlabs.io) |
| `STABILITY_API_KEY` | No | Stability AI image generation &mdash; [Get key](https://stability.ai) |
| `REPLICATE_API_TOKEN` | No | Replicate (MusicGen, SVD) &mdash; [Get key](https://replicate.com) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SECRET_KEY` | Yes | JWT signing key |

Cloud storage (pick one):

| Variable | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `S3_BUCKET_NAME` | AWS S3 |
| `AZURE_STORAGE_CONNECTION_STRING` / `AZURE_CONTAINER_NAME` | Azure Blob Storage |

Frontend: copy `frontend/.env.local.example` to `frontend/.env.local`. The only variable is `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

## Testing

```bash
cd backend
source venv/bin/activate
pytest                             # Run all tests
pytest --cov                       # With coverage report
```

CI runs backend tests automatically against PostgreSQL 15 and Redis 7 on every push and pull request (see `.github/workflows/ci.yml`).

## Deployment

- **Frontend** &mdash; Static export to GitHub Pages via the `deploy-frontend.yml` workflow. After enabling GitHub Pages (Settings &rarr; Pages &rarr; Source: GitHub Actions), push to `main` and the site will be available at `https://ai-cloud-tech-inc.github.io/AI-Film-Studio/`.
- **Backend** &mdash; Deploy to any platform that supports Docker or Python (Render, Railway, AWS, etc.). See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Documentation

| Document | Description |
|---|---|
| [Quick Start](QUICKSTART.md) | Get running in minutes |
| [Agent Architecture](AGENT_ARCHITECTURE.md) | Multi-agent system design |
| [Project Structure](PROJECT_STRUCTURE.md) | Codebase overview |
| [Development Guide](DEVELOPMENT.md) | Detailed dev instructions |
| [Contributing](CONTRIBUTING.md) | How to contribute |
| [Deployment](DEPLOYMENT.md) | Production deployment guide |
| [Security](SECURITY.md) | Security policy and vulnerability reporting |
| [Codespace Setup](CODESPACE_SETUP.md) | GitHub Codespaces configuration |
| [Architecture](docs/ARCHITECTURE.md) | System architecture deep-dive |
| [Getting Started](docs/GETTING_STARTED.md) | Extended onboarding guide |
| [Enterprise](docs/ENTERPRISE.md) | Enterprise features |
| [Integration](docs/INTEGRATION.md) | Third-party integrations |
| [Testing Guide](TESTING.md) | Central testing reference |
| [Backend Testing](docs/TESTING_BACKEND.md) | pytest fixtures, API and service tests |
| [Frontend Testing](docs/TESTING_FRONTEND.md) | ESLint, build checks, adding component tests |
| [Agent Testing](docs/TESTING_AGENTS.md) | Agent mocking, orchestrator tests, LLM integration |
| [E2E Testing](docs/TESTING_E2E.md) | Full-stack end-to-end workflows |
| [CI/CD Testing](docs/TESTING_CI.md) | GitHub Actions pipeline details |

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

Built by [AI Cloud Tech Inc](https://github.com/AI-Cloud-Tech-Inc)
