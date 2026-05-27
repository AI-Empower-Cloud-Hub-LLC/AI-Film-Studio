"""
Runway AI integration for video generation.

Provides a service wrapper for the Runway Gen-2/Gen-3 API.
Falls back gracefully to demo output when the API key is not configured.
"""
import logging
import os
from typing import Optional

import aiohttp

from app.core.config import settings

logger = logging.getLogger(__name__)

RUNWAY_API_BASE = "https://api.runwayml.com/v1"


class RunwayService:
    """Generate video clips from text or image prompts via Runway AI."""

    def __init__(self):
        self.api_key: str = getattr(settings, "RUNWAY_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and self.api_key != "your-runway-api-key-here"

    async def generate_video(
        self,
        prompt: str,
        duration: int = 4,
        style: str = "cinematic",
        image_url: Optional[str] = None,
    ) -> dict:
        """Request a video generation job from Runway.

        Returns a dict with ``status`` and either ``video_url`` (on success)
        or ``demo_path`` (when the API key is missing).
        """
        if not self.is_configured:
            return self._demo_output(prompt, duration)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            payload: dict = {
                "text_prompt": prompt,
                "seconds": min(duration, 16),
                "style": style,
            }
            if image_url:
                payload["init_image"] = image_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{RUNWAY_API_BASE}/generate/video",
                    json=payload,
                    headers=headers,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "submitted",
                            "task_id": data.get("id", ""),
                            "video_url": data.get("output", [None])[0],
                        }
                    body = await resp.text()
                    logger.error("Runway API error %s: %s", resp.status, body)
                    return {"status": "error", "detail": body}
        except Exception as exc:
            logger.error("Runway request failed: %s", exc)
            return {"status": "error", "detail": str(exc)}

    async def get_available_models(self) -> list[dict]:
        """List available Runway generation models."""
        if not self.is_configured:
            return [
                {"id": "gen3-alpha", "name": "Gen-3 Alpha (Demo)"},
                {"id": "gen2", "name": "Gen-2 (Demo)"},
            ]

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{RUNWAY_API_BASE}/models", headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception:
            pass
        return [{"id": "gen3-alpha", "name": "Gen-3 Alpha"}, {"id": "gen2", "name": "Gen-2"}]

    def _demo_output(self, prompt: str, duration: int) -> dict:
        os.makedirs("media/video", exist_ok=True)
        demo_path = "media/video/demo_runway.txt"
        with open(demo_path, "w") as f:
            f.write(
                f"Demo Runway video request:\n"
                f"Prompt: {prompt}\n"
                f"Duration: {duration}s\n\n"
                "Add your RUNWAY_API_KEY in .env for real video generation."
            )
        return {"status": "demo", "demo_path": demo_path}


runway_service = RunwayService()
