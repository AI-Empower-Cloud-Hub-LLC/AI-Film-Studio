"""
Unified LLM Service — supports Ollama (local), Google Generative AI (free tier),
and Anthropic Claude (premium).

Ollama runs locally with no API key. Google AI offers a free tier.
Claude requires an ANTHROPIC_API_KEY for premium quality.
"""
import logging
from enum import Enum
from typing import Optional

import aiohttp

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMBackend(str, Enum):
    OLLAMA = "ollama"
    GOOGLE = "google"
    CLAUDE = "claude"


class LLMService:
    """Thin async wrapper around Ollama, Google Generative AI, and Anthropic Claude."""

    def __init__(
        self,
        backend: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        google_api_key: Optional[str] = None,
        google_model: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        claude_model: Optional[str] = None,
    ):
        self.backend = backend or getattr(settings, "LLM_BACKEND", "ollama")
        self.ollama_base_url = (
            ollama_base_url
            or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self.ollama_model = (
            ollama_model or getattr(settings, "OLLAMA_MODEL", "mistral")
        )
        self.google_api_key = (
            google_api_key or getattr(settings, "GOOGLE_API_KEY", "")
        )
        self.google_model = (
            google_model
            or getattr(settings, "GOOGLE_MODEL", "gemini-2.0-flash")
        )
        self.anthropic_api_key = (
            anthropic_api_key or getattr(settings, "ANTHROPIC_API_KEY", "")
        )
        self.claude_model = (
            claude_model
            or getattr(settings, "CLAUDE_MODEL", "claude-sonnet-4-20250514")
        )

    @property
    def active_model(self) -> str:
        """Return the model name for the active backend."""
        if self.backend == LLMBackend.CLAUDE and self.anthropic_api_key:
            return self.claude_model
        if self.backend == LLMBackend.GOOGLE and self.google_api_key:
            return self.google_model
        return self.ollama_model

    @property
    def active_backend(self) -> str:
        """Return the actual backend in use (may differ from configured if key is missing)."""
        if self.backend == LLMBackend.CLAUDE and self.anthropic_api_key:
            return "claude"
        if self.backend == LLMBackend.GOOGLE and self.google_api_key:
            return "google"
        return "ollama"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Route to the configured backend."""
        if self.backend == LLMBackend.CLAUDE and self.anthropic_api_key:
            return await self._claude_generate(prompt, system, max_tokens, temperature)
        if self.backend == LLMBackend.GOOGLE and self.google_api_key:
            return await self._google_generate(prompt, system, max_tokens, temperature)
        return await self._ollama_generate(prompt, system, max_tokens, temperature)

    # ------------------------------------------------------------------
    # Ollama  (POST /api/generate)
    # ------------------------------------------------------------------

    async def _ollama_generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("Ollama error %s: %s", resp.status, body[:300])
                        return self._fallback(prompt)
                    data = await resp.json()
                    return data.get("response", "")
        except Exception as exc:
            logger.error("Ollama request failed: %s", exc)
            return self._fallback(prompt)

    # ------------------------------------------------------------------
    # Google Generative AI  (REST v1beta)
    # ------------------------------------------------------------------

    async def _google_generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self.google_model}:generateContent"
            f"?key={self.google_api_key}"
        )
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": f"[System Instructions]\n{system}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow those instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("Google AI error %s: %s", resp.status, body[:300])
                        return self._fallback(prompt)
                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        return "".join(p.get("text", "") for p in parts)
                    return self._fallback(prompt)
        except Exception as exc:
            logger.error("Google AI request failed: %s", exc)
            return self._fallback(prompt)

    # ------------------------------------------------------------------
    # Anthropic Claude  (Messages API)
    # ------------------------------------------------------------------

    async def _claude_generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.claude_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("Claude error %s: %s", resp.status, body[:300])
                        return self._fallback(prompt)
                    data = await resp.json()
                    content_blocks = data.get("content", [])
                    return "".join(
                        block.get("text", "")
                        for block in content_blocks
                        if block.get("type") == "text"
                    )
        except Exception as exc:
            logger.error("Claude request failed: %s", exc)
            return self._fallback(prompt)

    # ------------------------------------------------------------------
    # Fallback — deterministic placeholder when no LLM is reachable
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback(prompt: str) -> str:
        return (
            f"[LLM unavailable] Generated content based on: {prompt[:200]}...\n"
            "Start Ollama (`ollama serve`), set GOOGLE_API_KEY, or set ANTHROPIC_API_KEY."
        )


# Singleton used by agents and services
llm_service = LLMService()
