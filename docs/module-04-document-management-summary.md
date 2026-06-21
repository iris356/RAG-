# Module 04 Summary: Document Management

## 已完成的功能

- 实现文档原始文件保存和 SQLite 元数据管理。
- 支持上传 `PDF`、`Word .docx`、`Markdown`、`TXT` 文件。
- 上传时计算 `file_md5`，在保存原始文件前拦截重复文件。
- 文档元数据保存 `document_id`、文件名、类型、大小、状态、创建/更新时间、`file_md5`、`text_md5`、重复文档引用和分块数量。
- 支持文档列表查询、单文档查询、处理状态更新、正文指纹写回接口。
- 支持删除文档，并调用模块三 `delete_by_document_id()` 清理知识库向量。
- 支持重建索引请求状态入口，但不在模块四执行解析、切分或向量入库。
- 在 Streamlit 应用中增加 `Documents` 页面，支持上传、查看、删除和请求重建索引。

## 涉及的主要文件或模块

- `src/rag_app/documents/store.py`
- `src/rag_app/documents/__init__.py`
- `src/rag_app/core/exceptions.py`
- `src/rag_app/app.py`
- `tests/test_document_store.py`

## 关键实现思路

- 使用 Python 标准库 `sqlite3` 管理文档元数据，数据库文件为 `data/sqlite/rag_app.sqlite3`。
- 原始文件按 `{document_id}{extension}` 保存到 `data/raw`，避免重名、中文文件名和特殊字符影响存储路径。
- 上传流程先基于原始 bytes 计算 `file_md5`，若已有相同记录则不保存文件、不创建新元数据。
- 文档删除严格按 `document_id` 删除当前文档和对应向量，不按 `file_md5` 或 `text_md5` 批量删除，避免误删后续重复资料关联内容。
- `text_md5`、`duplicate_of_document_id`、解析状态、索引状态和分块数量在模块四先建模并提供更新接口，供模块五解析切分后写回。
- 已标记为重复正文的文档默认拒绝重建索引，避免绕过去重规则重复入库。

## 已验证的测试或检查

- `python -m compileall src` 已通过。
- `uv run pytest` 已通过，当前共 43 个测试。
- 新增测试覆盖：
  - SQLite 初始化和 `documents` 表创建。
  - `PDF`、`.docx`、Markdown、TXT 上传保存。
  - 不支持扩展名拦截。
  - `file_md5` 重复上传拦截，不重复保存文件或创建记录。
  - 文档列表稳定按新到旧返回。
  - 删除文档会删除原始文件、元数据，并调用向量清理接口。
  - 不存在文档删除返回受控错误。
  - 重建索引请求只更新状态。
  - 重复正文文档默认拒绝重建索引。
  - 模块五预留接口可写入 `text_md5`、重复引用、处理状态和分块数量。

## 未完成事项或后续建议

- 模块五需要实现正文解析、正文规范化、`text_md5` 去重、文本切分和向量入库。
- 模块五解析后应调用 `update_text_fingerprint()` 和 `update_processing_status()` 写回文档状态。
- 模块五重建索引时应先调用模块三 `delete_by_document_id()`，再重新写入知识库向量。
- 后续 Web 层可在模块五完成后展示真实解析和索引进度。

## 当前模块对后续模块的影响

- 后续文档解析模块应复用模块四的文档元数据和原始文件路径，不重复定义文档表。
- 后续 `text_md5` 去重必须写回 `duplicate_of_document_id`，重复资料不应进入切分和向量入库流程。
- 后续文档删除仍应通过模块四服务入口完成，确保 SQLite、原始文件和 Chroma 向量同步清理。
