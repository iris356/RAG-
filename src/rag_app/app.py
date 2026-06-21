"""Streamlit entrypoint for the RAG knowledge app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from rag_app.conversations.memory import (
    ConversationMemoryResult,
    ConversationMemoryService,
)
from rag_app.conversations.store import (
    ConversationSession,
    ConversationStore,
)
from rag_app.core.config import get_settings
from rag_app.core.logging import configure_logging
from rag_app.core.paths import DataDirectories, ensure_data_directories
from rag_app.documents.processing import DocumentProcessResult, DocumentProcessor
from rag_app.documents.store import DocumentRecord, DocumentStore
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
from rag_app.qa.service import RagAnswerResult, RagAnswerService
from rag_app.vectors.store import VectorStore, VectorWriteResult

PAGE_QA = "Q&A session"
PAGE_HISTORY = "Conversation history"
PAGE_DOCUMENTS = "Document management"
PAGE_MODEL = "Model configuration"
PAGE_OVERVIEW = "Overview"
NAVIGATION_PAGES = (
    PAGE_QA,
    PAGE_HISTORY,
    PAGE_DOCUMENTS,
    PAGE_MODEL,
    PAGE_OVERVIEW,
)
NAVIGATION_STATE_KEY = "module_09_selected_page"
REQUESTED_PAGE_STATE_KEY = "module_09_requested_page"
SELECTED_CONVERSATION_STATE_KEY = "selected_conversation_id"


@dataclass(frozen=True)
class AppServices:
    """Services shared by Streamlit pages during one render run."""

    directories: DataDirectories
    document_store: DocumentStore
    conversation_store: ConversationStore
    vector_store: VectorStore
    memory_service: ConversationMemoryService
    rag_service: RagAnswerService
    model_config: ModelConfig


def main() -> None:
    """Render the Streamlit application."""

    settings = get_settings()
    configure_logging(settings.log_level)
    directories = ensure_data_directories(settings.data_dir)

    st.set_page_config(page_title=settings.app_name, page_icon=":books:", layout="wide")
    st.title(settings.app_name)
    st.caption("Python + LangChain RAG knowledge base")

    services = build_app_services(directories)
    page = render_sidebar(directories)

    if page == PAGE_QA:
        render_qa_page(services)
    elif page == PAGE_HISTORY:
        render_conversation_history_page(services)
    elif page == PAGE_DOCUMENTS:
        render_document_management_page(services)
    elif page == PAGE_MODEL:
        render_model_configuration_page(directories.config)
    else:
        render_overview_page(directories)


def build_app_services(directories: DataDirectories) -> AppServices:
    """Initialize stores and service-layer objects for the current app run."""

    document_store = DocumentStore(sqlite_dir=directories.sqlite, raw_dir=directories.raw)
    document_store.initialize()
    conversation_store = ConversationStore(sqlite_dir=directories.sqlite)
    conversation_store.initialize()

    model_config = load_model_config(directories.config)
    vector_store = VectorStore(chroma_dir=directories.chroma, model_config=model_config)
    memory_service = ConversationMemoryService(
        conversation_store=conversation_store,
        vector_store=vector_store,
    )
    rag_service = RagAnswerService(
        conversation_store=conversation_store,
        memory_service=memory_service,
        vector_store=vector_store,
        model_config=model_config,
    )

    return AppServices(
        directories=directories,
        document_store=document_store,
        conversation_store=conversation_store,
        vector_store=vector_store,
        memory_service=memory_service,
        rag_service=rag_service,
        model_config=model_config,
    )


def render_sidebar(directories: DataDirectories) -> str:
    """Render page navigation and return the selected page."""

    requested_page = st.session_state.pop(REQUESTED_PAGE_STATE_KEY, None)
    if requested_page in NAVIGATION_PAGES:
        st.session_state[NAVIGATION_STATE_KEY] = requested_page

    st.sidebar.header("Navigation")
    selected_page = st.sidebar.radio(
        "Page",
        NAVIGATION_PAGES,
        key=NAVIGATION_STATE_KEY,
    )
    st.sidebar.divider()
    st.sidebar.caption(f"Data root: `{directories.root}`")
    return selected_page


def render_overview_page(directories: DataDirectories) -> None:
    """Render data directories and module status."""

    st.header("Overview")
    st.subheader("Data directories")
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
    for module_number, module_name in (
        ("01", "Project foundation"),
        ("02", "Model configuration"),
        ("03", "Vector store"),
        ("04", "Document management"),
        ("05", "Document parsing and splitting"),
        ("06", "Conversation history"),
        ("07", "Conversation long-term memory"),
        ("08", "RAG question answering"),
        ("09", "Web interaction"),
    ):
        st.success(f"Module {module_number}: {module_name} is ready.")


def render_qa_page(services: AppServices) -> None:
    """Render the main RAG question-answering page."""

    st.header("Q&A session")
    sessions = _load_sessions(services.conversation_store)

    control_col, selector_col = st.columns(2)
    with control_col:
        render_create_conversation_form(services.conversation_store, form_key="qa_create")

    selected_session_id: str | None = None
    with selector_col:
        if sessions:
            selected_session_id = render_conversation_selector(
                sessions=sessions,
                key="qa_conversation_selector",
            )
        else:
            st.info("No conversations yet. Ask a question to create one automatically.")

    submitted_result = render_rag_question_form(
        rag_service=services.rag_service,
        session_id=selected_session_id,
        form_key="qa_rag_question_form",
    )
    if submitted_result is not None:
        selected_session_id = submitted_result.session_id
        st.session_state[SELECTED_CONVERSATION_STATE_KEY] = selected_session_id
        _show_rag_result(submitted_result)

    if selected_session_id:
        render_current_conversation(
            services.conversation_store,
            selected_session_id,
        )


def render_create_conversation_form(
    conversation_store: ConversationStore,
    *,
    form_key: str,
) -> None:
    """Render a small form for explicitly creating a new conversation."""

    with st.form(form_key):
        title = st.text_input("New conversation title", placeholder="Optional")
        submitted = st.form_submit_button("Create conversation", use_container_width=True)

    if not submitted:
        return

    try:
        session = conversation_store.create_session(title.strip() or None)
        st.session_state[SELECTED_CONVERSATION_STATE_KEY] = session.session_id
        st.success(f"Created conversation: {session.title}.")
        st.rerun()
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(f"Failed to create conversation: {exc}")


def render_conversation_selector(
    *,
    sessions: list[ConversationSession],
    key: str,
) -> str:
    """Render a conversation selector and persist the selected session ID."""

    selected_session_id = _selected_session_id(
        sessions,
        st.session_state.get(SELECTED_CONVERSATION_STATE_KEY),
    )
    index = _conversation_select_index(sessions, selected_session_id)
    selected = st.selectbox(
        "Conversation",
        options=[session.session_id for session in sessions],
        index=index,
        format_func=lambda session_id: _format_conversation_option(session_id, sessions),
        key=key,
    )
    st.session_state[SELECTED_CONVERSATION_STATE_KEY] = selected
    return selected


def render_rag_question_form(
    *,
    rag_service: RagAnswerService,
    session_id: str | None,
    form_key: str,
) -> RagAnswerResult | None:
    """Render a RAG question form and return the submitted result."""

    with st.form(form_key):
        question = st.text_area("Question", placeholder="Ask the knowledge base")
        submitted = st.form_submit_button("Ask", use_container_width=True)

    if not submitted:
        return None

    try:
        return rag_service.answer_question(question, session_id=session_id)
    except Exception as exc:  # noqa: BLE001 - show controlled RAG errors in UI.
        st.error(f"Failed to answer question: {exc}")
        return None


def render_current_conversation(
    conversation_store: ConversationStore,
    session_id: str,
) -> None:
    """Render messages for the selected conversation."""

    try:
        conversation = conversation_store.get_conversation(session_id)
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(f"Failed to open conversation: {exc}")
        return

    st.subheader(conversation.session.title)
    if not conversation.messages:
        st.info("No messages in this conversation yet.")
        return

    for message in conversation.messages:
        with st.chat_message(message.role):
            st.write(message.content)
            st.caption(message.created_at)


def render_conversation_history_page(services: AppServices) -> None:
    """Render conversation listing and management actions."""

    st.header("Conversation history")
    sessions = _load_sessions(services.conversation_store)
    if not sessions:
        st.info("No conversations yet.")
        render_create_conversation_form(
            services.conversation_store,
            form_key="history_create",
        )
        return

    st.dataframe(
        [
            _conversation_table_row(services.conversation_store, session)
            for session in sessions
        ],
        use_container_width=True,
        hide_index=True,
    )

    selected_session_id = render_conversation_selector(
        sessions=sessions,
        key="history_conversation_selector",
    )

    try:
        conversation = services.conversation_store.get_conversation(selected_session_id)
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(f"Failed to load conversation: {exc}")
        return

    action_col_1, action_col_2, action_col_3, action_col_4 = st.columns(4)
    with action_col_1:
        if st.button("Open in Q&A", use_container_width=True):
            st.session_state[SELECTED_CONVERSATION_STATE_KEY] = selected_session_id
            st.session_state[REQUESTED_PAGE_STATE_KEY] = PAGE_QA
            st.rerun()

    with action_col_2:
        if st.button("Rebuild memory", use_container_width=True):
            try:
                result = services.memory_service.rebuild_session_memories(selected_session_id)
                _show_memory_result(result)
            except Exception as exc:  # noqa: BLE001 - show controlled memory errors.
                st.error(f"Failed to rebuild conversation memory: {exc}")

    with action_col_3:
        with st.form("rename_conversation_form"):
            new_title = st.text_input("New title", value=conversation.session.title)
            submitted = st.form_submit_button("Rename", use_container_width=True)
        if submitted:
            try:
                services.conversation_store.rename_session(selected_session_id, new_title)
                st.success("Conversation renamed.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
                st.error(f"Failed to rename conversation: {exc}")

    with action_col_4:
        if st.button("Delete conversation", use_container_width=True):
            try:
                result = services.memory_service.delete_session_with_memories(
                    selected_session_id
                )
                st.success(result.message)
                st.session_state.pop(SELECTED_CONVERSATION_STATE_KEY, None)
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
                st.error(f"Failed to delete conversation: {exc}")

    st.subheader(conversation.session.title)
    if not conversation.messages:
        st.info("No messages in this conversation.")
    else:
        for message in conversation.messages:
            with st.chat_message(message.role):
                st.write(message.content)
                st.caption(message.created_at)


def render_document_management_page(services: AppServices) -> None:
    """Render document upload, listing, indexing, and deletion controls."""

    st.header("Document management")
    st.subheader("Upload document")
    uploaded_file = st.file_uploader(
        "PDF, Word, Markdown, or TXT",
        type=["pdf", "docx", "md", "markdown", "txt"],
    )
    if uploaded_file and st.button("Upload document", use_container_width=True):
        try:
            result = services.document_store.upload_document(
                uploaded_file.name,
                uploaded_file.getvalue(),
            )
            if result.ok:
                st.success(result.message)
            else:
                st.warning(result.message)
                if result.duplicate_document is not None:
                    st.info(
                        "Duplicate of "
                        f"{result.duplicate_document.original_filename} "
                        f"({result.duplicate_document.document_id})."
                    )
        except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
            st.error(f"Failed to upload document: {exc}")

    documents = _load_documents(services.document_store)
    if not documents:
        st.info("No documents uploaded yet.")
        return

    st.subheader("Documents")
    st.dataframe(
        [_document_table_row(document, documents) for document in documents],
        use_container_width=True,
        hide_index=True,
    )

    selected_document_id = st.selectbox(
        "Document",
        options=[document.document_id for document in documents],
        format_func=lambda document_id: _format_document_option(document_id, documents),
    )
    selected_document = _find_document(selected_document_id, documents)
    if selected_document is not None and selected_document.duplicate_of_document_id:
        st.warning(
            "This document duplicates existing parsed text and is not indexed by default. "
            f"Original document_id={selected_document.duplicate_of_document_id}."
        )

    action_col_1, action_col_2 = st.columns(2)
    with action_col_1:
        if st.button("Parse and index", use_container_width=True):
            process_document_for_web(services, selected_document_id)

    with action_col_2:
        if st.button("Delete document", use_container_width=True):
            try:
                result = services.document_store.delete_document(
                    selected_document_id,
                    services.vector_store,
                )
                st.success(f"{result.message} Deleted vectors: {result.deleted_vectors}.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - show controlled storage/vector errors.
                st.error(f"Failed to delete document: {exc}")


def process_document_for_web(services: AppServices, document_id: str) -> None:
    """Run document parsing/indexing and render the resulting status."""

    try:
        services.document_store.mark_reindex_requested(document_id)
        processor = DocumentProcessor(
            document_store=services.document_store,
            vector_store=services.vector_store,
        )
        result = processor.process_document(document_id, reindex=True)
        _show_document_process_result(result)
    except Exception as exc:  # noqa: BLE001 - show controlled processing errors.
        message = str(exc)
        if "Duplicate documents are not re-indexed" in message:
            st.warning(message)
        else:
            st.error(f"Failed to parse and index document: {exc}")


def _show_document_process_result(result: DocumentProcessResult) -> None:
    if result.ok:
        st.success(result.message)
    else:
        st.error(result.message)

    if result.duplicate_of_document_id:
        st.info(
            "Document text duplicates an existing document; it was not indexed again. "
            f"Original document_id={result.duplicate_of_document_id}."
        )
    if result.vector_write_result is not None:
        _show_vector_write_progress("Vector write progress", result.vector_write_result)
    if result.deleted_vectors:
        st.caption(f"Deleted old vectors before reindex: {result.deleted_vectors}.")


def render_model_configuration_page(config_dir: Path) -> None:
    """Render the model configuration page."""

    st.header("Model configuration")
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


def _load_sessions(conversation_store: ConversationStore) -> list[ConversationSession]:
    try:
        return conversation_store.list_sessions()
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(f"Failed to load conversations: {exc}")
        return []


def _load_documents(document_store: DocumentStore) -> list[DocumentRecord]:
    try:
        return document_store.list_documents()
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(f"Failed to load documents: {exc}")
        return []


def _conversation_table_row(
    conversation_store: ConversationStore,
    session: ConversationSession,
) -> dict[str, Any]:
    try:
        message_count = len(conversation_store.get_messages(session.session_id))
    except Exception:  # noqa: BLE001 - table should still render if one row fails.
        message_count = "Unavailable"

    return {
        "Session ID": session.session_id,
        "Title": session.title,
        "Messages": message_count,
        "Created": session.created_at,
        "Updated": session.updated_at,
    }


def _document_table_row(
    document: DocumentRecord,
    documents: list[DocumentRecord],
) -> dict[str, Any]:
    return {
        "Document ID": document.document_id,
        "Filename": document.original_filename,
        "Type": document.file_type,
        "Size": document.file_size,
        "Status": document.status,
        "Parse": document.parse_status,
        "Index": document.index_status,
        "Chunks": document.chunk_count,
        "Duplicate": _format_duplicate_document(document, documents),
        "Created": document.created_at,
        "Updated": document.updated_at,
    }


def _show_rag_result(result: RagAnswerResult) -> None:
    if result.ok:
        st.success(result.message)
    else:
        st.warning(result.message)

    st.info(
        "Retrieved context: "
        f"{result.knowledge_result_count} knowledge chunks, "
        f"{result.memory_result_count} conversation memories."
    )
    if result.user_memory_result is not None:
        _show_memory_progress(result.user_memory_result)
    if result.assistant_memory_result is not None:
        _show_memory_progress(result.assistant_memory_result)


def _show_memory_result(result: ConversationMemoryResult) -> None:
    if result.ok:
        st.success(result.message)
    else:
        st.error(result.message)
    _show_memory_progress(result)
    if result.deleted_vectors:
        st.caption(f"Deleted old memory vectors before rebuild: {result.deleted_vectors}.")


def _show_memory_progress(result: ConversationMemoryResult) -> None:
    write = result.vector_write_result
    if write is not None:
        _show_vector_write_progress("Memory write progress", write, unit="messages")
    elif result.total_messages:
        st.info(
            "Memory sync progress: "
            f"{result.written_messages}/{result.total_messages} messages."
        )


def _show_vector_write_progress(
    label: str,
    write: VectorWriteResult,
    *,
    unit: str = "chunks",
) -> None:
    status = (
        f"{label}: {write.processed_texts}/{write.total_texts} {unit}, "
        f"{write.processed_batches}/{write.total_batches} batches."
    )
    if write.failed_batch_index is not None:
        status = f"{status} Failed batch: {write.failed_batch_index}."
    st.info(status)

    if not write.ok:
        st.warning(
            "If a local embedding model ran out of memory, lower the embedding batch "
            "size or max concurrency in Model configuration."
        )


def _selected_session_id(
    sessions: list[ConversationSession],
    selected_session_id: str | None,
) -> str | None:
    if not sessions:
        return None
    session_ids = {session.session_id for session in sessions}
    if selected_session_id in session_ids:
        return selected_session_id
    return sessions[0].session_id


def _conversation_select_index(
    sessions: list[ConversationSession],
    selected_session_id: str | None = None,
) -> int:
    resolved_session_id = _selected_session_id(sessions, selected_session_id)
    for index, session in enumerate(sessions):
        if session.session_id == resolved_session_id:
            return index
    return 0


def _format_conversation_option(
    session_id: str,
    sessions: list[ConversationSession],
) -> str:
    for session in sessions:
        if session.session_id == session_id:
            return f"{session.title} ({session.session_id})"
    return session_id


def _find_document(
    document_id: str,
    documents: list[DocumentRecord],
) -> DocumentRecord | None:
    for document in documents:
        if document.document_id == document_id:
            return document
    return None


def _format_document_option(
    document_id: str,
    documents: list[DocumentRecord],
) -> str:
    document = _find_document(document_id, documents)
    if document is None:
        return document_id
    return f"{document.original_filename} ({document.document_id})"


def _format_duplicate_document(
    document: DocumentRecord,
    documents: list[DocumentRecord],
) -> str:
    if not document.duplicate_of_document_id:
        return "No"

    original = _find_document(document.duplicate_of_document_id, documents)
    if original is None:
        return f"Yes: {document.duplicate_of_document_id}"
    return f"Yes: {original.original_filename} ({original.document_id})"


if __name__ == "__main__":
    main()
