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

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class AgentOrchestrator:
    """Orchestrates the full film production pipeline across all AI agents."""

    def __init__(self, model: str = "claude-opus-4-6", anthropic_api_key: str = ""):
        self.director = DirectorAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.screenwriter = ScreenwriterAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.cinematographer = CinematographerAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.sound_designer = SoundDesignerAgent(model=model, anthropic_api_key=anthropic_api_key)
        self.editor = EditorAgent(model=model, anthropic_api_key=anthropic_api_key)
        logger.info("Agent Orchestrator initialised with 5 agents")

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
                    "total_steps": 5,
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

            # Step 3: Cinematographer — shot plans + image prompts
            await _notify(3, "Cinematographer", "running", "Planning shots and image prompts")
            cinematographer_output = await self.cinematographer.process({
                "scenes": director_output["scenes"],
                "style": style,
                "vision": director_output["vision"],
            })
            await _notify(3, "Cinematographer", "completed", "Shot plans finalized")

            # Step 4: Sound Designer — music + SFX + voiceover guidance
            await _notify(4, "SoundDesigner", "running", "Designing audio and sound effects")
            sound_output = await self.sound_designer.process({
                "script_scenes": screenwriter_output["script_scenes"],
                "style": style,
                "vision": director_output["vision"],
            })
            await _notify(4, "SoundDesigner", "completed", "Audio design complete")

            # Step 5: Editor — assemble timeline
            await _notify(5, "Editor", "running", "Assembling final timeline")
            media_assets = self._build_media_asset_list(director_output["scenes"])
            editor_output = await self.editor.process({
                "scenes": director_output["scenes"],
                "video_clips": media_assets["video_clips"],
                "audio_files": media_assets["audio_files"],
            })
            await _notify(5, "Editor", "completed", "Film assembled")

            return {
                "status": "success",
                "user_prompt": user_prompt,
                "style": style,
                "duration": duration,
                "director": director_output,
                "script": screenwriter_output,
                "cinematography": cinematographer_output,
                "sound": sound_output,
                "media_assets": media_assets,
                "final_timeline": editor_output,
                "workflow_steps": [
                    {"agent": "Director", "status": "completed"},
                    {"agent": "Screenwriter", "status": "completed"},
                    {"agent": "Cinematographer", "status": "completed"},
                    {"agent": "SoundDesigner", "status": "completed"},
                    {"agent": "Editor", "status": "completed"},
                ],
            }

        except Exception as e:
            logger.error(f"Film creation error: {str(e)}")
            if on_progress:
                await on_progress({"step": 0, "total_steps": 5, "agent": "System", "status": "error", "detail": str(e)})
            return {"status": "error", "error": str(e), "user_prompt": user_prompt}

    def _build_media_asset_list(self, scenes: list) -> Dict[str, Any]:
        return {
            "video_clips": [f"scene_{s.get('scene_number', i + 1)}_video.mp4" for i, s in enumerate(scenes)],
            "audio_files": [f"scene_{s.get('scene_number', i + 1)}_audio.mp3" for i, s in enumerate(scenes)],
            "scene_count": len(scenes),
        }

    def get_agent_status(self) -> Dict[str, Any]:
        agents = [self.director, self.screenwriter, self.cinematographer, self.sound_designer, self.editor]
        return {a.name: {"memory_items": len(a.memory)} for a in agents}

    def clear_all_memory(self):
        for agent in [self.director, self.screenwriter, self.cinematographer, self.sound_designer, self.editor]:
            agent.clear_memory()
