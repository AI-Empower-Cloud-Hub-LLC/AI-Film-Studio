"""
Runway API Service — real video generation via Runway Gen-4 Turbo.

Set RUNWAY_API_KEY to enable. Falls back to local placeholder without key.
API docs: https://docs.dev.runwayml.com/
"""
import asyncio
import logging
import os
from typing import Optional

import aiohttp

from app.core.config import settings

logger = logging.getLogger(__name__)

RUNWAY_BASE_URL = "https://api.dev.runwayml.com/v1"


class RunwayService:
    """Video generation using Runway Gen-4 Turbo API."""

    def __init__(self):
        self.api_key: str = getattr(settings, "RUNWAY_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        style: str = "cinematic",
        image_url: Optional[str] = None,
        ratio: str = "16:9",
    ) -> dict:
        """Generate a video using Runway Gen-4 Turbo.

        Returns a dict with task_id, status, and output_url (when complete).
        """
        if not self.is_configured:
            return await self._local_fallback(prompt, duration, style)

        try:
            task = await self._create_generation(prompt, duration, image_url, ratio)
            if task.get("error"):
                logger.error("Runway create failed: %s", task["error"])
                return await self._local_fallback(prompt, duration, style)

            task_id = task.get("id", "")
            logger.info("Runway task created: %s", task_id)

            result = await self._poll_task(task_id)
            return result

        except Exception as exc:
            logger.error("Runway API error: %s", exc)
            return await self._local_fallback(prompt, duration, style)

    async def _create_generation(
        self,
        prompt: str,
        duration: int,
        image_url: Optional[str],
        ratio: str,
    ) -> dict:
        """Create a Runway image-to-video or text-to-video generation task."""
        url = f"{RUNWAY_BASE_URL}/image_to_video"
        payload: dict = {
            "model": "gen4_turbo",
            "ratio": ratio,
            "duration": min(duration, 10),
        }
        if image_url:
            payload["promptImage"] = image_url
        payload["promptText"] = prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                body = await resp.text()
                logger.error("Runway create error %s: %s", resp.status, body[:500])
                return {"error": f"HTTP {resp.status}: {body[:200]}"}

    async def _poll_task(
        self, task_id: str, max_wait: int = 300, interval: int = 5,
    ) -> dict:
        """Poll a Runway task until it completes or fails."""
        url = f"{RUNWAY_BASE_URL}/tasks/{task_id}"
        elapsed = 0

        while elapsed < max_wait:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("Runway poll error %s: %s", resp.status, body[:300])
                        return {"status": "error", "error": f"Poll failed: HTTP {resp.status}"}

                    data = await resp.json()
                    status = data.get("status", "")

                    if status == "SUCCEEDED":
                        output = data.get("output", [])
                        output_url = output[0] if output else ""
                        saved = await self._download_video(output_url, task_id) if output_url else ""
                        return {
                            "status": "completed",
                            "backend": "runway",
                            "task_id": task_id,
                            "output_url": output_url,
                            "local_path": saved,
                        }

                    if status == "FAILED":
                        failure = data.get("failure", "Unknown failure")
                        return {
                            "status": "failed",
                            "backend": "runway",
                            "task_id": task_id,
                            "error": failure,
                        }

                    logger.debug("Runway task %s status: %s (%ds)", task_id, status, elapsed)

            await asyncio.sleep(interval)
            elapsed += interval

        return {
            "status": "timeout",
            "backend": "runway",
            "task_id": task_id,
            "error": f"Timed out after {max_wait}s",
        }

    async def _download_video(self, url: str, task_id: str) -> str:
        """Download generated video to local storage."""
        os.makedirs("media/video", exist_ok=True)
        local_path = f"media/video/runway_{task_id}.mp4"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        with open(local_path, "wb") as f:
                            f.write(data)
                        logger.info("Downloaded Runway video: %s (%d bytes)", local_path, len(data))
                        return local_path
        except Exception as exc:
            logger.error("Failed to download Runway video: %s", exc)
        return ""

    async def _local_fallback(self, prompt: str, duration: int, style: str) -> dict:
        """Generate placeholder when Runway API is not available."""
        os.makedirs("media/video", exist_ok=True)
        demo_path = f"media/video/local_{abs(hash(prompt)) % 10000}.txt"
        with open(demo_path, "w") as f:
            f.write(
                f"Video generation request:\n"
                f"Prompt: {prompt}\nDuration: {duration}s\nStyle: {style}\n\n"
                "Set RUNWAY_API_KEY to generate real videos via Runway Gen-4 Turbo."
            )
        return {
            "status": "placeholder",
            "backend": "local",
            "local_path": demo_path,
            "note": "Set RUNWAY_API_KEY for real video generation.",
        }

    async def get_available_models(self) -> list[dict]:
        models = [
            {"id": "local-storyboard", "name": "Local Storyboard Generator", "backend": "local"},
        ]
        if self.is_configured:
            models.insert(0, {"id": "gen4_turbo", "name": "Runway Gen-4 Turbo", "backend": "runway"})
        return models


runway_service = RunwayService()
