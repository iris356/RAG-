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
    LOCAL_HUGGINGFACE = "local-huggingface"


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
    batch_size: int = Field(default=8, gt=0)
    max_concurrency: int = Field(default=1, gt=0)
    batch_interval_seconds: float = Field(default=0, ge=0)


class RetrievalConfig(BaseModel):
    """Retrieval settings shared by later RAG modules."""

    top_k: int = Field(default=5, gt=0)


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

    if config.embedding.provider == EmbeddingProvider.OPENAI_COMPATIBLE:
        _require_text(config.embedding.base_url, "Embedding base URL is required.")
        _require_text(config.embedding.api_key, "Embedding API key is required.")


def _require_text(value: str, message: str) -> None:
    if not value.strip():
        raise ConfigurationError(message)
