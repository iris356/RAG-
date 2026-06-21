"""Persistent model configuration."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from rag_app.core.exceptions import ConfigurationError

MODEL_CONFIG_FILE = "model-config.json"


class EmbeddingProvider(StrEnum):
    """Supported embedding model providers."""

    OPENAI_COMPATIBLE = "openai-compatible"
    LOCAL_API = "local-api"
    LOCAL_HUGGINGFACE = "local-huggingface"


RECOMMENDED_TOP_K = 5
RECOMMENDED_EMBEDDING_BATCH_SIZE = 8
RECOMMENDED_EMBEDDING_MAX_CONCURRENCY = 1
RECOMMENDED_EMBEDDING_BATCH_INTERVAL_SECONDS = 0.0


class ModelConfigPreset(StrEnum):
    """Recommended retrieval and embedding throughput presets."""

    STABLE = "stable"
    CLOUD_FAST = "cloud-fast"
    LOW_RESOURCE = "low-resource"


class ChatModelConfig(BaseModel):
    """OpenAI-compatible chat model settings."""

    base_url: str = ""
    api_key: str = ""
    model: str = ""


class EmbeddingModelConfig(BaseModel):
    """Embedding model settings."""

    provider: EmbeddingProvider = EmbeddingProvider.OPENAI_COMPATIBLE
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    batch_size: int = Field(default=RECOMMENDED_EMBEDDING_BATCH_SIZE, gt=0)
    max_concurrency: int = Field(default=RECOMMENDED_EMBEDDING_MAX_CONCURRENCY, gt=0)
    batch_interval_seconds: float = Field(
        default=RECOMMENDED_EMBEDDING_BATCH_INTERVAL_SECONDS,
        ge=0,
    )


class RetrievalConfig(BaseModel):
    """Retrieval settings shared by later RAG modules."""

    top_k: int = Field(default=RECOMMENDED_TOP_K, gt=0)


class ModelConfig(BaseModel):
    """Application model configuration."""

    chat: ChatModelConfig = Field(default_factory=ChatModelConfig)
    embedding: EmbeddingModelConfig = Field(default_factory=EmbeddingModelConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)


def get_model_config_path(config_dir: Path) -> Path:
    """Return the model configuration file path."""

    return config_dir / MODEL_CONFIG_FILE


def load_model_config(config_dir: Path) -> ModelConfig:
    """Load model configuration from JSON or return defaults."""

    config_path = get_model_config_path(config_dir)
    if not config_path.exists():
        return ModelConfig()

    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
        return ModelConfig.model_validate(raw_config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ConfigurationError(f"Failed to load model configuration: {exc}") from exc


def save_model_config(config: ModelConfig, config_dir: Path) -> Path:
    """Save model configuration to JSON."""

    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = get_model_config_path(config_dir)
    config_path.write_text(
        json.dumps(config.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config_path


def recommended_model_config() -> ModelConfig:
    """Return the stable recommended configuration defaults."""

    return ModelConfig(
        embedding=EmbeddingModelConfig(
            batch_size=RECOMMENDED_EMBEDDING_BATCH_SIZE,
            max_concurrency=RECOMMENDED_EMBEDDING_MAX_CONCURRENCY,
            batch_interval_seconds=RECOMMENDED_EMBEDDING_BATCH_INTERVAL_SECONDS,
        ),
        retrieval=RetrievalConfig(top_k=RECOMMENDED_TOP_K),
    )


def apply_model_config_preset(config: ModelConfig, preset: ModelConfigPreset) -> ModelConfig:
    """Return config with retrieval and embedding throughput values from a preset."""

    values = {
        ModelConfigPreset.STABLE: {
            "top_k": 5,
            "batch_size": 8,
            "max_concurrency": 1,
            "batch_interval_seconds": 0.0,
        },
        ModelConfigPreset.CLOUD_FAST: {
            "top_k": 5,
            "batch_size": 16,
            "max_concurrency": 3,
            "batch_interval_seconds": 0.5,
        },
        ModelConfigPreset.LOW_RESOURCE: {
            "top_k": 3,
            "batch_size": 4,
            "max_concurrency": 1,
            "batch_interval_seconds": 0.0,
        },
    }[preset]

    return config.model_copy(
        update={
            "embedding": config.embedding.model_copy(
                update={
                    "batch_size": values["batch_size"],
                    "max_concurrency": values["max_concurrency"],
                    "batch_interval_seconds": values["batch_interval_seconds"],
                }
            ),
            "retrieval": config.retrieval.model_copy(update={"top_k": values["top_k"]}),
        }
    )


def validate_model_config(config: ModelConfig) -> None:
    """Validate all model connections before full application use."""

    validate_chat_config(config)
    validate_embedding_config(config)


def validate_chat_config(config: ModelConfig) -> None:
    """Validate chat model settings before chat model use."""

    _require_text(config.chat.base_url, "Chat base URL is required.")
    _require_text(config.chat.api_key, "Chat API key is required.")
    _require_text(config.chat.model, "Chat model is required.")


def validate_embedding_config(config: ModelConfig) -> None:
    """Validate embedding model settings before embedding model use."""

    _require_text(config.embedding.model, "Embedding model is required.")

    if config.embedding.provider in (
        EmbeddingProvider.OPENAI_COMPATIBLE,
        EmbeddingProvider.LOCAL_API,
    ):
        _require_text(config.embedding.base_url, "Embedding base URL is required.")
        if config.embedding.provider == EmbeddingProvider.OPENAI_COMPATIBLE:
            _require_text(config.embedding.api_key, "Embedding API key is required.")


def _require_text(value: str, message: str) -> None:
    if not value.strip():
        raise ConfigurationError(message)
