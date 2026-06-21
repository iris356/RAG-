from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest
from pydantic import ValidationError

from rag_app.core.exceptions import ConfigurationError
from rag_app.models.config import (
    ChatModelConfig,
    EmbeddingModelConfig,
    EmbeddingProvider,
    ModelConfig,
    ModelConfigPreset,
    RetrievalConfig,
    apply_model_config_preset,
    get_model_config_path,
    load_model_config,
    recommended_model_config,
    save_model_config,
    validate_chat_config,
    validate_embedding_config,
)
from rag_app.models.service import (
    LocalApiEmbeddings,
    build_chat_model,
    build_embedding_model,
    test_chat_model as run_chat_model_test,
    test_embedding_model as run_embedding_model_test,
)


def test_load_model_config_returns_defaults_when_missing(tmp_path: Path) -> None:
    config = load_model_config(tmp_path)

    assert config.chat.model == ""
    assert config.embedding.provider == EmbeddingProvider.OPENAI_COMPATIBLE
    assert config.embedding.batch_size == 8
    assert config.embedding.max_concurrency == 1
    assert config.embedding.batch_interval_seconds == 0
    assert config.retrieval.top_k == 5


def test_recommended_model_config_uses_stable_defaults() -> None:
    config = recommended_model_config()

    assert config.retrieval.top_k == 5
    assert config.embedding.batch_size == 8
    assert config.embedding.max_concurrency == 1
    assert config.embedding.batch_interval_seconds == 0


@pytest.mark.parametrize(
    ("preset", "top_k", "batch_size", "max_concurrency", "interval"),
    [
        (ModelConfigPreset.STABLE, 5, 8, 1, 0),
        (ModelConfigPreset.CLOUD_FAST, 5, 16, 3, 0.5),
        (ModelConfigPreset.LOW_RESOURCE, 3, 4, 1, 0),
    ],
)
def test_apply_model_config_preset_updates_retrieval_and_embedding_limits(
    preset: ModelConfigPreset,
    top_k: int,
    batch_size: int,
    max_concurrency: int,
    interval: float,
) -> None:
    config = apply_model_config_preset(make_config(), preset)

    assert config.retrieval.top_k == top_k
    assert config.embedding.batch_size == batch_size
    assert config.embedding.max_concurrency == max_concurrency
    assert config.embedding.batch_interval_seconds == interval


def test_save_and_load_model_config_round_trip(tmp_path: Path) -> None:
    config = make_config()

    config_path = save_model_config(config, tmp_path)
    loaded_config = load_model_config(tmp_path)

    assert config_path == get_model_config_path(tmp_path)
    assert loaded_config == config
    assert json.loads(config_path.read_text(encoding="utf-8"))["chat"]["api_key"] == "chat-key"


def test_invalid_embedding_provider_is_rejected(tmp_path: Path) -> None:
    config_path = get_model_config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "chat": {"base_url": "https://example.test", "api_key": "key", "model": "qwen"},
                "embedding": {"provider": "bad", "model": "embed"},
                "retrieval": {"top_k": 5},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_model_config(tmp_path)


def test_limit_values_are_validated() -> None:
    with pytest.raises(ValidationError):
        EmbeddingModelConfig(model="embed", batch_size=0)

    with pytest.raises(ValidationError):
        EmbeddingModelConfig(model="embed", max_concurrency=0)

    with pytest.raises(ValidationError):
        EmbeddingModelConfig(model="embed", batch_interval_seconds=-0.1)


def test_chat_validation_requires_chat_fields() -> None:
    with pytest.raises(ConfigurationError, match="Chat base URL"):
        validate_chat_config(ModelConfig())


def test_embedding_validation_requires_remote_fields() -> None:
    config = ModelConfig(embedding=EmbeddingModelConfig(model="embed"))

    with pytest.raises(ConfigurationError, match="Embedding base URL"):
        validate_embedding_config(config)


def test_local_embedding_validation_does_not_require_remote_fields() -> None:
    config = ModelConfig(
        embedding=EmbeddingModelConfig(
            provider=EmbeddingProvider.LOCAL_HUGGINGFACE,
            model="local-model",
        )
    )

    validate_embedding_config(config)


def test_local_api_embedding_validation_requires_base_url_but_not_api_key() -> None:
    config = ModelConfig(
        embedding=EmbeddingModelConfig(
            provider=EmbeddingProvider.LOCAL_API,
            base_url="http://127.0.0.1:8000/v1",
            model="local-embed",
        )
    )

    validate_embedding_config(config)


def test_build_chat_model_uses_openai_compatible_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, str] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: str) -> None:
            created.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "langchain_openai",
        types.SimpleNamespace(ChatOpenAI=FakeChatOpenAI),
    )

    build_chat_model(make_config())

    assert created == {
        "model": "qwen-max",
        "api_key": "chat-key",
        "base_url": "https://chat.example.test/v1",
    }


def test_build_remote_embedding_uses_openai_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, str] = {}

    class FakeOpenAIEmbeddings:
        def __init__(self, **kwargs: str) -> None:
            created.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "langchain_openai",
        types.SimpleNamespace(OpenAIEmbeddings=FakeOpenAIEmbeddings),
    )

    build_embedding_model(make_config())

    assert created == {
        "model": "text-embedding-v4",
        "api_key": "embedding-key",
        "base_url": "https://embedding.example.test/v1",
    }


def test_build_local_embedding_uses_huggingface(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, str] = {}

    class FakeHuggingFaceEmbeddings:
        def __init__(self, **kwargs: str) -> None:
            created.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "langchain_huggingface",
        types.SimpleNamespace(HuggingFaceEmbeddings=FakeHuggingFaceEmbeddings),
    )

    build_embedding_model(
        make_config(
            embedding=EmbeddingModelConfig(
                provider=EmbeddingProvider.LOCAL_HUGGINGFACE,
                model="local-model",
            )
        )
    )

    assert created == {"model_name": "local-model"}


def test_build_local_api_embedding_uses_http_adapter() -> None:
    embedding = build_embedding_model(
        make_config(
            embedding=EmbeddingModelConfig(
                provider=EmbeddingProvider.LOCAL_API,
                base_url="http://127.0.0.1:8000/v1",
                api_key="optional-key",
                model="local-embed",
            )
        )
    )

    assert isinstance(embedding, LocalApiEmbeddings)
    assert embedding.base_url == "http://127.0.0.1:8000/v1"
    assert embedding.api_key == "optional-key"
    assert embedding.model == "local-embed"


def test_chat_test_reports_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        content = "OK"

    class FakeChatOpenAI:
        def __init__(self, **_: str) -> None:
            pass

        def invoke(self, _: str) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setitem(
        sys.modules,
        "langchain_openai",
        types.SimpleNamespace(ChatOpenAI=FakeChatOpenAI),
    )

    result = run_chat_model_test(make_config())

    assert result.ok is True
    assert "OK" in result.message


def test_embedding_test_reports_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOpenAIEmbeddings:
        def __init__(self, **_: str) -> None:
            pass

        def embed_query(self, _: str) -> list[float]:
            return [0.1, 0.2, 0.3]

    monkeypatch.setitem(
        sys.modules,
        "langchain_openai",
        types.SimpleNamespace(OpenAIEmbeddings=FakeOpenAIEmbeddings),
    )

    result = run_embedding_model_test(make_config())

    assert result.ok is True
    assert "dimension 3" in result.message


def test_embedding_test_reports_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOpenAIEmbeddings:
        def __init__(self, **_: str) -> None:
            pass

        def embed_query(self, _: str) -> list[float]:
            return []

    monkeypatch.setitem(
        sys.modules,
        "langchain_openai",
        types.SimpleNamespace(OpenAIEmbeddings=FakeOpenAIEmbeddings),
    )

    result = run_embedding_model_test(make_config())

    assert result.ok is False
    assert "empty vector" in result.message


def make_config(
    *,
    embedding: EmbeddingModelConfig | None = None,
) -> ModelConfig:
    return ModelConfig(
        chat=ChatModelConfig(
            base_url="https://chat.example.test/v1",
            api_key="chat-key",
            model="qwen-max",
        ),
        embedding=embedding
        or EmbeddingModelConfig(
            provider=EmbeddingProvider.OPENAI_COMPATIBLE,
            base_url="https://embedding.example.test/v1",
            api_key="embedding-key",
            model="text-embedding-v4",
        ),
        retrieval=RetrievalConfig(top_k=5),
    )
