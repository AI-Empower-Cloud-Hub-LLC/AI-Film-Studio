"""
Prompt optimization for film production — powered by Ollama or Google AI.

Enhances user prompts into detailed, structured creative briefs
that produce better results from AI agents. No paid API keys needed.
"""
import logging
from typing import Dict, Any

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a creative director at a world-class film studio. "
    "Your job is to take a rough concept and transform it into a rich, "
    "detailed creative brief suitable for AI-driven film production.\n\n"
    "Guidelines:\n"
    "- Expand vague ideas into vivid, specific descriptions\n"
    "- Add visual style cues (lighting, color palette, camera style)\n"
    "- Suggest emotional tone and pacing\n"
    "- Keep the core intent of the original prompt\n"
    "- Output a single enhanced prompt paragraph (3-5 sentences)\n"
    "- Do NOT add JSON or structured formatting"
)


class PromptOptimizer:
    """Optimizes user prompts using the configured free LLM backend."""

    async def optimize(
        self,
        prompt: str,
        style: str = "cinematic",
        duration: int = 30,
    ) -> Dict[str, Any]:
        try:
            user_msg = f"Style: {style}\nDuration: {duration}s\n\nOriginal concept: {prompt}"
            result = await llm_service.generate(
                prompt=user_msg,
                system=SYSTEM_PROMPT,
                max_tokens=1024,
                temperature=0.7,
            )
            if result and not result.startswith("["):
                return {"optimized_prompt": result, "was_optimized": True, "original_prompt": prompt}
            return {"optimized_prompt": prompt, "was_optimized": False}
        except Exception as exc:
            logger.error("Prompt optimization failed, using original: %s", exc)
            return {"optimized_prompt": prompt, "was_optimized": False}


prompt_optimizer = PromptOptimizer()
