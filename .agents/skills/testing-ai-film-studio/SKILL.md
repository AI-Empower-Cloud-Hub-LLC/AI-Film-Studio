---
name: testing-ai-film-studio
description: Test the AI Film Studio app end-to-end. Use when verifying auth, dashboard, sidebar navigation, page functionality, or multi-backend (Ollama/Google/Claude/ElevenLabs) changes.
---

# Testing AI Film Studio

## Architecture

- **Backend**: FastAPI (Python) on port 8000 with SQLAlchemy ORM
- **Frontend**: Next.js 16 (TypeScript + Tailwind) on port 3000
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Auth**: JWT Bearer tokens stored in localStorage
- **LLM Backend**: Ollama (local, default), Google Generative AI (optional), or Claude/Anthropic (premium)
- **Voice Backend**: Local Coqui TTS (default) or ElevenLabs (premium, set `VOICE_BACKEND=elevenlabs`)
- **Video Backend**: Local placeholder (default) or Runway Gen-4 Turbo (set `VIDEO_BACKEND=runway`)
- **Agent Pipeline**: LangGraph StateGraph with 10 agents — Director → Screenwriter → ScreenplayRefinement → [Cinematographer ∥ SoundDesigner ∥ CastSelection ∥ LocationResearch] → [VFXPlanning ∥ MoodBoard] → Editor → Review
- **Note:** The Create Film page pipeline tracker (`frontend/app/create/page.tsx` line 20) might still hardcode only the original 5 agents. Check the `AGENTS` array if the pipeline UI doesn't show all 10 agents.
- **Media Pipeline**: After LangGraph agents complete, generates video + voiceover per scene in parallel (Runway + ElevenLabs or local fallback)
- **Graph Visualization**: Frontend `PipelineGraph` component fetches topology from `/autonomous/graph`
- **Pipeline History**: In-memory run history via `/autonomous/pipeline-history` (clears on server restart); MongoDB persistence available if `MONGODB_URL` is set
- **SSE Streaming**: `/autonomous/create-film-stream` endpoint for real-time progress events
- **LLM Cache**: LRU cache (128 entries) in LLMService avoids redundant API calls

## Setup

1. Start backend (default — free, no keys):
   ```bash
   cd /home/ubuntu/repos/AI-Film-Studio/backend
   SECRET_KEY=test-secret-key-for-testing uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

   Or with Claude + ElevenLabs + Runway (premium):
   ```bash
   cd /home/ubuntu/repos/AI-Film-Studio/backend
   SECRET_KEY=test-secret-key-for-testing LLM_BACKEND=claude ANTHROPIC_API_KEY="your-key" VOICE_BACKEND=elevenlabs ELEVENLABS_API_KEY="your-key" VIDEO_BACKEND=runway RUNWAY_API_KEY="your-key" MONGODB_URL=mongodb://localhost:27017 uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Start frontend:
   ```bash
   cd /home/ubuntu/repos/AI-Film-Studio/frontend
   npm run dev
   ```

3. Verify both are running:
   ```bash
   curl -s http://localhost:8000/health  # Should return {"status":"healthy"}
   curl -s http://localhost:3000 | head -1  # Should return HTML
   ```

4. Verify LLM backend configuration:
   ```bash
   curl -s http://localhost:8000/api/v1/autonomous/agent-status
   # Default: {"status":"active","backend":"ollama","model":"mistral","available_backends":{"ollama":true,"google":false,"claude":false},"voice_backend":"local","video_backend":"local"}
   # With all premium: {"backend":"claude","model":"claude-sonnet-4-20250514","voice_backend":"elevenlabs","video_backend":"runway"}
   ```

## Key Pages & Routes

| Page | URL | Auth Required | Data Source |
|------|-----|---------------|-------------|
| Landing | `/` | No | Static |
| Register | `/register` | No | POST `/api/v1/auth/register` |
| Login | `/login` | No | POST `/api/v1/auth/login` |
| Dashboard | `/dashboard` | No (but shows user if logged in) | GET `/api/v1/autonomous/projects` |
| Scripts | `/scripts` | No | GET `/api/v1/autonomous/projects` + detail |
| Storyboards | `/storyboards` | No | GET `/api/v1/autonomous/projects` + detail |
| Scenes | `/scenes` | No | GET `/api/v1/autonomous/projects` + detail |
| Voiceovers | `/voiceovers` | No | GET `/api/v1/autonomous/projects` + detail |
| Projects | `/projects` | No | GET `/api/v1/autonomous/projects` |
| Create Film | `/create` | No | POST `/api/v1/autonomous/create-film` |
| Screenplay | `/screenplay` | No | GET `/api/v1/autonomous/projects` + detail |
| Cast | `/cast` | No | GET `/api/v1/autonomous/projects` + detail |
| Locations | `/locations` | No | GET `/api/v1/autonomous/projects` + detail |
| Mood Board | `/mood-board` | No | GET `/api/v1/autonomous/projects` + detail |
| VFX Plan | `/vfx-plan` | No | GET `/api/v1/autonomous/projects` + detail |
| Admin | `/admin` | No | GET `/api/v1/autonomous/admin/stats` |

## Auth Flow

1. Register: POST `/api/v1/auth/register` with `{email, username, password, full_name}`
   - Returns 201 with `{user, tokens: {access_token, refresh_token, token_type}}`
2. Login: POST `/api/v1/auth/login` with `{email, password}`
   - Returns 200 with same shape
   - Wrong credentials → 401 with `{detail: "Invalid email or password"}`
3. Frontend stores tokens in `localStorage` keys: `access_token`, `refresh_token`
4. Auth state managed by Zustand store (`lib/auth-store.ts`)
5. Sidebar shows user info (name + email) when logged in

## Key API Endpoints for Testing

- `GET /health` — returns `{"status":"healthy"}`
- `GET /api/v1/autonomous/agent-status` — returns `{status, backend, model, available_backends, voice_backend, video_backend}`
- `GET /api/v1/voiceovers/voices/list` — returns local voices + ElevenLabs voices (if configured), with `active_backend` field
- `POST /api/v1/autonomous/create-film` — accepts `{prompt, style, duration}`, runs LangGraph pipeline + media generation, returns `{data: {project_id, scenes, workflow_steps, node_timings, revision_count, generated_media}}`
- `POST /api/v1/autonomous/create-film-stream` — SSE streaming version; returns `text/event-stream` with `data:` lines per agent step, ends with `{type: "complete", result: {...}}`
- `GET /api/v1/autonomous/graph` — returns pipeline topology `{nodes, edges, features}` for frontend visualization
- `GET /api/v1/autonomous/pipeline-history` — returns `{runs: [...], storage: "memory"|"mongodb"}` with per-run timings, errors, revision_count, status, video_backend, voice_backend
- `GET /api/v1/autonomous/pipeline-analytics` — returns `{total_runs, successful_runs, storage}`
- `GET /api/v1/autonomous/projects/{project_id}/media` — returns generated content metadata for a project
- `PATCH /api/v1/autonomous/projects/{project_id}` — update project title/style/duration; body `{title?, style?, duration?}`
- `DELETE /api/v1/autonomous/projects/{project_id}` — delete project and cascade scenes/scripts
- `GET /api/v1/autonomous/admin/stats` — returns `{total_projects, total_users, total_scenes, completed_projects, agents_count, pipeline_runs}`

## Create Film Page

The Create Film page (`/create`) has:
- Film Concept textarea (required)
- Visual Style dropdown (cinematic, documentary, anime, cartoon, realistic, sci-fi)
- Duration input (10-300 seconds)
- AI Model dropdown (Gemini Flash, Gemini 2.0 Flash, Gemini 2.5 Pro, Gemini 2.5 Flash)
- The form sends `{prompt, style, duration, model}` to the backend

**Backend display varies by configuration:**
- Ollama (default): Green "Ollama (Local LLM) — Free, no API key needed", model: mistral
- Google AI: Blue "Google AI (Gemini) — Free tier"
- Claude: Purple "Claude (Anthropic) — Premium" with "ElevenLabs Voice" badge if configured, "Runway Video" emerald badge if RUNWAY_API_KEY set
- Helper text shows "Model: {name} · Available: {backends}"
- After film creation, a "Generated Media" section appears showing:
  - "Video: local" / "Video: runway" and "Voice: local" / "Voice: elevenlabs" backend labels
  - Per-scene status: "Video: placeholder/completed" and "Audio: placeholder/completed/skipped"

## Testing Tips

- The backend uses SQLite in dev mode. The database file might be at `backend/ai_film_studio.db` or `backend/film_studio.db`. If you need a clean state, delete these files and restart the backend.
- All content pages (Scripts, Scenes, Storyboards, Voiceovers) show empty states when no projects exist. They need at least one project created via `/create` to display real data.
- The `SECRET_KEY` environment variable is required for JWT token signing. Set it to any value for testing.
- The LangGraph pipeline gracefully falls back to demo content when Ollama is not running locally. Film creation will still return "success" with placeholder agent outputs.
- ESLint config uses flat config format (ESLint 9). Run `npm run lint` to verify.
- Frontend build: `npm run build` (standard mode). For GitHub Pages static export, set `GITHUB_PAGES=true`.
- The "Back to Dashboard" link on `/create` navigates to `/` (landing page), not `/dashboard`. Use the sidebar or direct URL to reach the dashboard.

## LangGraph Pipeline Testing

The Create Film page now has a two-column layout: form on the left, LangGraph Pipeline visualization on the right.

**Pipeline Graph** shows:
- The `AGENTS` array in `frontend/app/create/page.tsx` controls which agents appear in the pipeline tracker
- Backend graph API (`/autonomous/graph`) returns 11 nodes (10 agents + review), 15 edges
- Nodes start gray (pending), turn green (completed) after film creation

**After film creation**, verify:
1. All pipeline nodes shown in the tracker turn green ✓
2. Film creation redirects to project detail page with "completed" status
3. Project detail shows Edit/Delete/PDF/JSON buttons, video preview placeholder, Director's Vision, Scenes tab, Scripts tab
4. `GET /autonomous/admin/stats` shows incremented total_projects and total_scenes

**Known issue:** The frontend pipeline tracker might only show the original 5 agents even though the backend has 10. Check `frontend/app/create/page.tsx` line 20 — if only 5 agents are listed, the new agents won't appear in the UI progress tracker.

**Note:** Pipeline history is in-memory only — it clears when the backend server restarts. Pipeline runs counter might show 0 even after creating films if the orchestrator doesn't persist runs.

## Common Issues

- If `bcrypt` errors occur (AttributeError about `__about__`), ensure `bcrypt==4.0.1` is pinned in requirements.txt (bcrypt 5.x is incompatible with passlib 1.7.4).
- Root `.gitignore` has `lib/` pattern which blocks `frontend/lib/`. Use `git add -f frontend/lib/` to force-add files in that directory.
- If frontend build fails with "missing generateStaticParams", check that dynamic route pages export `generateStaticParams()`.
- If pip install fails with "ResolutionImpossible", check that requirements.txt uses `>=` instead of `==` for version constraints (especially pydantic, which must be >=2.7.4 for langchain-core compatibility).
- The `/api/v1/media/status` endpoint may return 404 — this is expected if the media routes are not mounted (they were removed/replaced in the free API migration).

## Multi-Backend Testing

To test backend switching:
1. Start with Claude keys → verify purple "Claude (Anthropic)" label + ElevenLabs badge on `/create`
2. Restart without keys (`LLM_BACKEND=ollama VOICE_BACKEND=local`) → verify green "Ollama (Local LLM)" label, no badge
3. Check `/api/v1/voiceovers/voices/list` — with ElevenLabs key: `active_backend=elevenlabs` + ~19 premium voices; without: `active_backend=local` + 3 local voices
4. Film creation works with any backend — if Claude has no credits, pipeline gracefully falls back to placeholder content

**Important:** The Claude API key might have insufficient credits. The integration code is correct but returns placeholder content via graceful error handling. This is expected behavior — verify the pipeline still completes successfully.

## Project CRUD Testing

1. **Edit title**: On project detail page (`/projects/{id}`), click "Edit" → inline text input appears with Save/Cancel → change title → click Save → h1 updates immediately
2. **Delete**: Click "Delete" → redirects to `/projects` → project removed from list → admin stats decrement
3. **Video preview**: Placeholder black area with "Video preview will appear here when generated" text and scene count
4. **Export**: PDF and JSON links point to `/api/v1/exports/pdf/{id}` and `/api/v1/exports/json/{id}`

## Admin Dashboard Testing

- Navigate to `/admin` via sidebar
- 6 stat cards: Total Projects, Completed, Total Users, Total Scenes, AI Agents (should be 10), Pipeline Runs
- Refresh button re-fetches stats
- Stats update in real-time as projects are created/deleted

## Theme Toggle Testing

- Sun/moon icon button in sidebar footer next to "10 AI Agents Active" badge
- Clicking toggles the theme state (button title switches between "Switch to light mode" / "Switch to dark mode")
- **Known issue:** The visual appearance might not change because components use hardcoded dark CSS classes instead of Tailwind `dark:` variants. The toggle mechanism works but light mode styling may not be implemented.

## Sidebar Testing

- Should show 13 nav items: Dashboard, Projects, Create Film, Scripts, Screenplay, Cast, Locations, Storyboards, Mood Board, VFX Plan, Scenes, Voiceovers, Admin
- Footer shows "10 AI Agents Active" badge, theme toggle button, user info (name + email), and sign-out button
- Dashboard stat cards should show "AI Agents 10" (check `frontend/app/dashboard/page.tsx` for hardcoded value)

## Devin Secrets Needed

- None required for basic testing (Ollama fallback with demo content)
- `GOOGLE_API_KEY` — optional, for Google AI backend (set `LLM_BACKEND=google`)
- `ANTHROPIC_API_KEY` — optional, for Claude backend (set `LLM_BACKEND=claude`)
- `ELEVENLABS_API_KEY` — optional, for ElevenLabs voices (set `VOICE_BACKEND=elevenlabs`)
- `RUNWAY_API_KEY` — optional, for Runway video generation (set `VIDEO_BACKEND=runway`)
- `MONGODB_URL` — optional, for persistent pipeline history (e.g. `mongodb://localhost:27017`)
- Note: API keys may have rate limits or insufficient credits — the app gracefully falls back to Ollama/local in these cases

## SSE Streaming Testing

To test the SSE streaming endpoint from the command line:
```bash
curl -s -N -X POST http://localhost:8000/api/v1/autonomous/create-film-stream \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"A sunset over mountains","style":"cinematic","duration":10}'
```
Expect: `data:` prefixed JSON lines with agent progress (running→completed), Media Generator sub-steps, and final `{type: "complete"}` event.
