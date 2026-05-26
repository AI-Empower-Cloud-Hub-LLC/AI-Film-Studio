"""
Scripts Endpoint - AI-powered scriptwriting (free LLM backends)
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.ai_services import OpenSourceLLMService

router = APIRouter()

llm_service = OpenSourceLLMService()


class ScriptGenerateRequest(BaseModel):
    project_id: str
    prompt: str
    duration: int = 60
    tone: str = "professional"


class ScriptResponse(BaseModel):
    id: str
    project_id: str
    content: str
    duration: int
    status: str


scripts_db = {}


@router.post("/generate", response_model=ScriptResponse)
async def generate_script(request: ScriptGenerateRequest, background_tasks: BackgroundTasks):
    try:
        script_content = await llm_service.generate_script(
            prompt=request.prompt,
            duration=request.duration,
            tone=request.tone,
        )

        script_id = f"script_{abs(hash(request.prompt))}"

        script_data = {
            "id": script_id,
            "project_id": request.project_id,
            "content": script_content,
            "duration": request.duration,
            "status": "completed",
        }

        scripts_db[script_id] = script_data
        return script_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(script_id: str):
    if script_id in scripts_db:
        return scripts_db[script_id]
    raise HTTPException(status_code=404, detail="Script not found")
