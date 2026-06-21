"""Streamlit entrypoint for the RAG knowledge app."""

from __future__ import annotations

import re
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

LANGUAGE_ZH = "zh"
LANGUAGE_EN = "en"
LANGUAGE_OPTIONS = ("中文", "English")
LANGUAGE_CODES_BY_LABEL = {"中文": LANGUAGE_ZH, "English": LANGUAGE_EN}
LANGUAGE_LABELS_BY_CODE = {value: key for key, value in LANGUAGE_CODES_BY_LABEL.items()}
DEFAULT_LANGUAGE = LANGUAGE_ZH
LANGUAGE_STATE_KEY = "app_language"
LANGUAGE_WIDGET_STATE_KEY = "app_language_label"

PAGE_QA = "qa"
PAGE_HISTORY = "history"
PAGE_DOCUMENTS = "documents"
PAGE_MODEL = "model"
PAGE_OVERVIEW = "overview"
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

LEGACY_PAGE_KEYS = {
    "Q&A session": PAGE_QA,
    "Conversation history": PAGE_HISTORY,
    "Document management": PAGE_DOCUMENTS,
    "Model configuration": PAGE_MODEL,
    "Overview": PAGE_OVERVIEW,
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    LANGUAGE_ZH: {
        "app.caption": "Python + LangChain RAG 知识库",
        "language.label": "界面语言",
        "sidebar.navigation": "导航",
        "sidebar.page": "页面",
        "sidebar.data_root": "数据根目录：`{root}`",
        "page.qa": "问答会话",
        "page.history": "历史会话",
        "page.documents": "文档管理",
        "page.model": "模型配置",
        "page.overview": "概览",
        "overview.data_directories": "数据目录",
        "overview.module_status": "模块状态",
        "overview.column.name": "名称",
        "overview.column.path": "路径",
        "overview.raw_files": "原始文件",
        "overview.chroma": "Chroma",
        "overview.sqlite": "SQLite",
        "overview.config": "配置",
        "overview.tmp": "临时文件",
        "overview.module_ready": "模块 {number}：{name} 已就绪。",
        "module.01": "项目基础",
        "module.02": "模型配置",
        "module.03": "向量库",
        "module.04": "文档管理",
        "module.05": "文档解析与切分",
        "module.06": "历史会话",
        "module.07": "会话长期记忆",
        "module.08": "RAG 问答",
        "module.09": "Web 交互",
        "conversation.no_conversations_auto": "暂无会话。直接提问会自动创建新会话。",
        "conversation.no_conversations": "暂无会话。",
        "conversation.new_title": "新会话标题",
        "conversation.optional": "可选",
        "conversation.create": "创建会话",
        "conversation.created": "已创建会话：{title}。",
        "conversation.create_failed": "创建会话失败：{error}",
        "conversation.selector": "会话",
        "qa.question": "问题",
        "qa.question_placeholder": "向知识库提问",
        "qa.ask": "提问",
        "qa.answer_failed": "回答问题失败：{error}",
        "conversation.open_failed": "打开会话失败：{error}",
        "conversation.no_messages_yet": "当前会话暂无消息。",
        "conversation.no_messages": "该会话暂无消息。",
        "conversation.load_failed": "加载会话失败：{error}",
        "conversation.open_in_qa": "在问答页打开",
        "conversation.rebuild_memory": "重建记忆",
        "conversation.rebuild_memory_failed": "重建会话记忆失败：{error}",
        "conversation.new_title_label": "新标题",
        "conversation.rename": "重命名",
        "conversation.renamed": "会话已重命名。",
        "conversation.rename_failed": "重命名会话失败：{error}",
        "conversation.delete": "删除会话",
        "conversation.delete_failed": "删除会话失败：{error}",
        "conversation.load_list_failed": "加载会话列表失败：{error}",
        "conversation.table.session_id": "会话 ID",
        "conversation.table.title": "标题",
        "conversation.table.messages": "消息数",
        "conversation.table.created": "创建时间",
        "conversation.table.updated": "更新时间",
        "document.upload_section": "上传文档",
        "document.file_label": "PDF、Word、Markdown 或 TXT",
        "document.upload": "上传文档",
        "document.duplicate_of": "重复来源：{filename}（{document_id}）。",
        "document.upload_failed": "上传文档失败：{error}",
        "document.none_uploaded": "暂无已上传文档。",
        "document.documents": "文档",
        "document.selector": "文档",
        "document.duplicate_warning": "该文档正文与已有文档重复，默认不会重复入库。原始 document_id={document_id}。",
        "document.parse_index": "解析并索引",
        "document.delete": "删除文档",
        "document.deleted_vectors": "{message} 已删除向量：{count}。",
        "document.delete_failed": "删除文档失败：{error}",
        "document.parse_failed": "解析并索引文档失败：{error}",
        "document.text_duplicate": "该资料正文与已有文档重复，未重复入库。原始 document_id={document_id}。",
        "document.deleted_old_vectors": "重建索引前已删除旧向量：{count}。",
        "document.load_failed": "加载文档列表失败：{error}",
        "document.table.document_id": "文档 ID",
        "document.table.filename": "文件名",
        "document.table.type": "类型",
        "document.table.size": "大小",
        "document.table.status": "状态",
        "document.table.parse": "解析",
        "document.table.index": "索引",
        "document.table.chunks": "分块数",
        "document.table.duplicate": "重复",
        "document.table.created": "创建时间",
        "document.table.updated": "更新时间",
        "duplicate.no": "否",
        "duplicate.yes_id": "是：{document_id}",
        "duplicate.yes_document": "是：{filename}（{document_id}）",
        "model.chat_section": "聊天模型",
        "model.chat_base_url": "聊天 Base URL",
        "model.chat_api_key": "聊天 API Key",
        "model.chat_model": "聊天模型",
        "model.embedding_section": "向量模型",
        "model.embedding_provider": "向量 Provider",
        "model.embedding_model": "向量模型",
        "model.embedding_placeholder": "text-embedding-v4 或本地模型路径",
        "model.embedding_base_url": "向量 Base URL",
        "model.embedding_api_key": "向量 API Key",
        "model.retrieval_limits": "检索与本地向量限速",
        "model.top_k": "Top K",
        "model.batch_size": "向量批量大小",
        "model.max_concurrency": "向量最大并发数",
        "model.batch_interval": "向量批次间隔秒数",
        "model.save_chat": "保存聊天配置",
        "model.save_embedding": "保存向量配置",
        "model.test_chat": "测试聊天模型",
        "model.test_embedding": "测试向量模型",
        "model.chat_saved": "聊天配置已保存到 `{path}`。",
        "model.chat_save_failed": "保存聊天配置失败：{error}",
        "model.embedding_saved": "向量配置已保存到 `{path}`。",
        "model.embedding_save_failed": "保存向量配置失败：{error}",
        "rag.retrieved_context": "已检索上下文：{knowledge} 个知识库片段，{memory} 条会话记忆。",
        "memory.deleted_old_vectors": "重建前已删除旧记忆向量：{count}。",
        "memory.write_progress": "记忆写入进度",
        "memory.sync_progress": "记忆同步进度：{written}/{total} 条消息。",
        "vector.write_progress": "向量写入进度",
        "vector.progress": "{label}：{processed_texts}/{total_texts} 个{unit}，{processed_batches}/{total_batches} 个批次。",
        "vector.failed_batch": "失败批次：{batch}。",
        "vector.local_memory_hint": "如果本地向量模型内存不足，请在模型配置中调小向量批量大小或降低最大并发数。",
        "unit.chunks": "分块",
        "unit.messages": "消息",
        "unavailable": "不可用",
        "service.document_uploaded": "文档已上传：{filename}。",
        "service.document_duplicate": "文档已存在，上传文件未重复保存。现有 document_id={document_id}。",
        "service.answer_saved": "回答已生成并保存。",
        "service.answer_saved_memory_failed": "回答已保存，但一条或多条会话记忆写入失败。请使用重建记忆修复该会话。",
        "service.no_vectors": "没有需要写入的向量。",
        "service.wrote_vectors": "已向 {collection} 写入 {count} 个向量。",
        "service.vector_batch_failed": "向量批次 {batch} 失败：{error}",
        "service.knowledge_vectors_exist": "document_id={document_id} 的知识库向量已存在。请先删除后再重建索引。",
        "service.no_messages_to_write": "没有需要写入的会话消息。",
        "service.deleted_memory_vectors": "已删除 {count} 个会话记忆向量。",
        "service.conversation_deleted": "会话已删除。已删除 SQLite 消息：{messages}。已删除记忆向量：{vectors}。",
        "service.document_deleted": "已删除文档 {document_id}。",
        "service.document_parse_failed": "文档解析失败：{error}",
        "service.document_split_failed": "文档切分失败：{error}",
        "service.document_text_duplicate": "该资料正文与已有文档重复，已跳过索引。原始 document_id={document_id}。",
        "service.duplicate_not_reindexed": "重复文档默认不会重建索引。原始 document_id={document_id}。",
        "service.chat_test_success": "聊天模型测试成功：{summary}",
        "service.chat_test_failed": "聊天模型测试失败：{error}",
        "service.embedding_empty": "向量模型返回了空向量。",
        "service.embedding_test_success": "向量模型测试成功：向量维度 {dimension}。",
        "service.embedding_test_failed": "向量模型测试失败：{error}",
    },
    LANGUAGE_EN: {
        "app.caption": "Python + LangChain RAG knowledge base",
        "language.label": "Language",
        "sidebar.navigation": "Navigation",
        "sidebar.page": "Page",
        "sidebar.data_root": "Data root: `{root}`",
        "page.qa": "Q&A session",
        "page.history": "Conversation history",
        "page.documents": "Document management",
        "page.model": "Model configuration",
        "page.overview": "Overview",
        "overview.data_directories": "Data directories",
        "overview.module_status": "Module status",
        "overview.column.name": "Name",
        "overview.column.path": "Path",
        "overview.raw_files": "Raw files",
        "overview.chroma": "Chroma",
        "overview.sqlite": "SQLite",
        "overview.config": "Config",
        "overview.tmp": "Temporary files",
        "overview.module_ready": "Module {number}: {name} is ready.",
        "module.01": "Project foundation",
        "module.02": "Model configuration",
        "module.03": "Vector store",
        "module.04": "Document management",
        "module.05": "Document parsing and splitting",
        "module.06": "Conversation history",
        "module.07": "Conversation long-term memory",
        "module.08": "RAG question answering",
        "module.09": "Web interaction",
        "conversation.no_conversations_auto": "No conversations yet. Ask a question to create one automatically.",
        "conversation.no_conversations": "No conversations yet.",
        "conversation.new_title": "New conversation title",
        "conversation.optional": "Optional",
        "conversation.create": "Create conversation",
        "conversation.created": "Created conversation: {title}.",
        "conversation.create_failed": "Failed to create conversation: {error}",
        "conversation.selector": "Conversation",
        "qa.question": "Question",
        "qa.question_placeholder": "Ask the knowledge base",
        "qa.ask": "Ask",
        "qa.answer_failed": "Failed to answer question: {error}",
        "conversation.open_failed": "Failed to open conversation: {error}",
        "conversation.no_messages_yet": "No messages in this conversation yet.",
        "conversation.no_messages": "No messages in this conversation.",
        "conversation.load_failed": "Failed to load conversation: {error}",
        "conversation.open_in_qa": "Open in Q&A",
        "conversation.rebuild_memory": "Rebuild memory",
        "conversation.rebuild_memory_failed": "Failed to rebuild conversation memory: {error}",
        "conversation.new_title_label": "New title",
        "conversation.rename": "Rename",
        "conversation.renamed": "Conversation renamed.",
        "conversation.rename_failed": "Failed to rename conversation: {error}",
        "conversation.delete": "Delete conversation",
        "conversation.delete_failed": "Failed to delete conversation: {error}",
        "conversation.load_list_failed": "Failed to load conversations: {error}",
        "conversation.table.session_id": "Session ID",
        "conversation.table.title": "Title",
        "conversation.table.messages": "Messages",
        "conversation.table.created": "Created",
        "conversation.table.updated": "Updated",
        "document.upload_section": "Upload document",
        "document.file_label": "PDF, Word, Markdown, or TXT",
        "document.upload": "Upload document",
        "document.duplicate_of": "Duplicate of {filename} ({document_id}).",
        "document.upload_failed": "Failed to upload document: {error}",
        "document.none_uploaded": "No documents uploaded yet.",
        "document.documents": "Documents",
        "document.selector": "Document",
        "document.duplicate_warning": "This document duplicates existing parsed text and is not indexed by default. Original document_id={document_id}.",
        "document.parse_index": "Parse and index",
        "document.delete": "Delete document",
        "document.deleted_vectors": "{message} Deleted vectors: {count}.",
        "document.delete_failed": "Failed to delete document: {error}",
        "document.parse_failed": "Failed to parse and index document: {error}",
        "document.text_duplicate": "Document text duplicates an existing document; it was not indexed again. Original document_id={document_id}.",
        "document.deleted_old_vectors": "Deleted old vectors before reindex: {count}.",
        "document.load_failed": "Failed to load documents: {error}",
        "document.table.document_id": "Document ID",
        "document.table.filename": "Filename",
        "document.table.type": "Type",
        "document.table.size": "Size",
        "document.table.status": "Status",
        "document.table.parse": "Parse",
        "document.table.index": "Index",
        "document.table.chunks": "Chunks",
        "document.table.duplicate": "Duplicate",
        "document.table.created": "Created",
        "document.table.updated": "Updated",
        "duplicate.no": "No",
        "duplicate.yes_id": "Yes: {document_id}",
        "duplicate.yes_document": "Yes: {filename} ({document_id})",
        "model.chat_section": "Chat model",
        "model.chat_base_url": "Chat base URL",
        "model.chat_api_key": "Chat API key",
        "model.chat_model": "Chat model",
        "model.embedding_section": "Embedding model",
        "model.embedding_provider": "Embedding provider",
        "model.embedding_model": "Embedding model",
        "model.embedding_placeholder": "text-embedding-v4 or local model path",
        "model.embedding_base_url": "Embedding base URL",
        "model.embedding_api_key": "Embedding API key",
        "model.retrieval_limits": "Retrieval and local embedding limits",
        "model.top_k": "Top K",
        "model.batch_size": "Embedding batch size",
        "model.max_concurrency": "Embedding max concurrency",
        "model.batch_interval": "Embedding batch interval seconds",
        "model.save_chat": "Save chat",
        "model.save_embedding": "Save embedding",
        "model.test_chat": "Test chat model",
        "model.test_embedding": "Test embedding model",
        "model.chat_saved": "Chat configuration saved to `{path}`.",
        "model.chat_save_failed": "Failed to save chat configuration: {error}",
        "model.embedding_saved": "Embedding configuration saved to `{path}`.",
        "model.embedding_save_failed": "Failed to save embedding configuration: {error}",
        "rag.retrieved_context": "Retrieved context: {knowledge} knowledge chunks, {memory} conversation memories.",
        "memory.deleted_old_vectors": "Deleted old memory vectors before rebuild: {count}.",
        "memory.write_progress": "Memory write progress",
        "memory.sync_progress": "Memory sync progress: {written}/{total} messages.",
        "vector.write_progress": "Vector write progress",
        "vector.progress": "{label}: {processed_texts}/{total_texts} {unit}, {processed_batches}/{total_batches} batches.",
        "vector.failed_batch": "Failed batch: {batch}.",
        "vector.local_memory_hint": "If a local embedding model ran out of memory, lower the embedding batch size or max concurrency in Model configuration.",
        "unit.chunks": "chunks",
        "unit.messages": "messages",
        "unavailable": "Unavailable",
        "service.document_uploaded": "Document uploaded: {filename}.",
        "service.document_duplicate": "Document already exists; the uploaded file was not saved again. Existing document_id={document_id}.",
        "service.answer_saved": "Answer generated and saved.",
        "service.answer_saved_memory_failed": "Answer saved, but one or more conversation memories failed to write. Use rebuild memory to repair this conversation.",
        "service.no_vectors": "No vectors to write.",
        "service.wrote_vectors": "Wrote {count} vectors to {collection}.",
        "service.vector_batch_failed": "Vector batch {batch} failed: {error}",
        "service.knowledge_vectors_exist": "Knowledge vectors already exist for document_id={document_id}. Delete them before re-indexing.",
        "service.no_messages_to_write": "No conversation messages to write.",
        "service.deleted_memory_vectors": "Deleted {count} conversation memory vectors.",
        "service.conversation_deleted": "Conversation deleted. Deleted SQLite messages: {messages}. Deleted memory vectors: {vectors}.",
        "service.document_deleted": "Deleted document {document_id}.",
        "service.document_parse_failed": "Document parsing failed: {error}",
        "service.document_split_failed": "Document splitting failed: {error}",
        "service.document_text_duplicate": "Document text duplicates an existing document; skipped indexing. Original document_id={document_id}.",
        "service.duplicate_not_reindexed": "Duplicate documents are not indexed by default. Original document_id={document_id}.",
        "service.chat_test_success": "Chat model test succeeded: {summary}",
        "service.chat_test_failed": "Chat model test failed: {error}",
        "service.embedding_empty": "Embedding model returned an empty vector.",
        "service.embedding_test_success": "Embedding model test succeeded: vector dimension {dimension}.",
        "service.embedding_test_failed": "Embedding model test failed: {error}",
    },
}


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


def tr(language: str, key: str, **values: Any) -> str:
    """Return localized Web UI text for the requested language."""

    catalog = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    template = catalog.get(key, TRANSLATIONS[LANGUAGE_EN].get(key, key))
    return template.format(**values) if values else template


def default_language() -> str:
    """Return the default UI language code."""

    return DEFAULT_LANGUAGE


def language_options() -> tuple[str, ...]:
    """Return labels shown by the language selector."""

    return LANGUAGE_OPTIONS


def resolve_language(label_or_code: str | None) -> str:
    """Resolve a user-facing language label or stored code to a language code."""

    if label_or_code in (LANGUAGE_ZH, LANGUAGE_EN):
        return label_or_code
    if label_or_code in LANGUAGE_CODES_BY_LABEL:
        return LANGUAGE_CODES_BY_LABEL[label_or_code]
    return DEFAULT_LANGUAGE


def page_label(page: str, language: str) -> str:
    """Return localized navigation label for a stable page key."""

    return tr(language, f"page.{page}")


def ui_message(message: str, language: str) -> str:
    """Localize known service-layer result messages for Web display."""

    exact_keys = {
        "Answer generated and saved.": "service.answer_saved",
        (
            "Answer saved, but one or more conversation memories failed to write. "
            "Use rebuild memory to repair this conversation."
        ): "service.answer_saved_memory_failed",
        "No vectors to write.": "service.no_vectors",
        "No conversation messages to write.": "service.no_messages_to_write",
        "Embedding model returned an empty vector.": "service.embedding_empty",
    }
    if message in exact_keys:
        return tr(language, exact_keys[message])

    patterns = (
        (
            r"^Wrote (?P<count>\d+) vectors to (?P<collection>.+)\.$",
            "service.wrote_vectors",
            ("count", "collection"),
        ),
        (
            r"^Vector batch (?P<batch>\d+) failed: (?P<error>.+)$",
            "service.vector_batch_failed",
            ("batch", "error"),
        ),
        (
            r"^Knowledge vectors already exist for document_id=(?P<document_id>.+)\. "
            r"Delete them before re-indexing\.$",
            "service.knowledge_vectors_exist",
            ("document_id",),
        ),
        (
            r"^Deleted (?P<count>\d+) conversation memory vectors\.$",
            "service.deleted_memory_vectors",
            ("count",),
        ),
        (
            r"^Conversation deleted\. Deleted SQLite messages: (?P<messages>\d+)\. "
            r"Deleted memory vectors: (?P<vectors>\d+)\.$",
            "service.conversation_deleted",
            ("messages", "vectors"),
        ),
        (
            r"^Deleted document (?P<document_id>.+)\.$",
            "service.document_deleted",
            ("document_id",),
        ),
        (
            r"^Document parsing failed: (?P<error>.+)$",
            "service.document_parse_failed",
            ("error",),
        ),
        (
            r"^Document splitting failed: (?P<error>.+)$",
            "service.document_split_failed",
            ("error",),
        ),
        (
            r"^Document text duplicates an existing document; skipped indexing\. "
            r"Original document_id=(?P<document_id>.+)\.$",
            "service.document_text_duplicate",
            ("document_id",),
        ),
        (
            r"^Duplicate documents are not indexed by default\. "
            r"Original document_id=(?P<document_id>.+)\.$",
            "service.duplicate_not_reindexed",
            ("document_id",),
        ),
        (
            r"^Chat model test succeeded: (?P<summary>.+)$",
            "service.chat_test_success",
            ("summary",),
        ),
        (
            r"^Chat model test failed: (?P<error>.+)$",
            "service.chat_test_failed",
            ("error",),
        ),
        (
            r"^Embedding model test succeeded: vector dimension (?P<dimension>\d+)\.$",
            "service.embedding_test_success",
            ("dimension",),
        ),
        (
            r"^Embedding model test failed: (?P<error>.+)$",
            "service.embedding_test_failed",
            ("error",),
        ),
    )
    for pattern, key, group_names in patterns:
        match = re.match(pattern, message)
        if match:
            return tr(
                language,
                key,
                **{group_name: match.group(group_name) for group_name in group_names},
            )
    return message


def main() -> None:
    """Render the Streamlit application."""

    settings = get_settings()
    configure_logging(settings.log_level)
    directories = ensure_data_directories(settings.data_dir)

    st.set_page_config(page_title=settings.app_name, page_icon=":books:", layout="wide")
    st.title(settings.app_name)

    services = build_app_services(directories)
    page, language = render_sidebar(directories)
    st.caption(tr(language, "app.caption"))

    if page == PAGE_QA:
        render_qa_page(services, language)
    elif page == PAGE_HISTORY:
        render_conversation_history_page(services, language)
    elif page == PAGE_DOCUMENTS:
        render_document_management_page(services, language)
    elif page == PAGE_MODEL:
        render_model_configuration_page(directories.config, language)
    else:
        render_overview_page(directories, language)


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


def render_sidebar(directories: DataDirectories) -> tuple[str, str]:
    """Render language selection and page navigation."""

    current_language = resolve_language(st.session_state.get(LANGUAGE_STATE_KEY))
    current_label = LANGUAGE_LABELS_BY_CODE[current_language]
    selected_language_label = st.sidebar.selectbox(
        tr(current_language, "language.label"),
        LANGUAGE_OPTIONS,
        index=LANGUAGE_OPTIONS.index(current_label),
        key=LANGUAGE_WIDGET_STATE_KEY,
    )
    language = resolve_language(selected_language_label)
    st.session_state[LANGUAGE_STATE_KEY] = language

    requested_page = st.session_state.pop(REQUESTED_PAGE_STATE_KEY, None)
    requested_page = LEGACY_PAGE_KEYS.get(requested_page, requested_page)
    if requested_page in NAVIGATION_PAGES:
        st.session_state[NAVIGATION_STATE_KEY] = requested_page
    current_page = LEGACY_PAGE_KEYS.get(st.session_state.get(NAVIGATION_STATE_KEY))
    if current_page:
        st.session_state[NAVIGATION_STATE_KEY] = current_page
    if st.session_state.get(NAVIGATION_STATE_KEY) not in NAVIGATION_PAGES:
        st.session_state[NAVIGATION_STATE_KEY] = PAGE_QA

    st.sidebar.header(tr(language, "sidebar.navigation"))
    selected_page = st.sidebar.radio(
        tr(language, "sidebar.page"),
        NAVIGATION_PAGES,
        format_func=lambda page: page_label(page, language),
        key=NAVIGATION_STATE_KEY,
    )
    st.sidebar.divider()
    st.sidebar.caption(tr(language, "sidebar.data_root", root=directories.root))
    return selected_page, language


def render_overview_page(directories: DataDirectories, language: str) -> None:
    """Render data directories and module status."""

    st.header(page_label(PAGE_OVERVIEW, language))
    st.subheader(tr(language, "overview.data_directories"))
    st.table(
        [
            {
                tr(language, "overview.column.name"): tr(language, "overview.raw_files"),
                tr(language, "overview.column.path"): str(directories.raw),
            },
            {
                tr(language, "overview.column.name"): tr(language, "overview.chroma"),
                tr(language, "overview.column.path"): str(directories.chroma),
            },
            {
                tr(language, "overview.column.name"): tr(language, "overview.sqlite"),
                tr(language, "overview.column.path"): str(directories.sqlite),
            },
            {
                tr(language, "overview.column.name"): tr(language, "overview.config"),
                tr(language, "overview.column.path"): str(directories.config),
            },
            {
                tr(language, "overview.column.name"): tr(language, "overview.tmp"),
                tr(language, "overview.column.path"): str(directories.tmp),
            },
        ]
    )

    st.subheader(tr(language, "overview.module_status"))
    for module_number, module_key in (
        ("01", "module.01"),
        ("02", "module.02"),
        ("03", "module.03"),
        ("04", "module.04"),
        ("05", "module.05"),
        ("06", "module.06"),
        ("07", "module.07"),
        ("08", "module.08"),
        ("09", "module.09"),
    ):
        st.success(
            tr(
                language,
                "overview.module_ready",
                number=module_number,
                name=tr(language, module_key),
            )
        )


def render_qa_page(services: AppServices, language: str) -> None:
    """Render the main RAG question-answering page."""

    st.header(page_label(PAGE_QA, language))
    sessions = _load_sessions(services.conversation_store, language)

    control_col, selector_col = st.columns(2)
    with control_col:
        render_create_conversation_form(
            services.conversation_store,
            form_key="qa_create",
            language=language,
        )

    selected_session_id: str | None = None
    with selector_col:
        if sessions:
            selected_session_id = render_conversation_selector(
                sessions=sessions,
                key="qa_conversation_selector",
                language=language,
            )
        else:
            st.info(tr(language, "conversation.no_conversations_auto"))

    submitted_result = render_rag_question_form(
        rag_service=services.rag_service,
        session_id=selected_session_id,
        form_key="qa_rag_question_form",
        language=language,
    )
    if submitted_result is not None:
        selected_session_id = submitted_result.session_id
        st.session_state[SELECTED_CONVERSATION_STATE_KEY] = selected_session_id
        _show_rag_result(submitted_result, language)

    if selected_session_id:
        render_current_conversation(
            services.conversation_store,
            selected_session_id,
            language,
        )


def render_create_conversation_form(
    conversation_store: ConversationStore,
    *,
    form_key: str,
    language: str,
) -> None:
    """Render a small form for explicitly creating a new conversation."""

    with st.form(form_key):
        title = st.text_input(
            tr(language, "conversation.new_title"),
            placeholder=tr(language, "conversation.optional"),
        )
        submitted = st.form_submit_button(
            tr(language, "conversation.create"),
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        session = conversation_store.create_session(title.strip() or None)
        st.session_state[SELECTED_CONVERSATION_STATE_KEY] = session.session_id
        st.success(tr(language, "conversation.created", title=session.title))
        st.rerun()
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(tr(language, "conversation.create_failed", error=exc))


def render_conversation_selector(
    *,
    sessions: list[ConversationSession],
    key: str,
    language: str,
) -> str:
    """Render a conversation selector and persist the selected session ID."""

    selected_session_id = _selected_session_id(
        sessions,
        st.session_state.get(SELECTED_CONVERSATION_STATE_KEY),
    )
    index = _conversation_select_index(sessions, selected_session_id)
    selected = st.selectbox(
        tr(language, "conversation.selector"),
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
    language: str,
) -> RagAnswerResult | None:
    """Render a RAG question form and return the submitted result."""

    with st.form(form_key):
        question = st.text_area(
            tr(language, "qa.question"),
            placeholder=tr(language, "qa.question_placeholder"),
        )
        submitted = st.form_submit_button(tr(language, "qa.ask"), use_container_width=True)

    if not submitted:
        return None

    try:
        return rag_service.answer_question(question, session_id=session_id)
    except Exception as exc:  # noqa: BLE001 - show controlled RAG errors in UI.
        st.error(tr(language, "qa.answer_failed", error=exc))
        return None


def render_current_conversation(
    conversation_store: ConversationStore,
    session_id: str,
    language: str,
) -> None:
    """Render messages for the selected conversation."""

    try:
        conversation = conversation_store.get_conversation(session_id)
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(tr(language, "conversation.open_failed", error=exc))
        return

    st.subheader(conversation.session.title)
    if not conversation.messages:
        st.info(tr(language, "conversation.no_messages_yet"))
        return

    for message in conversation.messages:
        with st.chat_message(message.role):
            st.write(message.content)
            st.caption(message.created_at)


def render_conversation_history_page(services: AppServices, language: str) -> None:
    """Render conversation listing and management actions."""

    st.header(page_label(PAGE_HISTORY, language))
    sessions = _load_sessions(services.conversation_store, language)
    if not sessions:
        st.info(tr(language, "conversation.no_conversations"))
        render_create_conversation_form(
            services.conversation_store,
            form_key="history_create",
            language=language,
        )
        return

    st.dataframe(
        [
            _conversation_table_row(services.conversation_store, session, language)
            for session in sessions
        ],
        use_container_width=True,
        hide_index=True,
    )

    selected_session_id = render_conversation_selector(
        sessions=sessions,
        key="history_conversation_selector",
        language=language,
    )

    try:
        conversation = services.conversation_store.get_conversation(selected_session_id)
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(tr(language, "conversation.load_failed", error=exc))
        return

    action_col_1, action_col_2, action_col_3, action_col_4 = st.columns(4)
    with action_col_1:
        if st.button(tr(language, "conversation.open_in_qa"), use_container_width=True):
            st.session_state[SELECTED_CONVERSATION_STATE_KEY] = selected_session_id
            st.session_state[REQUESTED_PAGE_STATE_KEY] = PAGE_QA
            st.rerun()

    with action_col_2:
        if st.button(tr(language, "conversation.rebuild_memory"), use_container_width=True):
            try:
                result = services.memory_service.rebuild_session_memories(selected_session_id)
                _show_memory_result(result, language)
            except Exception as exc:  # noqa: BLE001 - show controlled memory errors.
                st.error(tr(language, "conversation.rebuild_memory_failed", error=exc))

    with action_col_3:
        with st.form("rename_conversation_form"):
            new_title = st.text_input(
                tr(language, "conversation.new_title_label"),
                value=conversation.session.title,
            )
            submitted = st.form_submit_button(
                tr(language, "conversation.rename"),
                use_container_width=True,
            )
        if submitted:
            try:
                services.conversation_store.rename_session(selected_session_id, new_title)
                st.success(tr(language, "conversation.renamed"))
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
                st.error(tr(language, "conversation.rename_failed", error=exc))

    with action_col_4:
        if st.button(tr(language, "conversation.delete"), use_container_width=True):
            try:
                result = services.memory_service.delete_session_with_memories(
                    selected_session_id
                )
                st.success(ui_message(result.message, language))
                st.session_state.pop(SELECTED_CONVERSATION_STATE_KEY, None)
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
                st.error(tr(language, "conversation.delete_failed", error=exc))

    st.subheader(conversation.session.title)
    if not conversation.messages:
        st.info(tr(language, "conversation.no_messages"))
    else:
        for message in conversation.messages:
            with st.chat_message(message.role):
                st.write(message.content)
                st.caption(message.created_at)


def render_document_management_page(services: AppServices, language: str) -> None:
    """Render document upload, listing, indexing, and deletion controls."""

    st.header(page_label(PAGE_DOCUMENTS, language))
    st.subheader(tr(language, "document.upload_section"))
    uploaded_file = st.file_uploader(
        tr(language, "document.file_label"),
        type=["pdf", "docx", "md", "markdown", "txt"],
    )
    if uploaded_file and st.button(tr(language, "document.upload"), use_container_width=True):
        try:
            result = services.document_store.upload_document(
                uploaded_file.name,
                uploaded_file.getvalue(),
            )
            if result.ok:
                if result.document is not None:
                    st.success(
                        tr(
                            language,
                            "service.document_uploaded",
                            filename=result.document.original_filename,
                        )
                    )
                else:
                    st.success(ui_message(result.message, language))
            else:
                if result.duplicate_document is not None:
                    st.warning(
                        tr(
                            language,
                            "service.document_duplicate",
                            document_id=result.duplicate_document.document_id,
                        )
                    )
                else:
                    st.warning(ui_message(result.message, language))
                if result.duplicate_document is not None:
                    st.info(
                        tr(
                            language,
                            "document.duplicate_of",
                            filename=result.duplicate_document.original_filename,
                            document_id=result.duplicate_document.document_id,
                        )
                    )
        except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
            st.error(tr(language, "document.upload_failed", error=exc))

    documents = _load_documents(services.document_store, language)
    if not documents:
        st.info(tr(language, "document.none_uploaded"))
        return

    st.subheader(tr(language, "document.documents"))
    st.dataframe(
        [_document_table_row(document, documents, language) for document in documents],
        use_container_width=True,
        hide_index=True,
    )

    selected_document_id = st.selectbox(
        tr(language, "document.selector"),
        options=[document.document_id for document in documents],
        format_func=lambda document_id: _format_document_option(document_id, documents),
    )
    selected_document = _find_document(selected_document_id, documents)
    if selected_document is not None and selected_document.duplicate_of_document_id:
        st.warning(
            tr(
                language,
                "document.duplicate_warning",
                document_id=selected_document.duplicate_of_document_id,
            )
        )

    action_col_1, action_col_2 = st.columns(2)
    with action_col_1:
        if st.button(tr(language, "document.parse_index"), use_container_width=True):
            process_document_for_web(services, selected_document_id, language)

    with action_col_2:
        if st.button(tr(language, "document.delete"), use_container_width=True):
            try:
                result = services.document_store.delete_document(
                    selected_document_id,
                    services.vector_store,
                )
                st.success(
                    tr(
                        language,
                        "document.deleted_vectors",
                        message=result.message,
                        count=result.deleted_vectors,
                    )
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - show controlled storage/vector errors.
                st.error(tr(language, "document.delete_failed", error=exc))


def process_document_for_web(
    services: AppServices,
    document_id: str,
    language: str,
) -> None:
    """Run document parsing/indexing and render the resulting status."""

    try:
        services.document_store.mark_reindex_requested(document_id)
        processor = DocumentProcessor(
            document_store=services.document_store,
            vector_store=services.vector_store,
        )
        result = processor.process_document(document_id, reindex=True)
        _show_document_process_result(result, language)
    except Exception as exc:  # noqa: BLE001 - show controlled processing errors.
        message = str(exc)
        if "Duplicate documents are not indexed by default" in message:
            st.warning(ui_message(message, language))
        else:
            st.error(tr(language, "document.parse_failed", error=exc))


def _show_document_process_result(result: DocumentProcessResult, language: str) -> None:
    if result.ok:
        st.success(ui_message(result.message, language))
    else:
        st.error(ui_message(result.message, language))

    if result.duplicate_of_document_id:
        st.info(
            tr(
                language,
                "document.text_duplicate",
                document_id=result.duplicate_of_document_id,
            )
        )
    if result.vector_write_result is not None:
        _show_vector_write_progress(
            tr(language, "vector.write_progress"),
            result.vector_write_result,
            language=language,
        )
    if result.deleted_vectors:
        st.caption(
            tr(language, "document.deleted_old_vectors", count=result.deleted_vectors)
        )


def render_model_configuration_page(config_dir: Path, language: str) -> None:
    """Render the model configuration page."""

    st.header(page_label(PAGE_MODEL, language))
    model_config = load_model_config(config_dir)

    st.subheader(tr(language, "model.chat_section"))
    chat_base_url = st.text_input(
        tr(language, "model.chat_base_url"),
        value=model_config.chat.base_url,
        placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    chat_api_key = st.text_input(
        tr(language, "model.chat_api_key"),
        value=model_config.chat.api_key,
        type="password",
    )
    chat_model = st.text_input(
        tr(language, "model.chat_model"),
        value=model_config.chat.model,
        placeholder="qwen-max",
    )

    st.subheader(tr(language, "model.embedding_section"))
    provider_options = [provider.value for provider in EmbeddingProvider]
    embedding_provider = st.selectbox(
        tr(language, "model.embedding_provider"),
        options=provider_options,
        index=provider_options.index(model_config.embedding.provider.value),
    )
    embedding_model = st.text_input(
        tr(language, "model.embedding_model"),
        value=model_config.embedding.model,
        placeholder=tr(language, "model.embedding_placeholder"),
    )

    use_remote_embedding = embedding_provider == EmbeddingProvider.OPENAI_COMPATIBLE.value
    embedding_base_url = ""
    embedding_api_key = ""
    if use_remote_embedding:
        embedding_base_url = st.text_input(
            tr(language, "model.embedding_base_url"),
            value=model_config.embedding.base_url,
            placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        embedding_api_key = st.text_input(
            tr(language, "model.embedding_api_key"),
            value=model_config.embedding.api_key,
            type="password",
        )

    st.subheader(tr(language, "model.retrieval_limits"))
    top_k = st.number_input(
        tr(language, "model.top_k"),
        min_value=1,
        value=model_config.retrieval.top_k,
        step=1,
    )
    batch_size = st.number_input(
        tr(language, "model.batch_size"),
        min_value=1,
        value=model_config.embedding.batch_size,
        step=1,
    )
    max_concurrency = st.number_input(
        tr(language, "model.max_concurrency"),
        min_value=1,
        value=model_config.embedding.max_concurrency,
        step=1,
    )
    batch_interval_seconds = st.number_input(
        tr(language, "model.batch_interval"),
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
        if st.button(tr(language, "model.save_chat"), use_container_width=True):
            try:
                config_to_save = model_config.model_copy(update={"chat": updated_config.chat})
                config_path = save_model_config(config_to_save, config_dir)
                st.success(tr(language, "model.chat_saved", path=config_path))
            except Exception as exc:  # noqa: BLE001 - show validation and IO errors.
                st.error(tr(language, "model.chat_save_failed", error=exc))

    with embedding_save_col:
        if st.button(tr(language, "model.save_embedding"), use_container_width=True):
            try:
                config_to_save = model_config.model_copy(
                    update={
                        "embedding": updated_config.embedding,
                        "retrieval": updated_config.retrieval,
                    }
                )
                config_path = save_model_config(config_to_save, config_dir)
                st.success(tr(language, "model.embedding_saved", path=config_path))
            except Exception as exc:  # noqa: BLE001 - show validation and IO errors.
                st.error(tr(language, "model.embedding_save_failed", error=exc))

    with chat_test_col:
        if st.button(tr(language, "model.test_chat"), use_container_width=True):
            result = test_chat_model(updated_config)
            if result.ok:
                st.success(ui_message(result.message, language))
            else:
                st.error(ui_message(result.message, language))

    with embedding_test_col:
        if st.button(tr(language, "model.test_embedding"), use_container_width=True):
            result = test_embedding_model(updated_config)
            if result.ok:
                st.success(ui_message(result.message, language))
            else:
                st.error(ui_message(result.message, language))


def _load_sessions(
    conversation_store: ConversationStore,
    language: str = DEFAULT_LANGUAGE,
) -> list[ConversationSession]:
    try:
        return conversation_store.list_sessions()
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(tr(language, "conversation.load_list_failed", error=exc))
        return []


def _load_documents(
    document_store: DocumentStore,
    language: str = DEFAULT_LANGUAGE,
) -> list[DocumentRecord]:
    try:
        return document_store.list_documents()
    except Exception as exc:  # noqa: BLE001 - show controlled storage errors.
        st.error(tr(language, "document.load_failed", error=exc))
        return []


def _conversation_table_row(
    conversation_store: ConversationStore,
    session: ConversationSession,
    language: str = DEFAULT_LANGUAGE,
) -> dict[str, Any]:
    try:
        message_count = len(conversation_store.get_messages(session.session_id))
    except Exception:  # noqa: BLE001 - table should still render if one row fails.
        message_count = tr(language, "unavailable")

    return {
        tr(language, "conversation.table.session_id"): session.session_id,
        tr(language, "conversation.table.title"): session.title,
        tr(language, "conversation.table.messages"): message_count,
        tr(language, "conversation.table.created"): session.created_at,
        tr(language, "conversation.table.updated"): session.updated_at,
    }


def _document_table_row(
    document: DocumentRecord,
    documents: list[DocumentRecord],
    language: str = DEFAULT_LANGUAGE,
) -> dict[str, Any]:
    return {
        tr(language, "document.table.document_id"): document.document_id,
        tr(language, "document.table.filename"): document.original_filename,
        tr(language, "document.table.type"): document.file_type,
        tr(language, "document.table.size"): document.file_size,
        tr(language, "document.table.status"): document.status,
        tr(language, "document.table.parse"): document.parse_status,
        tr(language, "document.table.index"): document.index_status,
        tr(language, "document.table.chunks"): document.chunk_count,
        tr(language, "document.table.duplicate"): _format_duplicate_document(
            document,
            documents,
            language,
        ),
        tr(language, "document.table.created"): document.created_at,
        tr(language, "document.table.updated"): document.updated_at,
    }


def _show_rag_result(result: RagAnswerResult, language: str) -> None:
    if result.ok:
        st.success(ui_message(result.message, language))
    else:
        st.warning(ui_message(result.message, language))

    st.info(
        tr(
            language,
            "rag.retrieved_context",
            knowledge=result.knowledge_result_count,
            memory=result.memory_result_count,
        )
    )
    if result.user_memory_result is not None:
        _show_memory_progress(result.user_memory_result, language)
    if result.assistant_memory_result is not None:
        _show_memory_progress(result.assistant_memory_result, language)


def _show_memory_result(result: ConversationMemoryResult, language: str) -> None:
    if result.ok:
        st.success(ui_message(result.message, language))
    else:
        st.error(ui_message(result.message, language))
    _show_memory_progress(result, language)
    if result.deleted_vectors:
        st.caption(
            tr(language, "memory.deleted_old_vectors", count=result.deleted_vectors)
        )


def _show_memory_progress(result: ConversationMemoryResult, language: str) -> None:
    write = result.vector_write_result
    if write is not None:
        _show_vector_write_progress(
            tr(language, "memory.write_progress"),
            write,
            language=language,
            unit=tr(language, "unit.messages"),
        )
    elif result.total_messages:
        st.info(
            tr(
                language,
                "memory.sync_progress",
                written=result.written_messages,
                total=result.total_messages,
            )
        )


def _show_vector_write_progress(
    label: str,
    write: VectorWriteResult,
    *,
    language: str,
    unit: str | None = None,
) -> None:
    status = tr(
        language,
        "vector.progress",
        label=label,
        processed_texts=write.processed_texts,
        total_texts=write.total_texts,
        unit=unit or tr(language, "unit.chunks"),
        processed_batches=write.processed_batches,
        total_batches=write.total_batches,
    )
    if write.failed_batch_index is not None:
        status = f"{status} {tr(language, 'vector.failed_batch', batch=write.failed_batch_index)}"
    st.info(status)

    if not write.ok:
        st.warning(tr(language, "vector.local_memory_hint"))


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
    language: str = DEFAULT_LANGUAGE,
) -> str:
    if not document.duplicate_of_document_id:
        return tr(language, "duplicate.no")

    original = _find_document(document.duplicate_of_document_id, documents)
    if original is None:
        return tr(
            language,
            "duplicate.yes_id",
            document_id=document.duplicate_of_document_id,
        )
    return tr(
        language,
        "duplicate.yes_document",
        filename=original.original_filename,
        document_id=original.document_id,
    )


if __name__ == "__main__":
    main()
