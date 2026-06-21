# RAG Knowledge App

基于 `Python + LangChain + Streamlit + Chroma + SQLite` 的本地知识库问答项目。

当前第一版已经完成 `docs/rag-plan.md` 中定义的 1-9 个功能模块，支持模型配置、资料上传、文档解析、向量入库、历史会话、会话长期记忆和 RAG 问答。

## 文档

- 项目实现总结：[docs/project-implementation-summary.md](docs/project-implementation-summary.md)
- 运行与使用说明：[docs/project-runbook.md](docs/project-runbook.md)
- 原始实现计划：[docs/rag-plan.md](docs/rag-plan.md)

## 快速启动

```powershell
uv sync
uv run rag-app
```

启动后访问：

```text
http://localhost:8501
```

## 测试

```powershell
python -m compileall src
uv run --no-sync pytest
```
