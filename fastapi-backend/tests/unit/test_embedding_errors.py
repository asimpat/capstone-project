import pytest

from app.services.embedding import EmbeddingServiceError, generate_embedding


class DummyResponse:
    def json(self):
        return {"embeddings": []}


def test_generate_embedding_raises_clear_service_error_when_ollama_returns_empty(monkeypatch):
    seen = {}

    def fake_post(path, payload):
        seen["path"] = path
        seen["payload"] = payload
        return DummyResponse()

    monkeypatch.setattr(
        "app.services.embedding.openai_post_with_retry",
        fake_post,
    )

    with pytest.raises(EmbeddingServiceError, match="Ollama returned an empty embedding"):
        generate_embedding("hello world")

    assert seen["path"] == "/api/embed"
    assert seen["payload"]["model"] == "nomic-embed-text:latest"
