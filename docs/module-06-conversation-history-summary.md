# Module 06 Summary: Conversation History

## 已完成的功能

- 实现本地 SQLite 历史会话和消息记录模块。
- 新增会话元数据表，保存会话 ID、标题、创建时间和更新时间。
- 新增消息表，保存消息 ID、会话 ID、角色、内容和创建时间。
- 支持新建会话、首条用户消息自动生成标题、查看会话列表、打开会话、追加消息、重命名会话和删除会话。
- 删除会话时只删除 SQLite 中的会话和消息记录，不处理 Chroma 长期记忆向量。
- 在 Streamlit 应用中增加 `Conversations` 页面，用于验证会话历史保存、打开、重命名和删除流程。

## 涉及的主要文件或模块

- `src/rag_app/conversations/store.py`
- `src/rag_app/conversations/__init__.py`
- `src/rag_app/core/exceptions.py`
- `src/rag_app/app.py`
- `tests/test_conversation_store.py`

## 关键实现思路

- 使用 Python 标准库 `sqlite3` 管理历史会话，数据库文件继续复用 `data/sqlite/rag_app.sqlite3`。
- 使用 `ConversationStore` 封装所有会话和消息操作，后续模块八可以直接复用该入口保存真实问答消息。
- 会话标题生成不调用模型，只基于首个用户问题清理空白后截断到 40 个字符。
- 消息角色限制为 `user`、`assistant`、`system`，当前 Web 页面主要提供 `user` 和 `assistant` 写入验证。
- 每次追加消息都会更新所属会话的 `updated_at`，会话列表按最近更新时间倒序展示。
- 删除会话依赖 SQLite 外键级联删除消息；模块七再扩展同步删除 `conversation_memory` 向量。

## 已验证的测试或检查

- `python -m compileall src` 已通过。
- `uv run --no-sync pytest` 已通过，当前共 65 个测试。
- 新增测试覆盖：
  - SQLite 会话表和消息表初始化。
  - 默认标题和显式标题创建会话。
  - 首条用户消息自动生成标题。
  - 用户、助手和系统消息按时间顺序保存与读取。
  - 追加消息会更新会话 `updated_at` 并影响列表排序。
  - 重命名会话成功，空标题被拒绝。
  - 删除会话会删除 SQLite 消息记录。
  - 不存在会话、非法角色和空消息内容返回受控错误。

## 未完成事项或后续建议

- 模块六不调用聊天模型，不生成真实问答回复。
- 模块六不写入 Chroma 的 `conversation_memory` collection。
- 模块七需要在当前会话消息保存能力基础上，实现会话长期向量记忆。
- 模块八需要在真实 RAG 问答完成后，调用 `ConversationStore` 保存用户问题和模型回答。

## 当前模块对后续模块的影响

- 模块七应复用 `ConversationStore` 读取和管理会话消息，并通过模块三写入会话长期记忆向量。
- 模块七实现删除会话时，需要在当前 SQLite 删除流程基础上增加按 `session_id` 删除 Chroma 记忆向量。
- 模块八可以使用当前会话 ID 作为问答入口，并在模型回答后保存成 `user` 和 `assistant` 消息。
- 模块九后续可把当前验证型 Conversations 页面拆分或扩展为正式问答会话页和历史会话页。
