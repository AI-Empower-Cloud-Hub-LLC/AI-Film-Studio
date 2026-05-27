"""
Base Agent Class for AI Film Studio — uses free LLM backends (Ollama / Google AI).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from app.services.llm_service import LLMService, llm_service

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    def __init__(self, name: str, llm: Optional[LLMService] = None):
        self.name = name
        self.memory: list[Dict[str, Any]] = []
        self._llm = llm or llm_service
        logger.info("Initialized %s agent (backend=%s)", self.name, self._llm.backend)

    async def _ask_llm(self, prompt: str, system: str, max_tokens: int = 4096) -> str:
        """Send a prompt to the configured LLM backend and return text."""
        return await self._llm.generate(prompt=prompt, system=system, max_tokens=max_tokens)

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def add_to_memory(self, data: Dict[str, Any]):
        self.memory.append(data)

    def clear_memory(self):
        self.memory = []

    def get_context(self, max_items: int = 10) -> list[Dict[str, Any]]:
        return self.memory[-max_items:]
