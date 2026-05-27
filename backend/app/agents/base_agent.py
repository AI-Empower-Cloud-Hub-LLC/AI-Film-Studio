"""
Base Agent Class for AI Film Studio
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""

    def __init__(self, name: str, model: str = DEFAULT_MODEL, anthropic_api_key: str = ""):
        self.name = name
        self.model = model
        self.memory: list[Dict[str, Any]] = []
        self._llm = LLMService()
        logger.info(f"Initialized {self.name} agent with model {self.model} (backend: {self._llm.active_backend})")

    @classmethod
    def from_settings(cls, **kwargs):
        return cls(**kwargs)

    async def _ask_claude(self, prompt: str, system: str, max_tokens: int = 4096) -> str:
        """Call the configured LLM backend and return the text response."""
        return await self._llm.generate(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
        )

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def add_to_memory(self, data: Dict[str, Any]):
        self.memory.append(data)

    def clear_memory(self):
        self.memory = []

    def get_context(self, max_items: int = 10) -> list[Dict[str, Any]]:
        return self.memory[-max_items:]
