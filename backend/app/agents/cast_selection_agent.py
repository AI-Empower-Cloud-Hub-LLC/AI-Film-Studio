"""
Cast Selection Agent — Generate character descriptions, casting suggestions, and budget estimates.
"""
import json
from typing import Dict, Any, Optional, List
import logging

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a veteran casting director with deep knowledge of character archetypes,
physical descriptions, and talent budgeting. You create detailed casting sheets with physical
descriptions suitable for generating character reference images.
Always respond with valid JSON only."""


class CastSelectionAgent(BaseAgent):
    """Generates character descriptions, casting suggestions, and budget estimates."""

    def __init__(self, llm: Optional[LLMService] = None):
        super().__init__(name="CastSelection", llm=llm)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
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
        raw = await self._ask_llm(user_msg, SYSTEM_PROMPT, max_tokens=2048)
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
        total_budget_low = 0
        total_budget_high = 0
        for ch in characters:
            budget_str = ch.get("estimated_budget", "$0 - $0")
            parts = budget_str.replace("$", "").replace(",", "").split("-")
            try:
                total_budget_low += int(parts[0].strip())
                total_budget_high += int(parts[1].strip()) if len(parts) > 1 else int(parts[0].strip())
            except (ValueError, IndexError):
                pass
        return {
            "total_characters": len(characters),
            "leads": sum(1 for c in characters if c.get("role") == "lead"),
            "supporting": sum(1 for c in characters if c.get("role") == "supporting"),
            "extras": sum(1 for c in characters if c.get("role") == "extra"),
            "estimated_total_budget": f"${total_budget_low:,} - ${total_budget_high:,}",
        }
