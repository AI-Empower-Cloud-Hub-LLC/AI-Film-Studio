"""
Voiceovers Endpoint - AI voice generation (local / open-source)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.audio_generator import audio_generator

router = APIRouter()


class VoiceoverRequest(BaseModel):
    script_id: str
    text: str
    voice: str = "neutral"
    language: str = "en"


class VoiceoverResponse(BaseModel):
    id: str
    audio_url: str
    duration: float
    status: str


voiceovers_db = {}


@router.post("/generate", response_model=VoiceoverResponse)
async def generate_voiceover(request: VoiceoverRequest):
    try:
        result = await audio_generator.generate_voiceover(
            text=request.text,
            voice_type=request.voice,
        )

        voiceover_id = f"voice_{abs(hash(request.text))}"

        voiceover_data = {
            "id": voiceover_id,
            "audio_url": result.get("path", ""),
            "duration": len(request.text.split()) * 0.5,
            "status": result.get("status", "placeholder"),
        }

        voiceovers_db[voiceover_id] = voiceover_data
        return voiceover_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{voiceover_id}", response_model=VoiceoverResponse)
async def get_voiceover(voiceover_id: str):
    if voiceover_id in voiceovers_db:
        return voiceovers_db[voiceover_id]
    raise HTTPException(status_code=404, detail="Voiceover not found")


@router.get("/voices/list")
async def list_voices():
    return {
        "voices": [
            {"id": "neutral", "name": "Neutral"},
            {"id": "deep-male", "name": "Deep Male"},
            {"id": "warm-female", "name": "Warm Female"},
        ],
        "note": "Connect a local Coqui TTS server for real voice generation.",
    }
