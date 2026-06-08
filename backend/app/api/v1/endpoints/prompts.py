"""
Prompt optimization endpoint — uses LangChain to enhance user prompts.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.prompt_optimizer import prompt_optimizer
from app.services.sanitizer import sanitize_prompt

router = APIRouter()


class PromptOptimizeRequest(BaseModel):
    prompt: str = Field(..., min_length=5, description="Raw user prompt to optimize")
    style: str = Field(default="cinematic")
    duration: int = Field(default=30, ge=5, le=300)


class PromptOptimizeResponse(BaseModel):
    optimized_prompt: str
    original_prompt: str | None = None
    was_optimized: bool


@router.post("/optimize", response_model=PromptOptimizeResponse)
async def optimize_prompt(body: PromptOptimizeRequest):
    body.prompt = sanitize_prompt(body.prompt)
    result = await prompt_optimizer.optimize(
        prompt=body.prompt,
        style=body.style,
        duration=body.duration,
    )
    return PromptOptimizeResponse(**result)
