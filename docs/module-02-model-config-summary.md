# Module 02 Summary: Model Configuration

## 已完成的功能

- 实现聊天模型和向量模型的独立配置。
- 聊天模型按 OpenAI-compatible 接口接入，支持阿里云 Qwen 等兼容服务。
- 向量模型支持 `openai-compatible` 和 `local-huggingface` 两类 Provider。
- 模型配置保存到本地 JSON：`data/config/model-config.json`。
- API Key 支持通过 Web 页面保存到本地配置文件，该文件被 Git 忽略。
- 增加本地向量模型限速配置：
  - `embedding.batch_size`
  - `embedding.max_concurrency`
  - `embedding.batch_interval_seconds`
- 提供聊天模型测试和向量模型测试能力。
- 在 Streamlit 应用中增加模型配置页面，支持分别保存和分别测试。

## 涉及的主要文件或模块

- `src/rag_app/models/config.py`
- `src/rag_app/models/service.py`
- `src/rag_app/app.py`
- `src/rag_app/core/paths.py`
- `tests/test_model_config.py`
- `docs/module-02-model-config-summary.md`
- `pyproject.toml`
- `.gitignore`
- `.env.example`

## 关键实现思路

- 使用 `ModelConfig` 将配置拆为 `chat`、`embedding`、`retrieval` 三块。
- 使用 JSON 文件保存模型配置，避免模块二提前引入 SQLite。
- 使用 `langchain-openai` 构建 `ChatOpenAI` 和 `OpenAIEmbeddings`。
- 使用 `langchain-huggingface` 构建本地 `HuggingFaceEmbeddings`。
- 模型依赖在服务工厂中懒加载，便于测试和错误提示。
- 保存配置只保证结构和数值合法；实际测试某条链路时再校验该链路必填项。
- 本地向量限速参数先在模块二保存和校验，后续模块三统一实现分批 embedding 和写入。

## 已验证的测试或检查

- `uv sync` 已完成依赖同步。
- `uv run pytest` 已通过，当前共 19 个测试。
- 测试覆盖：
  - 缺失配置文件时返回默认配置。
  - 配置 JSON 保存和读取。
  - 非法向量 Provider 拦截。
  - 本地向量限速参数校验。
  - 聊天模型和向量模型工厂参数。
  - 聊天模型测试、向量模型测试成功和失败结果。
  - `data/config` 目录创建。
- `rag-app` 启动入口已通过本地 HTTP 烟测。

## 未完成事项或后续建议

- 模块三需要复用 `embedding.batch_size`、`embedding.max_concurrency` 和 `embedding.batch_interval_seconds` 实现统一分批向量化。
- 模块三需要负责 Chroma collection 初始化和向量写入。
- 模块五和模块七不得直接调用 embedding 模型，应统一调用模块三提供的限速向量化入口。
- 当前未接入 Ollama 专用 Provider；本模块按更新后的计划优先支持 OpenAI-compatible 和本地 HuggingFace 向量模型。

## 当前模块对后续模块的影响

- 后续 RAG 问答模块应通过 `build_chat_model()` 获取聊天模型。
- 后续向量化模块应通过 `build_embedding_model()` 获取向量模型。
- 后续检索逻辑应复用 `retrieval.top_k`。
- 真实模型配置文件位于 `data/config/model-config.json`，不得提交到 Git。
