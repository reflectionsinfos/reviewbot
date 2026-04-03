import pytest

from app.models import LLMConfig
from app.services.autonomous_review.connectors import llm


def _ollama_config(**overrides):
    data = {
        "name": "Local Ollama",
        "provider": "ollama",
        "model_name": "qwen2.5-coder:7b",
        "api_key": "",
        "base_url": "http://localhost:11434/api",
        "api_version": None,
        "is_active": False,
    }
    data.update(overrides)
    return LLMConfig(**data)


def test_build_client_normalizes_ollama_base_url(monkeypatch):
    monkeypatch.setattr(llm, "_running_in_container", lambda: False)
    client = llm.build_client(_ollama_config())
    assert str(client.base_url) == "http://localhost:11434/v1/"


def test_build_client_rewrites_localhost_for_container(monkeypatch):
    monkeypatch.setattr(llm, "_running_in_container", lambda: True)
    monkeypatch.setattr(llm, "_OLLAMA_DOCKER_HOST", "host.docker.internal")
    client = llm.build_client(_ollama_config(base_url="http://localhost:11434/v1"))
    assert str(client.base_url) == "http://host.docker.internal:11434/v1/"


@pytest.mark.asyncio
async def test_provider_is_configured_accepts_ollama_without_api_key(monkeypatch):
    async def fake_chain(_db=None):
        return [_ollama_config()]

    monkeypatch.setattr(llm, "get_config_chain", fake_chain)
    assert await llm.provider_is_configured() is True


@pytest.mark.asyncio
async def test_validate_llm_connectivity_reports_missing_ollama_model(monkeypatch):
    monkeypatch.setattr(llm, "_running_in_container", lambda: True)

    class FakeModels:
        async def list(self):
            class Response:
                data = [type("Model", (), {"id": "gemma3:4b"})()]

            return Response()

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    async def fake_get_llm_client(_db=None, overriding_config=None):
        return FakeClient()

    async def fake_pick_model(_db=None, overriding_config=None):
        return "qwen2.5-coder:7b"

    monkeypatch.setattr(llm, "get_llm_client", fake_get_llm_client)
    monkeypatch.setattr(llm, "pick_model", fake_pick_model)

    success, message = await llm.validate_llm_connectivity(
        overriding_config=_ollama_config(base_url="http://localhost:11434/api")
    )

    assert success is False
    assert "host.docker.internal:11434/v1" in message
    assert "ollama pull qwen2.5-coder:7b" in message
    assert "gemma3:4b" in message
