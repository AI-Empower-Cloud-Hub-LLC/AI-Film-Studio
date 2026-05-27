"""
Media generation endpoints — image generation, TTS voiceover, video (Runway).
"""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.runway_service import runway_service
from app.services.image_generator import image_generator
from app.services.audio_generator import audio_generator

router = APIRouter()


class VideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    duration: int = Field(default=4, ge=1, le=16)
    style: str = Field(default="cinematic")
    image_url: Optional[str] = None


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    category: str = Field(default="storyboard")
    width: int = Field(default=512, ge=256, le=1024)
    height: int = Field(default=512, ge=256, le=1024)


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice: str = Field(default="neutral")
    pace: str = Field(default="normal")


@router.post("/generate-image")
async def generate_image(req: ImageGenerateRequest):
    result = await image_generator.generate(
        prompt=req.prompt,
        category=req.category,
        width=req.width,
        height=req.height,
    )
    return result


@router.post("/generate-tts")
async def generate_tts(req: TTSRequest):
    result = await audio_generator.generate_voiceover(
        text=req.text,
        voice_type=req.voice,
        pace=req.pace,
    )
    return result


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
        "gemini_image": {"configured": bool(image_generator.google_api_key), "backend": image_generator.active_backend},
        "tts": {"configured": True, "backend": "gtts" if not audio_generator.is_elevenlabs_active else "elevenlabs"},
        "runway": {"configured": runway_service.is_configured},
        "elevenlabs": {"configured": audio_generator.is_elevenlabs_active},
    }
