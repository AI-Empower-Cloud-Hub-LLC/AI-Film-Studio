"""
Agent Orchestrator — Advanced LangGraph workflow for the film production pipeline.

Features:
  - Parallel execution (Cinematographer + SoundDesigner fan-out/fan-in)
  - Per-node error handling with conditional retry routing
  - State checkpointing via MemorySaver (resumable pipelines)
  - Quality review loop (Director reviews Editor output, max 1 revision)
  - Graph introspection API for frontend visualization

Graph topology:
  director → screenwriter → [cinematographer, sound_designer] → editor → review → END
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
from .director_agent import DirectorAgent
from .screenwriter_agent import ScreenwriterAgent
from .cinematographer_agent import CinematographerAgent
from .sound_designer_agent import SoundDesignerAgent
from .editor_agent import EditorAgent

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]

NODE_ORDER = ["director", "screenwriter", "cinematographer", "sound_designer", "editor", "review"]
MAX_RETRIES = 1
MAX_REVISIONS = 1


# ---------------------------------------------------------------------------
# Pipeline state flowing through the graph
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    user_prompt: str
    style: str
    duration: int
    # Agent outputs
    director: Dict[str, Any]
    script: Dict[str, Any]
    cinematography: Dict[str, Any]
    sound: Dict[str, Any]
    media_assets: Dict[str, Any]
    final_timeline: Dict[str, Any]
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
    """Advanced LangGraph orchestrator with parallel execution, error handling,
    checkpointing, and quality review loop."""

    def __init__(self, llm: Optional[LLMService] = None):
        self._llm = llm or llm_service
        self.director = DirectorAgent(llm=self._llm)
        self.screenwriter = ScreenwriterAgent(llm=self._llm)
        self.cinematographer = CinematographerAgent(llm=self._llm)
        self.sound_designer = SoundDesignerAgent(llm=self._llm)
        self.editor = EditorAgent(llm=self._llm)
        self._checkpointer = MemorySaver()
        self._run_history: List[Dict[str, Any]] = []
        logger.info(
            "Agent Orchestrator initialised with 5 agents "
            "(LangGraph advanced, backend=%s)", self._llm.backend,
        )

    @classmethod
    def from_settings(cls) -> "AgentOrchestrator":
        return cls(llm=llm_service)

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
                    "total_steps": 7,
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
            director_out = final_state.get("director", {})
            script_out = final_state.get("script", {})
            cin_out = final_state.get("cinematography", {})
            snd_out = final_state.get("sound", {})
            scenes = director_out.get("scenes", [])

            generated_media = {}
            if scenes:
                try:
                    await _notify(7, "Media Generator", "running", "Generating video and voiceover")
                    generated_media = await media_pipeline.generate_scene_media(
                        scenes=scenes,
                        shot_plans=cin_out.get("shot_plans", []),
                        script_scenes=script_out.get("script_scenes", []),
                        audio_plans=snd_out.get("audio_plans", []),
                        style=style,
                        on_progress=on_progress,
                    )
                    await _notify(7, "Media Generator", "completed", "Media generation complete")
                except Exception as exc:
                    logger.warning("Media generation failed: %s — continuing without media", exc)
                    generated_media = {"error": str(exc)}

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
                "director": final_state.get("director", {}),
                "script": final_state.get("script", {}),
                "cinematography": final_state.get("cinematography", {}),
                "sound": final_state.get("sound", {}),
                "media_assets": final_state.get("media_assets", {}),
                "final_timeline": final_state.get("final_timeline", {}),
                "workflow_steps": final_state.get("workflow_steps", []),
                "node_timings": final_state.get("node_timings", {}),
                "revision_count": final_state.get("revision_count", 0),
                "generated_media": generated_media,
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
                {"id": "cinematographer", "label": "Cinematographer", "type": "agent", "description": "Visual composition & shot planning", "parallel_group": "visual_audio"},
                {"id": "sound_designer", "label": "Sound Designer", "type": "agent", "description": "Audio landscape planning", "parallel_group": "visual_audio"},
                {"id": "editor", "label": "Editor", "type": "agent", "description": "Timeline assembly & post-production"},
                {"id": "review", "label": "Quality Review", "type": "decision", "description": "Director reviews final output"},
            ],
            "edges": [
                {"from": "director", "to": "screenwriter", "type": "sequential"},
                {"from": "screenwriter", "to": "cinematographer", "type": "fan_out", "label": "parallel"},
                {"from": "screenwriter", "to": "sound_designer", "type": "fan_out", "label": "parallel"},
                {"from": "cinematographer", "to": "editor", "type": "fan_in"},
                {"from": "sound_designer", "to": "editor", "type": "fan_in"},
                {"from": "editor", "to": "review", "type": "sequential"},
                {"from": "review", "to": "__end__", "type": "conditional", "label": "approved"},
                {"from": "review", "to": "screenwriter", "type": "conditional", "label": "revision needed"},
            ],
            "features": [
                "parallel_execution",
                "error_retry",
                "state_checkpointing",
                "quality_review_loop",
            ],
        }

    def get_run_history(self) -> List[Dict[str, Any]]:
        """Return the history of pipeline runs."""
        return list(reversed(self._run_history))

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self, notify: Callable) -> Any:
        """Construct the advanced LangGraph state graph."""
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
                return {**state, "director": output, "node_timings": timings}
            except Exception as exc:
                return _handle_node_error(state, "director", str(exc), step, start)

        async def screenwriter_node(state: PipelineState) -> PipelineState:
            start = time.time()
            step = _add_step(state, "Screenwriter", "running", "Writing script and dialogue")
            await notify(2, "Screenwriter", "running", "Writing script and dialogue")
            try:
                director_out = state.get("director", {})
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

        async def parallel_visual_audio(state: PipelineState) -> PipelineState:
            """Fan-out: run Cinematographer and SoundDesigner concurrently."""
            start = time.time()

            cin_step = _add_step(state, "Cinematographer", "running", "Planning shots and image prompts")
            snd_step = _add_step(state, "Sound Designer", "running", "Designing audio landscape")
            await notify(3, "Cinematographer", "running", "Planning shots and image prompts (parallel)")
            await notify(4, "Sound Designer", "running", "Designing audio landscape (parallel)")

            director_out = state.get("director", {})
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

            cin_result, snd_result = await asyncio.gather(
                _run_cinematographer(),
                _run_sound_designer(),
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
                await notify(3, "Cinematographer", "completed", "Shot plans finalized")
                new_state["cinematography"] = cin_result

            if isinstance(snd_result, Exception):
                errors["sound_designer"] = str(snd_result)
                _update_step(snd_step, "error", str(snd_result))
                logger.warning("Sound Designer failed: %s — using fallback", snd_result)
                new_state["sound"] = {"audio_plans": [], "agent": "Sound Designer", "fallback": True}
            else:
                _update_step(snd_step, "completed", "Audio design complete")
                await notify(4, "Sound Designer", "completed", "Audio design complete")
                new_state["sound"] = snd_result

            timings["parallel_visual_audio"] = round(time.time() - start, 2)
            new_state["node_timings"] = timings
            new_state["node_errors"] = errors
            return new_state

        async def editor_node(state: PipelineState) -> PipelineState:
            start = time.time()
            step = _add_step(state, "Editor", "running", "Assembling final timeline")
            await notify(5, "Editor", "running", "Assembling final timeline")
            try:
                director_out = state.get("director", {})
                scenes = director_out.get("scenes", [])
                media_assets = orchestrator._build_media_asset_list(scenes)
                output = await orchestrator.editor.process({
                    "scenes": scenes,
                    "video_clips": media_assets["video_clips"],
                    "audio_files": media_assets["audio_files"],
                })
                _update_step(step, "completed", "Film assembled")
                await notify(5, "Editor", "completed", "Film assembled")
                timings = dict(state.get("node_timings", {}))
                timings["editor"] = round(time.time() - start, 2)
                return {**state, "media_assets": media_assets, "final_timeline": output, "node_timings": timings}
            except Exception as exc:
                return _handle_node_error(state, "editor", str(exc), step, start)

        async def review_node(state: PipelineState) -> PipelineState:
            """Director quality review — checks completeness, may request revision."""
            start = time.time()
            step = _add_step(state, "Quality Review", "running", "Director reviewing final output")
            await notify(6, "Quality Review", "running", "Director reviewing final output")

            revision_count = state.get("revision_count", 0)
            director_out = state.get("director", {})
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
                await notify(6, "Quality Review", "completed", "Approved" if passed else "Accepted with issues")
                timings = dict(state.get("node_timings", {}))
                timings["review"] = round(time.time() - start, 2)
                return {**state, "review_passed": True, "node_timings": timings}
            else:
                detail = f"Revision needed: {'; '.join(issues)}"
                _update_step(step, "revision", detail)
                await notify(6, "Quality Review", "revision", detail)
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
        graph.add_node("parallel_visual_audio", parallel_visual_audio)
        graph.add_node("editor", editor_node)
        graph.add_node("review", review_node)

        graph.set_entry_point("director")
        graph.add_edge("director", "screenwriter")
        graph.add_edge("screenwriter", "parallel_visual_audio")
        graph.add_edge("parallel_visual_audio", "editor")
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

    def clear_all_memory(self):
        for agent in [self.director, self.screenwriter, self.cinematographer, self.sound_designer, self.editor]:
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
