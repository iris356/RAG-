"use client"

export type ApiEnvelope<T> = {
  ok: boolean
  message: string
  data: T
  code?: string
}

export type ConversationSession = {
  session_id: string
  title: string
  created_at: string
  updated_at: string
}

export type ConversationMessage = {
  message_id: string
  session_id: string
  role: "user" | "assistant" | "system"
  content: string
  created_at: string
}

export type ConversationDetail = {
  session: ConversationSession
  messages: ConversationMessage[]
}

export type DocumentRecord = {
  document_id: string
  original_filename: string
  stored_filename: string
  file_path: string
  file_type: string
  file_size: number
  file_md5: string
  text_md5: string | null
  duplicate_of_document_id: string | null
  status: string
  parse_status: string
  index_status: string
  chunk_count: number
  created_at: string
  updated_at: string
}

export type EmbeddingProvider =
  | "openai-compatible"
  | "local-api"
  | "local-huggingface"

export type ModelConfig = {
  chat: {
    base_url: string
    api_key: string
    model: string
  }
  embedding: {
    provider: EmbeddingProvider
    base_url: string
    api_key: string
    model: string
    batch_size: number
    max_concurrency: number
    batch_interval_seconds: number
  }
  retrieval: {
    top_k: number
  }
}

export type ChatResult = {
  result: {
    ok: boolean
    message: string
    session_id: string
    answer: string
    user_message: ConversationMessage | null
    assistant_message: ConversationMessage | null
    knowledge_result_count: number
    memory_result_count: number
  }
}

export type UploadResult = {
  results: Array<{
    filename: string
    upload: unknown
    process: unknown
    error?: string
  }>
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_RAG_API_BASE_URL ?? "http://localhost:8000"

async function requestJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init.headers,
    },
  })
  const payload = (await response.json()) as ApiEnvelope<T>
  if (!response.ok || !payload.ok) {
    throw new Error(payload.message || `Request failed: ${response.status}`)
  }
  return payload
}

export const api = {
  baseUrl: API_BASE_URL,
  async listConversations() {
    return requestJson<{ conversations: ConversationSession[] }>("/api/conversations")
  },
  async createConversation(title?: string) {
    return requestJson<{ conversation: ConversationSession }>("/api/conversations", {
      method: "POST",
      body: JSON.stringify({ title: title || null }),
    })
  },
  async getConversation(sessionId: string) {
    return requestJson<{ conversation: ConversationDetail }>(
      `/api/conversations/${sessionId}`,
    )
  },
  async deleteConversation(sessionId: string) {
    return requestJson<{ result: unknown }>(`/api/conversations/${sessionId}`, {
      method: "DELETE",
    })
  },
  async chat(question: string, sessionId?: string | null) {
    return requestJson<ChatResult>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question, session_id: sessionId || null }),
    })
  },
  async listDocuments() {
    return requestJson<{ documents: DocumentRecord[] }>("/api/documents")
  },
  async uploadDocuments(files: File[]) {
    const data = new FormData()
    files.forEach((file) => data.append("files", file))
    return requestJson<UploadResult>("/api/documents", {
      method: "POST",
      body: data,
    })
  },
  async deleteDocument(documentId: string) {
    return requestJson<{ result: unknown }>(`/api/documents/${documentId}`, {
      method: "DELETE",
    })
  },
  async reindexDocument(documentId: string) {
    return requestJson<{ result: unknown }>(`/api/documents/${documentId}/reindex`, {
      method: "POST",
    })
  },
  async getModelConfig() {
    return requestJson<{ config: ModelConfig }>("/api/config/model")
  },
  async saveModelConfig(config: ModelConfig) {
    return requestJson<{ config: ModelConfig; path: string }>("/api/config/model", {
      method: "PUT",
      body: JSON.stringify(config),
    })
  },
  async resetModelConfig() {
    return requestJson<{ config: ModelConfig; path: string }>("/api/config/model/reset", {
      method: "POST",
    })
  },
  async applyPreset(preset: "stable" | "cloud-fast" | "low-resource") {
    return requestJson<{ config: ModelConfig; path: string }>(
      "/api/config/model/preset",
      {
        method: "POST",
        body: JSON.stringify({ preset }),
      },
    )
  },
  async testChatModel() {
    return requestJson<{ result: { ok: boolean; message: string } }>(
      "/api/config/model/test-chat",
      { method: "POST" },
    )
  },
  async testEmbeddingModel() {
    return requestJson<{ result: { ok: boolean; message: string } }>(
      "/api/config/model/test-embedding",
      { method: "POST" },
    )
  },
}
