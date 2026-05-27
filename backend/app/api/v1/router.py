"""
API Router - Version 1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    prompts,
    scripts,
    storyboards,
    scenes,
    voiceovers,
    videos,
    projects,
    media,
    exports,
)
from app.api.routes import autonomous

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Prompt optimization
api_router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])

# Autonomous film pipeline
api_router.include_router(autonomous.router, prefix="/autonomous", tags=["Autonomous"])

# Media generation (Runway AI, etc.)
api_router.include_router(media.router, prefix="/media", tags=["Media"])

# Individual resource endpoints
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["Scripts"])
api_router.include_router(storyboards.router, prefix="/storyboards", tags=["Storyboards"])
api_router.include_router(scenes.router, prefix="/scenes", tags=["Scenes"])
api_router.include_router(voiceovers.router, prefix="/voiceovers", tags=["Voiceovers"])
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
