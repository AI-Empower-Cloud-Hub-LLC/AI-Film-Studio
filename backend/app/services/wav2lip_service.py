"""
Wav2Lip Lip Sync Service — FREE, open-source lip sync.

Uses the Wav2Lip model (https://github.com/Rudrabha/Wav2Lip) to sync
generated voiceover audio with video for realistic lip movements.

This is completely free — no API keys needed. Requires:
- wav2lip model checkpoint (downloaded on first use)
- ffmpeg for video processing
- torch for inference
"""
import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WAV2LIP_DIR = Path("models/wav2lip")
OUTPUT_DIR = Path("media/lipsync")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_URL = "https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth"
MODEL_PATH = WAV2LIP_DIR / "wav2lip_gan.pth"


class Wav2LipService:
    """FREE lip sync using Wav2Lip open-source model."""

    def __init__(self):
        self._model_ready = False
        self._ffmpeg_available = shutil.which("ffmpeg") is not None

    @property
    def is_available(self) -> bool:
        return self._ffmpeg_available

    @property
    def status(self) -> dict:
        return {
            "available": self.is_available,
            "model_downloaded": MODEL_PATH.exists(),
            "ffmpeg_available": self._ffmpeg_available,
            "backend": "wav2lip",
            "cost": "free",
        }

    async def download_model(self) -> bool:
        """Download the Wav2Lip pre-trained model if not present."""
        if MODEL_PATH.exists():
            logger.info("Wav2Lip model already downloaded")
            return True

        WAV2LIP_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading Wav2Lip model from %s...", MODEL_URL)

        try:
            import httpx
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                resp = await client.get(MODEL_URL)
                if resp.status_code == 200:
                    MODEL_PATH.write_bytes(resp.content)
                    logger.info("Wav2Lip model downloaded successfully")
                    return True
                logger.warning("Failed to download Wav2Lip model: HTTP %s", resp.status_code)
        except Exception as exc:
            logger.warning("Wav2Lip model download failed: %s", exc)

        return False

    async def lip_sync(
        self,
        video_path: str,
        audio_path: str,
        output_name: Optional[str] = None,
    ) -> dict:
        """Apply lip sync to a video using the given audio track.

        Args:
            video_path: Path to input video file
            audio_path: Path to voiceover audio file
            output_name: Optional output filename (auto-generated if None)

        Returns:
            dict with status, output_path, and metadata
        """
        if not self._ffmpeg_available:
            return {
                "status": "unavailable",
                "error": "ffmpeg not installed",
                "note": "Install ffmpeg: sudo apt-get install ffmpeg",
            }

        if not os.path.exists(video_path):
            return {"status": "error", "error": f"Video not found: {video_path}"}

        if not os.path.exists(audio_path):
            return {"status": "error", "error": f"Audio not found: {audio_path}"}

        if not output_name:
            base = Path(video_path).stem
            output_name = f"lipsync_{base}.mp4"
        output_path = OUTPUT_DIR / output_name

        if not MODEL_PATH.exists():
            logger.info("Wav2Lip model not found — using ffmpeg audio overlay fallback")
            return await self._ffmpeg_fallback(video_path, audio_path, str(output_path))

        try:
            return await self._run_wav2lip(video_path, audio_path, str(output_path))
        except Exception as exc:
            logger.warning("Wav2Lip inference failed: %s — using ffmpeg fallback", exc)
            return await self._ffmpeg_fallback(video_path, audio_path, str(output_path))

    async def _run_wav2lip(self, video_path: str, audio_path: str, output_path: str) -> dict:
        """Run Wav2Lip inference using the downloaded model."""
        cmd = [
            "python", "-m", "wav2lip.inference",
            "--checkpoint_path", str(MODEL_PATH),
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0 and os.path.exists(output_path):
            return {
                "status": "completed",
                "output_path": output_path,
                "backend": "wav2lip",
                "method": "neural_lipsync",
            }

        logger.warning("Wav2Lip inference returned code %s: %s", process.returncode, stderr.decode()[:200])
        return await self._ffmpeg_fallback(video_path, audio_path, output_path)

    async def _ffmpeg_fallback(self, video_path: str, audio_path: str, output_path: str) -> dict:
        """Fallback: use ffmpeg to overlay audio on video (no lip sync, just audio merge)."""
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode == 0 and os.path.exists(output_path):
            return {
                "status": "completed",
                "output_path": output_path,
                "backend": "ffmpeg",
                "method": "audio_overlay",
                "note": "Audio merged without lip sync (Wav2Lip model not available)",
            }

        return {
            "status": "fallback",
            "video_path": video_path,
            "audio_path": audio_path,
            "backend": "none",
            "note": "Lip sync not available — video and audio generated separately",
        }


wav2lip_service = Wav2LipService()
