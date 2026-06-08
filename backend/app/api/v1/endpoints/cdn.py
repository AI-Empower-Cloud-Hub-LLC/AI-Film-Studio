"""CDN / Azure Blob Storage endpoints — upload, list, and serve media."""
import uuid
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads", "cdn")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_blob_client():
    conn = settings.AZURE_STORAGE_CONNECTION_STRING
    if not conn:
        return None
    try:
        from azure.storage.blob import BlobServiceClient
        return BlobServiceClient.from_connection_string(conn)
    except ImportError:
        return None
    except Exception:
        return None


@router.get("/status")
def cdn_status():
    blob_client = _get_blob_client()
    return {
        "azure_blob_configured": blob_client is not None,
        "cdn_base_url": settings.CDN_BASE_URL or None,
        "container": settings.AZURE_STORAGE_CONTAINER,
        "fallback": "local" if not blob_client else "azure",
    }


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    project_id: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    file_id = str(uuid.uuid4())
    blob_name = f"{project_id or 'general'}/{file_id}{ext}"

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    blob_client = _get_blob_client()
    if blob_client:
        try:
            container = blob_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
            try:
                container.get_container_properties()
            except Exception:
                container.create_container(public_access="blob")
            blob = container.get_blob_client(blob_name)
            blob.upload_blob(content, overwrite=True, content_settings={
                "content_type": file.content_type or "application/octet-stream"
            })
            url = f"{settings.CDN_BASE_URL}/{blob_name}" if settings.CDN_BASE_URL else blob.url
            return {
                "id": file_id, "url": url, "filename": file.filename,
                "size": len(content), "storage": "azure_blob",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Azure upload failed: {str(e)}")
    else:
        local_dir = os.path.join(UPLOAD_DIR, project_id or "general")
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, f"{file_id}{ext}")
        with open(local_path, "wb") as f:
            f.write(content)
        return {
            "id": file_id, "url": f"/api/v1/cdn/files/{project_id or 'general'}/{file_id}{ext}",
            "filename": file.filename, "size": len(content), "storage": "local",
        }


@router.get("/files/{path:path}")
async def serve_file(path: str):
    file_path = os.path.join(UPLOAD_DIR, path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    from fastapi.responses import FileResponse
    return FileResponse(file_path)
