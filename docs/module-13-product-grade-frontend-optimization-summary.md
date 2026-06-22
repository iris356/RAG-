# Module 13 Summary: Product-grade Frontend Optimization

## 已完成的功能

- 使用 `build-web-apps` 插件流程对正式 `app/` Next.js 前端进行产品级优化。
- 重构工作台视觉层级：左侧栏增加系统状态、主要功能导航、会话列表和账号占位区域。
- 优化聊天页：增加工作区状态、消息/文档/索引块统计、当前会话标题、快捷问题和更清晰的消息气泡。
- 优化文档管理页：增加资料库状态、重复资料统计、上传 CTA、桌面表格和移动端卡片列表。
- 优化设置页：增加配置状态、Provider 概览、模型配置分组、保存/恢复/预设/测试操作区。
- 移动端从抽屉依赖改为本地菜单状态，导航到聊天、文档和设置页均可真实触发。
- 前端默认 API 地址统一为 `http://127.0.0.1:8000`，减少本地浏览器跨源和主机名不一致问题。
- API CORS 保留正式本地前端端口 `3000` 和 QA/备用端口 `3001`。
- 新增 Playwright 开发依赖，用于真实浏览器截图和交互验证。

## 涉及的主要文件或模块

- `app/components/rag-workspace.tsx`
- `app/app/globals.css`
- `app/app/layout.tsx`
- `app/lib/api.ts`
- `app/package.json`
- `app/package-lock.json`
- `app/README.md`
- `src/rag_app/api/main.py`

## 关键实现思路

- 继续使用既有 `Next.js + shadcn/ui + Tailwind CSS + lucide-react` 技术栈，不更换核心架构。
- 前端仍只通过 `app/lib/api.ts` 调用 FastAPI，不直接访问 SQLite、Chroma、chat 模型或 embedding 模型。
- 桌面端保留高信息密度工作台结构，强化侧边栏导航、状态卡片和配置面板。
- 移动端针对核心流程单独优化：顶部状态栏、可见菜单、文档卡片列表和稳定测试选择器。
- 文档列表操作抽成复用组件，保证桌面表格和移动卡片使用同一套重建索引、删除和状态展示逻辑。
- 使用真实生产构建和 Playwright Chromium 验证桌面与移动端页面，而不只依赖静态检查。

## 已验证的测试或检查

- `npm.cmd run typecheck` 已通过。
- `npm.cmd run lint` 已通过。
- `npm.cmd run build` 已通过。
- `uv run --no-sync pytest tests/test_api_app.py` 已通过，当前 5 个 API 测试通过。
- FastAPI 健康检查返回 200。
- Playwright 生产模式 QA 已通过：
  - URL：`http://127.0.0.1:3001`
  - 桌面视口：`1440x960`
  - 移动视口：`390x844`
  - 验证页面标题、聊天输入、桌面文档导航、设置页模型配置、移动菜单、移动端文档卡片和上传按钮。
  - 浏览器 console 未发现错误。
- 已通过截图人工检查桌面聊天页、文档页、设置页和移动端文档页，无明显重叠、空白或不可读布局。

## 未完成事项或后续建议

- 当前仍不实现真实账号登录，只保留设置和侧边栏中的占位入口。
- 当前不新增引用来源展示、流式回答和后台索引任务，这些属于后续功能增强。
- Playwright 目前作为开发依赖加入，后续可整理成正式 e2e 脚本并纳入 CI。
- 如后续需要更多本地前端端口，应同步维护 FastAPI CORS 配置，避免临时端口长期散落。

## 当前模块对后续模块的影响

- 后续前端功能应复用当前工作台结构、状态组件和移动端响应式模式。
- 新增页面或状态时应同步补充稳定 `data-testid`，便于真实浏览器自动化验证。
- 前端默认运行路径以 `127.0.0.1` 为准；如果 API 地址变化，应通过 `NEXT_PUBLIC_RAG_API_BASE_URL` 显式配置。
- Streamlit 入口继续作为兼容入口保留，不作为主要产品级 UI 优化目标。
