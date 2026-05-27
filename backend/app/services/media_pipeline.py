"""
Media Pipeline — generates video and voiceover for each scene after the LangGraph
agent pipeline produces scripts and shot plans.

Runs Runway video generation and ElevenLabs TTS in parallel per scene.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable

from app.services.runway_service import runway_service
from app.services.audio_generator import audio_generator

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class MediaPipeline:
    """Generates real video + voiceover for each scene."""

    async def generate_scene_media(
        self,
        scenes: List[Dict[str, Any]],
        shot_plans: List[Dict[str, Any]],
        script_scenes: List[Dict[str, Any]],
        audio_plans: List[Dict[str, Any]],
        style: str = "cinematic",
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Generate video clips and voiceovers for all scenes.

        Returns a dict with per-scene results for video and audio.
        """
        results: List[Dict[str, Any]] = []

        shot_by_scene = {p.get("scene_number"): p for p in shot_plans}
        script_by_scene = {s.get("scene_number"): s for s in script_scenes}
        audio_by_scene = {a.get("scene_number"): a for a in audio_plans}

        for scene in scenes:
            sn = scene.get("scene_number", 0)
            shot = shot_by_scene.get(sn, {})
            script = script_by_scene.get(sn, {})
            audio = audio_by_scene.get(sn, {})

            if on_progress:
                await on_progress({
                    "step": 7,
                    "total_steps": 8,
                    "agent": "Media Generator",
                    "status": "running",
                    "detail": f"Generating media for scene {sn}",
                })

            scene_result = await self._generate_scene(scene, shot, script, audio, style)
            results.append(scene_result)

        return {
            "scenes": results,
            "video_backend": "runway" if runway_service.is_configured else "local",
            "voice_backend": "elevenlabs" if audio_generator.is_elevenlabs_active else "local",
        }

    async def _generate_scene(
        self,
        scene: Dict[str, Any],
        shot: Dict[str, Any],
        script: Dict[str, Any],
        audio: Dict[str, Any],
        style: str,
    ) -> Dict[str, Any]:
        sn = scene.get("scene_number", 0)
        video_prompt = shot.get("image_generation_prompt", scene.get("visual_prompt", scene.get("description", "")))
        narration = script.get("narration", "")
        voice_type = audio.get("voice_type", "neutral")
        duration = scene.get("duration", 10)

        video_task = runway_service.generate_video(
            prompt=f"{video_prompt}. Style: {style}",
            duration=min(duration, 10),
            style=style,
        )

        audio_task = self._generate_voiceover(narration, voice_type) if narration else self._empty_audio()

        video_result, audio_result = await asyncio.gather(
            video_task, audio_task, return_exceptions=True,
        )

        if isinstance(video_result, Exception):
            logger.error("Video generation failed for scene %s: %s", sn, video_result)
            video_result = {"status": "error", "error": str(video_result)}
        if isinstance(audio_result, Exception):
            logger.error("Audio generation failed for scene %s: %s", sn, audio_result)
            audio_result = {"status": "error", "error": str(audio_result)}

        return {
            "scene_number": sn,
            "video": video_result,
            "audio": audio_result,
        }

    @staticmethod
    async def _generate_voiceover(text: str, voice_type: str) -> Dict[str, Any]:
        return await audio_generator.generate_voiceover(text=text, voice_type=voice_type)

    @staticmethod
    async def _empty_audio() -> Dict[str, Any]:
        return {"status": "skipped", "note": "No narration text for this scene"}


media_pipeline = MediaPipeline()
