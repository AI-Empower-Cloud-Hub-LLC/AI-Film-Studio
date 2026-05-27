"""
AI Film Studio - Main Application Entry Point
"""
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.api.v1.router import api_router
from app.middleware import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    LoggingMiddleware,
)
from app.database import create_tables
from app.services.ws_manager import ws_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    if settings.DEBUG:
        # Dev/test convenience — production schema is managed by Alembic migrations.
        create_tables()
    yield
    # Shutdown
    print("Shutting down AI Film Studio...")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered end-to-end video production platform",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware
app.add_middleware(LoggingMiddleware)

# Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")

# Serve generated media files (images, audio, video)
media_dir = Path("media")
media_dir.mkdir(exist_ok=True)
(media_dir / "images").mkdir(exist_ok=True)
(media_dir / "audio").mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AI Film Studio API",
        "version": settings.API_VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.websocket("/ws/projects/{project_id}")
async def websocket_project(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time project status updates."""
    await ws_manager.connect(websocket, project_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, project_id)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
