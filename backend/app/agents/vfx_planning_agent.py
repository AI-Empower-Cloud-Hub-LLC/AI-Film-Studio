"""
VFX Planning Agent - Identifies VFX shots and technical requirements

Analyzes scenes for:
- VFX shot identification
- Techniques (CGI, compositing, rotoscoping, etc.)
- Complexity assessment
- Render time and cost estimates
- Recommended VFX software
"""
import json
import logging
from typing import Dict, Any, Optional, List

from app.services.llm_service import LLMService
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert VFX supervisor who analyzes scripts for effects requirements.
You identify which shots need VFX, suggest techniques, estimate complexity and budget.
You recommend industry-standard software and provide technical notes.
Always respond with valid JSON only."""


class VFXPlanningAgent(BaseAgent):
    """Identifies VFX shots, suggests techniques, and plans budgets."""

    def __init__(self, model: str = "claude-opus-4-6", anthropic_api_key: str = "", llm: Optional[LLMService] = None):
        """Initialize with model/API key (preferred) or LLMService instance.
        
        Args:
            model: LLM model name (default: claude-opus-4-6)
            anthropic_api_key: Anthropic API key if needed
            llm: Optional LLMService instance (overrides model/key if provided)
        """
        super().__init__(name="VFXPlanning", model=model, anthropic_api_key=anthropic_api_key, llm=llm)

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
        """Analyze scenes and plan VFX requirements."""
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
        """Analyze which scenes need VFX and plan technical approach."""
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
        raw = await self._ask_claude(user_msg, SYSTEM_PROMPT, max_tokens=2048)
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
        """Build VFX summary with budget and timeline."""
        vfx_needed_count = sum(1 for v in vfx_shots if v.get("vfx_needed"))
        total_cost = 0
        total_render_hours = 0
        
        for vfx in vfx_shots:
            cost_str = vfx.get("estimated_cost", "$0").replace("$", "").replace(",", "")
            try:
                total_cost += int(cost_str)
            except Exception:
                pass
            
            render_str = vfx.get("render_time_estimate", "0").split("-")[0].replace("hours", "").strip()
            try:
                total_render_hours += int(render_str)
            except Exception:
                pass

        return {
            "total_shots": len(vfx_shots),
            "shots_requiring_vfx": vfx_needed_count,
            "estimated_total_budget": f"${total_cost:,}",
            "estimated_render_time": f"{total_render_hours} hours",
            "vfx_complexity": "high" if vfx_needed_count > len(vfx_shots) // 2 else "medium",
        }
