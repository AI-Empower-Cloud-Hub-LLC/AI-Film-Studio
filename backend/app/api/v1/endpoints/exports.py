"""
Export endpoints — PDF scripts, JSON project data, ZIP bundle with all assets.
"""
import io
import json
import logging
import os
import zipfile
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import SessionLocal
from app.models import Project, Scene, Script

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_project_data(project_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        scenes = db.query(Scene).filter(Scene.project_id == project_id).all()
        return {
            "id": project.id,
            "title": project.title,
            "prompt": project.prompt,
            "style": project.style,
            "duration": project.duration,
            "model": project.model,
            "status": project.status,
            "director_vision": project.director_vision,
            "created_at": str(project.created_at),
            "scenes": [
                {
                    "scene_number": s.scene_number,
                    "description": s.description,
                    "shot_type": s.shot_type,
                    "mood": s.mood,
                    "duration": s.duration,
                    "visual_prompt": s.visual_prompt,
                    "narration": s.narration,
                }
                for s in scenes
            ],
        }
    finally:
        db.close()


def _get_full_project(project_id: str) -> Dict[str, Any]:
    """Get project with all associated data including cast, locations, VFX, mood board."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        scenes = db.query(Scene).filter(Scene.project_id == project_id).all()
        scripts = db.query(Script).filter(Script.project_id == project_id).all()

        script_content = []
        if scripts:
            try:
                script_content = json.loads(scripts[0].content)
            except Exception:
                pass

        return {
            "id": project.id,
            "title": project.title,
            "prompt": project.prompt,
            "style": project.style,
            "duration": project.duration,
            "model": project.model,
            "status": project.status,
            "director_vision": project.director_vision,
            "refined_screenplay": project.refined_screenplay,
            "cast_data": project.cast_data,
            "location_data": project.location_data,
            "vfx_data": project.vfx_data,
            "mood_board_data": project.mood_board_data,
            "created_at": str(project.created_at),
            "scenes": [
                {
                    "scene_number": s.scene_number,
                    "description": s.description,
                    "shot_type": s.shot_type,
                    "mood": s.mood,
                    "duration": s.duration,
                    "visual_prompt": s.visual_prompt,
                    "narration": s.narration,
                    "dialogue": s.dialogue,
                    "audio_cues": s.audio_cues,
                    "video_url": s.video_url,
                    "audio_url": s.audio_url,
                }
                for s in sorted(scenes, key=lambda x: x.scene_number)
            ],
            "scripts": script_content,
        }
    finally:
        db.close()


@router.get("/json/{project_id}")
async def export_json(project_id: str):
    data = _get_project_data(project_id)
    content = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={project_id}.json"},
    )


@router.get("/pdf/{project_id}")
async def export_pdf(project_id: str):
    data = _get_project_data(project_id)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.colors import HexColor
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab not installed")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=18, textColor=HexColor("#6B21A8"))
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=HexColor("#7C3AED"))
    body_style = styles["BodyText"]
    italic_style = ParagraphStyle("Italic", parent=body_style, fontName="Helvetica-Oblique", textColor=HexColor("#666666"))

    story = []
    story.append(Paragraph("AI Film Studio — Script Export", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Project:</b> {data['title'][:100]}", body_style))
    story.append(Paragraph(f"<b>Style:</b> {data['style']} | <b>Duration:</b> {data['duration']}s", body_style))
    story.append(Spacer(1, 8))

    if data.get("director_vision"):
        story.append(Paragraph("Director's Vision", heading_style))
        story.append(Paragraph(data["director_vision"], italic_style))
        story.append(Spacer(1, 12))

    for scene in data.get("scenes", []):
        story.append(Paragraph(f"Scene {scene['scene_number']} — {scene.get('mood', '')} ({scene.get('duration', 0)}s)", heading_style))
        story.append(Paragraph(f"<b>Shot:</b> {scene.get('shot_type', 'medium')}", body_style))
        story.append(Paragraph(scene.get("description", ""), body_style))
        if scene.get("narration"):
            story.append(Paragraph(f"<i>Narration: {scene['narration']}</i>", italic_style))
        if scene.get("visual_prompt"):
            story.append(Paragraph(f"<i>Visual Prompt: {scene['visual_prompt'][:200]}</i>", italic_style))
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)

    safe_title = data["title"][:40].replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_title}.pdf"},
    )


def _format_screenplay_text(data: Dict[str, Any]) -> str:
    """Format the screenplay as plain text for download."""
    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  {data['title']}")
    lines.append(f"  Style: {data['style']} | Duration: {data['duration']}s")
    lines.append(f"{'=' * 60}\n")

    if data.get("director_vision"):
        lines.append("DIRECTOR'S VISION")
        lines.append("-" * 40)
        lines.append(data["director_vision"])
        lines.append("")

    refined = data.get("refined_screenplay")
    if refined and isinstance(refined, dict):
        scenes_data = refined.get("scenes", [])
        if scenes_data:
            lines.append("REFINED SCREENPLAY")
            lines.append("-" * 40)
            for scene in scenes_data:
                slug = scene.get("slug_line", f"Scene {scene.get('scene_number', '?')}")
                lines.append(f"\n{slug.upper()}")
                if scene.get("description"):
                    lines.append(f"  {scene['description']}")
                if scene.get("camera_direction"):
                    lines.append(f"  Camera: {scene['camera_direction']}")
                if scene.get("production_notes"):
                    lines.append(f"  Notes: {scene['production_notes']}")
            lines.append("")

    for scene in data.get("scenes", []):
        lines.append(f"\nSCENE {scene['scene_number']} — {scene.get('mood', '')} ({scene.get('duration', 0)}s)")
        lines.append(f"  Shot: {scene.get('shot_type', 'medium')}")
        lines.append(f"  {scene.get('description', '')}")
        if scene.get("narration"):
            lines.append(f"  (Narration) {scene['narration']}")
        if scene.get("dialogue"):
            for d in scene["dialogue"]:
                if isinstance(d, dict):
                    lines.append(f"    {d.get('character', 'UNKNOWN').upper()}")
                    lines.append(f"      {d.get('line', '')}")

    return "\n".join(lines)


def _format_cast_text(cast_data: Optional[Dict]) -> str:
    """Format cast data as plain text."""
    if not cast_data:
        return "No cast data available."
    lines = ["CAST SHEET", "=" * 40, ""]
    for char in cast_data.get("characters", []):
        if isinstance(char, dict):
            lines.append(f"Character: {char.get('name', 'Unknown')}")
            lines.append(f"  Role: {char.get('role', 'N/A')}")
            lines.append(f"  Description: {char.get('description', 'N/A')}")
            if char.get("budget_range"):
                lines.append(f"  Budget: {char['budget_range']}")
            lines.append("")
    return "\n".join(lines)


def _format_locations_text(location_data: Optional[Dict]) -> str:
    """Format location data as plain text."""
    if not location_data:
        return "No location data available."
    lines = ["FILMING LOCATIONS", "=" * 40, ""]
    for loc in location_data.get("locations", []):
        if isinstance(loc, dict):
            lines.append(f"Location: {loc.get('name', 'Unknown')}")
            lines.append(f"  Type: {loc.get('type', 'N/A')}")
            lines.append(f"  Description: {loc.get('description', 'N/A')}")
            if loc.get("budget"):
                lines.append(f"  Budget: {loc['budget']}")
            if loc.get("logistics"):
                lines.append(f"  Logistics: {loc['logistics']}")
            lines.append("")
    return "\n".join(lines)


def _format_vfx_text(vfx_data: Optional[Dict]) -> str:
    """Format VFX plan as plain text."""
    if not vfx_data:
        return "No VFX plan available."
    lines = ["VFX PLAN", "=" * 40, ""]
    for shot in vfx_data.get("vfx_shots", []):
        if isinstance(shot, dict):
            lines.append(f"Shot: {shot.get('name', shot.get('scene', 'Unknown'))}")
            lines.append(f"  Technique: {shot.get('technique', 'N/A')}")
            lines.append(f"  Complexity: {shot.get('complexity', 'N/A')}")
            if shot.get("budget"):
                lines.append(f"  Budget: {shot['budget']}")
            if shot.get("software"):
                lines.append(f"  Software: {shot['software']}")
            lines.append("")
    return "\n".join(lines)


def _format_mood_board_text(mood_board_data: Optional[Dict]) -> str:
    """Format mood board as plain text."""
    if not mood_board_data:
        return "No mood board available."
    lines = ["MOOD BOARD", "=" * 40, ""]
    if mood_board_data.get("style_guide"):
        lines.append(f"Style Guide: {mood_board_data['style_guide']}")
        lines.append("")
    if mood_board_data.get("color_palette"):
        lines.append(f"Color Palette: {mood_board_data['color_palette']}")
        lines.append("")
    if mood_board_data.get("reference_films"):
        lines.append(f"Reference Films: {mood_board_data['reference_films']}")
        lines.append("")
    for img in mood_board_data.get("mood_images", []):
        if isinstance(img, dict):
            lines.append(f"- {img.get('description', img.get('prompt', 'Image'))}")
        elif isinstance(img, str):
            lines.append(f"- {img}")
    return "\n".join(lines)


@router.get("/screenplay/{project_id}")
async def export_screenplay(project_id: str):
    """Download screenplay as a formatted text file."""
    data = _get_full_project(project_id)
    text = _format_screenplay_text(data)
    safe_title = data["title"][:40].replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_screenplay.txt"},
    )


@router.get("/cast/{project_id}")
async def export_cast(project_id: str):
    """Download cast sheet as a text file."""
    data = _get_full_project(project_id)
    text = _format_cast_text(data.get("cast_data"))
    safe_title = data["title"][:40].replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_cast.txt"},
    )


@router.get("/locations/{project_id}")
async def export_locations(project_id: str):
    """Download location plan as a text file."""
    data = _get_full_project(project_id)
    text = _format_locations_text(data.get("location_data"))
    safe_title = data["title"][:40].replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_locations.txt"},
    )


@router.get("/vfx/{project_id}")
async def export_vfx(project_id: str):
    """Download VFX plan as a text file."""
    data = _get_full_project(project_id)
    text = _format_vfx_text(data.get("vfx_data"))
    safe_title = data["title"][:40].replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_vfx_plan.txt"},
    )


@router.get("/mood-board/{project_id}")
async def export_mood_board(project_id: str):
    """Download mood board description as a text file."""
    data = _get_full_project(project_id)
    text = _format_mood_board_text(data.get("mood_board_data"))
    safe_title = data["title"][:40].replace(" ", "_").replace("/", "_")
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_mood_board.txt"},
    )


@router.get("/zip/{project_id}")
async def export_zip(project_id: str):
    """Download all project assets as a ZIP bundle."""
    data = _get_full_project(project_id)
    safe_title = data["title"][:40].replace(" ", "_").replace("/", "_")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(data, indent=2, default=str))
        zf.writestr("screenplay.txt", _format_screenplay_text(data))
        zf.writestr("cast_sheet.txt", _format_cast_text(data.get("cast_data")))
        zf.writestr("locations.txt", _format_locations_text(data.get("location_data")))
        zf.writestr("vfx_plan.txt", _format_vfx_text(data.get("vfx_data")))
        zf.writestr("mood_board.txt", _format_mood_board_text(data.get("mood_board_data")))

        media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "media")
        if os.path.isdir(media_dir):
            for root, _dirs, files in os.walk(media_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    arcname = os.path.join("media", os.path.relpath(fpath, media_dir))
                    zf.write(fpath, arcname)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_project.zip"},
    )
