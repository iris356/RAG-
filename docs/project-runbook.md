# Project Runbook

## 运行环境

本项目需要：

- Python `>=3.11,<3.14`
- `uv`
- Node.js 和 npm，用于运行新的 Next.js 前端
- 可用的聊天模型 API，或兼容 OpenAI 接口的模型服务
- 可用的向量模型 API，或本地 HuggingFace embedding 模型环境

安装 `uv`：

```powershell
python -m pip install uv
```

如果终端无法识别 `uv` 命令，可以使用 `python -m uv` 作为等价入口。

## 安装依赖

在项目根目录安装 Python 依赖：

```powershell
uv sync
```

备用命令：

```powershell
python -m uv sync
```

进入前端目录安装 Node.js 依赖：

```powershell
cd app
npm install
```

## 配置数据目录

默认数据目录是项目内的 `data/`。可以直接使用默认设置，也可以通过 `.env` 或环境变量覆盖：

```powershell
$env:APP_DATA_DIR="data"
$env:APP_LOG_LEVEL="INFO"
```

可以参考 `.env.example` 创建本地 `.env` 文件：

```text
APP_DATA_DIR=data
APP_LOG_LEVEL=INFO
```

主要数据目录：

- `data/raw/`：原始上传文件
- `data/chroma/`：Chroma 向量库
- `data/sqlite/`：SQLite 数据库
- `data/config/`：模型配置
- `data/tmp/`：临时文件

`data/config/model-config.json` 会由 Web 页面保存生成，包含模型连接信息和 API Key，不会提交到 Git。

## 启动应用（推荐）

新版界面使用 `Next.js + shadcn/ui + Tailwind CSS`，后端通过 `FastAPI` 暴露现有 RAG 能力。需要同时启动 API 和前端。

在第一个终端中，从项目根目录启动 API：

```powershell
uv run rag-api
```

API 默认地址：

```text
http://127.0.0.1:8000
```

在第二个终端中，进入前端目录启动 Next.js：

```powershell
cd app
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:3000
```

前端默认调用 `http://127.0.0.1:8000`。如果 API 地址不同，可以在 `app/.env.local` 中设置：

```text
NEXT_PUBLIC_RAG_API_BASE_URL=http://127.0.0.1:8000
```

## 启动旧版 Streamlit 入口

Streamlit 入口仍保留为兼容和回退入口，但不再是主要 UI 优化方向。

在项目根目录执行：

```powershell
uv run rag-app
```

备用命令：

```powershell
python -m uv run rag-app
```

启动后浏览器访问：

```text
http://localhost:8501
```

如果默认端口被占用，可以使用 Streamlit 参数指定端口：

```powershell
uv run streamlit run src/rag_app/app.py --server.port 8502
```

## 界面语言

Web 界面默认使用中文。

如果使用新版 Next.js 前端，在左下角打开 `设置`，在设置中切换语言：

- 选择 `中文`：显示中文 UI。
- 选择 `English`：显示英文 UI。

如果使用旧版 Streamlit 入口，在页面左侧边栏找到 `界面语言` 控件。

语言切换只影响 Web UI 文案，例如页面导航、标题、按钮、输入框提示、状态提示、错误提示和表格列名。用户上传的文档内容、历史会话消息、用户问题和模型回答不会被翻译。

## 首次使用流程

### 1. 配置模型

打开新版前端后，点击左下角 `设置`，进入模型配置区域。旧版 Streamlit 中对应页面为 `模型配置`，英文界面中对应为 `Model configuration`。

需要配置：

- Chat provider
- Chat base URL
- Chat API key
- Chat model
- Embedding provider
- Embedding base URL 或本地模型名
- Embedding API key，如果使用 OpenAI-compatible embedding
- Retrieval top K
- Embedding batch size
- Embedding max concurrency
- Embedding batch interval seconds

保存配置后，分别点击聊天模型测试和向量模型测试，确认连接可用。不熟悉参数时建议保持推荐默认值。

### 2. 上传资料

点击左侧栏顶部的 `文档管理`，上传支持的文件：

- PDF
- Word `.docx`
- Markdown `.md`
- TXT

新版前端支持批量上传。上传成功后会自动解析并索引，不需要再手动点击“解析并索引”。

上传时系统会计算 `file_md5`。如果文件内容完全重复，会提示资料已存在，不会重复保存，也不会触发解析索引。

### 3. 解析并索引

新版前端在上传成功后自动解析并索引。文档管理中仍提供重建索引入口，用于手动修复或重新生成向量。

系统会：

1. 解析文档正文。
2. 规范化正文并计算 `text_md5`。
3. 判断正文是否重复。
4. 非重复资料进入文本切分。
5. 分批调用 embedding。
6. 写入 Chroma `knowledge_chunks`。

如果本地 embedding 内存不足或处理失败，可以在 `Model configuration` 中调小 `Embedding batch size` 或降低 `Embedding max concurrency`。

### 4. 开始问答

新版前端默认展示中央聊天区。可以在左侧栏新建会话、打开历史会话，或直接在底部输入框提问。

可以：

- 新建会话
- 选择历史会话
- 输入问题
- 连续追问
- 查看当前会话消息

系统会同时检索知识库文档片段和当前会话长期记忆，然后生成回答。

### 5. 管理历史会话

新版前端左侧中部展示历史会话列表。

可以：

- 查看会话列表
- 打开会话继续问答
- 重命名会话
- 删除会话
- 重建会话长期记忆

删除会话会同步删除 SQLite 会话、消息和 Chroma 中对应的记忆向量。

## 运行测试

普通测试：

```powershell
uv run pytest
```

不重新同步依赖的测试：

```powershell
uv run --no-sync pytest
```

编译检查：

```powershell
python -m compileall src tests
```

前端检查：

```powershell
cd app
npm run typecheck
npm run lint
npm run build
```

当前项目验证结果为：

```text
104 passed
```

最近一次产品级前端验证还包括：

- `uv run --no-sync pytest tests/test_api_app.py`
- `npm.cmd run typecheck`
- `npm.cmd run lint`
- `npm.cmd run build`
- Playwright 生产模式桌面和移动端页面检查

## 常见问题

### 新版前端打不开

确认 Next.js 开发服务器仍在运行，并检查终端输出的实际端口。默认地址是：

```text
http://127.0.0.1:3000
```

如果前端能打开但无法加载数据，确认 API 已启动：

```powershell
uv run rag-api
```

并访问健康检查：

```text
http://127.0.0.1:8000/api/health
```

### API 启动时报端口占用

如果执行 `uv run rag-api` 时出现类似错误：

```text
[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)
```

说明 `127.0.0.1:8000` 已经被其他进程占用，通常是上一次启动的 API 没有关掉。先查看占用端口的 PID：

```powershell
netstat -ano | Select-String ':8000'
```

再查看该进程是否为 Python 或 uv 启动的旧 API：

```powershell
Get-Process -Id <PID>
```

确认无误后停止旧进程：

```powershell
Stop-Process -Id <PID> -Force
```

然后重新启动：

```powershell
uv run rag-api
```

### Streamlit 页面打不开

确认应用进程仍在运行，并检查终端输出的实际端口。默认地址是：

```text
http://localhost:8501
```

如果端口被占用，换一个端口启动：

```powershell
uv run streamlit run src/rag_app/app.py --server.port 8502
```

### 模型测试失败

检查：

- Base URL 是否正确。
- API Key 是否有效。
- 模型名是否和服务端一致。
- 本地 Ollama 或兼容服务是否已经启动。
- 如果使用本地 HuggingFace embedding，模型依赖和下载权限是否正常。

### 文档上传后没有进入问答结果

检查：

- 文档是否已经解析并索引成功。
- 文档是否被标记为重复正文。
- `knowledge_chunks` 写入是否失败。
- 模型配置中的 embedding 是否可用。
- Retrieval top K 是否过小。

### 本地 embedding 内存不足

进入 `Model configuration` 调整：

- 降低 `Embedding batch size`
- 降低 `Embedding max concurrency`
- 增加 `Embedding batch interval seconds`

本地 HuggingFace embedding 会自动强制单并发。

### 需要清空本地数据

停止应用后，可以按需清理 `data/` 下的数据目录。清理前建议备份：

- 清理 `data/raw/` 会删除原始上传文件。
- 清理 `data/sqlite/` 会删除文档元数据、会话和消息记录。
- 清理 `data/chroma/` 会删除知识库向量和会话记忆向量。
- 清理 `data/config/model-config.json` 会删除模型配置。

不要在应用运行中手动删除这些目录。
