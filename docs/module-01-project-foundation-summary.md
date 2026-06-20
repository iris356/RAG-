# Module 01 Summary: Project Foundation and Data Directories

## 已完成的功能

- 初始化 `Python + LangChain` 项目骨架。
- 使用 `pyproject.toml` 定义项目元数据、依赖和 `rag-app` 启动命令。
- 建立 `src/rag_app` 包结构和最小 Streamlit 应用入口。
- 增加基础配置、路径、日志和异常模块。
- 建立本地数据目录：`data/raw`、`data/chroma`、`data/sqlite`、`data/tmp`。
- 增加 `.gitignore`、`.env.example`、`README.md` 和基础测试。

## 涉及的主要文件或模块

- `pyproject.toml`
- `src/rag_app/app.py`
- `src/rag_app/cli.py`
- `src/rag_app/core/config.py`
- `src/rag_app/core/paths.py`
- `src/rag_app/core/logging.py`
- `src/rag_app/core/exceptions.py`
- `tests/`
- `data/`

## 关键实现思路

- 使用 `uv + pyproject.toml` 管理依赖和命令入口。
- 使用 `src/rag_app` 包结构隔离应用代码，便于后续模块扩展。
- 使用 `pydantic-settings` 读取 `.env` 和环境变量。
- 通过统一的路径工具创建并返回所有数据目录，后续文档、Chroma 和 SQLite 模块都复用该入口。
- Streamlit 入口当前只展示项目基础状态，不实现后续业务功能。

## 已验证的测试或检查

- `uv sync` 应能安装项目依赖。
- `uv run pytest` 应能通过配置、路径和异常的基础测试。
- `uv run rag-app` 应能启动最小 Streamlit 应用。

## 未完成事项或后续建议

- 模型配置模块尚未实现。
- 向量库 collection 初始化尚未实现。
- 文档上传、解析、会话和 RAG 问答尚未实现。

## 当前模块对后续模块的影响

- 后续模块应复用 `get_settings()` 获取配置。
- 后续模块应复用 `ensure_data_directories()` 获取数据目录。
- 后续模块应继续在 `src/rag_app` 包内按职责拆分实现。
