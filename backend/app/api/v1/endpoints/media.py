"""
Media generation endpoints — Runway AI, Stability AI, etc.
"""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.runway_service import runway_service

router = APIRouter()


class VideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    duration: int = Field(default=4, ge=1, le=16)
    style: str = Field(default="cinematic")
    image_url: Optional[str] = None


@router.post("/generate-video")
async def generate_video(req: VideoGenerateRequest):
    result = await runway_service.generate_video(
        prompt=req.prompt,
        duration=req.duration,
        style=req.style,
        image_url=req.image_url,
    )
    return result


@router.get("/models")
async def list_models():
    models = await runway_service.get_available_models()
    return {"models": models}


@router.get("/status")
async def integration_status():
    return {
        "runway": {"configured": runway_service.is_configured},
        "elevenlabs": {"configured": bool(getattr(__import__("app.core.config", fromlist=["settings"]).settings, "ELEVENLABS_API_KEY", ""))},
        "stability": {"configured": bool(getattr(__import__("app.core.config", fromlist=["settings"]).settings, "STABILITY_API_KEY", ""))},
        "replicate": {"configured": bool(getattr(__import__("app.core.config", fromlist=["settings"]).settings, "REPLICATE_API_TOKEN", ""))},
        "openai": {"configured": bool(getattr(__import__("app.core.config", fromlist=["settings"]).settings, "OPENAI_API_KEY", ""))},
        "anthropic": {"configured": bool(getattr(__import__("app.core.config", fromlist=["settings"]).settings, "ANTHROPIC_API_KEY", ""))},
    }
