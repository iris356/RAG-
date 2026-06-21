"""LangChain model factories and connection tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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


class LocalApiEmbeddings:
    """Minimal OpenAI-compatible embedding client for local HTTP services."""

    def __init__(self, *, model: str, base_url: str, api_key: str = "") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents using an OpenAI-compatible endpoint."""

        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed one query string using an OpenAI-compatible endpoint."""

        vectors = self._embed([text])
        return vectors[0] if vectors else []

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = Request(
            f"{self.base_url}/embeddings",
            data=json.dumps({"model": self.model, "input": inputs}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:  # noqa: S310 - user-configured local/API endpoint.
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ConfigurationError(
                f"Embedding API request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except (OSError, URLError, json.JSONDecodeError) as exc:
            raise ConfigurationError(f"Embedding API request failed: {exc}") from exc
        return _extract_embedding_vectors(payload)


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

    if config.embedding.provider == EmbeddingProvider.LOCAL_API:
        return LocalApiEmbeddings(
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


def _extract_embedding_vectors(payload: Any) -> list[list[float]]:
    if not isinstance(payload, dict):
        raise ConfigurationError("Embedding API returned a non-object response.")

    data = payload.get("data")
    if not isinstance(data, list):
        raise ConfigurationError("Embedding API response is missing data list.")

    vectors: list[list[float]] = []
    for item in data:
        if not isinstance(item, dict):
            raise ConfigurationError("Embedding API returned an invalid data item.")
        embedding = item.get("embedding")
        if not isinstance(embedding, list):
            raise ConfigurationError("Embedding API data item is missing embedding.")
        vectors.append([float(value) for value in embedding])
    return vectors


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
