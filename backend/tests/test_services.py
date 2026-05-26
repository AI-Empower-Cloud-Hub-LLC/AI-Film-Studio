"""
Tests for service modules.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
)
from app.services.prompt_optimizer import PromptOptimizer
from app.services.ws_manager import ConnectionManager
from app.services.llm_service import LLMService, LLMBackend


def test_password_hash_and_verify():
    pwd = "myP@ssw0rd"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_and_decode_access_token():
    token = create_access_token("user-123", "test@example.com")
    data = decode_token(token)
    assert data is not None
    assert data.user_id == "user-123"
    assert data.email == "test@example.com"


def test_create_and_decode_refresh_token():
    token = create_refresh_token("user-456", "test2@example.com")
    data = decode_token(token)
    assert data is not None
    assert data.user_id == "user-456"


def test_create_token_pair():
    pair = create_token_pair("user-789", "pair@example.com")
    assert pair.access_token
    assert pair.refresh_token
    assert pair.token_type == "bearer"


def test_decode_invalid_token():
    assert decode_token("invalid.token.value") is None
    assert decode_token("") is None


@pytest.mark.asyncio
async def test_prompt_optimizer_fallback():
    optimizer = PromptOptimizer()
    result = await optimizer.optimize("A sunset over mountains", "cinematic", 30)
    assert result["optimized_prompt"] == "A sunset over mountains"
    assert result["was_optimized"] is False


def test_ws_manager_init():
    mgr = ConnectionManager()
    assert mgr._connections == {}


def test_llm_service_defaults():
    svc = LLMService()
    assert svc.backend == "ollama"
    assert svc.ollama_model == "mistral"
    assert "11434" in svc.ollama_base_url


def test_llm_service_google_backend():
    svc = LLMService(backend="google", google_api_key="test-key")
    assert svc.backend == "google"
    assert svc.google_api_key == "test-key"
    assert svc.active_backend == "google"
    assert svc.active_model == "gemini-2.0-flash"


def test_llm_service_claude_backend():
    svc = LLMService(backend="claude", anthropic_api_key="sk-ant-test")
    assert svc.backend == "claude"
    assert svc.anthropic_api_key == "sk-ant-test"
    assert svc.active_backend == "claude"
    assert svc.active_model == "claude-sonnet-4-20250514"


def test_llm_service_claude_fallback_without_key():
    svc = LLMService(backend="claude")
    assert svc.backend == "claude"
    assert svc.active_backend == "ollama"  # falls back to ollama without key
    assert svc.active_model == "mistral"


@pytest.mark.asyncio
async def test_llm_service_fallback_on_error():
    svc = LLMService(ollama_base_url="http://localhost:99999")
    result = await svc.generate("test prompt", "system", max_tokens=100)
    assert "[LLM unavailable]" in result


@pytest.mark.asyncio
async def test_llm_service_ollama_success():
    svc = LLMService()

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"response": "test output"})

    mock_post_ctx = AsyncMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.post = lambda *a, **kw: mock_post_ctx

    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
        result = await svc.generate("test prompt", "system")
        assert result == "test output"
