"""
Agent Orchestrator - Coordinates all AI agents
"""
from typing import Dict, Any, Optional, Callable, Awaitable
import logging

from .director_agent import DirectorAgent
from .screenwriter_agent import ScreenwriterAgent
from .cinematographer_agent import CinematographerAgent
from .sound_designer_agent import SoundDesignerAgent
from .editor_agent import EditorAgent
from .cast_selection_agent import CastSelectionAgent
from .location_research_agent import LocationResearchAgent
from .mood_board_agent import MoodBoardAgent
from .screenplay_refinement_agent import ScreenplayRefinementAgent
from .vfx_planning_agent import VFXPlanningAgent

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]

TOTAL_STEPS = 10


class AgentOrchestrator:
    """Orchestrates the full film production pipeline across all 10 AI agents."""

    def __init__(self, model: str = "claude-opus-4-6", anthropic_api_key: str = ""):
        self.director = DirectorAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.screenwriter = ScreenwriterAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.screenplay_refiner = ScreenplayRefinementAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.cinematographer = CinematographerAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.mood_board = MoodBoardAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.cast_selection = CastSelectionAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.location_research = LocationResearchAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.sound_designer = SoundDesignerAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.vfx_planner = VFXPlanningAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.editor = EditorAgent(model=model, anthropic_api_key=anthropic_api_key)
        logger.info("Agent Orchestrator initialised with %d agents", TOTAL_STEPS)

    @classmethod
    def from_settings(cls):
        from app.core.config import settings
        return cls(anthropic_api_key=settings.ANTHROPIC_API_KEY)

    async def create_film(
        self,
        user_prompt: str,
        style: str = "cinematic",
        duration: int = 30,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Run the full autonomous film creation pipeline."""
        logger.info(f"Starting film creation: {user_prompt[:60]}...")

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
            # Step 1: Director — creative vision + scene breakdown
            await _notify(1, "Director", "running", "Creating creative vision and scene breakdown")
            director_output = await self.director.process({
                "prompt": user_prompt, "style": style, "duration": duration
            })
            await _notify(1, "Director", "completed", f"{len(director_output.get('scenes', []))} scenes planned")

            # Step 2: Screenwriter — script + dialogue
            await _notify(2, "Screenwriter", "running", "Writing script and dialogue")
            screenwriter_output = await self.screenwriter.process({
                "vision": director_output["vision"],
                "scenes": director_output["scenes"],
            })
            await _notify(2, "Screenwriter", "completed", "Script and dialogue written")

            # Step 3: Screenplay Refinement — polish and continuity
            await _notify(3, "ScreenplayRefiner", "running", "Refining screenplay for continuity")
            refinement_output = await self.screenplay_refiner.process({
                "script_scenes": screenwriter_output.get("script_scenes", []),
                "vision": director_output["vision"],
            })
            await _notify(3, "ScreenplayRefiner", "completed", "Screenplay refined")

            # Step 4: Cinematographer — shot plans + image prompts
            await _notify(4, "Cinematographer", "running", "Planning shots and image prompts")
            cinematographer_output = await self.cinematographer.process({
                "scenes": director_output["scenes"],
                "style": style,
                "vision": director_output["vision"],
            })
            await _notify(4, "Cinematographer", "completed", "Shot plans finalized")

            # Step 5: Mood Board — visual references and color palettes
            await _notify(5, "MoodBoard", "running", "Creating mood board and color palettes")
            mood_output = await self.mood_board.process({
                "scenes": director_output["scenes"],
                "style": style,
                "vision": director_output["vision"],
            })
            await _notify(5, "MoodBoard", "completed", "Mood board created")

            # Step 6: Cast Selection — character profiles and casting
            await _notify(6, "CastSelection", "running", "Selecting cast and character profiles")
            cast_output = await self.cast_selection.process({
                "scenes": director_output["scenes"],
                "script_scenes": screenwriter_output.get("script_scenes", []),
                "vision": director_output["vision"],
            })
            await _notify(6, "CastSelection", "completed", "Cast selected")

            # Step 7: Location Research — setting research and references
            await _notify(7, "LocationResearch", "running", "Researching locations and settings")
            location_output = await self.location_research.process({
                "scenes": director_output["scenes"],
                "style": style,
                "vision": director_output["vision"],
            })
            await _notify(7, "LocationResearch", "completed", "Locations researched")

            # Step 8: Sound Designer — music + SFX + voiceover guidance
            await _notify(8, "SoundDesigner", "running", "Designing audio and sound effects")
            sound_output = await self.sound_designer.process({
                "script_scenes": screenwriter_output["script_scenes"],
                "style": style,
                "vision": director_output["vision"],
            })
            await _notify(8, "SoundDesigner", "completed", "Audio design complete")

            # Step 9: VFX Planning — visual effects breakdown
            await _notify(9, "VFXPlanner", "running", "Planning visual effects")
            vfx_output = await self.vfx_planner.process({
                "scenes": director_output["scenes"],
                "style": style,
                "vision": director_output["vision"],
            })
            await _notify(9, "VFXPlanner", "completed", "VFX plan complete")

            # Step 10: Editor — assemble timeline
            await _notify(10, "Editor", "running", "Assembling final timeline")
            media_assets = self._build_media_asset_list(director_output["scenes"])
            editor_output = await self.editor.process({
                "scenes": director_output["scenes"],
                "video_clips": media_assets["video_clips"],
                "audio_files": media_assets["audio_files"],
            })
            await _notify(10, "Editor", "completed", "Film assembled")

            return {
                "status": "success",
                "user_prompt": user_prompt,
                "style": style,
                "duration": duration,
                "director": director_output,
                "script": screenwriter_output,
                "screenplay_refinement": refinement_output,
                "cinematography": cinematographer_output,
                "mood_board": mood_output,
                "cast_selection": cast_output,
                "location_research": location_output,
                "sound": sound_output,
                "vfx_planning": vfx_output,
                "media_assets": media_assets,
                "final_timeline": editor_output,
                "workflow_steps": [
                    {"agent": "Director", "status": "completed"},
                    {"agent": "Screenwriter", "status": "completed"},
                    {"agent": "ScreenplayRefiner", "status": "completed"},
                    {"agent": "Cinematographer", "status": "completed"},
                    {"agent": "MoodBoard", "status": "completed"},
                    {"agent": "CastSelection", "status": "completed"},
                    {"agent": "LocationResearch", "status": "completed"},
                    {"agent": "SoundDesigner", "status": "completed"},
                    {"agent": "VFXPlanner", "status": "completed"},
                    {"agent": "Editor", "status": "completed"},
                ],
            }

        except Exception as e:
            logger.error(f"Film creation error: {str(e)}")
            if on_progress:
                await on_progress({"step": 0, "total_steps": TOTAL_STEPS, "agent": "System", "status": "error", "detail": str(e)})
            return {"status": "error", "error": str(e), "user_prompt": user_prompt}

    def _build_media_asset_list(self, scenes: list) -> Dict[str, Any]:
        return {
            "video_clips": [f"scene_{s.get('scene_number', i + 1)}_video.mp4" for i, s in enumerate(scenes)],
            "audio_files": [f"scene_{s.get('scene_number', i + 1)}_audio.mp3" for i, s in enumerate(scenes)],
            "scene_count": len(scenes),
        }

    @property
    def all_agents(self) -> list:
        return [
            self.director, self.screenwriter, self.screenplay_refiner,
            self.cinematographer, self.mood_board, self.cast_selection,
            self.location_research, self.sound_designer, self.vfx_planner,
            self.editor,
        ]

    def get_agent_status(self) -> Dict[str, Any]:
        return {a.name: {"memory_items": len(a.memory)} for a in self.all_agents}

    def clear_all_memory(self):
        for agent in self.all_agents:
            agent.clear_memory()
