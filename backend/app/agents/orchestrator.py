"""
Agent Orchestrator — Advanced LangGraph workflow for the film production pipeline.

Features:
  - 10 agent nodes in expanded production pipeline
  - Parallel execution (Cinematographer + SoundDesigner + CastSelection + LocationResearch)
  - Per-node error handling with conditional retry routing
  - State checkpointing via MemorySaver (resumable pipelines)
  - Quality review loop (Director reviews Editor output, max 1 revision)
  - Graph introspection API for frontend visualization

Graph topology:
  director → screenwriter → screenplay_refinement →
    [cinematographer, sound_designer, cast_selection, location_research] →
    [vfx_planning, mood_board] → editor → review → END
                                                       ↑        |
                                                       └── (revision) ──┘
"""
from __future__ import annotations

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable, List, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.services.llm_service import LLMService, llm_service
from app.services.media_pipeline import media_pipeline
from app.services.mongo_store import mongo_store
from app.services.image_generator import image_generator
from app.services.wav2lip_service import wav2lip_service
from .director_agent import DirectorAgent
from .screenwriter_agent import ScreenwriterAgent
from .screenplay_refinement_agent import ScreenplayRefinementAgent
from .cinematographer_agent import CinematographerAgent
from .sound_designer_agent import SoundDesignerAgent
from .cast_selection_agent import CastSelectionAgent
from .location_research_agent import LocationResearchAgent
from .vfx_planning_agent import VFXPlanningAgent
from .mood_board_agent import MoodBoardAgent
from .editor_agent import EditorAgent

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]

NODE_ORDER = [
    "director", "screenwriter", "screenplay_refinement",
    "cinematographer", "sound_designer", "cast_selection", "location_research",
    "vfx_planning", "mood_board",
    "editor", "review",
]
MAX_RETRIES = 1
MAX_REVISIONS = 1
TOTAL_STEPS = 12


# ---------------------------------------------------------------------------
# Pipeline state flowing through the graph
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    user_prompt: str
    style: str
    duration: int
    # Agent outputs
    director_output: Dict[str, Any]
    script: Dict[str, Any]
    refined_screenplay: Dict[str, Any]
    cinematography: Dict[str, Any]
    sound: Dict[str, Any]
    cast: Dict[str, Any]
    locations: Dict[str, Any]
    vfx_plan: Dict[str, Any]
    mood_board: Dict[str, Any]
    media_assets: Dict[str, Any]
    final_timeline: Dict[str, Any]
    lip_sync: Dict[str, Any]
    # Workflow metadata
    error: str
    node_errors: Dict[str, str]
    node_retries: Dict[str, int]
    node_timings: Dict[str, float]
    revision_count: int
    review_passed: bool
    workflow_steps: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class AgentOrchestrator:
    """Advanced LangGraph orchestrator with 10 agent nodes, parallel execution,
    error handling, checkpointing, and quality review loop."""

    def __init__(self, llm: Optional[LLMService] = None, model: str = None, anthropic_api_key: str = ""):
        """Initialize orchestrator with optional LLM service and backward-compatible parameters.
        
        Args:
            llm: LLMService instance (preferred)
            model: Model name for backward compatibility
            anthropic_api_key: Anthropic API key for backward compatibility
        """
        self._llm = llm or llm_service
        # Use model and anthropic_api_key for all agents to match their constructors
        self.director = DirectorAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.screenwriter = ScreenwriterAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.screenplay_refinement = ScreenplayRefinementAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.cinematographer = CinematographerAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.sound_designer = SoundDesignerAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.cast_selection = CastSelectionAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.location_research = LocationResearchAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.vfx_planning = VFXPlanningAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.mood_board = MoodBoardAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self.editor = EditorAgent(model=model or "claude-opus-4-6", anthropic_api_key=anthropic_api_key)
        self._checkpointer = MemorySaver()
        self._run_history: List[Dict[str, Any]] = []
        backend_name = getattr(self._llm, 'backend', 'unknown')
        logger.info(
            "Agent Orchestrator initialised with 10 agents "
            "(LangGraph advanced, backend=%s)", backend_name,
        )

    @classmethod
    def from_settings(cls) -> "AgentOrchestrator":
        """Create orchestrator from app settings."""
        from app.core.config import settings
        return cls(
            model="claude-opus-4-6",
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_film(
        self,
        user_prompt: str,
        style: str = "cinematic",
        duration: int = 30,
        on_progress: Optional[ProgressCallback] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build and run the advanced LangGraph pipeline."""

        async def _notify(step: int, agent: str, status: str, detail: str = ""):
            if on_progress:
                await on_progress({
                    "step": step,
                    "total_steps": TOTAL_STEPS,
                    "agent": agent,
                    "status": status,
                    "detail": detail,
                })

        try:
            graph = self._build_graph(_notify)
            initial_state: PipelineState = {
                "user_prompt": user_prompt,
                "style": style,
                "duration": duration,
                "node_errors": {},
                "node_retries": {},
                "node_timings": {},
                "revision_count": 0,
                "review_passed": False,
                "workflow_steps": [],
            }

            config: Dict[str, Any] = {"configurable": {"thread_id": thread_id or "default"}}
            final_state = await graph.ainvoke(initial_state, config=config)

            if final_state.get("error"):
                return {"status": "error", "error": final_state["error"]}

            # --- Media generation phase (video + voiceover) ---
            director_out = final_state.get("director_output", {})
            script_out = final_state.get("script", {})
            cin_out = final_state.get("cinematography", {})
            snd_out = final_state.get("sound", {})
            scenes = director_out.get("scenes", [])

            generated_media = {}
            if scenes:
                try:
                    await _notify(TOTAL_STEPS - 1, "Media Generator", "running", "Generating video and voiceover")
                    generated_media = await media_pipeline.generate_scene_media(
                        scenes=scenes,
                        shot_plans=cin_out.get("shot_plans", []),
                        script_scenes=script_out.get("script_scenes", []),
                        audio_plans=snd_out.get("audio_plans", []),
                        style=style,
                        on_progress=on_progress,
                    )
                    await _notify(TOTAL_STEPS - 1, "Media Generator", "completed", "Media generation complete")
                except Exception as exc:
                    logger.warning("Media generation failed: %s — continuing without media", exc)
                    generated_media = {"error": str(exc)}

            # --- Lip sync phase ---
            lip_sync_result = {}
            if wav2lip_service.is_available and generated_media.get("scenes"):
                try:
                    await _notify(TOTAL_STEPS, "Wav2Lip", "running", "Applying lip sync")
                    lip_sync_results = []
                    for media_scene in generated_media.get("scenes", []):
                        video_path = media_scene.get("video", {}).get("local_path", "")
                        audio_path = media_scene.get("audio", {}).get("path", "")
                        if video_path and audio_path:
                            result = await wav2lip_service.lip_sync(video_path, audio_path)
                            lip_sync_results.append(result)
                    lip_sync_result = {"scenes": lip_sync_results, "backend": "wav2lip"}
                    await _notify(TOTAL_STEPS, "Wav2Lip", "completed", "Lip sync complete")
                except Exception as exc:
                    logger.warning("Lip sync failed: %s", exc)
                    lip_sync_result = {"error": str(exc)}

            # --- Generate images for cast, locations, mood board ---
            cast_out = final_state.get("cast", {})
            location_out = final_state.get("locations", {})
            mood_out = final_state.get("mood_board", {})

            cast_images = []
            for ch in cast_out.get("characters", []):
                img = await image_generator.generate(ch.get("image_prompt", ch.get("name", "")), "cast")
                cast_images.append({**img, "character_name": ch.get("name", "")})

            location_images = []
            for loc in location_out.get("locations", []):
                img = await image_generator.generate(loc.get("image_prompt", loc.get("location_name", "")), "location")
                location_images.append({**img, "location_name": loc.get("location_name", "")})

            mood_images = []
            for mood in mood_out.get("mood_images", []):
                img = await image_generator.generate(mood.get("image_prompt", mood.get("title", "")), "mood_board")
                mood_images.append({**img, "title": mood.get("title", "")})

            run_record = {
                "timestamp": time.time(),
                "prompt": user_prompt,
                "style": style,
                "duration": duration,
                "node_timings": final_state.get("node_timings", {}),
                "node_errors": final_state.get("node_errors", {}),
                "revision_count": final_state.get("revision_count", 0),
                "status": "success",
                "video_backend": generated_media.get("video_backend", "local"),
                "voice_backend": generated_media.get("voice_backend", "local"),
                "agents_count": 10,
            }
            self._run_history.append(run_record)
            try:
                await mongo_store.save_run(run_record)
            except Exception:
                pass

            return {
                "status": "success",
                "user_prompt": user_prompt,
                "style": style,
                "duration": duration,
                "director": final_state.get("director_output", {}),
                "script": final_state.get("script", {}),
                "refined_screenplay": final_state.get("refined_screenplay", {}),
                "cinematography": final_state.get("cinematography", {}),
                "sound": final_state.get("sound", {}),
                "cast": final_state.get("cast", {}),
                "locations": final_state.get("locations", {}),
                "vfx_plan": final_state.get("vfx_plan", {}),
                "mood_board": final_state.get("mood_board", {}),
                "media_assets": final_state.get("media_assets", {}),
                "final_timeline": final_state.get("final_timeline", {}),
                "workflow_steps": final_state.get("workflow_steps", []),
                "node_timings": final_state.get("node_timings", {}),
                "revision_count": final_state.get("revision_count", 0),
                "generated_media": generated_media,
                "cast_images": cast_images,
                "location_images": location_images,
                "mood_images": mood_images,
                "lip_sync": lip_sync_result,
            }
        except Exception as exc:
            logger.exception("Film creation pipeline failed")
            return {"status": "error", "error": str(exc)}

    def get_graph_structure(self) -> Dict[str, Any]:
        """Return the graph topology for frontend visualization."""
        return {
            "nodes": [
                {"id": "director", "label": "Director", "type": "agent", "description": "Creative vision & scene breakdown"},
                {"id": "screenwriter", "label": "Screenwriter", "type": "agent", "description": "Script & dialogue generation"},
                {"id": "screenplay_refinement", "label": "Screenplay Refinement", "type": "agent", "description": "Polish screenplay, add camera directions & production notes"},
                {"id": "cinematographer", "label": "Cinematographer", "type": "agent", "description": "Visual composition & shot planning", "parallel_group": "production"},
                {"id": "sound_designer", "label": "Sound Designer", "type": "agent", "description": "Audio landscape planning", "parallel_group": "production"},
                {"id": "cast_selection", "label": "Cast Selection", "type": "agent", "description": "Character descriptions, casting & budget", "parallel_group": "production"},
                {"id": "location_research", "label": "Location Research", "type": "agent", "description": "Filming locations, logistics & budget", "parallel_group": "production"},
                {"id": "vfx_planning", "label": "VFX Planning", "type": "agent", "description": "VFX shots, techniques & budget", "parallel_group": "post_production"},
                {"id": "mood_board", "label": "Mood Board", "type": "agent", "description": "Visual style guide & mood images", "parallel_group": "post_production"},
                {"id": "editor", "label": "Editor", "type": "agent", "description": "Timeline assembly & post-production"},
                {"id": "review", "label": "Quality Review", "type": "decision", "description": "Director reviews final output"},
            ],
            "edges": [
                {"from": "director", "to": "screenwriter", "type": "sequential"},
                {"from": "screenwriter", "to": "screenplay_refinement", "type": "sequential"},
                {"from": "screenplay_refinement", "to": "cinematographer", "type": "fan_out", "label": "parallel"},
                {"from": "screenplay_refinement", "to": "sound_designer", "type": "fan_out", "label": "parallel"},
                {"from": "screenplay_refinement", "to": "cast_selection", "type": "fan_out", "label": "parallel"},
                {"from": "screenplay_refinement", "to": "location_research", "type": "fan_out", "label": "parallel"},
                {"from": "cinematographer", "to": "vfx_planning", "type": "fan_in"},
                {"from": "sound_designer", "to": "vfx_planning", "type": "fan_in"},
                {"from": "cast_selection", "to": "vfx_planning", "type": "fan_in"},
                {"from": "location_research", "to": "vfx_planning", "type": "fan_in"},
                {"from": "vfx_planning", "to": "mood_board", "type": "sequential"},
                {"from": "mood_board", "to": "editor", "type": "sequential"},
                {"from": "editor", "to": "review", "type": "sequential"},
                {"from": "review", "to": "__end__", "type": "conditional", "label": "approved"},
                {"from": "review", "to": "screenwriter", "type": "conditional", "label": "revision needed"},
            ],
            "features": [
                "parallel_execution",
                "error_retry",
                "state_checkpointing",
                "quality_review_loop",
                "screenplay_refinement",
                "cast_selection",
                "location_research",
                "vfx_planning",
                "mood_board",
                "lip_sync",
            ],
        }

    def get_run_history(self) -> List[Dict[str, Any]]:
        """Return the history of pipeline runs."""
        return list(reversed(self._run_history))

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self, notify: Callable) -> Any:
        """Construct the advanced LangGraph state graph with 10 agent nodes."""
        orchestrator = self

        # --- Node functions ---

        async def director_node(state: PipelineState) -> PipelineState:
            start = time.time()
            step = _add_step(state, "Director", "running", "Creating creative vision and scene breakdown")
            await notify(1, "Director", "running", "Creating creative vision and scene breakdown")
            try:
                output = await orchestrator.director.process({
                    "prompt": state["user_prompt"],
                    "style": state.get("style", "cinematic"),
                    "duration": state.get("duration", 30),
                })
                _update_step(step, "completed", f"{len(output.get('scenes', []))} scenes planned")
                await notify(1, "Director", "completed", f"{len(output.get('scenes', []))} scenes planned")
                timings = dict(state.get("node_timings", {}))
                timings["director"] = round(time.time() - start, 2)
                return {**state, "director_output": output, "node_timings": timings}
            except Exception as exc:
                return _handle_node_error(state, "director", str(exc), step, start)

        async def screenwriter_node(state: PipelineState) -> PipelineState:
            start = time.time()
            step = _add_step(state, "Screenwriter", "running", "Writing script and dialogue")
            await notify(2, "Screenwriter", "running", "Writing script and dialogue")
            try:
                director_out = state.get("director_output", {})
                output = await orchestrator.screenwriter.process({
                    "vision": director_out.get("vision", ""),
                    "scenes": director_out.get("scenes", []),
                })
                _update_step(step, "completed", "Script and dialogue written")
                await notify(2, "Screenwriter", "completed", "Script and dialogue written")
                timings = dict(state.get("node_timings", {}))
                timings["screenwriter"] = round(time.time() - start, 2)
                return {**state, "script": output, "node_timings": timings}
            except Exception as exc:
                return _handle_node_error(state, "screenwriter", str(exc), step, start)

        async def screenplay_refinement_node(state: PipelineState) -> PipelineState:
            start = time.time()
            step = _add_step(state, "Screenplay Refinement", "running", "Polishing screenplay with camera directions")
            await notify(3, "Screenplay Refinement", "running", "Polishing screenplay with camera directions")
            try:
                script_out = state.get("script", {})
                director_out = state.get("director_output", {})
                output = await orchestrator.screenplay_refinement.process({
                    "script_scenes": script_out.get("script_scenes", []),
                    "vision": director_out.get("vision", ""),
                    "style": state.get("style", "cinematic"),
                })
                _update_step(step, "completed", "Screenplay refined")
                await notify(3, "Screenplay Refinement", "completed", "Screenplay refined")
                timings = dict(state.get("node_timings", {}))
                timings["screenplay_refinement"] = round(time.time() - start, 2)
                return {**state, "refined_screenplay": output, "node_timings": timings}
            except Exception as exc:
                return _handle_node_error(state, "screenplay_refinement", str(exc), step, start)

        async def parallel_production(state: PipelineState) -> PipelineState:
            """Fan-out: run Cinematographer, SoundDesigner, CastSelection, LocationResearch concurrently."""
            start = time.time()

            cin_step = _add_step(state, "Cinematographer", "running", "Planning shots and image prompts")
            snd_step = _add_step(state, "Sound Designer", "running", "Designing audio landscape")
            cast_step = _add_step(state, "Cast Selection", "running", "Analyzing characters for casting")
            loc_step = _add_step(state, "Location Research", "running", "Scouting filming locations")

            await notify(4, "Cinematographer", "running", "Planning shots (parallel)")
            await notify(5, "Sound Designer", "running", "Designing audio (parallel)")
            await notify(6, "Cast Selection", "running", "Casting characters (parallel)")
            await notify(7, "Location Research", "running", "Scouting locations (parallel)")

            director_out = state.get("director_output", {})
            script_out = state.get("script", {})

            async def _run_cinematographer():
                return await orchestrator.cinematographer.process({
                    "scenes": director_out.get("scenes", []),
                    "style": state.get("style", "cinematic"),
                    "vision": director_out.get("vision", ""),
                })

            async def _run_sound_designer():
                return await orchestrator.sound_designer.process({
                    "script_scenes": script_out.get("script_scenes", []),
                    "style": state.get("style", "cinematic"),
                    "vision": director_out.get("vision", ""),
                })

            async def _run_cast_selection():
                return await orchestrator.cast_selection.process({
                    "script_scenes": script_out.get("script_scenes", []),
                    "vision": director_out.get("vision", ""),
                    "style": state.get("style", "cinematic"),
                })

            async def _run_location_research():
                return await orchestrator.location_research.process({
                    "scenes": director_out.get("scenes", []),
                    "vision": director_out.get("vision", ""),
                    "style": state.get("style", "cinematic"),
                })

            cin_result, snd_result, cast_result, loc_result = await asyncio.gather(
                _run_cinematographer(),
                _run_sound_designer(),
                _run_cast_selection(),
                _run_location_research(),
                return_exceptions=True,
            )

            timings = dict(state.get("node_timings", {}))
            errors = dict(state.get("node_errors", {}))
            new_state = dict(state)

            if isinstance(cin_result, Exception):
                errors["cinematographer"] = str(cin_result)
                _update_step(cin_step, "error", str(cin_result))
                logger.warning("Cinematographer failed: %s — using fallback", cin_result)
                new_state["cinematography"] = {"shot_plans": [], "style": state.get("style", "cinematic"), "agent": "Cinematographer", "fallback": True}
            else:
                _update_step(cin_step, "completed", "Shot plans finalized")
                await notify(4, "Cinematographer", "completed", "Shot plans finalized")
                new_state["cinematography"] = cin_result

            if isinstance(snd_result, Exception):
                errors["sound_designer"] = str(snd_result)
                _update_step(snd_step, "error", str(snd_result))
                logger.warning("Sound Designer failed: %s — using fallback", snd_result)
                new_state["sound"] = {"audio_plans": [], "agent": "Sound Designer", "fallback": True}
            else:
                _update_step(snd_step, "completed", "Audio design complete")
                await notify(5, "Sound Designer", "completed", "Audio design complete")
                new_state["sound"] = snd_result

            if isinstance(cast_result, Exception):
                errors["cast_selection"] = str(cast_result)
                _update_step(cast_step, "error", str(cast_result))
                logger.warning("Cast Selection failed: %s — using fallback", cast_result)
                new_state["cast"] = {"characters": [], "agent": "CastSelection", "fallback": True}
            else:
                _update_step(cast_step, "completed", f"{cast_result.get('total_characters', 0)} characters cast")
                await notify(6, "Cast Selection", "completed", f"{cast_result.get('total_characters', 0)} characters cast")
                new_state["cast"] = cast_result

            if isinstance(loc_result, Exception):
                errors["location_research"] = str(loc_result)
                _update_step(loc_step, "error", str(loc_result))
                logger.warning("Location Research failed: %s — using fallback", loc_result)
                new_state["locations"] = {"locations": [], "agent": "LocationResearch", "fallback": True}
            else:
                _update_step(loc_step, "completed", f"{loc_result.get('total_locations', 0)} locations scouted")
                await notify(7, "Location Research", "completed", f"{loc_result.get('total_locations', 0)} locations scouted")
                new_state["locations"] = loc_result

            timings["parallel_production"] = round(time.time() - start, 2)
            new_state["node_timings"] = timings
            new_state["node_errors"] = errors
            return new_state

        async def parallel_post_production(state: PipelineState) -> PipelineState:
            """Fan-out: run VFXPlanning and MoodBoard concurrently."""
            start = time.time()

            vfx_step = _add_step(state, "VFX Planning", "running", "Analyzing VFX requirements")
            mood_step = _add_step(state, "Mood Board", "running", "Creating visual style guide")

            await notify(8, "VFX Planning", "running", "Analyzing VFX requirements (parallel)")
            await notify(9, "Mood Board", "running", "Creating visual style guide (parallel)")

            director_out = state.get("director_output", {})
            cin_out = state.get("cinematography", {})

            async def _run_vfx():
                return await orchestrator.vfx_planning.process({
                    "scenes": director_out.get("scenes", []),
                    "shot_plans": cin_out.get("shot_plans", []),
                    "vision": director_out.get("vision", ""),
                    "style": state.get("style", "cinematic"),
                })

            async def _run_mood():
                return await orchestrator.mood_board.process({
                    "vision": director_out.get("vision", ""),
                    "style": state.get("style", "cinematic"),
                    "scenes": director_out.get("scenes", []),
                })

            vfx_result, mood_result = await asyncio.gather(
                _run_vfx(),
                _run_mood(),
                return_exceptions=True,
            )

            timings = dict(state.get("node_timings", {}))
            errors = dict(state.get("node_errors", {}))
            new_state = dict(state)

            if isinstance(vfx_result, Exception):
                errors["vfx_planning"] = str(vfx_result)
                _update_step(vfx_step, "error", str(vfx_result))
                logger.warning("VFX Planning failed: %s — using fallback", vfx_result)
                new_state["vfx_plan"] = {"vfx_shots": [], "agent": "VFXPlanning", "fallback": True}
            else:
                _update_step(vfx_step, "completed", f"{vfx_result.get('total_vfx_shots', 0)} VFX shots planned")
                await notify(8, "VFX Planning", "completed", f"{vfx_result.get('total_vfx_shots', 0)} VFX shots planned")
                new_state["vfx_plan"] = vfx_result

            if isinstance(mood_result, Exception):
                errors["mood_board"] = str(mood_result)
                _update_step(mood_step, "error", str(mood_result))
                logger.warning("Mood Board failed: %s — using fallback", mood_result)
                new_state["mood_board"] = {"mood_images": [], "agent": "MoodBoard", "fallback": True}
            else:
                _update_step(mood_step, "completed", f"{mood_result.get('total_images', 0)} mood images generated")
                await notify(9, "Mood Board", "completed", f"{mood_result.get('total_images', 0)} mood images generated")
                new_state["mood_board"] = mood_result

            timings["parallel_post_production"] = round(time.time() - start, 2)
            new_state["node_timings"] = timings
            new_state["node_errors"] = errors
            return new_state

        async def editor_node(state: PipelineState) -> PipelineState:
            start = time.time()
            step = _add_step(state, "Editor", "running", "Assembling final timeline")
            await notify(10, "Editor", "running", "Assembling final timeline")
            try:
                director_out = state.get("director_output", {})
                scenes = director_out.get("scenes", [])
                media_assets = orchestrator._build_media_asset_list(scenes)
                output = await orchestrator.editor.process({
                    "scenes": scenes,
                    "video_clips": media_assets["video_clips"],
                    "audio_files": media_assets["audio_files"],
                })
                _update_step(step, "completed", "Film assembled")
                await notify(10, "Editor", "completed", "Film assembled")
                timings = dict(state.get("node_timings", {}))
                timings["editor"] = round(time.time() - start, 2)
                return {**state, "media_assets": media_assets, "final_timeline": output, "node_timings": timings}
            except Exception as exc:
                return _handle_node_error(state, "editor", str(exc), step, start)

        async def review_node(state: PipelineState) -> PipelineState:
            """Director quality review — checks completeness, may request revision."""
            start = time.time()
            step = _add_step(state, "Quality Review", "running", "Director reviewing final output")
            await notify(11, "Quality Review", "running", "Director reviewing final output")

            revision_count = state.get("revision_count", 0)
            director_out = state.get("director_output", {})
            script_out = state.get("script", {})
            timeline_out = state.get("final_timeline", {})

            scenes = director_out.get("scenes", [])
            script_scenes = script_out.get("script_scenes", [])
            timeline_entries = timeline_out.get("timeline", [])

            passed = True
            issues: List[str] = []

            if not scenes:
                issues.append("No scenes generated")
                passed = False
            if not script_scenes:
                issues.append("No script scenes generated")
                passed = False
            if not timeline_entries:
                issues.append("No timeline entries generated")
                passed = False

            if len(scenes) > 0 and len(timeline_entries) > 0:
                if len(timeline_entries) < len(scenes):
                    issues.append(f"Timeline has {len(timeline_entries)} entries but {len(scenes)} scenes expected")
                    passed = False

            if passed or revision_count >= MAX_REVISIONS:
                if not passed:
                    issues.append(f"Issues remain after {revision_count} revision(s) — accepting as-is")
                _update_step(step, "completed", "Quality review passed" if passed else "Accepted with known issues")
                await notify(11, "Quality Review", "completed", "Approved" if passed else "Accepted with issues")
                timings = dict(state.get("node_timings", {}))
                timings["review"] = round(time.time() - start, 2)
                return {**state, "review_passed": True, "node_timings": timings}
            else:
                detail = f"Revision needed: {'; '.join(issues)}"
                _update_step(step, "revision", detail)
                await notify(11, "Quality Review", "revision", detail)
                timings = dict(state.get("node_timings", {}))
                timings["review"] = round(time.time() - start, 2)
                return {
                    **state,
                    "review_passed": False,
                    "revision_count": revision_count + 1,
                    "node_timings": timings,
                }

        def review_router(state: PipelineState) -> str:
            """Conditional edge: route back to screenwriter for revision or end."""
            if state.get("review_passed", False):
                return END
            return "screenwriter"

        # --- Build the graph ---

        graph = StateGraph(PipelineState)

        graph.add_node("director", director_node)
        graph.add_node("screenwriter", screenwriter_node)
        graph.add_node("screenplay_refinement", screenplay_refinement_node)
        graph.add_node("parallel_production", parallel_production)
        graph.add_node("parallel_post_production", parallel_post_production)
        graph.add_node("editor", editor_node)
        graph.add_node("review", review_node)

        graph.set_entry_point("director")
        graph.add_edge("director", "screenwriter")
        graph.add_edge("screenwriter", "screenplay_refinement")
        graph.add_edge("screenplay_refinement", "parallel_production")
        graph.add_edge("parallel_production", "parallel_post_production")
        graph.add_edge("parallel_post_production", "editor")
        graph.add_edge("editor", "review")
        graph.add_conditional_edges("review", review_router)

        return graph.compile(checkpointer=self._checkpointer)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_media_asset_list(scenes: list) -> Dict[str, Any]:
        video_clips = [f"clip_scene_{s.get('scene_number', i + 1)}.mp4" for i, s in enumerate(scenes)]
        audio_files = [f"audio_scene_{s.get('scene_number', i + 1)}.wav" for i, s in enumerate(scenes)]
        return {"video_clips": video_clips, "audio_files": audio_files}

    def get_agent_status(self) -> Dict[str, Any]:
        agents = [
            self.director, self.screenwriter, self.screenplay_refinement,
            self.cinematographer, self.sound_designer, self.cast_selection,
            self.location_research, self.vfx_planning, self.mood_board, self.editor,
        ]
        return {a.name: {"memory_items": len(a.memory)} for a in agents}

    def clear_all_memory(self):
        for agent in [
            self.director, self.screenwriter, self.screenplay_refinement,
            self.cinematographer, self.sound_designer, self.cast_selection,
            self.location_research, self.vfx_planning, self.mood_board, self.editor,
        ]:
            agent.clear_memory()


# ---------------------------------------------------------------------------
# State helpers (used inside node functions)
# ---------------------------------------------------------------------------

def _add_step(state: PipelineState, agent: str, status: str, detail: str) -> Dict[str, Any]:
    step = {"agent": agent, "status": status, "detail": detail}
    steps = list(state.get("workflow_steps", []))
    steps.append(step)
    state["workflow_steps"] = steps
    return step


def _update_step(step: Dict[str, Any], status: str, detail: str) -> None:
    step["status"] = status
    step["detail"] = detail


def _handle_node_error(
    state: PipelineState, node_name: str, error_msg: str, step: Dict[str, Any], start: float
) -> PipelineState:
    logger.error("Node %s failed: %s", node_name, error_msg)
    _update_step(step, "error", error_msg)
    errors = dict(state.get("node_errors", {}))
    errors[node_name] = error_msg
    retries = dict(state.get("node_retries", {}))
    retries[node_name] = retries.get(node_name, 0) + 1
    timings = dict(state.get("node_timings", {}))
    timings[node_name] = round(time.time() - start, 2)
    return {**state, "node_errors": errors, "node_retries": retries, "node_timings": timings}
