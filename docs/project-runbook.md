# Project Runbook

本项目当前只保留一套 Web 入口：

- 后端：`FastAPI`，命令为 `uv run rag-api`
- 前端：`app/` 下的 `Next.js + shadcn/ui + Tailwind CSS`

旧版 Streamlit 入口已经删除，不再支持 `uv run rag-app`。

## 启动后端

在项目根目录运行：

```powershell
uv sync
uv run rag-api
```

默认地址：

```text
http://127.0.0.1:8000
```

健康检查：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
```

## 启动前端

在项目根目录运行：

```powershell
cd app
npm install
npm run dev
```

默认地址：

```text
http://127.0.0.1:3000
```

前端默认调用：

```text
http://127.0.0.1:8000
```

如需修改 API 地址，在 `app/.env.local` 中设置：

```text
NEXT_PUBLIC_RAG_API_BASE_URL=http://127.0.0.1:8000
```

## 常用检查

后端：

```powershell
python -m compileall src tests
uv run --no-sync pytest
```

前端：

```powershell
cd app
npm run typecheck
npm run lint
npm run build
```

## 端口占用

如果后端启动时报 `Errno 10048`，说明 `127.0.0.1:8000` 已被占用：

```powershell
netstat -ano | Select-String ':8000'
```

确认 PID 是旧的本项目 API 进程后再停止：

```powershell
Stop-Process -Id <PID> -Force
```

如果前端端口 `3000` 被占用，可以指定其他端口：

```powershell
cd app
npm run dev -- --port 3001
```

## 当前前端

首页是知识库控制台总览，视觉参考 RAGFlow 风格：左侧导航、顶部搜索、统计卡片、问答测试、导入任务、活动和趋势面板。文档管理、对话测试和系统设置仍通过同一个 Next.js 应用完成。
