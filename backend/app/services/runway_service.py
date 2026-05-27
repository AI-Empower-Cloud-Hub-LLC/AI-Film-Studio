"""
Video generation service — local-first replacement for Runway AI.

No paid API keys needed. Generates demo/placeholder output locally.
Connect a local Stable Video Diffusion instance for real video output.
"""
import logging
import os

logger = logging.getLogger(__name__)


class RunwayService:
    """Local video generation (replaces Runway AI)."""

    @property
    def is_configured(self) -> bool:
        return True

    async def generate_video(
        self,
        prompt: str,
        duration: int = 4,
        style: str = "cinematic",
        image_url: str | None = None,
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

    async def get_available_models(self) -> list[dict]:
        return [
            {"id": "local-storyboard", "name": "Local Storyboard Generator"},
            {"id": "svd-local", "name": "Stable Video Diffusion (local, if available)"},
        ]


runway_service = RunwayService()
