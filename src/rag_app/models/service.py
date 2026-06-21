"""LangChain model factories and connection tests."""

from __future__ import annotations

from dataclasses import dataclass

from rag_app.core.exceptions import ConfigurationError
from rag_app.models.config import (
    EmbeddingProvider,
    ModelConfig,
    validate_chat_config,
    validate_embedding_config,
)


@dataclass(frozen=True)
class ModelTestResult:
    """Result returned by model connectivity tests."""

    ok: bool
    message: str


def build_chat_model(config: ModelConfig):
    """Build the configured OpenAI-compatible chat model."""

    validate_chat_config(config)

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise ConfigurationError("Missing dependency: langchain-openai") from exc

    return ChatOpenAI(
        model=config.chat.model,
        api_key=config.chat.api_key,
        base_url=config.chat.base_url,
    )


def build_embedding_model(config: ModelConfig):
    """Build the configured embedding model."""

    validate_embedding_config(config)

    if config.embedding.provider == EmbeddingProvider.OPENAI_COMPATIBLE:
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise ConfigurationError("Missing dependency: langchain-openai") from exc

        return OpenAIEmbeddings(
            model=config.embedding.model,
            api_key=config.embedding.api_key,
            base_url=config.embedding.base_url,
        )

    if config.embedding.provider == EmbeddingProvider.LOCAL_HUGGINGFACE:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError as exc:
            raise ConfigurationError("Missing dependency: langchain-huggingface") from exc

        return HuggingFaceEmbeddings(model_name=config.embedding.model)

    raise ConfigurationError(f"Unsupported embedding provider: {config.embedding.provider}")


def test_chat_model(config: ModelConfig) -> ModelTestResult:
    """Invoke the chat model with a short prompt."""

    try:
        chat_model = build_chat_model(config)
        response = chat_model.invoke("Reply with a short OK message.")
        content = getattr(response, "content", str(response))
        summary = str(content).strip()[:200] or "No content returned."
        return ModelTestResult(True, f"Chat model test succeeded: {summary}")
    except Exception as exc:  # noqa: BLE001 - convert provider errors for UI display.
        return ModelTestResult(False, f"Chat model test failed: {exc}")


def test_embedding_model(config: ModelConfig) -> ModelTestResult:
    """Embed a short text and report the resulting vector dimension."""

    try:
        embedding_model = build_embedding_model(config)
        vector = embedding_model.embed_query("Embedding connectivity test.")
        if not vector:
            return ModelTestResult(False, "Embedding model returned an empty vector.")
        return ModelTestResult(
            True,
            f"Embedding model test succeeded: vector dimension {len(vector)}.",
        )
    except Exception as exc:  # noqa: BLE001 - convert provider errors for UI display.
        return ModelTestResult(False, f"Embedding model test failed: {exc}")
