"""FastAPI routes for the RAG knowledge app."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rag_app.api.services import ApiServices, build_api_services
from rag_app.documents.processing import DocumentProcessor
from rag_app.models.config import (
    ModelConfig,
    ModelConfigPreset,
    apply_model_config_preset,
    recommended_model_config,
    save_model_config,
)
from rag_app.models.service import test_chat_model, test_embedding_model


class ChatRequest(BaseModel):
    """Payload for a RAG chat turn."""

    question: str
    session_id: str | None = None


class ConversationCreateRequest(BaseModel):
    """Payload for creating a conversation."""

    title: str | None = None


class ConversationRenameRequest(BaseModel):
    """Payload for renaming a conversation."""

    title: str


class ConfigPresetRequest(BaseModel):
    """Payload for applying a model configuration preset."""

    preset: ModelConfigPreset


def create_app() -> FastAPI:
    """Create the HTTP API application."""

    app = FastAPI(title="RAG Knowledge API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        return api_failure_response(str(exc.detail), f"http_{exc.status_code}", exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return api_failure_response(str(exc), "validation_error", 422)

    @app.exception_handler(Exception)
    async def general_exception_handler(_: Request, exc: Exception):
        return api_failure_response(str(exc), exc.__class__.__name__, 500)

    @app.get("/api/health")
    def health(services: Annotated[ApiServices, Depends(build_api_services)]):
        return api_success(
            "API is ready.",
            {
                "app": "RAG Knowledge API",
                "data_root": str(services.directories.root),
            },
        )

    @app.get("/api/conversations")
    def list_conversations(services: Annotated[ApiServices, Depends(build_api_services)]):
        sessions = services.conversation_store.list_sessions()
        return api_success(
            "Conversations loaded.",
            {"conversations": [to_jsonable(session) for session in sessions]},
        )

    @app.post("/api/conversations")
    def create_conversation(
        payload: ConversationCreateRequest,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        session = services.conversation_store.create_session(payload.title)
        return api_success("Conversation created.", {"conversation": to_jsonable(session)})

    @app.get("/api/conversations/{session_id}")
    def get_conversation(
        session_id: str,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        conversation = services.conversation_store.get_conversation(session_id)
        return api_success("Conversation loaded.", {"conversation": to_jsonable(conversation)})

    @app.patch("/api/conversations/{session_id}")
    def rename_conversation(
        session_id: str,
        payload: ConversationRenameRequest,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        session = services.conversation_store.rename_session(session_id, payload.title)
        return api_success("Conversation renamed.", {"conversation": to_jsonable(session)})

    @app.delete("/api/conversations/{session_id}")
    def delete_conversation(
        session_id: str,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        result = services.memory_service.delete_session_with_memories(session_id)
        return api_success(result.message, {"result": to_jsonable(result)})

    @app.post("/api/chat")
    def chat(
        payload: ChatRequest,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        result = services.rag_service.answer_question(
            payload.question,
            session_id=payload.session_id,
        )
        return api_success(result.message, {"result": to_jsonable(result)})

    @app.get("/api/documents")
    def list_documents(services: Annotated[ApiServices, Depends(build_api_services)]):
        documents = services.document_store.list_documents()
        return api_success(
            "Documents loaded.",
            {"documents": [to_jsonable(document) for document in documents]},
        )

    @app.post("/api/documents")
    async def upload_documents(
        services: Annotated[ApiServices, Depends(build_api_services)],
        files: Annotated[list[UploadFile], File()],
    ):
        processor = DocumentProcessor(
            document_store=services.document_store,
            vector_store=services.vector_store,
        )
        results: list[dict[str, Any]] = []

        for uploaded_file in files:
            try:
                content = await uploaded_file.read()
                upload_result = services.document_store.upload_document(
                    uploaded_file.filename or "document",
                    content,
                )
                item: dict[str, Any] = {
                    "filename": uploaded_file.filename,
                    "upload": to_jsonable(upload_result),
                    "process": None,
                }
                if upload_result.ok and upload_result.document is not None:
                    process_result = processor.process_document(
                        upload_result.document.document_id,
                        reindex=True,
                    )
                    item["process"] = to_jsonable(process_result)
                results.append(item)
            except Exception as exc:  # noqa: BLE001 - keep batch uploads independent.
                results.append(
                    {
                        "filename": uploaded_file.filename,
                        "upload": None,
                        "process": None,
                        "error": str(exc),
                    }
                )

        return api_success("Documents processed.", {"results": results})

    @app.delete("/api/documents/{document_id}")
    def delete_document(
        document_id: str,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        result = services.document_store.delete_document(
            document_id,
            services.vector_store,
        )
        return api_success(result.message, {"result": to_jsonable(result)})

    @app.post("/api/documents/{document_id}/reindex")
    def reindex_document(
        document_id: str,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        services.document_store.mark_reindex_requested(document_id)
        processor = DocumentProcessor(
            document_store=services.document_store,
            vector_store=services.vector_store,
        )
        result = processor.process_document(document_id, reindex=True)
        return api_success(result.message, {"result": to_jsonable(result)})

    @app.get("/api/config/model")
    def get_model_config(services: Annotated[ApiServices, Depends(build_api_services)]):
        return api_success(
            "Model configuration loaded.",
            {"config": services.model_config.model_dump(mode="json")},
        )

    @app.put("/api/config/model")
    def put_model_config(
        config: ModelConfig,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        path = save_model_config(config, services.directories.config)
        return api_success(
            "Model configuration saved.",
            {"path": str(path), "config": config.model_dump(mode="json")},
        )

    @app.post("/api/config/model/reset")
    def reset_model_config(services: Annotated[ApiServices, Depends(build_api_services)]):
        recommended = recommended_model_config()
        config = services.model_config.model_copy(
            update={
                "embedding": services.model_config.embedding.model_copy(
                    update={
                        "batch_size": recommended.embedding.batch_size,
                        "max_concurrency": recommended.embedding.max_concurrency,
                        "batch_interval_seconds": recommended.embedding.batch_interval_seconds,
                    }
                ),
                "retrieval": recommended.retrieval,
            }
        )
        path = save_model_config(config, services.directories.config)
        return api_success(
            "Recommended defaults restored.",
            {"path": str(path), "config": config.model_dump(mode="json")},
        )

    @app.post("/api/config/model/preset")
    def apply_model_preset(
        payload: ConfigPresetRequest,
        services: Annotated[ApiServices, Depends(build_api_services)],
    ):
        config = apply_model_config_preset(services.model_config, payload.preset)
        path = save_model_config(config, services.directories.config)
        return api_success(
            "Model configuration preset applied.",
            {"path": str(path), "config": config.model_dump(mode="json")},
        )

    @app.post("/api/config/model/test-chat")
    def test_chat(services: Annotated[ApiServices, Depends(build_api_services)]):
        result = test_chat_model(services.model_config)
        return api_success(result.message, {"result": to_jsonable(result)})

    @app.post("/api/config/model/test-embedding")
    def test_embedding(services: Annotated[ApiServices, Depends(build_api_services)]):
        result = test_embedding_model(services.model_config)
        return api_success(result.message, {"result": to_jsonable(result)})

    return app


def api_success(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the standard API success envelope."""

    return {"ok": True, "message": message, "data": data or {}}


def api_failure_response(message: str, code: str, status_code: int) -> JSONResponse:
    """Return the standard API failure envelope."""

    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "message": message, "code": code},
    )


def to_jsonable(value: Any) -> Any:
    """Convert dataclasses, pydantic models, and paths to JSON-safe objects."""

    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value
