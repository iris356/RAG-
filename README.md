# RAG Knowledge App

基于 `Python + LangChain + Chroma + SQLite` 的本地知识库问答项目，正式前端使用 `Next.js + shadcn/ui + Tailwind CSS`，通过 `FastAPI` 调用 Python RAG 服务。旧版 Streamlit 入口仍保留为兼容和回退入口。

当前已经完成项目计划中的核心 RAG 功能和产品级前端优化，支持模型配置、资料上传、文档解析、向量入库、历史会话、会话长期记忆、RAG 问答、响应式文档管理和设置页。

## 文档

- 运行与使用说明：[docs/project-runbook.md](docs/project-runbook.md)
- 项目实现总结：[docs/project-implementation-summary.md](docs/project-implementation-summary.md)
- 前端使用说明：[app/README.md](app/README.md)
- 原始实现计划：[docs/rag-plan.md](docs/rag-plan.md)
- 最新前端优化总结：[docs/module-13-product-grade-frontend-optimization-summary.md](docs/module-13-product-grade-frontend-optimization-summary.md)

## 快速启动

安装 Python 依赖：

```powershell
uv sync
```

启动 Python API：

```powershell
uv run rag-api
```

API 默认地址：

```text
http://127.0.0.1:8000
```

启动新版前端：

```powershell
cd app
npm install
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:3000
```

## 兼容入口

如需使用旧版 Streamlit 入口，可以在项目根目录运行：

```powershell
uv run rag-app
```

启动后访问：

```text
http://localhost:8501
```

## 测试

Python 检查：

```powershell
python -m compileall src tests
uv run --no-sync pytest
```

前端检查：

```powershell
cd app
npm run typecheck
npm run lint
npm run build
```

## 端口占用

如果 `uv run rag-api` 报错 `Errno 10048`，说明 `127.0.0.1:8000` 已被占用。可以查看占用进程：

```powershell
netstat -ano | Select-String ':8000'
```

确认是旧的 Python API 进程后再停止：

```powershell
Stop-Process -Id <PID> -Force
```
