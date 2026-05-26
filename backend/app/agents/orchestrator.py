"""
Agent Orchestrator — LangGraph-based workflow for the film production pipeline.

Uses a directed graph to coordinate agents:
  Director → Screenwriter → Cinematographer → SoundDesigner → Editor
"""
from typing import Dict, Any, Optional, Callable, Awaitable, TypedDict
import logging

from langgraph.graph import StateGraph, END

from app.services.llm_service import LLMService, llm_service
from .director_agent import DirectorAgent
from .screenwriter_agent import ScreenwriterAgent
from .cinematographer_agent import CinematographerAgent
from .sound_designer_agent import SoundDesignerAgent
from .editor_agent import EditorAgent

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


# ---------------------------------------------------------------------------
# Shared pipeline state flowing through the graph
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    user_prompt: str
    style: str
    duration: int
    director: Dict[str, Any]
    script: Dict[str, Any]
    cinematography: Dict[str, Any]
    sound: Dict[str, Any]
    media_assets: Dict[str, Any]
    final_timeline: Dict[str, Any]
    error: str


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class AgentOrchestrator:
    """LangGraph orchestrator for the autonomous film pipeline."""

    def __init__(self, llm: Optional[LLMService] = None):
        self._llm = llm or llm_service
        self.director = DirectorAgent(llm=self._llm)
        self.screenwriter = ScreenwriterAgent(llm=self._llm)
        self.cinematographer = CinematographerAgent(llm=self._llm)
        self.sound_designer = SoundDesignerAgent(llm=self._llm)
        self.editor = EditorAgent(llm=self._llm)
        logger.info("Agent Orchestrator initialised with 5 agents (LangGraph, backend=%s)", self._llm.backend)

    @classmethod
    def from_settings(cls):
        return cls(llm=llm_service)

    # ------------------------------------------------------------------

    async def create_film(
        self,
        user_prompt: str,
        style: str = "cinematic",
        duration: int = 30,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Build and run the LangGraph pipeline."""

        async def _notify(step: int, agent: str, status: str, detail: str = ""):
            if on_progress:
                await on_progress({
                    "step": step,
                    "total_steps": 5,
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
            }
            final_state = await graph.ainvoke(initial_state)

            if final_state.get("error"):
                return {"status": "error", "error": final_state["error"]}

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
                "workflow_steps": [
                    {"agent": "Director", "status": "completed"},
                    {"agent": "Screenwriter", "status": "completed"},
                    {"agent": "Cinematographer", "status": "completed"},
                    {"agent": "SoundDesigner", "status": "completed"},
                    {"agent": "Editor", "status": "completed"},
                ],
            }
        except Exception as exc:
            logger.exception("Film creation pipeline failed")
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self, notify: Callable) -> Any:
        """Construct the LangGraph state graph."""
        orchestrator = self

        async def director_node(state: PipelineState) -> PipelineState:
            await notify(1, "Director", "running", "Creating creative vision and scene breakdown")
            output = await orchestrator.director.process({
                "prompt": state["user_prompt"],
                "style": state.get("style", "cinematic"),
                "duration": state.get("duration", 30),
            })
            await notify(1, "Director", "completed", f"{len(output.get('scenes', []))} scenes planned")
            return {**state, "director": output}

        async def screenwriter_node(state: PipelineState) -> PipelineState:
            await notify(2, "Screenwriter", "running", "Writing script and dialogue")
            director_out = state.get("director", {})
            output = await orchestrator.screenwriter.process({
                "vision": director_out.get("vision", ""),
                "scenes": director_out.get("scenes", []),
            })
            await notify(2, "Screenwriter", "completed", "Script and dialogue written")
            return {**state, "script": output}

        async def cinematographer_node(state: PipelineState) -> PipelineState:
            await notify(3, "Cinematographer", "running", "Planning shots and image prompts")
            director_out = state.get("director", {})
            output = await orchestrator.cinematographer.process({
                "scenes": director_out.get("scenes", []),
                "style": state.get("style", "cinematic"),
                "vision": director_out.get("vision", ""),
            })
            await notify(3, "Cinematographer", "completed", "Shot plans finalized")
            return {**state, "cinematography": output}

        async def sound_designer_node(state: PipelineState) -> PipelineState:
            await notify(4, "SoundDesigner", "running", "Designing audio and sound effects")
            script_out = state.get("script", {})
            director_out = state.get("director", {})
            output = await orchestrator.sound_designer.process({
                "script_scenes": script_out.get("script_scenes", []),
                "style": state.get("style", "cinematic"),
                "vision": director_out.get("vision", ""),
            })
            await notify(4, "SoundDesigner", "completed", "Audio design complete")
            return {**state, "sound": output}

        async def editor_node(state: PipelineState) -> PipelineState:
            await notify(5, "Editor", "running", "Assembling final timeline")
            director_out = state.get("director", {})
            scenes = director_out.get("scenes", [])
            media_assets = self._build_media_asset_list(scenes)
            output = await orchestrator.editor.process({
                "scenes": scenes,
                "video_clips": media_assets["video_clips"],
                "audio_files": media_assets["audio_files"],
            })
            await notify(5, "Editor", "completed", "Film assembled")
            return {**state, "media_assets": media_assets, "final_timeline": output}

        graph = StateGraph(PipelineState)
        graph.add_node("director", director_node)
        graph.add_node("screenwriter", screenwriter_node)
        graph.add_node("cinematographer", cinematographer_node)
        graph.add_node("sound_designer", sound_designer_node)
        graph.add_node("editor", editor_node)

        graph.set_entry_point("director")
        graph.add_edge("director", "screenwriter")
        graph.add_edge("screenwriter", "cinematographer")
        graph.add_edge("cinematographer", "sound_designer")
        graph.add_edge("sound_designer", "editor")
        graph.add_edge("editor", END)

        return graph.compile()

    # ------------------------------------------------------------------

    @staticmethod
    def _build_media_asset_list(scenes: list) -> Dict[str, Any]:
        video_clips = [f"clip_scene_{s.get('scene_number', i + 1)}.mp4" for i, s in enumerate(scenes)]
        audio_files = [f"audio_scene_{s.get('scene_number', i + 1)}.wav" for i, s in enumerate(scenes)]
        return {"video_clips": video_clips, "audio_files": audio_files}

    def clear_all_memory(self):
        for agent in [self.director, self.screenwriter, self.cinematographer, self.sound_designer, self.editor]:
            agent.clear_memory()
