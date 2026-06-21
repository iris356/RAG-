from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from rag_app.api.main import create_app
from rag_app.api.services import build_api_services
from rag_app.conversations.store import ConversationMessage, ConversationSession
from rag_app.documents.store import (
    INDEX_STATUS_INDEXED,
    PARSE_STATUS_PARSED,
    STATUS_UPLOADED,
    DocumentRecord,
)
from rag_app.models.config import (
    ChatModelConfig,
    EmbeddingModelConfig,
    EmbeddingProvider,
    ModelConfig,
    RetrievalConfig,
    load_model_config,
)


def test_health_uses_standard_envelope(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["data_root"] == str(tmp_path)


def test_conversation_lifecycle_routes_use_services(tmp_path: Path) -> None:
    client, services = make_client(tmp_path)

    created = client.post("/api/conversations", json={"title": "Research"}).json()
    session_id = created["data"]["conversation"]["session_id"]

    assert session_id == "session-1"
    assert services.conversation_store.created_titles == ["Research"]

    renamed = client.patch(
        f"/api/conversations/{session_id}",
        json={"title": "Updated"},
    ).json()
    assert renamed["data"]["conversation"]["title"] == "Updated"

    listed = client.get("/api/conversations").json()
    assert listed["data"]["conversations"][0]["title"] == "Updated"

    deleted = client.delete(f"/api/conversations/{session_id}").json()
    assert deleted["ok"] is True
    assert services.memory_service.deleted == ["session-1"]


def test_chat_route_returns_rag_result(tmp_path: Path) -> None:
    client, services = make_client(tmp_path)

    response = client.post(
        "/api/chat",
        json={"question": "Python 容易学习吗？", "session_id": "session-1"},
    )

    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["result"]["answer"] == "容易"
    assert services.rag_service.questions == [("Python 容易学习吗？", "session-1")]


def test_upload_indexes_new_files_and_skips_duplicate_files(
    monkeypatch,
    tmp_path: Path,
) -> None:
    client, services = make_client(tmp_path)
    processor = FakeDocumentProcessor()
    monkeypatch.setattr("rag_app.api.main.DocumentProcessor", lambda **_: processor)

    response = client.post(
        "/api/documents",
        files=[
            ("files", ("new.txt", b"new body", "text/plain")),
            ("files", ("duplicate.txt", b"duplicate body", "text/plain")),
        ],
    )

    payload = response.json()
    assert payload["ok"] is True
    assert services.document_store.uploaded == [
        ("new.txt", b"new body"),
        ("duplicate.txt", b"duplicate body"),
    ]
    assert processor.processed == [("doc-new", True)]
    assert payload["data"]["results"][1]["process"] is None


def test_model_config_routes_save_reset_and_apply_presets(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    config = make_config().model_dump(mode="json")
    config["retrieval"]["top_k"] = 9
    saved = client.put("/api/config/model", json=config).json()
    assert saved["ok"] is True
    assert load_model_config(tmp_path / "config").retrieval.top_k == 9

    reset = client.post("/api/config/model/reset").json()
    assert reset["data"]["config"]["retrieval"]["top_k"] == 5
    assert reset["data"]["config"]["embedding"]["batch_size"] == 8

    preset = client.post(
        "/api/config/model/preset",
        json={"preset": "low-resource"},
    ).json()
    assert preset["data"]["config"]["retrieval"]["top_k"] == 3
    assert preset["data"]["config"]["embedding"]["batch_size"] == 4


def make_client(tmp_path: Path) -> tuple[TestClient, SimpleNamespace]:
    services = SimpleNamespace(
        directories=SimpleNamespace(root=tmp_path, config=tmp_path / "config"),
        document_store=FakeDocumentStore(),
        conversation_store=FakeConversationStore(),
        vector_store=FakeVectorStore(),
        memory_service=FakeMemoryService(),
        rag_service=FakeRagService(),
        model_config=make_config(),
    )
    app = create_app()
    app.dependency_overrides[build_api_services] = lambda: services
    return TestClient(app), services


def make_config() -> ModelConfig:
    return ModelConfig(
        chat=ChatModelConfig(
            base_url="https://chat.example.test/v1",
            api_key="chat-key",
            model="qwen-max",
        ),
        embedding=EmbeddingModelConfig(
            provider=EmbeddingProvider.OPENAI_COMPATIBLE,
            base_url="https://embedding.example.test/v1",
            api_key="embedding-key",
            model="text-embedding-v4",
        ),
        retrieval=RetrievalConfig(top_k=5),
    )


def make_session(session_id: str, title: str) -> ConversationSession:
    return ConversationSession(
        session_id=session_id,
        title=title,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def make_message(message_id: str, session_id: str, role: str, content: str):
    return ConversationMessage(
        message_id=message_id,
        session_id=session_id,
        role=role,
        content=content,
        created_at="2026-01-01T00:00:00+00:00",
    )


def make_document(document_id: str, filename: str) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        original_filename=filename,
        stored_filename=f"{document_id}.txt",
        file_path=Path(f"/tmp/{document_id}.txt"),
        file_type="txt",
        file_size=10,
        file_md5=f"{document_id}-file-md5",
        text_md5=f"{document_id}-text-md5",
        duplicate_of_document_id=None,
        status=STATUS_UPLOADED,
        parse_status=PARSE_STATUS_PARSED,
        index_status=INDEX_STATUS_INDEXED,
        chunk_count=2,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


class FakeConversationStore:
    def __init__(self) -> None:
        self.session = make_session("session-1", "Initial")
        self.created_titles: list[str | None] = []

    def create_session(self, title: str | None = None) -> ConversationSession:
        self.created_titles.append(title)
        self.session = make_session("session-1", title or "New conversation")
        return self.session

    def list_sessions(self) -> list[ConversationSession]:
        return [self.session]

    def get_conversation(self, session_id: str):
        return SimpleNamespace(
            session=self.session,
            messages=[
                make_message("message-1", session_id, "user", "Question"),
                make_message("message-2", session_id, "assistant", "Answer"),
            ],
        )

    def rename_session(self, session_id: str, title: str) -> ConversationSession:
        self.session = make_session(session_id, title)
        return self.session


class FakeMemoryService:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def delete_session_with_memories(self, session_id: str):
        self.deleted.append(session_id)
        return SimpleNamespace(ok=True, message="Conversation deleted.", session_id=session_id)


class FakeRagService:
    def __init__(self) -> None:
        self.questions: list[tuple[str, str | None]] = []

    def answer_question(self, question: str, *, session_id: str | None = None):
        self.questions.append((question, session_id))
        return SimpleNamespace(
            ok=True,
            message="Answer generated and saved.",
            session_id=session_id or "session-1",
            answer="容易",
            user_message=None,
            assistant_message=None,
            knowledge_result_count=1,
            memory_result_count=0,
        )


class FakeDocumentStore:
    def __init__(self) -> None:
        self.uploaded: list[tuple[str, bytes]] = []

    def list_documents(self) -> list[DocumentRecord]:
        return [make_document("doc-new", "new.txt")]

    def upload_document(self, filename: str, content_bytes: bytes):
        self.uploaded.append((filename, content_bytes))
        if "duplicate" in filename:
            return SimpleNamespace(
                ok=False,
                message="Document already exists.",
                document=None,
                duplicate_document=make_document("doc-existing", "existing.txt"),
            )
        return SimpleNamespace(
            ok=True,
            message="Document uploaded.",
            document=make_document("doc-new", filename),
            duplicate_document=None,
        )

    def delete_document(self, document_id: str, vector_store):
        return SimpleNamespace(
            ok=True,
            message=f"Deleted document {document_id}.",
            document_id=document_id,
            deleted_vectors=1,
        )

    def mark_reindex_requested(self, document_id: str):
        return make_document(document_id, "new.txt")


class FakeDocumentProcessor:
    def __init__(self) -> None:
        self.processed: list[tuple[str, bool]] = []

    def process_document(self, document_id: str, *, reindex: bool = False):
        self.processed.append((document_id, reindex))
        return SimpleNamespace(
            ok=True,
            message="Wrote 1 vectors to knowledge_chunks.",
            document=make_document(document_id, "new.txt"),
            text_md5="text-md5",
            duplicate_of_document_id=None,
            chunk_count=1,
        )


class FakeVectorStore:
    pass
