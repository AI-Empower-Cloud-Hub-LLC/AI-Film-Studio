"""
Audio Generation Service — multi-backend approach.

Default: local placeholder (ready for Coqui TTS).
Optional: ElevenLabs for premium voice generation.
"""
from typing import Dict, Any, List
import logging
import os

import aiohttp

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioGenerator:
    """Audio generation using local tools or ElevenLabs."""

    def __init__(self):
        self.elevenlabs_api_key = getattr(settings, "ELEVENLABS_API_KEY", "")
        self.elevenlabs_model = getattr(settings, "ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self.voice_backend = getattr(settings, "VOICE_BACKEND", "local")

    @property
    def is_elevenlabs_active(self) -> bool:
        return bool(self.elevenlabs_api_key) and self.voice_backend == "elevenlabs"

    async def generate_voiceover(
        self,
        text: str,
        voice_type: str = "neutral",
        pace: str = "normal",
    ) -> Dict[str, Any]:
        if self.is_elevenlabs_active:
            return await self._elevenlabs_generate(text, voice_type)
        return await self._local_generate(text, voice_type, pace)

    async def _local_generate(
        self,
        text: str,
        voice_type: str,
        pace: str,
    ) -> Dict[str, Any]:
        logger.info("Voiceover request (local): %d chars, voice=%s", len(text), voice_type)
        os.makedirs("media/audio", exist_ok=True)
        placeholder = f"media/audio/voiceover_{abs(hash(text)) % 10000}.txt"
        with open(placeholder, "w") as f:
            f.write(f"Voiceover text:\n{text}\nVoice: {voice_type}, Pace: {pace}\n")
        return {
            "status": "placeholder",
            "backend": "local",
            "path": placeholder,
            "note": "Connect a local Coqui TTS server for real voiceover generation.",
        }

    async def _elevenlabs_generate(
        self,
        text: str,
        voice_type: str,
    ) -> Dict[str, Any]:
        voice_id = self._resolve_voice_id(voice_type)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.elevenlabs_model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("ElevenLabs error %s: %s", resp.status, body[:300])
                        return {
                            "status": "error",
                            "backend": "elevenlabs",
                            "error": f"ElevenLabs API error: {resp.status}",
                        }
                    os.makedirs("media/audio", exist_ok=True)
                    audio_path = f"media/audio/voiceover_{abs(hash(text)) % 10000}.mp3"
                    audio_data = await resp.read()
                    with open(audio_path, "wb") as f:
                        f.write(audio_data)
                    return {
                        "status": "completed",
                        "backend": "elevenlabs",
                        "path": audio_path,
                        "size_bytes": len(audio_data),
                    }
        except Exception as exc:
            logger.error("ElevenLabs request failed: %s", exc)
            return {
                "status": "error",
                "backend": "elevenlabs",
                "error": str(exc),
            }

    async def list_elevenlabs_voices(self) -> List[Dict[str, str]]:
        """Fetch available voices from ElevenLabs API."""
        if not self.elevenlabs_api_key:
            return []
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": self.elevenlabs_api_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return [
                        {"id": v["voice_id"], "name": v["name"], "category": v.get("category", "custom")}
                        for v in data.get("voices", [])[:20]
                    ]
        except Exception as exc:
            logger.error("Failed to fetch ElevenLabs voices: %s", exc)
            return []

    @staticmethod
    def _resolve_voice_id(voice_type: str) -> str:
        """Map friendly voice type to ElevenLabs voice ID."""
        mapping = {
            "neutral": "21m00Tcm4TlvDq8ikWAM",    # Rachel
            "deep-male": "29vD33N1CtxCmqQRPOHJ",   # Drew
            "warm-female": "EXAVITQu4vr4xnSDxMaL",  # Bella
        }
        return mapping.get(voice_type, mapping["neutral"])

    async def generate_music(
        self,
        prompt: str,
        duration: int = 30,
    ) -> Dict[str, Any]:
        logger.info("Music request: %s (%ds)", prompt[:40], duration)
        os.makedirs("media/audio", exist_ok=True)
        placeholder = f"media/audio/music_{abs(hash(prompt)) % 10000}.txt"
        with open(placeholder, "w") as f:
            f.write(f"Music prompt: {prompt}\nDuration: {duration}s\n")
        return {
            "status": "placeholder",
            "path": placeholder,
            "note": "Use local MusicGen or AudioCraft for real music generation.",
        }

    async def generate_sound_effects(
        self,
        description: str,
        duration: int = 5,
    ) -> Dict[str, Any]:
        logger.info("SFX request: %s (%ds)", description[:40], duration)
        return {
            "status": "placeholder",
            "note": f"SFX: {description} ({duration}s)",
        }


audio_generator = AudioGenerator()
