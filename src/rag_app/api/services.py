"""Service assembly for the FastAPI application."""

from __future__ import annotations

from dataclasses import dataclass

from rag_app.conversations.memory import ConversationMemoryService
from rag_app.conversations.store import ConversationStore
from rag_app.core.config import get_settings
from rag_app.core.paths import DataDirectories, ensure_data_directories
from rag_app.documents.store import DocumentStore
from rag_app.models.config import ModelConfig, load_model_config
from rag_app.qa.service import RagAnswerService
from rag_app.vectors.store import VectorStore


@dataclass(frozen=True)
class ApiServices:
    """Services used by one API request."""

    directories: DataDirectories
    document_store: DocumentStore
    conversation_store: ConversationStore
    vector_store: VectorStore
    memory_service: ConversationMemoryService
    rag_service: RagAnswerService
    model_config: ModelConfig


def build_api_services() -> ApiServices:
    """Create service objects from the current settings and saved config."""

    settings = get_settings()
    directories = ensure_data_directories(settings.data_dir)

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

    return ApiServices(
        directories=directories,
        document_store=document_store,
        conversation_store=conversation_store,
        vector_store=vector_store,
        memory_service=memory_service,
        rag_service=rag_service,
        model_config=model_config,
    )
