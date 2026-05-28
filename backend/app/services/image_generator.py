"""
Image Generation Service — generates reference images for cast, locations, mood boards,
and storyboard frames.

Priority: Gemini (Imagen) → Runway → local SVG placeholder.
"""
import base64
import hashlib
import logging
import os
from pathlib import Path

import aiohttp

from app.core.config import settings

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("media/images")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


class ImageGenerator:
    """Generates reference images — Gemini Imagen, Runway, or local placeholder."""

    def __init__(self):
        self.google_api_key = getattr(settings, "GOOGLE_API_KEY", "")
        self.runway_api_key = os.getenv("RUNWAY_API_KEY", "")

    @property
    def active_backend(self) -> str:
        if self.google_api_key:
            return "gemini"
        if self.runway_api_key:
            return "runway"
        return "local"

    def _cached_path(self, prompt: str, category: str) -> Path | None:
        """Return path if an image for this prompt already exists on disk."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
        for ext in ("png", "jpg", "svg"):
            candidate = MEDIA_DIR / f"{category}_{prompt_hash}.{ext}"
            if candidate.exists():
                return candidate
        return None

    async def generate(
        self,
        prompt: str,
        category: str = "reference",
        width: int = 512,
        height: int = 512,
    ) -> dict:
        """Generate an image from a text prompt. Returns cached result if available."""
        cached = self._cached_path(prompt, category)
        if cached and not str(cached).endswith(".svg"):
            return {
                "status": "generated",
                "path": str(cached),
                "prompt": prompt,
                "category": category,
                "backend": "cache",
            }
        if self.google_api_key:
            result = await self._gemini_generate(prompt, category, width, height)
            if result["status"] != "placeholder":
                return result
        if self.runway_api_key:
            result = await self._runway_generate(prompt, category, width, height)
            if result["status"] != "placeholder":
                return result
        return self._local_placeholder(prompt, category, width, height)

    async def _gemini_generate(
        self, prompt: str, category: str, width: int, height: int
    ) -> dict:
        """Use Gemini's image generation (Imagen 3) via Google AI API."""
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-2.0-flash-exp:generateContent"
            f"?key={self.google_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.warning("Gemini image gen error %s: %s", resp.status, body[:200])
                        return self._local_placeholder(prompt, category, width, height)
                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    for candidate in candidates:
                        parts = candidate.get("content", {}).get("parts", [])
                        for part in parts:
                            if "inlineData" in part:
                                img_data = part["inlineData"]["data"]
                                mime = part["inlineData"].get("mimeType", "image/png")
                                ext = "png" if "png" in mime else "jpg"
                                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
                                filename = f"{category}_{prompt_hash}.{ext}"
                                filepath = MEDIA_DIR / filename
                                filepath.write_bytes(base64.b64decode(img_data))
                                return {
                                    "status": "generated",
                                    "path": str(filepath),
                                    "prompt": prompt,
                                    "category": category,
                                    "backend": "gemini",
                                }
        except Exception as exc:
            logger.warning("Gemini image generation failed: %s", exc)
        return self._local_placeholder(prompt, category, width, height)

    def _local_placeholder(
        self, prompt: str, category: str, width: int, height: int
    ) -> dict:
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
        filename = f"{category}_{prompt_hash}.svg"
        filepath = MEDIA_DIR / filename

        label = prompt[:60].replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<rect width="100%" height="100%" fill="#1a1a2e"/>'
            f'<text x="50%" y="45%" text-anchor="middle" fill="#e94560" font-size="14" '
            f'font-family="Arial">{category.upper()}</text>'
            f'<text x="50%" y="55%" text-anchor="middle" fill="#aaa" font-size="11" '
            f'font-family="Arial">{label}</text>'
            f'</svg>'
        )
        filepath.write_text(svg)

        return {
            "status": "placeholder",
            "path": str(filepath),
            "prompt": prompt,
            "category": category,
            "backend": "local",
        }

    async def _runway_generate(
        self, prompt: str, category: str, width: int, height: int
    ) -> dict:
        """Use Runway API for image generation."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.dev.runwayml.com/v1/image_to_image",
                    headers={
                        "Authorization": f"Bearer {self.runway_api_key}",
                        "X-Runway-Version": "2024-11-06",
                    },
                    json={"prompt": prompt, "width": width, "height": height},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": "generated",
                        "url": data.get("output", [None])[0],
                        "prompt": prompt,
                        "category": category,
                        "backend": "runway",
                    }
        except Exception as exc:
            logger.warning("Runway image generation failed: %s — using placeholder", exc)

        return self._local_placeholder(prompt, category, width, height)


image_generator = ImageGenerator()
