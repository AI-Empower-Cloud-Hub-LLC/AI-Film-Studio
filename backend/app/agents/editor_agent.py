"""
Editor Agent - Video Assembly & Post-Production
"""
from typing import Dict, Any, List, Optional
import logging

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EditorAgent(BaseAgent):
    """Editor agent for video assembly and post-production"""

    def __init__(self, llm: Optional[LLMService] = None):
        super().__init__(name="Editor", llm=llm)
        self.transitions = ["fade", "cut", "dissolve", "wipe"]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        scenes = input_data.get("scenes", [])
        audio_files = input_data.get("audio_files", [])
        video_clips = input_data.get("video_clips", [])

        logger.info("Editor assembling %d scenes", len(scenes))

        timeline = await self._create_timeline(scenes, video_clips, audio_files)
        timeline_with_transitions = self._add_transitions(timeline)
        final_timeline = self._apply_effects(timeline_with_transitions)

        result = {
            "timeline": final_timeline,
            "total_duration": sum(scene.get("duration", 0) for scene in scenes),
            "scenes_count": len(scenes),
            "agent": self.name,
        }

        self.add_to_memory(result)
        return result

    async def _create_timeline(
        self,
        scenes: List[Dict[str, Any]],
        video_clips: List[str],
        audio_files: List[str],
    ) -> List[Dict[str, Any]]:
        timeline = []
        current_time = 0

        for idx, scene in enumerate(scenes):
            timeline_entry = {
                "scene_number": scene.get("scene_number", idx + 1),
                "start_time": current_time,
                "end_time": current_time + scene.get("duration", 10),
                "duration": scene.get("duration", 10),
                "video_clip": video_clips[idx] if idx < len(video_clips) else None,
                "audio_track": audio_files[idx] if idx < len(audio_files) else None,
                "description": scene.get("description", ""),
            }
            timeline.append(timeline_entry)
            current_time += scene.get("duration", 10)

        return timeline

    def _add_transitions(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for idx in range(len(timeline) - 1):
            timeline[idx]["transition_out"] = self._select_transition(
                timeline[idx], timeline[idx + 1]
            )
        return timeline

    def _select_transition(
        self, current_scene: Dict[str, Any], next_scene: Dict[str, Any]
    ) -> str:
        if "emotional" in current_scene.get("description", "").lower():
            return "fade"
        elif "action" in current_scene.get("description", "").lower():
            return "cut"
        else:
            return "dissolve"

    def _apply_effects(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for scene in timeline:
            scene["effects"] = {
                "color_grade": self._suggest_color_grade(scene),
                "visual_effects": self._suggest_vfx(scene),
                "audio_mix": {
                    "music_level": 0.6,
                    "dialogue_level": 0.9,
                    "sfx_level": 0.7,
                },
            }
        return timeline

    def _suggest_color_grade(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        description = scene.get("description", "").lower()
        if "dark" in description or "night" in description:
            return {"temperature": "cool", "contrast": "high", "saturation": 0.8}
        elif "bright" in description or "day" in description:
            return {"temperature": "warm", "contrast": "medium", "saturation": 1.1}
        else:
            return {"temperature": "neutral", "contrast": "medium", "saturation": 1.0}

    def _suggest_vfx(self, scene: Dict[str, Any]) -> List[str]:
        effects = []
        description = scene.get("description", "").lower()
        if "dramatic" in description:
            effects.append("lens_flare")
        if "rain" in description or "storm" in description:
            effects.append("particle_rain")
        if "dream" in description or "fantasy" in description:
            effects.append("gaussian_blur")
        return effects
