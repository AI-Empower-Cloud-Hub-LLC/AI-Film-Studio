"""
Screenplay Refinement Agent — Polish and format the screenplay.
Adds camera directions, production notes, and professional formatting.
"""
import json
from typing import Dict, Any, Optional
import logging

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a veteran screenplay editor who polishes scripts to professional standards.
You refine dialogue, add precise camera directions (e.g. CLOSE-UP, DOLLY, STEADICAM),
insert production notes, and ensure proper screenplay format.
Always respond with valid JSON only."""


class ScreenplayRefinementAgent(BaseAgent):
    """Refines raw scripts into polished, production-ready screenplays."""

    def __init__(self, llm: Optional[LLMService] = None):
        super().__init__(name="ScreenplayRefinement", llm=llm)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        script_scenes = input_data.get("script_scenes", [])
        vision = input_data.get("vision", "")
        style = input_data.get("style", "cinematic")

        logger.info("ScreenplayRefinement polishing %d scenes...", len(script_scenes))

        refined_scenes = []
        for scene in script_scenes:
            refined_scenes.append(await self._refine_scene(scene, vision, style))

        result = {
            "refined_scenes": refined_scenes,
            "total_scenes": len(refined_scenes),
            "format": "professional_screenplay",
            "agent": self.name,
        }
        self.add_to_memory(result)
        return result

    async def _refine_scene(self, scene: Dict[str, Any], vision: str, style: str) -> Dict[str, Any]:
        user_msg = (
            f"Director's vision: {vision}\nVisual style: {style}\n\n"
            f"Scene {scene.get('scene_number')}: {scene.get('description', '')}\n"
            f"Original narration: {scene.get('narration', '')}\n"
            f"Original dialogue: {json.dumps(scene.get('dialogue', []))}\n"
            f"Visual description: {scene.get('visual_description', '')}\n\n"
            "Return a JSON object with:\n"
            "- scene_number (int)\n"
            "- slug_line (string, e.g. 'INT. LABORATORY - NIGHT')\n"
            "- action_lines (string, refined action/description)\n"
            "- dialogue (array of {character, parenthetical, line})\n"
            "- camera_directions (array of strings, e.g. 'CLOSE-UP on face')\n"
            "- transitions (string, e.g. 'CUT TO:', 'DISSOLVE TO:')\n"
            "- production_notes (array of strings, practical notes for crew)\n"
            "- polished_narration (string, refined voiceover text)"
        )
        raw = await self._ask_llm(user_msg, SYSTEM_PROMPT, max_tokens=1024)
        try:
            start, end = raw.find("{"), raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("ScreenplayRefinement: parse failed for scene %s", scene.get("scene_number"))
            return {
                "scene_number": scene.get("scene_number", 1),
                "slug_line": f"INT. LOCATION - DAY",
                "action_lines": scene.get("description", ""),
                "dialogue": scene.get("dialogue", []),
                "camera_directions": [f"{scene.get('shot_type', 'MEDIUM').upper()} SHOT"],
                "transitions": "CUT TO:",
                "production_notes": ["Standard setup required"],
                "polished_narration": scene.get("narration", ""),
            }
