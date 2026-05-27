"""
Autonomous Film Creation API Routes — multi-backend LLM + media generation.
"""
import asyncio
import json
import uuid
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.agents.orchestrator import AgentOrchestrator
from app.database import get_db
from app.models.project import Project, Scene, Script, ProjectStatus

logger = logging.getLogger(__name__)

router = APIRouter()

_orchestrator: Optional[AgentOrchestrator] = None


def _get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator.from_settings()
    return _orchestrator


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class FilmRequest(BaseModel):
    prompt: str = Field(..., min_length=10, description="Film concept / idea")
    style: str = Field(default="cinematic", description="Visual style")
    duration: int = Field(default=30, ge=5, le=300, description="Target duration in seconds")


class FilmResponse(BaseModel):
    status: str
    project_id: str
    message: str
    persisted: bool = True
    data: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _persist_project(
    db: Session, request: FilmRequest, result: Dict[str, Any], project_id: Optional[str] = None
) -> Project:
    director_out = result.get("director", {})
    script_out = result.get("script", {})
    scenes_raw: List[Dict] = director_out.get("scenes", [])
    script_scenes: List[Dict] = script_out.get("script_scenes", [])
    generated_media = result.get("generated_media", {})
    media_scenes: List[Dict] = generated_media.get("scenes", [])

    project = Project(
        id=project_id or str(uuid.uuid4()),
        title=request.prompt[:120],
        prompt=request.prompt,
        style=request.style,
        duration=request.duration,
        status=ProjectStatus.completed,
        director_vision=director_out.get("vision", ""),
    )
    db.add(project)
    db.flush()

    script_lookup = {s.get("scene_number"): s for s in script_scenes}
    media_lookup = {m.get("scene_number"): m for m in media_scenes}
    for scene_data in scenes_raw:
        sn = scene_data.get("scene_number", 0)
        script_scene = script_lookup.get(sn, {})
        media_scene = media_lookup.get(sn, {})
        video_data = media_scene.get("video", {})
        audio_data = media_scene.get("audio", {})
        scene = Scene(
            id=str(uuid.uuid4()),
            project_id=project.id,
            scene_number=sn,
            description=scene_data.get("description", ""),
            shot_type=scene_data.get("shot_type", "medium"),
            mood=scene_data.get("mood", "neutral"),
            duration=scene_data.get("duration", 10),
            visual_prompt=scene_data.get("visual_prompt", ""),
            narration=script_scene.get("narration", ""),
            dialogue=script_scene.get("dialogue", []),
            audio_cues=script_scene.get("audio_cues", []),
            video_url=video_data.get("output_url") or video_data.get("local_path", ""),
            audio_url=audio_data.get("path", ""),
        )
        db.add(scene)

    if script_scenes:
        script = Script(
            id=str(uuid.uuid4()),
            project_id=project.id,
            content=json.dumps(script_scenes),
            scene_count=len(script_scenes),
        )
        db.add(script)

    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/create-film", response_model=FilmResponse)
async def create_autonomous_film(request: FilmRequest, db: Session = Depends(get_db)):
    """
    Orchestrate the full autonomous film pipeline (LangGraph):
    Director -> Screenwriter -> Cinematographer -> Sound Designer -> Editor
    """
    from app.services.ws_manager import ws_manager

    logger.info("Film creation started: %s...", request.prompt[:60])

    project_id = str(uuid.uuid4())

    async def _broadcast_progress(data: Dict[str, Any]):
        await ws_manager.broadcast(project_id, {"type": "progress", **data})

    orchestrator = _get_orchestrator()

    result = await orchestrator.create_film(
        user_prompt=request.prompt,
        style=request.style,
        duration=request.duration,
        on_progress=_broadcast_progress,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Pipeline failed"))

    persisted = True
    try:
        project = _persist_project(db, request, result, project_id=project_id)
        project_id = project.id
    except Exception:
        logger.exception("Failed to persist project")
        persisted = False
        project_id = str(uuid.uuid4())

    director_out = result.get("director", {})
    scenes = director_out.get("scenes", [])

    return FilmResponse(
        status="success",
        project_id=project_id,
        persisted=persisted,
        message=f"Film pipeline complete — {len(scenes)} scenes created"
        + ("" if persisted else " (warning: DB persistence failed)"),
        data={
            "project_id": project_id,
            "prompt": request.prompt,
            "style": request.style,
            "duration": request.duration,
            "scene_count": len(scenes),
            "total_duration": sum(s.get("duration", 0) for s in scenes),
            "director": director_out,
            "script": result.get("script", {}),
            "cinematography": result.get("cinematography", {}),
            "sound": result.get("sound", {}),
            "media_assets": result.get("media_assets", {}),
            "final_timeline": result.get("final_timeline", {}),
            "workflow_steps": result.get("workflow_steps", []),
            "node_timings": result.get("node_timings", {}),
            "revision_count": result.get("revision_count", 0),
            "generated_media": result.get("generated_media", {}),
        },
    )


@router.get("/projects", response_model=List[Dict[str, Any]])
def list_projects(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    scene_count_sq = (
        db.query(func.count(Scene.id))
        .filter(Scene.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )
    rows = (
        db.query(Project, scene_count_sq.label("scene_count"))
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": p.id,
            "title": p.title,
            "style": p.style,
            "duration": p.duration,
            "status": p.status,
            "scene_count": count,
            "created_at": p.created_at.isoformat(),
        }
        for p, count in rows
    ]


@router.get("/projects/{project_id}", response_model=Dict[str, Any])
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(selectinload(Project.scenes), selectinload(Project.scripts))
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    script_content: List = []
    if project.scripts:
        try:
            script_content = json.loads(project.scripts[0].content)
        except Exception:
            pass

    return {
        "id": project.id,
        "title": project.title,
        "prompt": project.prompt,
        "style": project.style,
        "duration": project.duration,
        "status": project.status,
        "director_vision": project.director_vision,
        "created_at": project.created_at.isoformat(),
        "scenes": [
            {
                "scene_number": s.scene_number,
                "description": s.description,
                "shot_type": s.shot_type,
                "mood": s.mood,
                "duration": s.duration,
                "visual_prompt": s.visual_prompt,
                "narration": s.narration,
                "dialogue": s.dialogue,
                "audio_cues": s.audio_cues,
                "video_url": s.video_url,
                "audio_url": s.audio_url,
            }
            for s in sorted(project.scenes, key=lambda x: x.scene_number)
        ],
        "script": script_content,
    }


@router.get("/agent-status")
def get_agent_status():
    llm = _get_orchestrator()._llm
    from app.services.audio_generator import audio_generator
    from app.services.runway_service import runway_service
    return {
        "status": "active",
        "backend": llm.active_backend,
        "model": llm.active_model,
        "available_backends": {
            "ollama": True,
            "google": bool(llm.google_api_key),
            "claude": bool(llm.anthropic_api_key),
        },
        "voice_backend": "elevenlabs" if audio_generator.is_elevenlabs_active else "local",
        "video_backend": "runway" if runway_service.is_configured else "local",
    }


@router.get("/graph")
def get_graph_structure():
    """Return the LangGraph pipeline topology for frontend visualization."""
    return _get_orchestrator().get_graph_structure()


@router.get("/pipeline-history")
async def get_pipeline_history():
    """Return the history of pipeline runs with timings and error info."""
    from app.services.mongo_store import mongo_store
    mongo_runs = await mongo_store.get_runs(limit=20)
    if mongo_runs:
        return {"runs": mongo_runs, "storage": "mongodb"}
    return {"runs": _get_orchestrator().get_run_history(), "storage": "memory"}


@router.get("/pipeline-analytics")
async def get_pipeline_analytics():
    """Return pipeline analytics (total runs, success rate, etc.)."""
    from app.services.mongo_store import mongo_store
    return await mongo_store.get_analytics()


@router.get("/projects/{project_id}/media")
async def get_project_media(project_id: str):
    """Return generated media (video/audio) for a project."""
    from app.services.mongo_store import mongo_store
    content = await mongo_store.get_generated_content(project_id)
    return {"project_id": project_id, "content": content}


@router.post("/create-film-stream")
async def create_film_stream(request: FilmRequest, db: Session = Depends(get_db)):
    """SSE streaming endpoint for film creation with real-time progress."""
    progress_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def _on_progress(data: Dict[str, Any]):
        await progress_queue.put(data)

    async def _event_generator():
        orchestrator = _get_orchestrator()
        project_id = str(uuid.uuid4())

        task = asyncio.create_task(
            orchestrator.create_film(
                user_prompt=request.prompt,
                style=request.style,
                duration=request.duration,
                on_progress=_on_progress,
            )
        )

        while not task.done():
            try:
                progress = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                yield f"data: {json.dumps(progress)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        result = task.result()

        if result.get("status") == "success":
            try:
                _persist_project(db, request, result, project_id=project_id)
            except Exception:
                logger.exception("Failed to persist project (stream)")

        yield f"data: {json.dumps({'type': 'complete', 'result': result, 'project_id': project_id})}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/clear-memory")
def clear_agent_memory():
    _get_orchestrator().clear_all_memory()
    return {"status": "success", "message": "All agent memories cleared"}
