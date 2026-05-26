"""
AI Services Integration Layer — free-only backends.

Uses the unified LLM service (Ollama / Google AI) instead of paid APIs.
"""
import json
from typing import List, Dict
import logging

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class OpenSourceLLMService:
    """Script generation using Ollama / Google AI (replaces OpenAI)."""

    async def generate_script(self, prompt: str, duration: int, tone: str = "professional") -> str:
        system_prompt = (
            f"You are a professional video scriptwriter. "
            f"Create a {duration}-second video script with a {tone} tone.\n\n"
            "Format the script with:\n"
            "- Scene numbers and descriptions\n"
            "- Voiceover/narration text\n"
            "- Approximate timing for each scene\n"
            "- Visual direction notes\n\n"
            "Make it engaging, concise, and suitable for AI video generation."
        )
        try:
            return await llm_service.generate(
                prompt=prompt,
                system=system_prompt,
                max_tokens=1500,
                temperature=0.7,
            )
        except Exception as e:
            logger.error("Script generation failed: %s", e)
            return self._generate_demo_script(prompt, duration, tone)

    async def analyze_script_for_scenes(self, script: str) -> List[Dict]:
        prompt = (
            f"Analyze this video script and break it into distinct scenes.\n"
            f"Return a JSON array where each scene has:\n"
            f"- scene_number: integer\n"
            f"- description: visual description for image generation\n"
            f"- narration: the voiceover text\n"
            f"- duration: duration in seconds\n\n"
            f"Script:\n{script}\n\n"
            f"Return ONLY valid JSON — a JSON object with a \"scenes\" key containing the array."
        )
        try:
            raw = await llm_service.generate(prompt=prompt, system="", max_tokens=1000, temperature=0.5)
            data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
            return data.get("scenes", [])
        except Exception as e:
            logger.error("Scene analysis failed: %s", e)
            return self._generate_demo_scenes()

    @staticmethod
    def _generate_demo_script(prompt: str, duration: int, tone: str) -> str:
        return (
            f"DEMO VIDEO SCRIPT - {duration} seconds\n"
            f"Theme: {prompt}\nTone: {tone}\n\n"
            f"SCENE 1 (0-10s)\n"
            "Visual: Opening shot with dynamic graphics\n"
            'Narration: "Welcome to the future of video creation with AI Film Studio."\n\n'
            f"SCENE 2 (10-20s)\n"
            "Visual: Showcase of AI-powered features\n"
            'Narration: "Transform your ideas into professional videos in minutes."\n\n'
            f"SCENE 3 (20-{duration}s)\n"
            "Visual: Call to action with branding\n"
            'Narration: "Start creating your masterpiece today."\n\n'
            "Note: Start Ollama or set GOOGLE_API_KEY for AI-generated scripts."
        )

    @staticmethod
    def _generate_demo_scenes() -> List[Dict]:
        return [
            {"scene_number": 1, "description": "Dynamic opening with colorful graphics", "narration": "Welcome to AI Film Studio", "duration": 5},
            {"scene_number": 2, "description": "Professional workspace visualization", "narration": "Create amazing videos with AI", "duration": 5},
        ]


class LocalImageService:
    """Placeholder for local image generation (e.g. Stable Diffusion via ComfyUI)."""

    async def generate_storyboard_frame(self, description: str) -> str:
        return "media/storyboards/placeholder.png"


class LocalVideoService:
    """Placeholder for local video generation."""

    async def generate_video_scene(self, description: str, duration: int, style: str) -> str:
        return "media/video/placeholder.mp4"
