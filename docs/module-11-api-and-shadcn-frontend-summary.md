# Module 11 Summary: API and shadcn Frontend

## 已完成的功能

- 新增 FastAPI HTTP API，供独立前端调用现有 RAG 服务。
- 新增 `rag-api` 命令行入口，保留原 `rag-app` Streamlit 入口。
- API 覆盖健康检查、会话、问答、文档、模型配置、预设、默认值恢复和模型测试。
- 将 `app/` 作为正式 Next.js 前端，使用 shadcn/ui、Radix 组件、Tailwind CSS 和 lucide 图标实现工作台界面。
- 前端提供左侧会话栏、文档管理、新建会话、设置入口、中央聊天区、批量上传、配置保存、语言切换和账号登录预留位置。
- Streamlit 仍保留为兼容入口，核心 RAG 服务、SQLite、Chroma 和配置文件路径不迁移。

## 涉及的主要文件或模块

- `src/rag_app/api/`
- `src/rag_app/api/main.py`
- `src/rag_app/api/services.py`
- `app/`
- `tests/test_api_app.py`
- `pyproject.toml`

## 关键实现思路

- API 层只做 HTTP 编排，通过 `DocumentStore`、`DocumentProcessor`、`ConversationStore`、`ConversationMemoryService` 和 `RagAnswerService` 复用现有能力。
- API 返回统一 envelope：成功包含 `ok`、`message`、`data`；失败包含 `ok=false`、`message`、`code`。
- 文档上传接口支持多文件 multipart 上传，新文件上传后自动解析和索引，重复文件不触发解析索引。
- Next 前端通过 `NEXT_PUBLIC_RAG_API_BASE_URL` 调用 Python API；当前默认地址已统一为 `http://127.0.0.1:8000`。
- 设置页保留模型配置、检索参数、向量限速参数、预设、恢复推荐默认值、语言切换和账号登录占位。

## 已验证的测试或检查

- `uv run --no-sync pytest tests/test_api_app.py` 已通过。
- `uv run --no-sync pytest` 已通过，当前共 104 个测试。
- FastAPI 启动后 `GET /api/health` 返回 200。
- `npm run typecheck` 已通过。
- `npm run lint` 已通过。
- `npm run build` 已通过。
- Next 前端启动后首页 HTTP 返回 200。

## 未完成事项或后续建议

- 当前 API 不做鉴权，仍面向本机或内网单用户使用。
- 当前文档索引仍在请求流程内同步执行，大文件上传可能需要后续引入后台任务。
- 模块 11 阶段主要使用构建、HTTP 200 和静态检查覆盖基础可运行性；后续模块 13 已补充 Playwright 生产模式桌面和移动端 QA。
- 后续可在新前端稳定后，再决定是否淡出 Streamlit 入口。
- 如需账号登录，应优先在 FastAPI 层增加认证与用户上下文，再让前端设置入口接入。

## 当前模块对后续模块的影响

- 后续 Web 功能优先在 Next.js 前端实现，Streamlit 仅作为兼容入口维护。
- 后续前端不得绕过 API 直接访问 SQLite、Chroma 或模型服务。
- 后续新增模型 Provider、文档状态或会话字段时，需要同步更新 API 响应类型和前端 `app/lib/api.ts`。
