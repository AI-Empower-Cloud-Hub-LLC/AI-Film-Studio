"""
LangChain-based prompt optimization for film production.

Enhances user prompts into detailed, structured creative briefs
that produce better results from AI agents.
"""
import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """Optimizes user prompts using LangChain and Claude for better film generation results."""

    def __init__(self):
        self._chain = None

    def _ensure_chain(self):
        if self._chain is not None:
            return
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set — prompt optimizer will use passthrough mode")
            return
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=1024,
                temperature=0.7,
            )

            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
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
                ),
                ("human", "Style: {style}\nDuration: {duration}s\n\nOriginal concept: {prompt}"),
            ])

            self._chain = prompt | llm
        except Exception as exc:
            logger.error(f"Failed to initialise LangChain prompt optimizer: {exc}")
            self._chain = None

    async def optimize(
        self,
        prompt: str,
        style: str = "cinematic",
        duration: int = 30,
    ) -> Dict[str, Any]:
        self._ensure_chain()

        if self._chain is None:
            return {"optimized_prompt": prompt, "was_optimized": False}

        try:
            result = await self._chain.ainvoke({
                "prompt": prompt,
                "style": style,
                "duration": str(duration),
            })
            optimized = result.content if hasattr(result, "content") else str(result)
            return {"optimized_prompt": optimized, "was_optimized": True, "original_prompt": prompt}
        except Exception as exc:
            logger.error(f"Prompt optimization failed, using original: {exc}")
            return {"optimized_prompt": prompt, "was_optimized": False}


prompt_optimizer = PromptOptimizer()
