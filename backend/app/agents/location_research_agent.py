"""
Location Research Agent - Scouts filming locations

Suggests locations with:
- Geographic descriptions and coordinates
- Logistics and permit information
- Cost estimates and weather considerations
- Alternative location suggestions
- Image prompts for location reference generation
"""
import json
import logging
from typing import Dict, Any, Optional, List

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an experienced location scout who finds ideal filming locations.
You consider aesthetics, logistics, permits, weather, and budget.
You suggest realistic locations with practical production notes.
Always respond with valid JSON only."""


class LocationResearchAgent(BaseAgent):
    """Suggests filming locations with geographic descriptions, budgets, and logistics."""

    def __init__(self, model: str = "claude-opus-4-6", anthropic_api_key: str = "", llm: Optional[LLMService] = None):
        """Initialize with model/API key (preferred) or LLMService instance.
        
        Args:
            model: LLM model name (default: claude-opus-4-6)
            anthropic_api_key: Anthropic API key if needed
            llm: Optional LLMService instance (overrides model/key if provided)
        """
        super().__init__(name="LocationResearch", model=model, anthropic_api_key=anthropic_api_key, llm=llm)

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
        """Scout locations for all scenes in the film."""
        scenes = input_data.get("scenes", [])
        vision = input_data.get("vision", "")
        style = input_data.get("style", "cinematic")

        logger.info("LocationResearch scouting for %d scenes...", len(scenes))

        locations = await self._scout_locations(scenes, vision, style)

        result = {
            "locations": locations,
            "total_locations": len(locations),
            "logistics_summary": self._build_logistics(locations),
            "agent": self.name,
        }
        self.add_to_memory(result)
        return result

    async def _scout_locations(
        self, scenes: List[Dict[str, Any]], vision: str, style: str
    ) -> List[Dict[str, Any]]:
        """Scout filming locations for all scenes."""
        scene_descs = "; ".join(
            f"Scene {s.get('scene_number')}: {s.get('description', '')}" for s in scenes
        )
        user_msg = (
            f"Director's vision: {vision}\nVisual style: {style}\n\n"
            f"Scenes to find locations for: {scene_descs}\n\n"
            "Return a JSON array of location objects, one per scene. Each object must have:\n"
            "- scene_number (int)\n"
            "- location_name (string, specific place name)\n"
            "- type (string: interior/exterior/both)\n"
            "- geographic_description (string, detailed geography and surroundings)\n"
            "- visual_description (string, detailed description for reference image generation)\n"
            "- image_prompt (string, detailed prompt for generating location reference image)\n"
            "- city_country (string)\n"
            "- permit_required (boolean)\n"
            "- estimated_cost (string, e.g. '$5,000/day')\n"
            "- logistics (string, transportation and access notes)\n"
            "- alternatives (array of 2 alternative location name strings)\n"
            "- weather_considerations (string)"
        )
        raw = await self._ask_claude(user_msg, SYSTEM_PROMPT, max_tokens=2048)
        try:
            start, end = raw.find("["), raw.rfind("]") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("LocationResearch: parse failed, using fallback")
            return [
                {
                    "scene_number": s.get("scene_number", i + 1),
                    "location_name": f"Studio Lot {i + 1}",
                    "type": "interior",
                    "geographic_description": f"Controlled studio environment for {style} production",
                    "visual_description": f"Professional film studio with {style} set dressing",
                    "image_prompt": f"Professional film set for {style} movie, studio lighting, detailed production design",
                    "city_country": "Los Angeles, USA",
                    "permit_required": False,
                    "estimated_cost": "$2,000/day",
                    "logistics": "Standard studio access, crew parking available",
                    "alternatives": ["Backlot A", "Green screen stage"],
                    "weather_considerations": "Indoor, no weather concerns",
                }
                for i, s in enumerate(scenes)
            ]

    @staticmethod
    def _build_logistics(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build logistics summary across all locations."""
        total_cost = 0
        permits_needed = 0
        
        for loc in locations:
            cost_str = loc.get("estimated_cost", "$0/day").replace("$", "").replace(",", "").split("/")[0]
            try:
                total_cost += int(cost_str)
            except Exception:
                pass
            
            if loc.get("permit_required"):
                permits_needed += 1

        return {
            "total_locations": len(locations),
            "permits_required": permits_needed,
            "estimated_daily_cost": f"${total_cost:,}/day",
            "logistics_complexity": "high" if permits_needed > 0 else "medium",
        }
