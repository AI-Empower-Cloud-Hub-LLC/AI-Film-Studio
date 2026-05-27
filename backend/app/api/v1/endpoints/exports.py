"""
Export endpoints — PDF scripts, JSON project data, storyboard images.
"""
import io
import json
import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import SessionLocal
from app.models import Project, Scene

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
