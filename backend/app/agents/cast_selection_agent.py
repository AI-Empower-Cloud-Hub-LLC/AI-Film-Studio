"""
Cast Selection Agent - Identifies characters and generates casting suggestions

Generates:
- Character descriptions and archetypes
- Casting suggestions and budget estimates
- Wardrobe and appearance details
- Image prompts for character reference generation
"""
import json
import logging
from typing import Dict, Any, Optional, List

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a veteran casting director who analyzes scripts and suggests perfect casting.
You describe characters deeply, estimate budgets, and create detailed character briefs.
Always respond with valid JSON only."""


class CastSelectionAgent(BaseAgent):
    """Generates character descriptions, casting suggestions, and budget estimates."""

    def __init__(self, model: str = "claude-opus-4-6", anthropic_api_key: str = "", llm: Optional[LLMService] = None):
        """Initialize with model/API key (preferred) or LLMService instance.
        
        Args:
            model: LLM model name (default: claude-opus-4-6)
            anthropic_api_key: Anthropic API key if needed
            llm: Optional LLMService instance (overrides model/key if provided)
        """
        super().__init__(name="CastSelection", model=model, anthropic_api_key=anthropic_api_key, llm=llm)

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
        """Analyze script and generate character casting sheet."""
        script_scenes = input_data.get("script_scenes", [])
        vision = input_data.get("vision", "")
        style = input_data.get("style", "cinematic")

        logger.info("CastSelection analyzing %d scenes for characters...", len(script_scenes))

        characters = await self._identify_characters(script_scenes, vision, style)

        result = {
            "characters": characters,
            "total_characters": len(characters),
            "casting_sheet": self._build_casting_sheet(characters),
            "agent": self.name,
        }
        self.add_to_memory(result)
        return result

    async def _identify_characters(
        self, script_scenes: List[Dict[str, Any]], vision: str, style: str
    ) -> List[Dict[str, Any]]:
        """Identify unique characters from script scenes."""
        dialogue_summary = []
        for sc in script_scenes:
            for d in sc.get("dialogue", []):
                if d.get("character"):
                    dialogue_summary.append(d["character"])

        unique_chars = list(set(dialogue_summary)) if dialogue_summary else ["Narrator"]

        user_msg = (
            f"Director's vision: {vision}\nVisual style: {style}\n\n"
            f"Characters found in script: {', '.join(unique_chars)}\n\n"
            "For each character, return a JSON array of objects with:\n"
            "- name (string)\n"
            "- role (string: lead/supporting/extra)\n"
            "- description (string, 2-3 sentences about personality)\n"
            "- physical_description (string, detailed appearance for image generation)\n"
            "- age_range (string, e.g. '25-35')\n"
            "- gender (string)\n"
            "- wardrobe (string, costume description)\n"
            "- image_prompt (string, detailed prompt for generating character reference image)\n"
            "- estimated_budget (string, simulated salary range e.g. '$50,000 - $80,000')\n"
            "- notes (string, casting notes)"
        )
        raw = await self._ask_claude(user_msg, SYSTEM_PROMPT, max_tokens=2048)
        try:
            start, end = raw.find("["), raw.rfind("]") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("CastSelection: parse failed, using fallback")
            return [
                {
                    "name": name,
                    "role": "lead" if i == 0 else "supporting",
                    "description": f"Key character in {style} production",
                    "physical_description": f"Professional actor suited for {style} style",
                    "age_range": "25-40",
                    "gender": "any",
                    "wardrobe": f"Appropriate for {style} genre",
                    "image_prompt": f"Professional headshot of a {style} film character named {name}, studio lighting, detailed face",
                    "estimated_budget": "$30,000 - $60,000",
                    "notes": "Open casting",
                }
                for i, name in enumerate(unique_chars)
            ]

    @staticmethod
    def _build_casting_sheet(characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a casting summary sheet."""
        total_budget_low = 0
        total_budget_high = 0
        
        for char in characters:
            budget_str = char.get("estimated_budget", "$0 - $0")
            try:
                low, high = budget_str.replace("$", "").replace(",", "").split("-")
                total_budget_low += int(low.strip())
                total_budget_high += int(high.strip())
            except Exception:
                pass

        return {
            "total_characters": len(characters),
            "lead_count": sum(1 for c in characters if c.get("role") == "lead"),
            "supporting_count": sum(1 for c in characters if c.get("role") == "supporting"),
            "estimated_total_budget": f"${total_budget_low:,} - ${total_budget_high:,}",
        }
