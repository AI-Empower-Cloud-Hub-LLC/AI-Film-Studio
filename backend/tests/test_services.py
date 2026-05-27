"""
Tests for service modules.
"""
import pytest
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
from app.services.runway_service import RunwayService


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
async def test_prompt_optimizer_passthrough():
    optimizer = PromptOptimizer()
    result = await optimizer.optimize("A sunset over mountains", "cinematic", 30)
    assert result["optimized_prompt"] == "A sunset over mountains"
    assert result["was_optimized"] is False


def test_ws_manager_init():
    mgr = ConnectionManager()
    assert mgr._connections == {}


def test_runway_service_not_configured():
    svc = RunwayService()
    assert not svc.is_configured


@pytest.mark.asyncio
async def test_runway_demo_output():
    svc = RunwayService()
    result = await svc.generate_video("A sunset over the ocean", duration=4)
    assert result["status"] == "demo"
    assert "demo_path" in result


@pytest.mark.asyncio
async def test_runway_available_models_demo():
    svc = RunwayService()
    models = await svc.get_available_models()
    assert len(models) >= 2
    assert any("gen" in m["id"].lower() for m in models)
