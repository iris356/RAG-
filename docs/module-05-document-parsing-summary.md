# Module 05 Summary: Document Parsing and Splitting

## 已完成的功能

- 实现文档解析、正文规范化、`text_md5` 去重、文本切分和知识库向量入库链路。
- 支持通过 LangChain loaders 解析 `PDF`、`.docx`、Markdown 和 TXT。
- 使用 LangChain `RecursiveCharacterTextSplitter` 切分正文，默认 `chunk_size=1000`、`chunk_overlap=150`。
- 每个知识库 chunk 写入稳定 ID 和 metadata，包括 `document_id`、文件名、文件类型、`file_md5`、`text_md5`、`chunk_index`，并保留 loader 提供的 `page`、`source`。
- 解析后基于规范化正文计算 `text_md5`，识别正文重复资料。
- 正文重复文档会写回 `duplicate_of_document_id`，不切分、不调用向量入库。
- 非重复文档通过模块三 `VectorStore.add_knowledge_chunks()` 写入 Chroma，不直接调用 embedding 模型。
- 重建索引时先按 `document_id` 删除旧知识库向量，再重新解析、切分和入库。
- 文档管理页的操作按钮已接入实际解析和索引流程，并展示向量写入进度。

## 涉及的主要文件或模块

- `src/rag_app/documents/processing.py`
- `src/rag_app/documents/__init__.py`
- `src/rag_app/app.py`
- `src/rag_app/core/exceptions.py`
- `tests/test_document_processing.py`
- `pyproject.toml`
- `uv.lock`

## 关键实现思路

- 使用 `DocumentProcessor` 串联模块四的文档元数据、LangChain loader、文本 splitter 和模块三向量写入接口。
- 文本规范化规则为：统一换行、去除首尾空白、合并连续空白字符，再计算 `text_md5`。
- 正文去重只匹配已有相同 `text_md5` 且不是重复副本的文档，避免重复资料继续进入切分和 Chroma。
- 状态写回区分解析失败、切分失败和向量写入失败，便于 Web 层展示问题位置。
- 测试中通过 fake loader、fake splitter 和 fake vector store 验证处理流程，避免依赖真实模型服务和复杂真实文档。

## 已验证的测试或检查

- `python -m compileall src` 已通过。
- `uv run --no-sync pytest` 已通过，当前共 54 个测试。
- 新增测试覆盖：
  - 正文规范化和 `text_md5` 稳定性。
  - TXT/Markdown/PDF/DOCX loader 选择逻辑。
  - 文档切分后生成完整 metadata 和稳定 chunk ID。
  - 相同正文文档被 `text_md5` 标记为重复，且不调用向量入库。
  - 重建时发现正文重复会先删除当前文档旧向量，避免残留索引。
  - 非重复文档可调用模块三写入知识库向量。
  - 重建索引先删除旧向量再写入。
  - 向量写入失败会标记 `index_status=failed`。
  - 空正文会标记 `parse_status=failed`，且不会入库。

## 未完成事项或后续建议

- 第一版不做 OCR、图片理解和复杂表格结构化解析。
- Markdown 当前按纯文本解析，未做标题层级结构化。
- 解析和索引失败原因当前通过处理结果返回，未持久化到 SQLite 字段。
- 后续模块九可进一步优化 Web 层进度展示和失败原因展示。

## 当前模块对后续模块的影响

- 模块八 RAG 问答可直接从 `knowledge_chunks` 检索带 `document_id`、`file_md5`、`text_md5` 的知识片段。
- 后续模块不得绕过模块三直接调用 embedding 模型。
- 后续删除文档仍应通过模块四入口，以确保 SQLite、原始文件和 Chroma 向量同步清理。
- 模块七会话长期记忆应复用模块三统一向量写入入口，与模块五保持同一限速约束。
