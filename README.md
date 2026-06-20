# RAG Knowledge App

基于 `Python + LangChain` 的本地知识库问答项目。当前阶段完成项目基础骨架和数据目录初始化，后续会按 `docs/rag-plan.md` 继续实现模型配置、向量库、文档管理、历史会话和 RAG 问答。

## 环境要求

- Python `>=3.11,<3.14`
- uv

如果本机尚未安装 `uv`：

```powershell
python -m pip install uv
```

如果安装后当前终端仍无法识别 `uv` 命令，可以使用 `python -m uv` 作为等价入口。

## 安装依赖

```powershell
uv sync
```

备用命令：

```powershell
python -m uv sync
```

## 启动应用

```powershell
uv run rag-app
```

备用命令：

```powershell
python -m uv run rag-app
```

启动后会打开一个最小 Streamlit 页面，展示项目名称、数据目录和模块状态。

## 运行测试

```powershell
uv run pytest
```

备用命令：

```powershell
python -m uv run pytest
```

## 数据目录

默认数据目录位于项目内 `data/`，可通过 `.env` 或环境变量 `APP_DATA_DIR` 覆盖。

- `data/raw/`：原始上传文件
- `data/chroma/`：Chroma 持久化数据
- `data/sqlite/`：SQLite 数据库文件
- `data/tmp/`：临时文件
