"""Minimal Streamlit entrypoint for the RAG knowledge app."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from rag_app.core.config import get_settings
from rag_app.core.logging import configure_logging
from rag_app.core.paths import ensure_data_directories
from rag_app.models.config import (
    ChatModelConfig,
    EmbeddingModelConfig,
    EmbeddingProvider,
    ModelConfig,
    RetrievalConfig,
    load_model_config,
    save_model_config,
)
from rag_app.models.service import test_chat_model, test_embedding_model


def main() -> None:
    """Render the initial application shell."""

    settings = get_settings()
    configure_logging(settings.log_level)
    directories = ensure_data_directories(settings.data_dir)

    st.set_page_config(page_title=settings.app_name, page_icon=":books:", layout="wide")
    st.title(settings.app_name)
    st.caption("Python + LangChain RAG knowledge base foundation")

    overview_tab, model_tab = st.tabs(["Overview", "Model configuration"])

    with overview_tab:
        st.subheader("Data directories")
        st.write(f"Data root: `{directories.root}`")

        st.table(
            [
                {"Name": "Raw files", "Path": str(directories.raw)},
                {"Name": "Chroma", "Path": str(directories.chroma)},
                {"Name": "SQLite", "Path": str(directories.sqlite)},
                {"Name": "Config", "Path": str(directories.config)},
                {"Name": "Temporary files", "Path": str(directories.tmp)},
            ]
        )

        st.subheader("Module status")
        st.success("Module 01: Project foundation is ready.")
        st.success("Module 02: Model configuration is ready.")
        st.success("Module 03: Vector store is ready.")

    with model_tab:
        render_model_configuration(directories.config)


def render_model_configuration(config_dir: Path) -> None:
    """Render the model configuration page."""

    model_config = load_model_config(config_dir)

    st.subheader("Chat model")
    chat_base_url = st.text_input(
        "Chat base URL",
        value=model_config.chat.base_url,
        placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    chat_api_key = st.text_input(
        "Chat API key",
        value=model_config.chat.api_key,
        type="password",
    )
    chat_model = st.text_input(
        "Chat model",
        value=model_config.chat.model,
        placeholder="qwen-max",
    )

    st.subheader("Embedding model")
    provider_options = [provider.value for provider in EmbeddingProvider]
    embedding_provider = st.selectbox(
        "Embedding provider",
        options=provider_options,
        index=provider_options.index(model_config.embedding.provider.value),
    )
    embedding_model = st.text_input(
        "Embedding model",
        value=model_config.embedding.model,
        placeholder="text-embedding-v4 or local model path",
    )

    use_remote_embedding = embedding_provider == EmbeddingProvider.OPENAI_COMPATIBLE.value
    embedding_base_url = ""
    embedding_api_key = ""
    if use_remote_embedding:
        embedding_base_url = st.text_input(
            "Embedding base URL",
            value=model_config.embedding.base_url,
            placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        embedding_api_key = st.text_input(
            "Embedding API key",
            value=model_config.embedding.api_key,
            type="password",
        )
    else:
        embedding_base_url = ""
        embedding_api_key = ""

    st.subheader("Retrieval and local embedding limits")
    top_k = st.number_input(
        "Top K",
        min_value=1,
        value=model_config.retrieval.top_k,
        step=1,
    )
    batch_size = st.number_input(
        "Embedding batch size",
        min_value=1,
        value=model_config.embedding.batch_size,
        step=1,
    )
    max_concurrency = st.number_input(
        "Embedding max concurrency",
        min_value=1,
        value=model_config.embedding.max_concurrency,
        step=1,
    )
    batch_interval_seconds = st.number_input(
        "Embedding batch interval seconds",
        min_value=0.0,
        value=float(model_config.embedding.batch_interval_seconds),
        step=0.1,
    )

    updated_config = ModelConfig(
        chat=ChatModelConfig(
            base_url=chat_base_url.strip(),
            api_key=chat_api_key.strip(),
            model=chat_model.strip(),
        ),
        embedding=EmbeddingModelConfig(
            provider=EmbeddingProvider(embedding_provider),
            base_url=embedding_base_url.strip(),
            api_key=embedding_api_key.strip(),
            model=embedding_model.strip(),
            batch_size=int(batch_size),
            max_concurrency=int(max_concurrency),
            batch_interval_seconds=float(batch_interval_seconds),
        ),
        retrieval=RetrievalConfig(top_k=int(top_k)),
    )

    chat_save_col, embedding_save_col, chat_test_col, embedding_test_col = st.columns(4)
    with chat_save_col:
        if st.button("Save chat", use_container_width=True):
            try:
                config_to_save = model_config.model_copy(update={"chat": updated_config.chat})
                config_path = save_model_config(config_to_save, config_dir)
                st.success(f"Chat configuration saved to `{config_path}`.")
            except Exception as exc:  # noqa: BLE001 - show validation and IO errors.
                st.error(f"Failed to save chat configuration: {exc}")

    with embedding_save_col:
        if st.button("Save embedding", use_container_width=True):
            try:
                config_to_save = model_config.model_copy(
                    update={
                        "embedding": updated_config.embedding,
                        "retrieval": updated_config.retrieval,
                    }
                )
                config_path = save_model_config(config_to_save, config_dir)
                st.success(f"Embedding configuration saved to `{config_path}`.")
            except Exception as exc:  # noqa: BLE001 - show validation and IO errors.
                st.error(f"Failed to save embedding configuration: {exc}")

    with chat_test_col:
        if st.button("Test chat model", use_container_width=True):
            result = test_chat_model(updated_config)
            if result.ok:
                st.success(result.message)
            else:
                st.error(result.message)

    with embedding_test_col:
        if st.button("Test embedding model", use_container_width=True):
            result = test_embedding_model(updated_config)
            if result.ok:
                st.success(result.message)
            else:
                st.error(result.message)


if __name__ == "__main__":
    main()
