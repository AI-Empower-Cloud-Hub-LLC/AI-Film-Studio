"""
CrewAI Film Studio — 5-agent film pipeline using the CrewAI framework.

Agents: Director, Screenwriter, Cinematographer, SoundDesigner, Editor
Each agent runs sequentially; downstream agents receive upstream task outputs as
context so they can build on prior work without re-prompting from scratch.

CrewAI's Crew.kickoff() is synchronous, so create_film() runs it inside
asyncio.to_thread() to avoid blocking FastAPI's event loop.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List

from crewai import Agent, Crew, Process, Task
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-6"


def _llm(model: str, api_key: str) -> ChatAnthropic:
    return ChatAnthropic(
        model=model,
        anthropic_api_key=api_key,
        max_tokens=4096,
    )


class CrewFilmStudio:
    """Orchestrates film production via CrewAI agents and sequential tasks."""

    def __init__(self, model: str = DEFAULT_MODEL, anthropic_api_key: str = ""):
        self.model = model
        self.anthropic_api_key = anthropic_api_key

    @classmethod
    def from_settings(cls, model: str = DEFAULT_MODEL) -> "CrewFilmStudio":
        from app.core.config import settings
        return cls(model=model, anthropic_api_key=settings.ANTHROPIC_API_KEY)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_crew(self, prompt: str, style: str, duration: int) -> Crew:
        llm = _llm(self.model, self.anthropic_api_key)
        scene_count = max(3, duration // 10)

        # ---- Agents ----
        director = Agent(
            role="Film Director",
            goal="Craft a compelling creative vision and detailed scene breakdown",
            backstory=(
                "Award-winning director with decades of experience. You create distinctive "
                "aesthetic identities and break stories into dynamic, emotionally resonant scenes."
            ),
            llm=llm,
            verbose=False,
        )

        screenwriter = Agent(
            role="Screenwriter",
            goal="Write vivid scripts with natural dialogue and evocative narration",
            backstory=(
                "Professional screenwriter who crafts scripts that move audiences. "
                "You write precise visual directions, authentic dialogue, and poetic narration."
            ),
            llm=llm,
            verbose=False,
        )

        cinematographer = Agent(
            role="Cinematographer",
            goal="Design stunning visual compositions and shot plans for each scene",
            backstory=(
                "World-class cinematographer who creates breathtaking visual compositions. "
                "You specify camera movements, lighting, color grading, and lens choices "
                "that serve the story's emotional needs."
            ),
            llm=llm,
            verbose=False,
        )

        sound_designer = Agent(
            role="Sound Designer",
            goal="Create an immersive audio landscape plan for the entire film",
            backstory=(
                "Acclaimed sound designer who transports audiences through audio. "
                "You specify music genres, SFX, voiceover tone, and mixing instructions."
            ),
            llm=llm,
            verbose=False,
        )

        editor = Agent(
            role="Film Editor",
            goal="Assemble a cohesive editing timeline that brings the film to life",
            backstory=(
                "Master film editor who shapes raw footage into compelling stories. "
                "You select transitions, pacing, and effects that maximise emotional impact."
            ),
            llm=llm,
            verbose=False,
        )

        # ---- Tasks ----
        vision_task = Task(
            description=(
                f"Create the creative vision and scene breakdown for this film.\n\n"
                f"Concept: {prompt}\n"
                f"Visual style: {style}\n"
                f"Duration: {duration} seconds\n\n"
                f"Return a JSON object with exactly these keys:\n"
                f'  "vision": 3-4 sentence creative vision (tone, aesthetic, pacing, emotional arc)\n'
                f'  "scenes": array of exactly {scene_count} objects, each containing:\n'
                f"    scene_number (int), description (string), duration (int seconds),\n"
                f"    shot_type (wide/medium/close-up/extreme-close-up), mood (string),\n"
                f"    visual_prompt (detailed image-generation prompt)\n\n"
                "Return valid JSON only — no markdown, no prose outside the JSON."
            ),
            expected_output=(
                f'JSON object with "vision" string and "scenes" array of {scene_count} scene objects'
            ),
            agent=director,
        )

        script_task = Task(
            description=(
                "Using the director's scene breakdown, write a detailed script for every scene.\n\n"
                "Return a JSON object with exactly this key:\n"
                '  "script_scenes": array of objects, one per scene, each containing:\n'
                "    scene_number (int), description (string), narration (string voiceover text),\n"
                "    dialogue (array of {character, line} objects — empty array if none),\n"
                "    visual_description (string), audio_cues (array of strings), duration (int seconds)\n\n"
                "Return valid JSON only."
            ),
            expected_output='JSON object with "script_scenes" array matching the scene count',
            agent=screenwriter,
            context=[vision_task],
        )

        shot_task = Task(
            description=(
                "Using the director's scene breakdown, plan detailed shots for every scene.\n\n"
                "Return a JSON object with exactly this key:\n"
                '  "shot_plans": array of objects, one per scene, each containing:\n'
                "    scene_number (int),\n"
                "    camera_movement (static/pan/tilt/dolly/handheld/crane),\n"
                "    lens (wide-angle/standard/telephoto/macro),\n"
                "    lighting (natural/golden-hour/low-key/high-key/neon/dramatic),\n"
                "    color_palette (array of 3-5 color descriptors),\n"
                "    image_generation_prompt (highly detailed Stable Diffusion prompt),\n"
                "    depth_of_field (shallow/deep/rack-focus)\n\n"
                "Return valid JSON only."
            ),
            expected_output='JSON object with "shot_plans" array',
            agent=cinematographer,
            context=[vision_task],
        )

        audio_task = Task(
            description=(
                "Using the script, plan the complete audio landscape for every scene.\n\n"
                "Return a JSON object with exactly this key:\n"
                '  "audio_plans": array of objects, one per scene, each containing:\n'
                "    scene_number (int), music_genre (string), music_tempo (slow/medium/fast/dynamic),\n"
                "    music_instruments (array of strings), sound_effects (array of strings),\n"
                "    voiceover_tone (calm/dramatic/excited/mysterious/warm),\n"
                "    voiceover_pace (slow/normal/fast), mixing_notes (string),\n"
                "    elevenlabs_voice_id (deep-male/warm-female/neutral)\n\n"
                "Return valid JSON only."
            ),
            expected_output='JSON object with "audio_plans" array',
            agent=sound_designer,
            context=[script_task],
        )

        timeline_task = Task(
            description=(
                "Using all prior agent outputs, assemble the final editing timeline.\n\n"
                "Return a JSON object with exactly these keys:\n"
                '  "timeline": array of timeline entries, one per scene, each containing:\n'
                "    scene_number (int), start_time (float), end_time (float), duration (int),\n"
                "    transition_out (fade/cut/dissolve/wipe),\n"
                "    effects: { color_grade: {temperature, contrast, saturation}, visual_effects: [string] }\n"
                '  "total_duration": int (sum of all scene durations)\n'
                '  "scenes_count": int\n\n'
                "Return valid JSON only."
            ),
            expected_output='JSON object with "timeline" array and summary totals',
            agent=editor,
            context=[vision_task, script_task, shot_task, audio_task],
        )

        return Crew(
            agents=[director, screenwriter, cinematographer, sound_designer, editor],
            tasks=[vision_task, script_task, shot_task, audio_task, timeline_task],
            process=Process.sequential,
            verbose=False,
        )

    @staticmethod
    def _extract_json(raw: str) -> Dict[str, Any]:
        """Pull the first complete JSON object (or array) out of a raw string."""
        raw = raw.strip()
        for start_ch, end_ch in [("{", "}"), ("[", "]")]:
            start = raw.find(start_ch)
            if start != -1:
                end = raw.rfind(end_ch) + 1
                try:
                    parsed = json.loads(raw[start:end])
                    return parsed if isinstance(parsed, dict) else {"items": parsed}
                except json.JSONDecodeError:
                    pass
        logger.warning("CrewAI: could not extract JSON from task output")
        return {}

    def _parse_outputs(self, crew_output: Any) -> List[Dict[str, Any]]:
        """Return a list of parsed dicts, one per task, from a CrewOutput object."""
        tasks_output = getattr(crew_output, "tasks_output", [])
        results = []
        for task_out in tasks_output:
            raw = getattr(task_out, "raw", str(task_out))
            results.append(self._extract_json(raw))
        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_film(
        self, prompt: str, style: str = "cinematic", duration: int = 30
    ) -> Dict[str, Any]:
        """Run the CrewAI film pipeline and return a structured result dict."""
        logger.info(f"CrewAI pipeline starting: {prompt[:60]}...")
        crew = self._build_crew(prompt, style, duration)

        try:
            # kickoff() is synchronous — run it off the event loop
            crew_output = await asyncio.to_thread(crew.kickoff)
        except Exception as exc:
            logger.error(f"CrewAI pipeline error: {exc}")
            return {"status": "error", "error": str(exc), "user_prompt": prompt}

        outputs = self._parse_outputs(crew_output)

        director_out = outputs[0] if len(outputs) > 0 else {}
        script_out = outputs[1] if len(outputs) > 1 else {}
        shot_out = outputs[2] if len(outputs) > 2 else {}
        audio_out = outputs[3] if len(outputs) > 3 else {}
        timeline_out = outputs[4] if len(outputs) > 4 else {}

        scenes: List[Dict] = director_out.get("scenes", [])

        return {
            "status": "success",
            "user_prompt": prompt,
            "style": style,
            "duration": duration,
            "framework": "crewai",
            "director": {
                "vision": director_out.get("vision", ""),
                "scenes": scenes,
                "agent": "Director (CrewAI)",
            },
            "script": {
                "script_scenes": script_out.get("script_scenes", []),
                "total_scenes": len(scenes),
                "agent": "Screenwriter (CrewAI)",
            },
            "cinematography": {
                "shot_plans": shot_out.get("shot_plans", []),
                "agent": "Cinematographer (CrewAI)",
            },
            "sound": {
                "audio_plans": audio_out.get("audio_plans", []),
                "agent": "SoundDesigner (CrewAI)",
            },
            "final_timeline": timeline_out,
            "media_assets": {
                "video_clips": [
                    f"scene_{s.get('scene_number', i + 1)}_video.mp4"
                    for i, s in enumerate(scenes)
                ],
                "audio_files": [
                    f"scene_{s.get('scene_number', i + 1)}_audio.mp3"
                    for i, s in enumerate(scenes)
                ],
                "scene_count": len(scenes),
            },
            "workflow_steps": [
                {"agent": "Director", "status": "completed", "framework": "crewai"},
                {"agent": "Screenwriter", "status": "completed", "framework": "crewai"},
                {"agent": "Cinematographer", "status": "completed", "framework": "crewai"},
                {"agent": "SoundDesigner", "status": "completed", "framework": "crewai"},
                {"agent": "Editor", "status": "completed", "framework": "crewai"},
            ],
        }
