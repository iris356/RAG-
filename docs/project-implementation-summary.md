# Project Implementation Summary

## 项目概述

本项目已经按 `docs/rag-plan.md` 完成第一版 RAG 知识库问答应用。项目面向单用户本地或内网部署场景，使用 `Python + LangChain + Streamlit + Chroma + SQLite` 构建，支持资料上传、文档解析、向量入库、历史会话、会话长期记忆、RAG 问答和 Web 交互。

当前第一版不包含多用户登录、权限系统、引用来源展示、流式输出、后台任务队列、OCR、图片理解和复杂表格结构化解析。

## 技术栈

- 语言：Python 3.11+
- RAG 编排：LangChain
- Web 框架：Streamlit
- 向量数据库：Chroma，本地持久化
- 结构化存储：SQLite
- 配置存储：本地 JSON 配置文件
- 文档解析：LangChain document loaders、`pypdf`、`docx2txt`
- 模型接入：
  - Chat：OpenAI-compatible API
  - Embedding：OpenAI-compatible API、local HuggingFace

## 已实现模块

### 1. 项目基础与数据目录

- 初始化 Python 项目结构、依赖管理和命令行启动入口。
- 建立本地数据目录：
  - `data/raw/`：原始上传文件
  - `data/chroma/`：Chroma 持久化数据
  - `data/sqlite/`：SQLite 数据库
  - `data/config/`：模型配置
  - `data/tmp/`：临时文件
- 提供统一配置、路径、日志和异常基础设施。

### 2. 模型配置

- 支持聊天模型和向量模型分开配置。
- 支持 OpenAI-compatible 聊天模型。
- 支持 OpenAI-compatible 和 local HuggingFace 向量模型。
- 模型配置保存到 `data/config/model-config.json`，该文件不会提交到 Git。
- 支持模型连接测试。
- 支持本地 embedding 保护参数：
  - `embedding.batch_size`
  - `embedding.max_concurrency`
  - `embedding.batch_interval_seconds`

### 3. 向量库

- 使用 Chroma 建立两个 collection：
  - `knowledge_chunks`：知识库文档片段
  - `conversation_memory`：会话长期记忆
- 封装统一的分批 embedding 和写入入口。
- 文档索引和会话记忆写入都通过统一向量层，避免业务层直接调用 embedding 模型。
- 本地 HuggingFace embedding 强制单并发。
- 支持按向量 ID、`document_id`、`session_id` 删除。
- 支持知识库和会话记忆相似度检索。

### 4. 文档管理

- 支持上传 PDF、Word、Markdown、TXT。
- 保存原始文件和文档元数据。
- 文档元数据包括文件名、类型、大小、状态、创建/更新时间、`file_md5`、`text_md5`、重复来源和分块数量。
- 上传时使用 `file_md5` 拦截完全相同文件，避免重复保存。
- 支持文档列表、删除和重建索引。
- 删除文档时同步清理 SQLite 记录、原始文件和对应 Chroma 向量。

### 5. 文档解析与切分

- 使用 LangChain loaders 解析 PDF、Word、Markdown、TXT。
- 使用 LangChain text splitter 切分正文。
- 基于规范化正文计算 `text_md5`，识别正文重复资料。
- 正文重复资料会标记 `duplicate_of_document_id`，不会重复切分或入库。
- 非重复资料写入 `knowledge_chunks`。
- 向量 metadata 保留 `document_id`、文件名、文件类型、`file_md5`、`text_md5`、`chunk_index`、页码或来源等信息。

### 6. 历史会话

- 使用 SQLite 保存会话和消息记录。
- 支持新建会话、打开历史会话、重命名会话、删除会话。
- 用户问题和模型回答都会写入消息表。
- 新会话可基于首个用户问题生成标题。

### 7. 会话长期记忆

- 会话记忆仅在当前会话内生效，不跨会话共享。
- 完整消息保存到 SQLite，长期记忆片段写入 Chroma `conversation_memory` collection。
- 记忆 metadata 包含 `session_id`、`message_id`、`role`、`created_at`。
- 删除会话时同步删除 SQLite 会话、消息和对应 Chroma 记忆向量。
- 支持重建当前会话记忆。

### 8. RAG 问答

- `RagAnswerService` 串联知识库检索、当前会话记忆检索、Prompt 组装、聊天模型调用、消息保存和记忆写入。
- 每次回答同时检索：
  - 知识库文档片段
  - 当前会话长期记忆片段
- 未传入会话 ID 时自动创建会话。
- 当知识库或会话记忆为空时，仍允许模型基于已有上下文回答，并提示缺少相关上下文。
- 第一版只返回直接回答，不展示引用来源。

### 9. Web 交互

- 使用 Streamlit 构建正式 Web 应用。
- 使用侧边栏导航组织页面：
  - `Q&A session`
  - `Conversation history`
  - `Document management`
  - `Model configuration`
  - `Overview`
- 问答页支持新建会话、选择历史会话、连续追问和展示当前会话消息。
- 历史页支持查看、打开、重命名、删除和重建记忆。
- 文档页支持上传、查看、删除、解析和重建索引。
- 模型配置页支持保存配置和测试连接。
- Web 层只调用服务层接口，不直接绕过 RAG 服务或 embedding 层。

## 关键设计

- 模块边界清晰：Web 层负责交互编排，RAG 服务负责问答链路，向量层负责 embedding 与 Chroma 写入。
- 本地数据优先：原始文件、SQLite、Chroma 和模型配置都默认保存在项目 `data/` 目录下。
- 去重分两层：
  - `file_md5` 识别完全相同原始文件。
  - `text_md5` 识别不同文件名或格式但正文相同的资料。
- 本地 embedding 受保护：通过批量大小、并发数和批次间隔降低内存或显存压力。
- 删除保持一致性：删除文档或会话时，同时清理对应的结构化记录和向量数据。

## 验证状态

当前已完成以下验证：

- `python -m compileall src`
- `uv run --no-sync pytest`
- 当前测试结果：`88 passed`
- Streamlit 本地启动验证通过，HTTP 状态码 `200`
- Git 当前主分支已同步到远程：
  - 最新提交：`6f156e7 feat: add web interaction module`

## 后续增强建议

- 增加引用来源展示和来源编号。
- 增加模型回答流式输出。
- 增加更完整的浏览器端 E2E 测试。
- 增加后台任务队列，避免大文档索引阻塞页面。
- 增加 OCR、图片理解和复杂表格结构化解析。
- 增加多用户登录、权限隔离和审计日志。
- 当 `src/rag_app/app.py` 继续变大时，可拆分为独立 `web/` 子模块。
