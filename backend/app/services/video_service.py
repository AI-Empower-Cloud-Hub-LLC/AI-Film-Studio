"""
Video service — local-first, no paid APIs.
"""
import os
import logging

logger = logging.getLogger(__name__)


class VideoService:
    """Local video generation service (replaces Runway API)."""

    @property
    def is_configured(self) -> bool:
        return True

    async def generate_video(
        self,
        prompt: str,
        duration: int = 4,
        style: str = "cinematic",
    ) -> dict:
        os.makedirs("media/video", exist_ok=True)
        demo_path = f"media/video/local_{abs(hash(prompt)) % 10000}.txt"
        with open(demo_path, "w") as f:
            f.write(
                f"Local video generation request:\n"
                f"Prompt: {prompt}\n"
                f"Duration: {duration}s\n"
                f"Style: {style}\n\n"
                "Connect a local Stable Video Diffusion instance for real video output."
            )
        return {"status": "demo", "demo_path": demo_path}

    async def get_available_models(self) -> list:
        return [
            {"id": "local-storyboard", "name": "Local Storyboard Generator"},
            {"id": "svd-local", "name": "Stable Video Diffusion (local, if available)"},
        ]


video_service = VideoService()
