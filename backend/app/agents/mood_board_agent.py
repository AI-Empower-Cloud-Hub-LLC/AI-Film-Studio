"""
Mood Board Agent — Generate mood board descriptions and visual style references.
Produces detailed image prompts for mood board generation.
"""
import json
from typing import Dict, Any, Optional, List
import logging

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a creative director who crafts compelling mood boards and visual
style guides for film productions. You describe color palettes, textures, compositions,
lighting references, and overall aesthetic — detailed enough for image generation.
Always respond with valid JSON only."""


class MoodBoardAgent(BaseAgent):
    """Generates mood board descriptions, color palettes, and image prompts."""

    def __init__(self, llm: Optional[LLMService] = None):
        super().__init__(name="MoodBoard", llm=llm)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        vision = input_data.get("vision", "")
        style = input_data.get("style", "cinematic")
        scenes = input_data.get("scenes", [])

        logger.info("MoodBoard generating visual style guide for %s style...", style)

        mood_images = await self._generate_mood_descriptions(vision, style, scenes)
        style_guide = await self._create_style_guide(vision, style)

        result = {
            "mood_images": mood_images,
            "style_guide": style_guide,
            "total_images": len(mood_images),
            "agent": self.name,
        }
        self.add_to_memory(result)
        return result

    async def _generate_mood_descriptions(
        self, vision: str, style: str, scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        scene_moods = ", ".join(s.get("mood", "neutral") for s in scenes[:5])
        user_msg = (
            f"Director's vision: {vision}\nVisual style: {style}\n"
            f"Scene moods: {scene_moods}\n\n"
            "Generate 8 mood board image descriptions. Return a JSON array of objects with:\n"
            "- id (int, 1-8)\n"
            "- title (string, short title like 'Color Palette Reference')\n"
            "- category (string: color_palette/texture/lighting/composition/atmosphere/character_look/set_design/typography)\n"
            "- description (string, what the image represents)\n"
            "- image_prompt (string, detailed prompt for image generation, 50+ words)\n"
            "- color_hex_codes (array of 3-5 hex color strings)\n"
            "- reference_notes (string, brief artistic reference)"
        )
        raw = await self._ask_llm(user_msg, SYSTEM_PROMPT, max_tokens=2048)
        try:
            start, end = raw.find("["), raw.rfind("]") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("MoodBoard: parse failed, using fallback")
            categories = [
                "color_palette", "texture", "lighting", "composition",
                "atmosphere", "character_look", "set_design", "typography",
            ]
            return [
                {
                    "id": i + 1,
                    "title": f"{cat.replace('_', ' ').title()} Reference",
                    "category": cat,
                    "description": f"{style.title()} {cat.replace('_', ' ')} reference",
                    "image_prompt": f"Professional {style} film mood board, {cat.replace('_', ' ')} reference, cinematic quality, award-winning photography, detailed, 8k",
                    "color_hex_codes": ["#1a1a2e", "#16213e", "#0f3460", "#e94560", "#533483"],
                    "reference_notes": f"Inspired by classic {style} cinema",
                }
                for i, cat in enumerate(categories)
            ]

    async def _create_style_guide(self, vision: str, style: str) -> Dict[str, Any]:
        user_msg = (
            f"Director's vision: {vision}\nVisual style: {style}\n\n"
            "Create a visual style guide. Return a JSON object with:\n"
            "- primary_colors (array of 3 hex strings)\n"
            "- accent_colors (array of 2 hex strings)\n"
            "- typography_style (string)\n"
            "- lighting_approach (string)\n"
            "- texture_keywords (array of 5 strings)\n"
            "- composition_rules (array of 3 strings)\n"
            "- reference_films (array of 3 film name strings)\n"
            "- overall_tone (string)"
        )
        raw = await self._ask_llm(user_msg, SYSTEM_PROMPT, max_tokens=1024)
        try:
            start, end = raw.find("{"), raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except Exception:
            return {
                "primary_colors": ["#1a1a2e", "#16213e", "#0f3460"],
                "accent_colors": ["#e94560", "#533483"],
                "typography_style": "Clean sans-serif with cinematic serifs for titles",
                "lighting_approach": f"Natural with {style} contrast",
                "texture_keywords": ["grain", "matte", "organic", "subtle", "refined"],
                "composition_rules": ["Rule of thirds", "Leading lines", "Symmetry for impact"],
                "reference_films": ["Blade Runner 2049", "The Grand Budapest Hotel", "Mad Max: Fury Road"],
                "overall_tone": f"Modern {style} with emotional depth",
            }
