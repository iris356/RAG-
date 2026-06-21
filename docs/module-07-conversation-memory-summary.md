# Module 07 Summary: Conversation Long-Term Memory

## 已完成的功能

- 实现会话长期记忆同步服务，将 SQLite 中已保存的会话消息写入 Chroma 的 `conversation_memory` collection。
- 支持单条消息写入长期记忆，写入前按稳定向量 ID 删除旧记录，避免重复写入冲突。
- 支持对当前会话已有历史消息批量补写长期记忆，补写前按 `session_id` 清理旧记忆向量。
- 支持仅删除当前会话的长期记忆向量。
- 支持删除会话时同步删除 Chroma 记忆向量和 SQLite 会话/消息记录。
- 删除会话采用先删 Chroma 记忆向量、再删 SQLite 记录的顺序；如果向量删除失败，不继续删除 SQLite。
- 在 Streamlit `Conversations` 页面增加长期记忆验证入口：
  - 保存首条用户消息后写入长期记忆。
  - 手动追加消息后写入长期记忆。
  - 支持重建当前会话记忆。
  - 删除会话时同步删除记忆向量。

## 涉及的主要文件或模块

- `src/rag_app/conversations/memory.py`
- `src/rag_app/conversations/__init__.py`
- `src/rag_app/core/exceptions.py`
- `src/rag_app/app.py`
- `tests/test_conversation_memory.py`

## 关键实现思路

- 新增 `ConversationMemoryService` 作为模块六和模块三之间的组合层。
- 模块七不直接调用 embedding 模型，只调用模块三 `VectorStore.add_conversation_memories()` 写入记忆向量。
- 每条会话消息转换为一个 `VectorRecord`：
  - 向量 ID：`conversation:{session_id}:message:{message_id}`
  - 文本内容：SQLite 消息原文
  - metadata：`session_id`、`message_id`、`role`、`created_at`
- 批量重建会话记忆时，先调用 `VectorStore.delete_by_session_id(session_id)` 清理当前会话旧记忆，再写入当前 SQLite 消息快照。
- 删除会话时先清理 `conversation_memory`，再调用 `ConversationStore.delete_session()` 删除 SQLite 数据，避免 SQLite 已删除但 Chroma 向量残留。
- 模块七只实现长期记忆存储和清理，不实现真实 RAG 问答、不检索知识库、不组合 Prompt、不调用聊天模型。

## 已验证的测试或检查

- `python -m compileall src` 已通过。
- `uv run --no-sync pytest` 已通过，当前共 73 个测试。
- 新增测试覆盖：
  - 会话消息转换为稳定向量 ID 和完整 metadata。
  - 单条消息记忆写入调用模块三的 `add_conversation_memories()`。
  - 向量写入失败时透传 `VectorWriteResult` 进度和错误信息。
  - 批量补写会话历史消息时按 `session_id` 先清理旧向量，再写入所有消息。
  - 空会话重建只清理旧向量，不写入空记录。
  - 删除会话时先删除记忆向量，再删除 SQLite 会话和消息。
  - 记忆向量删除失败时保留 SQLite 会话和消息。
  - 不存在会话的记忆操作返回受控错误。

## 未完成事项或后续建议

- 模块七不做消息摘要或记忆压缩，第一版直接将完整消息内容作为长期记忆文本。
- 模块七不实现会话记忆检索参与回答；模块八需要在 RAG 问答链路中按当前 `session_id` 检索 `conversation_memory`。
- 当前 Streamlit 页面仍是验证型 Conversations 页面；模块九可进一步拆分为正式问答会话页和历史会话页。
- 后续模块八保存真实用户问题和模型回答后，应调用模块七服务写入长期记忆。

## 当前模块对后续模块的影响

- 模块八可以直接复用 `ConversationMemoryService.write_message_memory()`，在保存用户问题和助手回答后写入长期记忆。
- 模块八检索长期记忆时必须使用当前会话过滤条件，例如 `where={"session_id": current_session_id}`，不得跨会话共享记忆。
- 后续任何会话删除入口都应复用 `delete_session_with_memories()`，确保 SQLite 和 Chroma 同步清理。
- 后续 Web 层不应绕过模块三或模块七直接调用 embedding 模型写入会话记忆。
