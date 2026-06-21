"""Minimal Streamlit entrypoint for the RAG knowledge app."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from rag_app.core.config import get_settings
from rag_app.core.logging import configure_logging
from rag_app.core.paths import ensure_data_directories
from rag_app.documents.processing import DocumentProcessor
from rag_app.documents.store import DocumentStore
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
from rag_app.vectors.store import VectorStore


def main() -> None:
    """Render the initial application shell."""

    settings = get_settings()
    configure_logging(settings.log_level)
    directories = ensure_data_directories(settings.data_dir)

    st.set_page_config(page_title=settings.app_name, page_icon=":books:", layout="wide")
    st.title(settings.app_name)
    st.caption("Python + LangChain RAG knowledge base foundation")

    document_store = DocumentStore(sqlite_dir=directories.sqlite, raw_dir=directories.raw)
    document_store.initialize()

    overview_tab, documents_tab, model_tab = st.tabs(
        ["Overview", "Documents", "Model configuration"]
    )

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
        st.success("Module 04: Document management is ready.")

    with documents_tab:
        render_document_management(
            document_store=document_store,
            chroma_dir=directories.chroma,
            config_dir=directories.config,
        )

    with model_tab:
        render_model_configuration(directories.config)


def render_document_management(
    *,
    document_store: DocumentStore,
    chroma_dir: Path,
    config_dir: Path,
) -> None:
    """Render the document management page."""

    model_config = load_model_config(config_dir)
    vector_store = VectorStore(chroma_dir=chroma_dir, model_config=model_config)

    st.subheader("Upload document")
    uploaded_file = st.file_uploader(
        "PDF, Word, Markdown, or TXT",
        type=["pdf", "docx", "md", "markdown", "txt"],
    )
    if uploaded_file and st.button("Upload document", use_container_width=True):
        try:
            result = document_store.upload_document(
                uploaded_file.name,
                uploaded_file.getvalue(),
            )
            if result.ok:
                st.success(result.message)
            else:
                st.warning(result.message)
        except Exception as exc:  # noqa: BLE001 - show controlled storage errors in UI.
            st.error(f"Failed to upload document: {exc}")

    st.subheader("Documents")
    try:
        documents = document_store.list_documents()
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors in UI.
        st.error(f"Failed to load documents: {exc}")
        documents = []

    if not documents:
        st.info("No documents uploaded yet.")
        return

    st.dataframe(
        [
            {
                "Document ID": document.document_id,
                "Filename": document.original_filename,
                "Type": document.file_type,
                "Size": document.file_size,
                "Status": document.status,
                "Parse": document.parse_status,
                "Index": document.index_status,
                "Chunks": document.chunk_count,
                "Duplicate": document.duplicate_of_document_id or "",
                "Created": document.created_at,
                "Updated": document.updated_at,
            }
            for document in documents
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Document actions")
    selected_document_id = st.selectbox(
        "Document",
        options=[document.document_id for document in documents],
        format_func=lambda document_id: _format_document_option(document_id, documents),
    )
    action_col_1, action_col_2 = st.columns(2)
    with action_col_1:
        if st.button("Parse and index", use_container_width=True):
            try:
                document_store.mark_reindex_requested(selected_document_id)
                processor = DocumentProcessor(
                    document_store=document_store,
                    vector_store=vector_store,
                )
                result = processor.process_document(selected_document_id, reindex=True)
                if result.ok:
                    st.success(result.message)
                else:
                    st.error(result.message)
                if result.vector_write_result is not None:
                    write = result.vector_write_result
                    st.info(
                        "Vector write progress: "
                        f"{write.processed_texts}/{write.total_texts} chunks, "
                        f"{write.processed_batches}/{write.total_batches} batches."
                    )
                if result.deleted_vectors:
                    st.caption(f"Deleted old vectors before reindex: {result.deleted_vectors}.")
            except Exception as exc:  # noqa: BLE001 - show controlled storage errors in UI.
                st.error(f"Failed to parse and index document: {exc}")
    with action_col_2:
        if st.button("Delete document", use_container_width=True):
            try:
                result = document_store.delete_document(selected_document_id, vector_store)
                st.success(
                    f"{result.message} Deleted vectors: {result.deleted_vectors}."
                )
            except Exception as exc:  # noqa: BLE001 - show controlled storage/vector errors in UI.
                st.error(f"Failed to delete document: {exc}")


def _format_document_option(document_id: str, documents: list) -> str:
    for document in documents:
        if document.document_id == document_id:
            return f"{document.original_filename} ({document.document_id})"
    return document_id


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
