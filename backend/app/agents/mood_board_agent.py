"""
Mood Board Agent - Creates visual style guides

Generates:
- Mood board image descriptions (color palette, texture, lighting, composition, etc.)
- Style guide with art direction notes
- Color palettes and reference materials
- Image prompts for mood board generation
"""
import json
import logging
from typing import Dict, Any, Optional, List

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a creative director and visual stylist who builds mood boards.
You describe visual atmospheres, color palettes, textures, and artistic references.
You create detailed image prompts that capture the film's aesthetic and mood.
Always respond with valid JSON only."""


class MoodBoardAgent(BaseAgent):
    """Generates mood board descriptions, color palettes, and image prompts."""

    def __init__(self, model: str = "claude-opus-4-6", anthropic_api_key: str = "", llm: Optional[LLMService] = None):
        """Initialize with model/API key (preferred) or LLMService instance.
        
        Args:
            model: LLM model name (default: claude-opus-4-6)
            anthropic_api_key: Anthropic API key if needed
            llm: Optional LLMService instance (overrides model/key if provided)
        """
        super().__init__(name="MoodBoard", model=model, anthropic_api_key=anthropic_api_key, llm=llm)

    @classmethod
    def from_settings(cls, **kwargs):
        """Create instance from app settings."""
        from app.core.config import settings
        return cls(
            model=kwargs.get("model", "claude-opus-4-6"),
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            llm=kwargs.get("llm"),
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mood board and style guide for the film."""
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
        """Generate 8 mood board image descriptions covering different visual aspects."""
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
        raw = await self._ask_claude(user_msg, SYSTEM_PROMPT, max_tokens=2048)
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
        """Create a comprehensive style guide."""
        user_msg = (
            f"Director's vision: {vision}\nVisual style: {style}\n\n"
            "Create a style guide for this film. Return a JSON object with:\n"
            "- title (string, style guide title)\n"
            "- primary_aesthetic (string, 1-2 sentences describing the main look)\n"
            "- color_theory (string, explanation of color choices)\n"
            "- influences (array of strings, films/artists that inspire this style)\n"
            "- cinematography_notes (string, lighting and camera movement philosophy)\n"
            "- production_design_notes (string, set and costume design direction)\n"
            "- tone_summary (string, emotional tone of the film)"
        )
        raw = await self._ask_claude(user_msg, SYSTEM_PROMPT, max_tokens=1024)
        try:
            start, end = raw.find("{"), raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("MoodBoard: style guide parse failed, using fallback")
            return {
                "title": f"{style.title()} Style Guide",
                "primary_aesthetic": vision,
                "color_theory": f"Colors chosen to support {style} aesthetic",
                "influences": ["Contemporary cinema"],
                "cinematography_notes": f"{style} cinematography approach",
                "production_design_notes": "Professional production design",
                "tone_summary": "Professional and polished",
            }
