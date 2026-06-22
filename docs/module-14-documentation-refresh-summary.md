# Module 14 Summary: Documentation Refresh

## 已完成的功能

- 更新根目录 `README.md`，将新版 `Next.js + shadcn/ui + Tailwind CSS` 前端标记为推荐入口。
- 更新 `app/README.md`，补充当前 UI 能力、API 健康检查、生产模式烟测、CORS 端口和端口占用处理。
- 更新 `docs/project-runbook.md`，修正默认 API 地址为 `http://127.0.0.1:8000`，并加入 `Errno 10048` 端口占用排查流程。
- 更新 `docs/project-implementation-summary.md`，补充模块 12 和模块 13 的前端优化状态、Playwright QA 结果和最新提交记录。
- 明确 Streamlit 仍是兼容入口，`app/` Next.js 前端是当前主要 UI。

## 涉及的主要文件或模块

- `README.md`
- `app/README.md`
- `docs/project-runbook.md`
- `docs/project-implementation-summary.md`
- `docs/module-14-documentation-refresh-summary.md`

## 关键实现思路

- 只更新使用说明和进度总结，不修改前端、API、RAG 服务、SQLite、Chroma 或模型调用逻辑。
- 文档中的启动顺序统一为先启动 `uv run rag-api`，再启动 `app/` 下的 `npm run dev`。
- 本地 API 地址统一使用 `127.0.0.1`，避免 `localhost` 与 `127.0.0.1` 混用造成排查困扰。
- 将最近遇到的端口占用问题沉淀为 runbook 步骤，便于后续快速处理。

## 已验证的测试或检查

- 文档更新前已确认当前最新功能状态来自模块 13 总结。
- 文档更新范围仅包含 Markdown 文档。
- 后续提交前应执行 `git diff --check` 和 `git status --short` 检查改动范围。

## 未完成事项或后续建议

- 可后续把 Playwright QA 命令整理为正式 npm script。
- 如果新增 API 端口或前端 QA 端口，需要同步更新 CORS 说明和运行手册。
- 如果未来淡出 Streamlit，应同步删除或迁移 README 与 runbook 中的兼容入口说明。

## 当前模块对后续模块的影响

- 后续使用和排障应优先参考 `docs/project-runbook.md`。
- 后续前端开发应优先参考 `app/README.md` 和模块 13 总结。
- 后续模块总结应继续写入 `docs/`，保持项目进度记录集中。
