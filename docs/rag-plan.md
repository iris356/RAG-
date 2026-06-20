# RAG 知识库问答项目计划

## Summary

构建一个基于 `Python + LangChain` 的单用户 Web 知识库问答项目。第一版支持文件知识库、模型配置、RAG 问答、历史会话保存，以及会话内长期向量记忆；删除会话时同步删除消息记录和记忆向量。

## 功能模块实现顺序

### 1. 项目基础与数据目录模块

- 初始化 Python 项目结构、依赖管理和启动脚本。
- 建立本地数据目录：原始文件目录、Chroma 持久化目录、SQLite 数据库目录。
- 定义核心配置、日志、异常处理和基础工具函数。
- 明确运行方式：本机或内网服务器启动 Streamlit 应用。

### 2. 模型配置模块

- 支持 `OpenAI-compatible` 和 `Ollama` 两类 Provider。
- Web 设置页配置：provider、base_url、api_key、chat_model、embedding_model、top_k。
- 配置保存到本地配置文件或 SQLite。
- 提供聊天模型测试、Embedding 模型测试和 Ollama 服务测试。
- 先完成该模块，保证后续文档向量化和问答链路都有可用模型。

### 3. 向量化与向量库模块

- 使用 LangChain Embeddings 接口统一管理向量化。
- 使用本地 `Chroma` 持久化向量数据。
- 建立两个 collection：`knowledge_chunks` 保存知识库文档向量，`conversation_memory` 保存会话长期记忆向量。
- 封装向量写入、检索、按 ID 删除、按 `session_id` 删除、按 `document_id` 删除等基础能力。

### 4. 文档管理模块

- 支持上传 `PDF`、`Word`、`Markdown`、`TXT` 文件。
- 保存原始文件和文档元数据，包括文档 ID、文件名、类型、状态、创建时间、更新时间。
- 支持查看文档列表、解析状态、索引状态、分块数量。
- 支持删除文档，并同步删除对应文本块和知识库向量。
- 支持单个文档重新解析和重建索引。

### 5. 文档解析与切分模块

- 使用 LangChain document loaders 处理不同文件类型。
- 使用 LangChain text splitters 对正文进行分块。
- 每个文本块保留文档 ID、文件名、页码或位置等元数据。
- 分块完成后调用向量化与向量库模块写入 `knowledge_chunks`。
- 第一版不做 OCR、图片理解和复杂表格结构化解析。

### 6. 历史会话模块

- 使用本地 `SQLite` 保存会话和消息记录。
- 核心数据包括：会话 ID、标题、创建时间、更新时间、消息角色、消息内容、消息时间。
- 用户每次提问和模型每次回答都写入消息表。
- 新会话默认使用首个问题自动生成标题，也允许用户手动重命名。
- 支持查看会话列表、打开历史会话、重命名会话、删除会话。

### 7. 会话长期记忆模块

- 记忆范围：仅当前会话内生效，不做跨会话共享。
- 记忆形式：`消息记录 + 向量记忆`。
- 完整聊天消息保存在 SQLite；长期记忆片段写入 Chroma 的 `conversation_memory` collection。
- 每条记忆向量写入 `session_id`、`message_id`、`role`、`created_at` 等元数据。
- 删除会话时按 `session_id` 删除 SQLite 消息、会话记录，以及 Chroma 中对应的记忆向量。

### 8. RAG 问答模块

- 用户问题进入当前选中的会话。
- 同时检索两类上下文：知识库文档片段、当前会话长期记忆片段。
- 使用 LangChain 组合检索结果、会话上下文、Prompt 和 ChatModel。
- 模型回答后保存用户问题、模型回答，并将会话消息写入长期记忆向量库。
- 第一版前端只展示直接回答，不展示引用来源。
- 当知识库为空、会话记忆为空或检索不到相关内容时，仍允许模型基于已有上下文回答，并给出清晰提示。

### 9. Web 交互模块

- 使用 `Streamlit` 构建 Python Web 应用。
- 页面按功能划分为：问答会话页、历史会话页、文档管理页、模型配置页。
- 问答会话页支持新建会话、选择历史会话、连续追问、展示当前会话消息。
- 历史会话页支持查看、打开、重命名和删除会话。
- 文档管理页支持上传、查看、删除、重建索引。
- 模型配置页支持填写配置并测试连接。

## 技术栈

- 语言：`Python`
- RAG 框架：`LangChain`
- Web 框架：`Streamlit`
- 向量库：`Chroma`
- 结构化存储：`SQLite`
- 文档解析：LangChain document loaders
- 文本切分：LangChain text splitters
- 模型接入：OpenAI-compatible API、Ollama
- 数据存储：本地文件目录 + SQLite + Chroma 持久化目录

## Test Plan

- 先测试模型配置连接，再测试 Embedding 写入和 Chroma 检索。
- 测试 PDF、Word、Markdown、TXT 上传后能解析、分块、入库。
- 测试删除文档后，对应知识库向量不再参与检索。
- 测试新建会话、连续问答、刷新页面后历史消息仍可恢复。
- 测试切换会话时，只加载当前会话的消息和长期记忆。
- 测试删除会话后，SQLite 记录和 Chroma 中对应 `session_id` 的记忆向量都被删除。
- 测试 OpenAI-compatible 与 Ollama 均可完成问答。
- 测试空知识库、空会话、模型配置错误、文件解析失败时有清晰提示。

## Assumptions

- 第一版为单用户本机或内网部署，不做登录和权限系统。
- 长期记忆只在单个会话内生效，不沉淀全局用户偏好。
- 会话记忆使用向量检索参与回答，但前端不单独展示记忆来源。
- 用户自行准备云端 API Key 或本地 Ollama 服务。
