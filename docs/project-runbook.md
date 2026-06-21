# Project Runbook

## 运行环境

本项目需要：

- Python `>=3.11,<3.14`
- `uv`
- 可用的聊天模型 API，或兼容 OpenAI 接口的模型服务
- 可用的向量模型 API，或本地 HuggingFace embedding 模型环境

安装 `uv`：

```powershell
python -m pip install uv
```

如果终端无法识别 `uv` 命令，可以使用 `python -m uv` 作为等价入口。

## 安装依赖

在项目根目录执行：

```powershell
uv sync
```

备用命令：

```powershell
python -m uv sync
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

## 启动应用

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

如果需要切换语言，在页面左侧边栏找到 `界面语言` 控件：

- 选择 `中文`：显示中文 UI。
- 选择 `English`：显示英文 UI。

语言切换只影响 Web UI 文案，例如页面导航、标题、按钮、输入框提示、状态提示、错误提示和表格列名。用户上传的文档内容、历史会话消息、用户问题和模型回答不会被翻译。

## 首次使用流程

### 1. 配置模型

打开 Web 页面后进入 `模型配置`，英文界面中对应为 `Model configuration`。

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

保存配置后，分别点击聊天模型测试和向量模型测试，确认连接可用。

### 2. 上传资料

进入 `文档管理` 页面，英文界面中对应为 `Document management`，上传支持的文件：

- PDF
- Word `.docx`
- Markdown `.md`
- TXT

上传时系统会计算 `file_md5`。如果文件内容完全重复，会提示资料已存在，不会重复保存。

### 3. 解析并索引

在文档管理页选择文档，执行解析或重建索引。

系统会：

1. 解析文档正文。
2. 规范化正文并计算 `text_md5`。
3. 判断正文是否重复。
4. 非重复资料进入文本切分。
5. 分批调用 embedding。
6. 写入 Chroma `knowledge_chunks`。

如果本地 embedding 内存不足或处理失败，可以在 `Model configuration` 中调小 `Embedding batch size` 或降低 `Embedding max concurrency`。

### 4. 开始问答

进入 `问答会话` 页面，英文界面中对应为 `Q&A session`。

可以：

- 新建会话
- 选择历史会话
- 输入问题
- 连续追问
- 查看当前会话消息

系统会同时检索知识库文档片段和当前会话长期记忆，然后生成回答。

### 5. 管理历史会话

进入 `历史会话` 页面，英文界面中对应为 `Conversation history`。

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
python -m compileall src
```

当前项目验证结果为：

```text
88 passed
```

## 常见问题

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
