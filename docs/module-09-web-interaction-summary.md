# Module 09 Summary: Web Interaction

## 已完成的功能

- 将 Streamlit 应用从验证型 tabs 改为正式侧边栏导航页面。
- 完成五个页面入口：
  - `Q&A session`
  - `Conversation history`
  - `Document management`
  - `Model configuration`
  - `Overview`
- 问答会话页支持创建会话、选择历史会话、连续追问和展示当前会话消息。
- 问答会话页继续通过 `RagAnswerService.answer_question()` 执行完整 RAG 流程，Web 层不直接拼接检索、Prompt、模型调用或记忆写入。
- 历史会话页支持查看会话列表、打开到问答页、重命名、删除和重建记忆。
- 删除会话继续通过 `ConversationMemoryService.delete_session_with_memories()` 同步清理 SQLite 记录和 Chroma 记忆向量。
- 文档管理页支持上传、查看、删除、解析并重建索引。
- 文档管理页展示文档状态、解析状态、索引状态、分块数和重复来源。
- 上传重复文件和解析后正文重复时展示明确提示，不默认重复入库。
- 文档索引结果展示向量写入进度、批次数、失败批次和本地 embedding 内存/并发调整建议。
- 模型配置页保留 Chat、Embedding、Retrieval 和本地 embedding 限速配置，并支持保存与连接测试。
- Overview 页面增加 Module 09 状态。

## 涉及的主要文件或模块

- `src/rag_app/app.py`
- `tests/test_web_app.py`
- `docs/module-09-web-interaction-summary.md`

## 关键实现思路

- 新增 `AppServices` 聚合对象，在每次 Streamlit 渲染中统一构建并传递 `DocumentStore`、`ConversationStore`、`VectorStore`、`ConversationMemoryService`、`RagAnswerService` 和当前模型配置。
- 使用 sidebar radio 作为正式页面导航，并用 `st.session_state` 保存当前页面和当前会话 ID。
- 历史会话页的 `Open in Q&A` 会写入选中会话 ID 并请求切换到问答页，便于继续追问。
- 会话选择逻辑增加 fallback：当 session state 中的会话不存在时，自动选择当前列表第一条会话。
- 文档重复来源展示会尽量解析为原始文件名和文档 ID；如果原始文档已不存在，则显示关联的原始文档 ID。
- 所有问答、文档索引、会话记忆和模型测试仍调用已有服务层接口，避免 Web 层绕过模块边界。

## 已验证的测试或检查

- `python -m compileall src` 已通过。
- `uv run --no-sync pytest` 已通过，当前共 88 个测试。
- 新增 `tests/test_web_app.py` 覆盖：
  - 选中会话存在时保持选择。
  - 选中会话缺失时 fallback 到第一条会话。
  - 会话 selectbox index 计算。
  - 会话和文档选项格式化。
  - 历史会话列表消息数量。
  - 重复文档来源展示。
- 已完成 Streamlit 启动验证：
  - `http://localhost:8501`
  - HTTP 状态码 200

## 未完成事项或后续建议

- 第一版仍不展示引用来源、不做来源编号、不做流式输出。
- 第一版仍不做多用户登录、权限系统或后台任务队列。
- 未来可增加更完整的浏览器自动化交互测试，覆盖上传、页面切换、重命名和删除按钮。
- 如果需要更复杂的页面结构，后续可将 `src/rag_app/app.py` 拆分为 `web/` 子模块，但当前模块保持单入口以降低迁移成本。

## 当前模块对后续模块的影响

- 后续用户主要从模块九的正式页面进入 RAG 问答、历史会话管理、文档管理和模型配置。
- 后续扩展引用展示或流式输出时，应优先扩展 `RagAnswerResult` 或新增服务层返回结构，再由 Web 页面展示。
- Web 层应继续保持编排职责，不直接调用 embedding 模型或绕过 RAG 服务。
