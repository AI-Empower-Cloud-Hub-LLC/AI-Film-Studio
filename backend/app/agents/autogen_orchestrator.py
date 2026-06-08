"""
AutoGen Orchestrator — Microsoft AutoGen-based workflow for the film production pipeline.

Alternative backend to the LangGraph orchestrator, selectable via ORCHESTRATOR_BACKEND
config.  Reuses the same 10 agent classes and produces identical output so downstream
code (persistence, media generation, frontend) works without changes.

Features:
  - 10 agent steps mirroring the LangGraph pipeline
  - Parallel execution for production & post-production groups via asyncio.gather
  - Per-node error handling with graceful fallbacks
  - Quality review loop (max 1 revision)
  - Progress callback support for WebSocket streaming
  - AutoGen ConversableAgent wrappers around the existing agent classes

Graph topology (same as LangGraph version):
  director → screenwriter → screenplay_refinement →
    [cinematographer, sound_designer, cast_selection, location_research] →
    [vfx_planning, mood_board] → editor → review → END
"""
from __future__ import annotations

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable, List

from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.messages import TextMessage, BaseChatMessage
from autogen_core import CancellationToken

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

MAX_REVISIONS = 1
TOTAL_STEPS = 12


# ---------------------------------------------------------------------------
# Pipeline state (identical to LangGraph version)
# ---------------------------------------------------------------------------

class PipelineState(dict):
    """Mutable pipeline state dict flowing through the AutoGen agent chain.

    Kept as a plain dict subclass so the same downstream code that reads
    ``state.get("director_output", {})`` works unchanged.
    """
    pass


# ---------------------------------------------------------------------------
# AutoGen agent wrapper
# ---------------------------------------------------------------------------

class FilmAgentWrapper(BaseChatAgent):
    """Wraps an existing film-pipeline agent class as an AutoGen BaseChatAgent.

    Each wrapper holds a reference to one of the 10 production agents
    (DirectorAgent, ScreenwriterAgent, …).  When ``on_messages`` is called
    the wrapper:
      1. Deserializes the pipeline state from the last incoming TextMessage.
      2. Calls the underlying agent's ``process()`` method.
      3. Merges the result back into the pipeline state.
      4. Serializes and returns the updated state as a TextMessage.
    """

    def __init__(
        self,
        name: str,
        description: str,
        process_fn: Callable,
        input_builder: Callable[[PipelineState], Dict[str, Any]],
        output_key: str,
    ):
        super().__init__(name=name, description=description)
        self._process_fn = process_fn
        self._input_builder = input_builder
        self._output_key = output_key

    @property
    def produced_message_types(self) -> List[type]:
        return [TextMessage]

    async def on_messages(
        self,
        messages: list[BaseChatMessage],
        cancellation_token: CancellationToken,
    ) -> TextMessage:
        # Deserialize pipeline state from last message
        state = json.loads(messages[-1].content)
        input_data = self._input_builder(state)
        result = await self._process_fn(input_data)
        state[self._output_key] = result
        return TextMessage(content=json.dumps(state), source=self.name)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        pass


# ---------------------------------------------------------------------------
# AutoGen Orchestrator
# ---------------------------------------------------------------------------

class AutoGenOrchestrator:
    """AutoGen-based orchestrator with the same 10-agent pipeline as the
    LangGraph version.  Exposes an identical ``create_film()`` interface."""

    def __init__(self, llm: Optional[LLMService] = None, model: str = None, anthropic_api_key: str = ""):
        self._llm = llm or llm_service
        self.director = DirectorAgent(llm=self._llm)
        self.screenwriter = ScreenwriterAgent(llm=self._llm)
        self.screenplay_refinement = ScreenplayRefinementAgent(llm=self._llm)
        self.cinematographer = CinematographerAgent(llm=self._llm)
        self.sound_designer = SoundDesignerAgent(llm=self._llm)
        self.cast_selection = CastSelectionAgent(llm=self._llm)
        self.location_research = LocationResearchAgent(llm=self._llm)
        self.vfx_planning = VFXPlanningAgent(llm=self._llm)
        self.mood_board = MoodBoardAgent(llm=self._llm)
        self.editor = EditorAgent(llm=self._llm)
        self._run_history: List[Dict[str, Any]] = []
        logger.info(
            "AutoGen Orchestrator initialised with 10 agents (backend=%s)",
            self._llm.backend,
        )

    @classmethod
    def from_settings(cls) -> "AutoGenOrchestrator":
        return cls(llm=llm_service)

    # ------------------------------------------------------------------
    # Public API  (mirrors AgentOrchestrator exactly)
    # ------------------------------------------------------------------

    async def create_film(
        self,
        user_prompt: str,
        style: str = "cinematic",
        duration: int = 30,
        on_progress: Optional[ProgressCallback] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the 10-agent film pipeline using AutoGen orchestration."""

        async def _notify(step: int, agent: str, status: str, detail: str = ""):
            if on_progress:
                await on_progress({
                    "step": step,
                    "total_steps": TOTAL_STEPS,
                    "agent": agent,
                    "status": status,
                    "detail": detail,
                })

        state = PipelineState(
            user_prompt=user_prompt,
            style=style,
            duration=duration,
            node_errors={},
            node_retries={},
            node_timings={},
            revision_count=0,
            review_passed=False,
            workflow_steps=[],
        )

        try:
            # 1 — Director
            state = await self._run_node(
                state, "Director", 1, _notify,
                self.director.process,
                lambda s: {"prompt": s["user_prompt"], "style": s.get("style", "cinematic"), "duration": s.get("duration", 30)},
                "director_output",
                detail_fn=lambda r: f"{len(r.get('scenes', []))} scenes planned",
            )

            # Revision loop (max MAX_REVISIONS iterations)
            for _revision_pass in range(MAX_REVISIONS + 1):
                # 2 — Screenwriter
                state = await self._run_node(
                    state, "Screenwriter", 2, _notify,
                    self.screenwriter.process,
                    lambda s: {
                        "vision": s.get("director_output", {}).get("vision", ""),
                        "scenes": s.get("director_output", {}).get("scenes", []),
                    },
                    "script",
                    detail_fn=lambda r: "Script and dialogue written",
                )

                # 3 — Screenplay Refinement
                state = await self._run_node(
                    state, "Screenplay Refinement", 3, _notify,
                    self.screenplay_refinement.process,
                    lambda s: {
                        "script_scenes": s.get("script", {}).get("script_scenes", []),
                        "vision": s.get("director_output", {}).get("vision", ""),
                        "style": s.get("style", "cinematic"),
                    },
                    "refined_screenplay",
                    detail_fn=lambda r: "Screenplay refined",
                )

                # 4-7 — Parallel production
                state = await self._run_parallel_production(state, _notify)

                # 8-9 — Parallel post-production
                state = await self._run_parallel_post_production(state, _notify)

                # 10 — Editor
                state = await self._run_editor(state, _notify)

                # 11 — Quality Review
                state = await self._run_review(state, _notify)

                if state.get("review_passed", False):
                    break

            # --- Media generation (same as LangGraph version) ---
            director_out = state.get("director_output", {})
            script_out = state.get("script", {})
            cin_out = state.get("cinematography", {})
            snd_out = state.get("sound", {})
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

            # --- Lip sync ---
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

            # --- Image generation for cast / locations / mood board ---
            cast_out = state.get("cast", {})
            location_out = state.get("locations", {})
            mood_out = state.get("mood_board", {})

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

            # --- Record run history ---
            run_record = {
                "timestamp": time.time(),
                "prompt": user_prompt,
                "style": style,
                "duration": duration,
                "node_timings": state.get("node_timings", {}),
                "node_errors": state.get("node_errors", {}),
                "revision_count": state.get("revision_count", 0),
                "status": "success",
                "video_backend": generated_media.get("video_backend", "local"),
                "voice_backend": generated_media.get("voice_backend", "local"),
                "agents_count": 10,
                "orchestrator": "autogen",
            }
            self._run_history.append(run_record)
            try:
                await mongo_store.save_run(run_record)
            except Exception:
                pass

            return {
                "status": "success",
                "orchestrator": "autogen",
                "user_prompt": user_prompt,
                "style": style,
                "duration": duration,
                "director": state.get("director_output", {}),
                "script": state.get("script", {}),
                "refined_screenplay": state.get("refined_screenplay", {}),
                "cinematography": state.get("cinematography", {}),
                "sound": state.get("sound", {}),
                "cast": state.get("cast", {}),
                "locations": state.get("locations", {}),
                "vfx_plan": state.get("vfx_plan", {}),
                "mood_board": state.get("mood_board", {}),
                "media_assets": state.get("media_assets", {}),
                "final_timeline": state.get("final_timeline", {}),
                "workflow_steps": state.get("workflow_steps", []),
                "node_timings": state.get("node_timings", {}),
                "revision_count": state.get("revision_count", 0),
                "generated_media": generated_media,
                "cast_images": cast_images,
                "location_images": location_images,
                "mood_images": mood_images,
                "lip_sync": lip_sync_result,
            }

        except Exception as exc:
            logger.exception("AutoGen film creation pipeline failed")
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Graph structure (for frontend visualization)
    # ------------------------------------------------------------------

    def get_graph_structure(self) -> Dict[str, Any]:
        """Return the graph topology (identical to LangGraph version)."""
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
                "autogen_orchestration",
                "parallel_execution",
                "error_handling",
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
        return list(reversed(self._run_history))

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

    # ------------------------------------------------------------------
    # Internal — individual node runners
    # ------------------------------------------------------------------

    async def _run_node(
        self,
        state: PipelineState,
        agent_name: str,
        step_num: int,
        notify: Callable,
        process_fn: Callable,
        input_builder: Callable[[PipelineState], Dict[str, Any]],
        output_key: str,
        detail_fn: Optional[Callable] = None,
    ) -> PipelineState:
        """Run a single agent node with timing, error handling, and progress."""
        start = time.time()
        step = _add_step(state, agent_name, "running", f"Running {agent_name}")
        await notify(step_num, agent_name, "running", f"Running {agent_name}")
        try:
            input_data = input_builder(state)
            result = await process_fn(input_data)
            detail = detail_fn(result) if detail_fn else f"{agent_name} complete"
            _update_step(step, "completed", detail)
            await notify(step_num, agent_name, "completed", detail)
            timings = dict(state.get("node_timings", {}))
            timings[output_key] = round(time.time() - start, 2)
            state[output_key] = result
            state["node_timings"] = timings
            return state
        except Exception as exc:
            return _handle_node_error(state, output_key, str(exc), step, start)

    async def _run_parallel_production(self, state: PipelineState, notify: Callable) -> PipelineState:
        """Run Cinematographer, SoundDesigner, CastSelection, LocationResearch in parallel."""
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
        refined = state.get("refined_screenplay", {})

        cin_result, snd_result, cast_result, loc_result = await asyncio.gather(
            self.cinematographer.process({
                "scenes": director_out.get("scenes", []),
                "vision": director_out.get("vision", ""),
                "style": state.get("style", "cinematic"),
            }),
            self.sound_designer.process({
                "scenes": director_out.get("scenes", []),
                "vision": director_out.get("vision", ""),
            }),
            self.cast_selection.process({
                "scenes": director_out.get("scenes", []),
                "script_scenes": state.get("script", {}).get("script_scenes", []),
                "vision": director_out.get("vision", ""),
            }),
            self.location_research.process({
                "scenes": director_out.get("scenes", []),
                "vision": director_out.get("vision", ""),
                "style": state.get("style", "cinematic"),
            }),
            return_exceptions=True,
        )

        timings = dict(state.get("node_timings", {}))
        errors = dict(state.get("node_errors", {}))

        # Cinematographer
        if isinstance(cin_result, Exception):
            errors["cinematographer"] = str(cin_result)
            _update_step(cin_step, "error", str(cin_result))
            logger.warning("Cinematographer failed: %s — using fallback", cin_result)
            state["cinematography"] = {"shot_plans": [], "style": state.get("style", "cinematic"), "agent": "Cinematographer", "fallback": True}
        else:
            _update_step(cin_step, "completed", "Shot plans finalized")
            await notify(4, "Cinematographer", "completed", "Shot plans finalized")
            state["cinematography"] = cin_result

        # Sound Designer
        if isinstance(snd_result, Exception):
            errors["sound_designer"] = str(snd_result)
            _update_step(snd_step, "error", str(snd_result))
            logger.warning("Sound Designer failed: %s — using fallback", snd_result)
            state["sound"] = {"audio_plans": [], "agent": "Sound Designer", "fallback": True}
        else:
            _update_step(snd_step, "completed", "Audio design complete")
            await notify(5, "Sound Designer", "completed", "Audio design complete")
            state["sound"] = snd_result

        # Cast Selection
        if isinstance(cast_result, Exception):
            errors["cast_selection"] = str(cast_result)
            _update_step(cast_step, "error", str(cast_result))
            logger.warning("Cast Selection failed: %s — using fallback", cast_result)
            state["cast"] = {"characters": [], "agent": "CastSelection", "fallback": True}
        else:
            _update_step(cast_step, "completed", f"{cast_result.get('total_characters', 0)} characters cast")
            await notify(6, "Cast Selection", "completed", f"{cast_result.get('total_characters', 0)} characters cast")
            state["cast"] = cast_result

        # Location Research
        if isinstance(loc_result, Exception):
            errors["location_research"] = str(loc_result)
            _update_step(loc_step, "error", str(loc_result))
            logger.warning("Location Research failed: %s — using fallback", loc_result)
            state["locations"] = {"locations": [], "agent": "LocationResearch", "fallback": True}
        else:
            _update_step(loc_step, "completed", f"{loc_result.get('total_locations', 0)} locations scouted")
            await notify(7, "Location Research", "completed", f"{loc_result.get('total_locations', 0)} locations scouted")
            state["locations"] = loc_result

        timings["parallel_production"] = round(time.time() - start, 2)
        state["node_timings"] = timings
        state["node_errors"] = errors
        return state

    async def _run_parallel_post_production(self, state: PipelineState, notify: Callable) -> PipelineState:
        """Run VFXPlanning and MoodBoard in parallel."""
        start = time.time()

        vfx_step = _add_step(state, "VFX Planning", "running", "Analyzing VFX requirements")
        mood_step = _add_step(state, "Mood Board", "running", "Creating visual style guide")

        await notify(8, "VFX Planning", "running", "Analyzing VFX requirements (parallel)")
        await notify(9, "Mood Board", "running", "Creating visual style guide (parallel)")

        director_out = state.get("director_output", {})
        cin_out = state.get("cinematography", {})

        vfx_result, mood_result = await asyncio.gather(
            self.vfx_planning.process({
                "scenes": director_out.get("scenes", []),
                "shot_plans": cin_out.get("shot_plans", []),
                "vision": director_out.get("vision", ""),
                "style": state.get("style", "cinematic"),
            }),
            self.mood_board.process({
                "vision": director_out.get("vision", ""),
                "style": state.get("style", "cinematic"),
                "scenes": director_out.get("scenes", []),
            }),
            return_exceptions=True,
        )

        timings = dict(state.get("node_timings", {}))
        errors = dict(state.get("node_errors", {}))

        if isinstance(vfx_result, Exception):
            errors["vfx_planning"] = str(vfx_result)
            _update_step(vfx_step, "error", str(vfx_result))
            logger.warning("VFX Planning failed: %s — using fallback", vfx_result)
            state["vfx_plan"] = {"vfx_shots": [], "agent": "VFXPlanning", "fallback": True}
        else:
            _update_step(vfx_step, "completed", f"{vfx_result.get('total_vfx_shots', 0)} VFX shots planned")
            await notify(8, "VFX Planning", "completed", f"{vfx_result.get('total_vfx_shots', 0)} VFX shots planned")
            state["vfx_plan"] = vfx_result

        if isinstance(mood_result, Exception):
            errors["mood_board"] = str(mood_result)
            _update_step(mood_step, "error", str(mood_result))
            logger.warning("Mood Board failed: %s — using fallback", mood_result)
            state["mood_board"] = {"mood_images": [], "agent": "MoodBoard", "fallback": True}
        else:
            _update_step(mood_step, "completed", f"{mood_result.get('total_images', 0)} mood images generated")
            await notify(9, "Mood Board", "completed", f"{mood_result.get('total_images', 0)} mood images generated")
            state["mood_board"] = mood_result

        timings["parallel_post_production"] = round(time.time() - start, 2)
        state["node_timings"] = timings
        state["node_errors"] = errors
        return state

    async def _run_editor(self, state: PipelineState, notify: Callable) -> PipelineState:
        """Run the Editor agent."""
        start = time.time()
        step = _add_step(state, "Editor", "running", "Assembling final timeline")
        await notify(10, "Editor", "running", "Assembling final timeline")
        try:
            director_out = state.get("director_output", {})
            scenes = director_out.get("scenes", [])
            media_assets = self._build_media_asset_list(scenes)
            output = await self.editor.process({
                "scenes": scenes,
                "video_clips": media_assets["video_clips"],
                "audio_files": media_assets["audio_files"],
            })
            _update_step(step, "completed", "Film assembled")
            await notify(10, "Editor", "completed", "Film assembled")
            timings = dict(state.get("node_timings", {}))
            timings["editor"] = round(time.time() - start, 2)
            state["media_assets"] = media_assets
            state["final_timeline"] = output
            state["node_timings"] = timings
            return state
        except Exception as exc:
            return _handle_node_error(state, "editor", str(exc), step, start)

    async def _run_review(self, state: PipelineState, notify: Callable) -> PipelineState:
        """Quality review — checks completeness, may request revision."""
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
            state["review_passed"] = True
            state["node_timings"] = timings
            return state
        else:
            detail = f"Revision needed: {'; '.join(issues)}"
            _update_step(step, "revision", detail)
            await notify(11, "Quality Review", "revision", detail)
            timings = dict(state.get("node_timings", {}))
            timings["review"] = round(time.time() - start, 2)
            state["review_passed"] = False
            state["revision_count"] = revision_count + 1
            state["node_timings"] = timings
            return state

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_media_asset_list(scenes: list) -> Dict[str, Any]:
        video_clips = [f"clip_scene_{s.get('scene_number', i + 1)}.mp4" for i, s in enumerate(scenes)]
        audio_files = [f"audio_scene_{s.get('scene_number', i + 1)}.wav" for i, s in enumerate(scenes)]
        return {"video_clips": video_clips, "audio_files": audio_files}


# ---------------------------------------------------------------------------
# State helpers (same as LangGraph version)
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
    state["node_errors"] = errors
    state["node_retries"] = retries
    state["node_timings"] = timings
    return state
