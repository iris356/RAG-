from __future__ import annotations

from pathlib import Path

from rag_app.app import (
    AppServices,
    DEFAULT_LANGUAGE,
    LANGUAGE_EN,
    LANGUAGE_ZH,
    _conversation_select_index,
    _conversation_table_row,
    _document_table_row,
    _format_conversation_option,
    _format_document_option,
    _format_duplicate_document,
    _selected_session_id,
    default_language,
    language_options,
    page_label,
    process_uploaded_document_for_web,
    resolve_language,
    tr,
    ui_message,
)
from rag_app.conversations.store import ROLE_USER, ConversationSession, ConversationStore
from rag_app.documents.store import (
    INDEX_STATUS_INDEXED,
    PARSE_STATUS_PARSED,
    STATUS_DUPLICATE,
    STATUS_UPLOADED,
    DocumentRecord,
)


def test_default_language_and_language_options() -> None:
    assert default_language() == DEFAULT_LANGUAGE == LANGUAGE_ZH
    assert language_options() == ("中文", "English")
    assert resolve_language("中文") == LANGUAGE_ZH
    assert resolve_language("English") == LANGUAGE_EN
    assert resolve_language("missing") == LANGUAGE_ZH


def test_key_ui_text_is_localized() -> None:
    assert page_label("qa", LANGUAGE_ZH) == "问答会话"
    assert page_label("qa", LANGUAGE_EN) == "Q&A session"
    assert tr(LANGUAGE_ZH, "app.title") == "RAG 知识库助手"
    assert tr(LANGUAGE_ZH, "app.caption") == "基于 Python 和 LangChain 的本地知识库问答工具"
    assert tr(LANGUAGE_ZH, "qa.ask") == "提问"
    assert tr(LANGUAGE_EN, "qa.ask") == "Ask"
    assert tr(LANGUAGE_ZH, "document.table.filename") == "文件名"
    assert tr(LANGUAGE_EN, "document.table.filename") == "Filename"
    assert "不是重试次数" in tr(LANGUAGE_ZH, "model.batch_interval_help")


def test_known_service_messages_are_localized() -> None:
    assert ui_message("Answer generated and saved.", LANGUAGE_ZH) == "回答已生成并保存。"
    assert ui_message("Answer generated and saved.", LANGUAGE_EN) == "Answer generated and saved."
    assert (
        ui_message("Wrote 3 vectors to knowledge_chunks.", LANGUAGE_ZH)
        == "已向 knowledge_chunks 写入 3 个向量。"
    )
    assert (
        ui_message("Chat model test failed: bad key", LANGUAGE_ZH)
        == "聊天模型测试失败：bad key"
    )


def test_selected_session_falls_back_to_first_session() -> None:
    sessions = [
        make_session("session-1", "First"),
        make_session("session-2", "Second"),
    ]

    assert _selected_session_id(sessions, "session-2") == "session-2"
    assert _selected_session_id(sessions, "missing") == "session-1"
    assert _selected_session_id(sessions, None) == "session-1"
    assert _selected_session_id([], "session-1") is None


def test_conversation_select_index_uses_selected_session_or_first() -> None:
    sessions = [
        make_session("session-1", "First"),
        make_session("session-2", "Second"),
    ]

    assert _conversation_select_index(sessions, "session-2") == 1
    assert _conversation_select_index(sessions, "missing") == 0
    assert _conversation_select_index([], "missing") == 0


def test_conversation_option_formatting() -> None:
    sessions = [make_session("session-1", "Research")]

    assert _format_conversation_option("session-1", sessions) == "Research (session-1)"
    assert _format_conversation_option("missing", sessions) == "missing"


def test_conversation_table_row_includes_message_count(tmp_path: Path) -> None:
    store = ConversationStore(
        sqlite_dir=tmp_path,
        id_factory=next_value(["session-1", "message-1", "message-2"]),
    )
    session = store.create_session("Research")
    store.add_message(session.session_id, ROLE_USER, "First")
    store.add_message(session.session_id, ROLE_USER, "Second")

    row = _conversation_table_row(store, session, LANGUAGE_EN)

    assert row["Session ID"] == "session-1"
    assert row["Title"] == "Research"
    assert row["Messages"] == 2

    zh_row = _conversation_table_row(store, session, LANGUAGE_ZH)
    assert zh_row["会话 ID"] == "session-1"
    assert zh_row["标题"] == "Research"
    assert zh_row["消息数"] == 2


def test_document_option_and_duplicate_formatting() -> None:
    original = make_document("doc-1", "original.txt")
    duplicate = make_document(
        "doc-2",
        "copy.txt",
        status=STATUS_DUPLICATE,
        duplicate_of_document_id="doc-1",
    )
    documents = [duplicate, original]

    assert _format_document_option("doc-1", documents) == "original.txt (doc-1)"
    assert _format_document_option("missing", documents) == "missing"
    assert _format_duplicate_document(original, documents, LANGUAGE_EN) == "No"
    assert (
        _format_duplicate_document(duplicate, documents, LANGUAGE_EN)
        == "Yes: original.txt (doc-1)"
    )
    assert _format_duplicate_document(original, documents, LANGUAGE_ZH) == "否"
    assert (
        _format_duplicate_document(duplicate, documents, LANGUAGE_ZH)
        == "是：original.txt（doc-1）"
    )


def test_document_table_row_shows_duplicate_source() -> None:
    original = make_document("doc-1", "original.txt")
    duplicate = make_document(
        "doc-2",
        "copy.txt",
        status=STATUS_DUPLICATE,
        duplicate_of_document_id="doc-1",
    )

    row = _document_table_row(duplicate, [duplicate, original], LANGUAGE_EN)

    assert row["Document ID"] == "doc-2"
    assert row["Status"] == STATUS_DUPLICATE
    assert row["Duplicate"] == "Yes: original.txt (doc-1)"

    zh_row = _document_table_row(duplicate, [duplicate, original], LANGUAGE_ZH)
    assert zh_row["文档 ID"] == "doc-2"
    assert zh_row["状态"] == STATUS_DUPLICATE
    assert zh_row["重复"] == "是：original.txt（doc-1）"


def test_uploaded_new_document_is_automatically_indexed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store = FakeDocumentStore(upload_result=FakeUploadResult(ok=True))
    processor = FakeDocumentProcessor(ok=True)
    monkeypatch.setattr("rag_app.app.DocumentProcessor", lambda **_: processor)
    silence_streamlit(monkeypatch)

    process_uploaded_document_for_web(
        make_services(tmp_path, document_store=store, vector_store=object()),
        FakeUploadedFile("new.txt", b"content"),
        LANGUAGE_EN,
    )

    assert store.uploaded == [("new.txt", b"content")]
    assert processor.processed == [("doc-1", True)]


def test_uploaded_duplicate_document_is_not_indexed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store = FakeDocumentStore(
        upload_result=FakeUploadResult(
            ok=False,
            document=None,
            duplicate_document=make_document("doc-existing", "existing.txt"),
        )
    )
    processor = FakeDocumentProcessor(ok=True)
    monkeypatch.setattr("rag_app.app.DocumentProcessor", lambda **_: processor)
    silence_streamlit(monkeypatch)

    process_uploaded_document_for_web(
        make_services(tmp_path, document_store=store, vector_store=object()),
        FakeUploadedFile("existing.txt", b"content"),
        LANGUAGE_EN,
    )

    assert store.uploaded == [("existing.txt", b"content")]
    assert processor.processed == []


def make_session(session_id: str, title: str) -> ConversationSession:
    return ConversationSession(
        session_id=session_id,
        title=title,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def make_document(
    document_id: str,
    filename: str,
    *,
    status: str = STATUS_UPLOADED,
    duplicate_of_document_id: str | None = None,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        original_filename=filename,
        stored_filename=f"{document_id}.txt",
        file_path=Path(f"/tmp/{document_id}.txt"),
        file_type="txt",
        file_size=10,
        file_md5=f"{document_id}-file-md5",
        text_md5=f"{document_id}-text-md5",
        duplicate_of_document_id=duplicate_of_document_id,
        status=status,
        parse_status=PARSE_STATUS_PARSED,
        index_status=INDEX_STATUS_INDEXED,
        chunk_count=2,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def next_value(values: list[str]):
    remaining = list(values)

    def _next_value() -> str:
        if len(remaining) == 1:
            return remaining[0]
        return remaining.pop(0)

    return _next_value


class FakeUploadedFile:
    def __init__(self, name: str, content: bytes) -> None:
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content


class FakeUploadResult:
    def __init__(
        self,
        *,
        ok: bool,
        document: DocumentRecord | None = None,
        duplicate_document: DocumentRecord | None = None,
    ) -> None:
        self.ok = ok
        self.message = "Document uploaded: new.txt." if ok else "Document already exists."
        self.document = document if document is not None else make_document("doc-1", "new.txt")
        self.duplicate_document = duplicate_document
        if not ok and duplicate_document is not None:
            self.document = None


class FakeDocumentStore:
    def __init__(self, *, upload_result: FakeUploadResult) -> None:
        self.upload_result = upload_result
        self.uploaded: list[tuple[str, bytes]] = []

    def upload_document(self, filename: str, content_bytes: bytes) -> FakeUploadResult:
        self.uploaded.append((filename, content_bytes))
        return self.upload_result


class FakeDocumentProcessor:
    def __init__(self, *, ok: bool) -> None:
        self.ok = ok
        self.processed: list[tuple[str, bool]] = []

    def process_document(self, document_id: str, *, reindex: bool = False):
        self.processed.append((document_id, reindex))
        document = make_document(document_id, "new.txt")

        class Result:
            duplicate_of_document_id = None
            vector_write_result = None
            deleted_vectors = 0

            def __init__(self, ok: bool) -> None:
                self.ok = ok
                self.message = "Wrote 1 vectors to knowledge_chunks."
                self.document = document

        return Result(self.ok)


def make_services(
    tmp_path: Path,
    *,
    document_store,
    vector_store,
) -> AppServices:
    return AppServices(
        directories=None,
        document_store=document_store,
        conversation_store=None,
        vector_store=vector_store,
        memory_service=None,
        rag_service=None,
        model_config=None,
    )


def silence_streamlit(monkeypatch) -> None:
    for name in ("success", "info", "warning", "error", "caption"):
        monkeypatch.setattr(f"rag_app.app.st.{name}", lambda *_, **__: None)
