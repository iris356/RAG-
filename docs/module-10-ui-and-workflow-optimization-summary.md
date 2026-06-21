# Module 10 Summary: UI and Workflow Optimization

## 已完成的功能

- 将 Streamlit 主界面调整为工作台式布局：左侧提供文档管理、新建会话、对话记录和设置入口，中央保留问答主流程。
- 左侧对话记录支持快速打开和快捷删除；删除仍通过会话记忆服务同步清理 SQLite 与 Chroma 记忆向量。
- 中文模式品牌标题改为 `RAG 知识库助手`，副标题改为 `基于 Python 和 LangChain 的本地知识库问答工具`；英文模式保留 `RAG Knowledge App`。
- 设置页集中放置语言切换、模型配置、检索与向量限速参数，并为未来账号登录预留入口。
- 模型配置页新增新手提示、参数说明、恢复推荐默认值和三种配置预设：
  - 稳定模式：Top K=5，批量=8，并发=1，间隔=0
  - 云端加速模式：Top K=5，批量=16，并发=3，间隔=0.5
  - 低性能电脑模式：Top K=3，批量=4，并发=1，间隔=0
- 文档管理页支持批量上传，并在新文件上传成功后自动解析和索引。
- 重复文件仍按 `file_md5` 拦截，重复正文仍按 `text_md5` 标记，不重复入库。
- 新增 `local-api` 向量 Provider，用于通过 HTTP 调用本地 OpenAI-compatible embedding 服务；旧 `local-huggingface` Provider 保留兼容。

## 涉及的主要文件或模块

- `src/rag_app/app.py`
- `src/rag_app/models/config.py`
- `src/rag_app/models/service.py`
- `tests/test_model_config.py`
- `tests/test_web_app.py`

## 关键实现思路

- Web 层继续只负责交互编排，不绕过 `RagAnswerService`、`DocumentProcessor`、`ConversationMemoryService` 或 `VectorStore`。
- 工作台布局仍基于 Streamlit sidebar 实现，配合少量 CSS 接近 Codex 风格，不引入新的前端框架。
- 设置页通过配置预设函数统一生成 Top K、批量、并发和间隔值，避免 UI 内硬编码散落。
- `local-api` Provider 使用标准库 HTTP 请求调用 `/embeddings`，保持与 OpenAI-compatible embedding 返回结构一致。
- 文档批量上传逐个处理：上传、去重判断、自动解析索引和状态展示相互独立，单个文件失败不阻断用户查看其他文件结果。

## 已验证的测试或检查

- `python -m compileall src tests` 已通过。
- `uv run --no-sync pytest` 已通过，当前共 99 个测试。
- Streamlit 启动验证已通过：
  - Local URL: `http://localhost:8501`
  - HTTP 状态码：200

## 未完成事项或后续建议

- 当前仍不实现真实账号登录，只保留设置入口占位。
- 当前不做像素级 Codex 克隆；如需更精细的前端体验，可后续考虑把 Web 层拆分到更完整的组件结构。
- 文档自动索引仍在请求流程内同步执行，大文件可能阻塞页面；后续可引入后台任务队列。
- 本地 embedding API 当前假设兼容 `/embeddings` 接口；如需支持非兼容服务，可扩展 Provider adapter。

## 当前模块对后续模块的影响

- 后续新增设置项应优先放入设置页，而不是重新暴露为普通导航页。
- 后续账号登录、用户信息和权限入口可接入当前设置页预留区域。
- 后续文档管理默认行为应保持“上传后自动解析索引”，除非明确增加手动模式开关。
- 后续 embedding Provider 扩展应继续通过模型配置和 `build_embedding_model()` 接入，不能让 Web 层直接调用模型服务。
