"""
Image Generation Service — generates reference images for cast, locations, mood boards,
and storyboard frames using free/local methods with Runway API fallback.

Uses Runway's image generation endpoint if RUNWAY_API_KEY is set,
otherwise generates placeholder SVG images locally.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("media/images")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


class ImageGenerator:
    """Generates reference images — local placeholder or Runway API."""

    def __init__(self):
        self.runway_api_key = os.getenv("RUNWAY_API_KEY", "")
        self.is_configured = bool(self.runway_api_key)

    async def generate(
        self,
        prompt: str,
        category: str = "reference",
        width: int = 512,
        height: int = 512,
    ) -> dict:
        """Generate an image from a text prompt.

        Returns dict with keys: status, path, prompt, category, backend.
        """
        if self.is_configured:
            return await self._runway_generate(prompt, category, width, height)
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
        """Use Runway API for image generation (future — currently falls back)."""
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
