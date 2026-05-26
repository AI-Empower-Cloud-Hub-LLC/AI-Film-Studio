"""
Unified LLM Service — supports Ollama (local) and Google Generative AI (free tier).

No paid API keys required. Ollama runs locally; Google AI offers a free tier
at https://ai.google.dev with no credit card.
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


class LLMService:
    """Thin async wrapper around Ollama and Google Generative AI."""

    def __init__(
        self,
        backend: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        google_api_key: Optional[str] = None,
        google_model: Optional[str] = None,
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
    # Fallback — deterministic placeholder when no LLM is reachable
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback(prompt: str) -> str:
        return (
            f"[LLM unavailable] Generated content based on: {prompt[:200]}...\n"
            "Start Ollama (`ollama serve`) or set GOOGLE_API_KEY for real generation."
        )


# Singleton used by agents and services
llm_service = LLMService()
