"""
Attachments endpoint — upload and download files for projects.
"""
import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.database import SessionLocal
from app.models import Project, Attachment

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/{project_id}")
async def upload_file(
    project_id: str,
    file: UploadFile = File(...),
    category: str = Form("general"),
):
    """Upload a file attachment to a project."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

        ext = Path(file.filename or "file").suffix
        stored_name = f"{uuid.uuid4().hex}{ext}"

        project_dir = UPLOADS_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        file_path = project_dir / stored_name
        file_path.write_bytes(content)

        attachment = Attachment(
            project_id=project_id,
            filename=stored_name,
            original_name=file.filename or "file",
            file_size=len(content),
            content_type=file.content_type or "application/octet-stream",
            category=category,
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        return {
            "id": attachment.id,
            "filename": attachment.original_name,
            "size": attachment.file_size,
            "content_type": attachment.content_type,
            "category": attachment.category,
            "created_at": str(attachment.created_at),
        }
    finally:
        db.close()


@router.get("/{project_id}")
async def list_attachments(project_id: str):
    """List all attachments for a project."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        attachments = (
            db.query(Attachment)
            .filter(Attachment.project_id == project_id)
            .order_by(Attachment.created_at.desc())
            .all()
        )
        return [
            {
                "id": a.id,
                "filename": a.original_name,
                "size": a.file_size,
                "content_type": a.content_type,
                "category": a.category,
                "created_at": str(a.created_at),
            }
            for a in attachments
        ]
    finally:
        db.close()


@router.get("/{project_id}/{attachment_id}/download")
async def download_attachment(project_id: str, attachment_id: str):
    """Download a specific attachment."""
    db = SessionLocal()
    try:
        attachment = (
            db.query(Attachment)
            .filter(Attachment.id == attachment_id, Attachment.project_id == project_id)
            .first()
        )
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")

        file_path = UPLOADS_DIR / project_id / attachment.filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            path=str(file_path),
            filename=attachment.original_name,
            media_type=attachment.content_type,
        )
    finally:
        db.close()


@router.delete("/{project_id}/{attachment_id}")
async def delete_attachment(project_id: str, attachment_id: str):
    """Delete an attachment."""
    db = SessionLocal()
    try:
        attachment = (
            db.query(Attachment)
            .filter(Attachment.id == attachment_id, Attachment.project_id == project_id)
            .first()
        )
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")

        file_path = UPLOADS_DIR / project_id / attachment.filename
        if file_path.exists():
            file_path.unlink()

        db.delete(attachment)
        db.commit()
        return {"status": "deleted", "id": attachment_id}
    finally:
        db.close()
