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


def test_ollama_base_url_candidates_include_rewritten_and_direct_localhost(monkeypatch):
    monkeypatch.setattr(llm, "_running_in_container", lambda: True)
    monkeypatch.setattr(llm, "_OLLAMA_DOCKER_HOST", "host.docker.internal")

    candidates = llm._ollama_base_url_candidates(
        _ollama_config(base_url="http://localhost:11434/api")
    )

    assert candidates == [
        "http://host.docker.internal:11434/v1",
        "http://localhost:11434/v1",
    ]


@pytest.mark.asyncio
async def test_provider_is_configured_accepts_ollama_without_api_key(monkeypatch):
    async def fake_chain(_db=None):
        return [_ollama_config()]

    monkeypatch.setattr(llm, "get_config_chain", fake_chain)
    assert await llm.provider_is_configured() is True


@pytest.mark.asyncio
async def test_validate_llm_connectivity_reports_missing_ollama_model(monkeypatch):
    monkeypatch.setattr(llm, "_running_in_container", lambda: True)

    async def fake_pick_model(_db=None, overriding_config=None):
        return "qwen2.5-coder:7b"

    monkeypatch.setattr(llm, "pick_model", fake_pick_model)

    def fake_build_client(config, base_url):
        class FakeModels:
            async def list(self):
                class Response:
                    data = [type("Model", (), {"id": "gemma3:4b"})()]

                return Response()

        class FakeClient:
            def __init__(self):
                self.base_url = base_url
                self.models = FakeModels()

        return FakeClient()

    monkeypatch.setattr(llm, "_build_client_for_base_url", fake_build_client)

    success, message = await llm.validate_llm_connectivity(
        overriding_config=_ollama_config(base_url="http://localhost:11434/api")
    )

    assert success is False
    assert "host.docker.internal:11434/v1" in message
    assert "ollama pull qwen2.5-coder:7b" in message
    assert "gemma3:4b" in message


@pytest.mark.asyncio
async def test_validate_llm_connectivity_falls_back_to_direct_localhost_for_ollama(monkeypatch):
    monkeypatch.setattr(llm, "_running_in_container", lambda: True)
    monkeypatch.setattr(llm, "_OLLAMA_DOCKER_HOST", "host.docker.internal")

    async def fake_pick_model(_db=None, overriding_config=None):
        return "gemma3:4b"

    def fake_build_client(config, base_url):
        class FakeModels:
            async def list(self):
                if "host.docker.internal" in base_url:
                    raise ConnectionError("docker host alias not reachable")

                class Response:
                    data = [type("Model", (), {"id": "gemma3:4b"})()]

                return Response()

        class FakeChatCompletions:
            async def create(self, **kwargs):
                if "host.docker.internal" in base_url:
                    raise ConnectionError("docker host alias not reachable")

                class Response:
                    choices = [type("Choice", (), {
                        "message": type("Message", (), {"content": "Connectivity Verified"})()
                    })()]

                return Response()

        class FakeChat:
            def __init__(self):
                self.completions = FakeChatCompletions()

        class FakeClient:
            def __init__(self):
                self.base_url = base_url
                self.models = FakeModels()
                self.chat = FakeChat()

        return FakeClient()

    monkeypatch.setattr(llm, "pick_model", fake_pick_model)
    monkeypatch.setattr(llm, "_build_client_for_base_url", fake_build_client)

    success, message = await llm.validate_llm_connectivity(
        overriding_config=_ollama_config(base_url="http://localhost:11434/v1")
    )

    assert success is True
    assert message == "Connectivity Verified"


@pytest.mark.asyncio
async def test_validate_llm_connectivity_reports_ollama_runtime_memory_error(monkeypatch):
    monkeypatch.setattr(llm, "_running_in_container", lambda: True)
    monkeypatch.setattr(llm, "_OLLAMA_DOCKER_HOST", "host.docker.internal")

    async def fake_pick_model(_db=None, overriding_config=None):
        return "gemma3:4b"

    def fake_build_client(config, base_url):
        class FakeModels:
            async def list(self):
                class Response:
                    data = [type("Model", (), {"id": "gemma3:4b"})()]

                return Response()

        class FakeChatCompletions:
            async def create(self, **kwargs):
                raise RuntimeError("Error code: 500 - {'error': {'message': 'memory layout cannot be allocated'}}")

        class FakeChat:
            def __init__(self):
                self.completions = FakeChatCompletions()

        class FakeClient:
            def __init__(self):
                self.base_url = base_url
                self.models = FakeModels()
                self.chat = FakeChat()

        return FakeClient()

    monkeypatch.setattr(llm, "pick_model", fake_pick_model)
    monkeypatch.setattr(llm, "_build_client_for_base_url", fake_build_client)

    success, message = await llm.validate_llm_connectivity(
        overriding_config=_ollama_config(base_url="http://host.docker.internal:11434/v1")
    )

    assert success is False
    assert "Ollama is reachable" in message
    assert "needs more available memory" in message
    assert "llama3.2:3b" in message
