# Module 03 Summary: Vector Store

## 已完成的功能

- 实现本地 Chroma 持久化向量库模块。
- 建立两个固定 collection：
  - `knowledge_chunks`：保存知识库文档分块向量。
  - `conversation_memory`：保存会话长期记忆向量。
- 封装统一的分批 embedding 写入入口，所有写入 Chroma 的文本都通过该入口生成向量。
- 写入流程复用模块二的向量限速配置：
  - `embedding.batch_size`
  - `embedding.max_concurrency`
  - `embedding.batch_interval_seconds`
- 本地 `local-huggingface` 向量模型强制使用单并发，避免本地模型重复加载或显存冲突。
- 每批 embedding 完成后立即写入 Chroma，避免一次性在内存中保留全部向量。
- 支持相似度检索，并默认复用 `retrieval.top_k`。
- 支持按向量 ID、`document_id`、`session_id` 删除向量。
- 写入知识库向量前会防御性检查相同 `document_id` 是否已存在，避免重复入库。
- 向量 metadata 保留后续模块需要的 `document_id`、`file_md5`、`text_md5`、`session_id`、`message_id`、`role`、`created_at` 等字段。

## 涉及的主要文件或模块

- `src/rag_app/vectors/store.py`
- `src/rag_app/vectors/__init__.py`
- `src/rag_app/core/exceptions.py`
- `src/rag_app/app.py`
- `tests/test_vector_store.py`
- `docs/module-03-vector-store-summary.md`

## 关键实现思路

- 使用 `chromadb.PersistentClient` 直接管理本地 Chroma，保证模块三可以控制 embedding、分批和写入顺序。
- 使用 `VectorStore` 封装 collection 初始化、写入、检索和删除操作。
- 使用 `VectorRecord`、`VectorSearchResult`、`VectorWriteResult` 明确模块三对后续模块暴露的数据结构。
- 通过 `build_embedding_model()` 懒加载真实 LangChain Embeddings；测试中可注入 fake embedding，避免依赖真实模型服务。
- 写入时按批次提交 embedding 任务，远程 provider 按配置限制并发，本地 HuggingFace provider 强制并发为 1。
- 单批 embedding 或 Chroma 写入失败时返回 `VectorWriteResult(ok=False, ...)`，包含已处理文本数、已处理批次数和失败批次编号，便于后续 Web 层展示。
- 删除文档向量只按 `document_id` 删除，不按 `file_md5` 或 `text_md5` 删除，避免影响后续重复资料处理。

## 已验证的测试或检查

- `uv run pytest` 已通过，当前共 27 个测试。
- 新增测试覆盖：
  - Chroma collection 初始化。
  - `embedding.batch_size` 控制实际分批数量。
  - `local-huggingface` provider 强制单并发。
  - 写入后可检索并返回 ID、文本、metadata 和 score。
  - 默认 `top_k` 使用 `retrieval.top_k`，显式传入可覆盖。
  - 相同 `document_id` 重复写入会被拒绝。
  - `delete_by_document_id()` 只删除目标文档向量。
  - `delete_by_session_id()` 只删除目标会话记忆向量。
  - 单批 embedding 失败时返回清晰进度和错误信息。

## 未完成事项或后续建议

- 模块四需要实现文档上传、原始文件保存、文档元数据和 `file_md5` 去重。
- 模块五需要实现文档解析、正文规范化、`text_md5` 去重、文本切分，并调用模块三写入 `knowledge_chunks`。
- 模块七需要调用模块三写入 `conversation_memory`，不得直接调用 embedding 模型。
- 后续重建索引功能应先显式调用 `delete_by_document_id()`，再重新写入对应文档向量。

## 当前模块对后续模块的影响

- 后续文档索引和会话记忆写入必须统一通过 `VectorStore`，不能绕过模块三直接调用 embedding 模型。
- 后续文档删除应调用 `delete_by_document_id()` 清理知识库向量。
- 后续会话删除应调用 `delete_by_session_id()` 清理长期记忆向量。
- 后续 RAG 问答应通过 `similarity_search()` 检索知识库片段和当前会话记忆片段。
