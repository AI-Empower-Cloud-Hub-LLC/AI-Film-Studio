"""
VFX Planning Agent — Identify VFX shots, suggest techniques, and plan budgets.
"""
import json
from typing import Dict, Any, Optional, List
import logging

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a VFX supervisor with experience on blockbuster productions.
You identify which shots need visual effects, suggest appropriate techniques
(CGI, compositing, particle effects, matte painting, motion capture, etc.),
estimate complexity and budget per shot.
Always respond with valid JSON only."""


class VFXPlanningAgent(BaseAgent):
    """Identifies VFX shots, suggests techniques, and plans budgets."""

    def __init__(self, llm: Optional[LLMService] = None):
        super().__init__(name="VFXPlanning", llm=llm)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        scenes = input_data.get("scenes", [])
        shot_plans = input_data.get("shot_plans", [])
        vision = input_data.get("vision", "")
        style = input_data.get("style", "cinematic")

        logger.info("VFXPlanning analyzing %d scenes for effects...", len(scenes))

        vfx_shots = await self._analyze_vfx(scenes, shot_plans, vision, style)

        result = {
            "vfx_shots": vfx_shots,
            "total_vfx_shots": len(vfx_shots),
            "vfx_summary": self._build_summary(vfx_shots),
            "agent": self.name,
        }
        self.add_to_memory(result)
        return result

    async def _analyze_vfx(
        self,
        scenes: List[Dict[str, Any]],
        shot_plans: List[Dict[str, Any]],
        vision: str,
        style: str,
    ) -> List[Dict[str, Any]]:
        scene_descs = "; ".join(
            f"Scene {s.get('scene_number')}: {s.get('description', '')} (mood: {s.get('mood', '')})"
            for s in scenes
        )
        user_msg = (
            f"Director's vision: {vision}\nVisual style: {style}\n\n"
            f"Scenes: {scene_descs}\n\n"
            "Identify which scenes need VFX. Return a JSON array of objects with:\n"
            "- scene_number (int)\n"
            "- vfx_needed (boolean)\n"
            "- techniques (array of strings, e.g. 'CGI', 'compositing', 'matte painting')\n"
            "- description (string, what VFX is needed)\n"
            "- complexity (string: low/medium/high/extreme)\n"
            "- estimated_cost (string, e.g. '$10,000')\n"
            "- render_time_estimate (string, e.g. '2-4 hours')\n"
            "- software_recommended (array of strings, e.g. 'Nuke', 'Houdini')\n"
            "- notes (string)\n"
            "Include ALL scenes, even those with vfx_needed=false."
        )
        raw = await self._ask_llm(user_msg, SYSTEM_PROMPT, max_tokens=2048)
        try:
            start, end = raw.find("["), raw.rfind("]") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("VFXPlanning: parse failed, using fallback")
            return [
                {
                    "scene_number": s.get("scene_number", i + 1),
                    "vfx_needed": "fantasy" in s.get("mood", "").lower() or "action" in s.get("description", "").lower(),
                    "techniques": ["color grading", "compositing"],
                    "description": "Standard post-production color work",
                    "complexity": "low",
                    "estimated_cost": "$1,000",
                    "render_time_estimate": "30 minutes",
                    "software_recommended": ["DaVinci Resolve"],
                    "notes": "Minimal VFX required",
                }
                for i, s in enumerate(scenes)
            ]

    @staticmethod
    def _build_summary(vfx_shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_cost = 0
        for shot in vfx_shots:
            cost_str = shot.get("estimated_cost", "$0")
            try:
                num = int(cost_str.replace("$", "").replace(",", "").strip())
                total_cost += num
            except (ValueError, IndexError):
                pass
        vfx_needed = [s for s in vfx_shots if s.get("vfx_needed")]
        return {
            "total_scenes": len(vfx_shots),
            "scenes_with_vfx": len(vfx_needed),
            "complexity_breakdown": {
                "low": sum(1 for s in vfx_needed if s.get("complexity") == "low"),
                "medium": sum(1 for s in vfx_needed if s.get("complexity") == "medium"),
                "high": sum(1 for s in vfx_needed if s.get("complexity") == "high"),
                "extreme": sum(1 for s in vfx_needed if s.get("complexity") == "extreme"),
            },
            "estimated_total_cost": f"${total_cost:,}",
        }
