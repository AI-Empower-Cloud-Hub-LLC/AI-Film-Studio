"""
AI Film Studio - Main Application Entry Point
"""
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import uvicorn
import logging

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sentry error monitoring (only if DSN is configured)
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
        environment=settings.APP_ENV,
        send_default_pii=False,
    )

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


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
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def root(request: Request):
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
