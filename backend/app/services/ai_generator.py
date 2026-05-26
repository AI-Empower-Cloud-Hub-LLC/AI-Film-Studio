"""
AI Content Generation Service — uses free LLM backends (Ollama / Google AI).
"""
from typing import Dict, Optional
import logging

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AIGenerator:
    """AI content generation using the unified free LLM service."""

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        try:
            return await llm_service.generate(
                prompt=prompt,
                system=system_prompt or "You are a helpful AI assistant for film production.",
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            logger.error("Error generating text: %s", e)
            return f"Generated content based on: {prompt[:100]}..."


ai_generator = AIGenerator()
