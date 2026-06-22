"use client"

import * as React from "react"
import {
  AlertTriangleIcon,
  BotIcon,
  CheckIcon,
  CheckCircle2Icon,
  Clock3Icon,
  CommandIcon,
  DatabaseIcon,
  FileTextIcon,
  GaugeIcon,
  HardDriveIcon,
  HistoryIcon,
  InfoIcon,
  Layers3Icon,
  Loader2Icon,
  MenuIcon,
  MessageSquareIcon,
  PlusIcon,
  RefreshCwIcon,
  SearchIcon,
  SendIcon,
  SettingsIcon,
  SparklesIcon,
  Trash2Icon,
  UploadIcon,
  UserIcon,
  XCircleIcon,
} from "lucide-react"
import { toast } from "sonner"

import {
  api,
  type ConversationMessage,
  type ConversationSession,
  type DocumentRecord,
  type ModelConfig,
} from "@/lib/api"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldSet,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarSeparator,
} from "@/components/ui/sidebar"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

type View = "chat" | "documents" | "settings"
type Language = "zh" | "en"
type StatusTone = "success" | "warning" | "destructive" | "neutral"

const text = {
  zh: {
    title: "RAG 知识库助手",
    subtitle: "基于 Python 和 LangChain 的本地知识库问答工具",
    workspace: "本地工作台",
    documents: "文档管理",
    newChat: "新建会话",
    conversations: "对话记录",
    settings: "设置",
    account: "账号登录",
    accountHint: "预留入口",
    inputPlaceholder: "向知识库提问，按 Enter 发送",
    emptyTitle: "选择或新建一个会话",
    emptyDescription: "上传资料后，提问时会自动检索知识库和当前会话记忆。",
    send: "发送",
    upload: "上传文档",
    filename: "文件名",
    status: "状态",
    parse: "解析",
    index: "索引",
    chunks: "分块",
    actions: "操作",
    reindex: "重建索引",
    delete: "删除",
    noDocuments: "还没有文档",
    noDocumentsDesc: "支持 PDF、Word、Markdown 和 TXT。上传后会自动解析并索引。",
    modelSettings: "模型配置",
    retrievalSettings: "检索与向量限速",
    beginnerHint: "不熟悉参数时建议保持默认值。批次间隔秒数不是重试次数。",
    language: "语言",
    chatBaseUrl: "聊天 Base URL",
    chatApiKey: "聊天 API Key",
    chatModel: "聊天模型",
    embeddingProvider: "向量 Provider",
    embeddingBaseUrl: "向量 Base URL",
    embeddingApiKey: "向量 API Key",
    embeddingModel: "向量模型",
    topK: "Top K",
    batchSize: "向量批量大小",
    maxConcurrency: "向量最大并发数",
    interval: "向量批次间隔秒数",
    save: "保存配置",
    reset: "恢复推荐默认值",
    stable: "稳定模式",
    cloud: "云端加速模式",
    low: "低性能电脑模式",
    testChat: "测试聊天",
    testEmbedding: "测试向量",
    apiOffline: "无法连接 Python API",
    ready: "API 已连接",
    localVector: "本地向量库",
    currentSession: "当前会话",
    messageCount: "消息",
    documentCount: "文档",
    indexedChunks: "索引块",
    uploadHint: "拖选或批量选择资料，系统会自动解析、去重并写入向量库。",
    askHint: "知识库检索和当前会话记忆会一起参与回答。",
    quickStart: "开始使用",
    promptOne: "这份资料的核心结论是什么？",
    promptTwo: "根据知识库给我一个简短答案。",
    promptThree: "当前会话里我们确认了哪些事项？",
    primaryNav: "主要功能",
    systemStatus: "系统状态",
    apiEndpoint: "API 地址",
    connected: "已连接",
    disconnected: "未连接",
    knowledgeReady: "知识库就绪",
    noSession: "未选择会话",
    startChat: "开始提问",
    openDocuments: "管理文档",
    configured: "已配置",
    notConfigured: "待配置",
    duplicate: "重复资料",
    processed: "已处理",
    pending: "处理中",
    failed: "失败",
    clean: "正常",
    documentLibrary: "资料库",
    documentLibraryDesc: "上传、去重、解析并写入本地 Chroma 向量库。",
    uploadCta: "选择文件",
    uploadBusy: "正在处理",
    reindexHint: "重新解析并更新向量索引",
    deleteHint: "删除文档及其向量数据",
    sourceStatus: "资料状态",
    storageStatus: "存储状态",
    fileId: "文档 ID",
    fileType: "类型",
    duplicateOf: "重复来源",
    noSelection: "新会话",
    composerHint: "Enter 发送，Shift + Enter 换行",
    thinking: "正在生成回答",
    quickPrompts: "快捷问题",
    operational: "运行正常",
    settingsActions: "配置操作",
    providerSettings: "Provider 与模型",
    chatSettings: "聊天模型",
    embeddingSettings: "向量模型",
    limitDescription: "控制检索数量、批量向量化和本地模型资源占用。",
    presetDescription: "根据机器资源快速套用推荐参数。",
    testDescription: "保存前可先测试模型服务连通性。",
    accountPlaceholder: "未来的登录、权限和用户偏好将放在这里。",
    saveFirst: "保存后立即对后端生效",
    stableDescription: "适合本地模型与普通电脑",
    cloudDescription: "适合云端 API 与稳定网络",
    lowDescription: "适合低内存或低性能设备",
    refresh: "刷新",
    retry: "重试",
    activity: "工作区概览",
  },
  en: {
    title: "RAG Knowledge App",
    subtitle: "Local knowledge-base Q&A with Python and LangChain",
    workspace: "Local workspace",
    documents: "Documents",
    newChat: "New chat",
    conversations: "Conversations",
    settings: "Settings",
    account: "Account",
    accountHint: "Reserved",
    inputPlaceholder: "Ask the knowledge base. Press Enter to send",
    emptyTitle: "Choose or create a conversation",
    emptyDescription:
      "After uploading documents, questions retrieve both knowledge chunks and current-session memory.",
    send: "Send",
    upload: "Upload documents",
    filename: "Filename",
    status: "Status",
    parse: "Parse",
    index: "Index",
    chunks: "Chunks",
    actions: "Actions",
    reindex: "Reindex",
    delete: "Delete",
    noDocuments: "No documents yet",
    noDocumentsDesc:
      "PDF, Word, Markdown, and TXT are supported. Uploads are parsed and indexed automatically.",
    modelSettings: "Model configuration",
    retrievalSettings: "Retrieval and embedding limits",
    beginnerHint:
      "Keep the defaults if you are unsure. Batch interval seconds are not retry attempts.",
    language: "Language",
    chatBaseUrl: "Chat Base URL",
    chatApiKey: "Chat API Key",
    chatModel: "Chat model",
    embeddingProvider: "Embedding provider",
    embeddingBaseUrl: "Embedding Base URL",
    embeddingApiKey: "Embedding API Key",
    embeddingModel: "Embedding model",
    topK: "Top K",
    batchSize: "Embedding batch size",
    maxConcurrency: "Embedding max concurrency",
    interval: "Embedding batch interval seconds",
    save: "Save config",
    reset: "Restore recommended defaults",
    stable: "Stable mode",
    cloud: "Cloud fast mode",
    low: "Low-resource mode",
    testChat: "Test chat",
    testEmbedding: "Test embedding",
    apiOffline: "Python API is unreachable",
    ready: "API connected",
    localVector: "Local vector store",
    currentSession: "Current session",
    messageCount: "Messages",
    documentCount: "Documents",
    indexedChunks: "Indexed chunks",
    uploadHint:
      "Select documents in batches. The system parses, deduplicates, and indexes automatically.",
    askHint: "Knowledge retrieval and current-session memory are both used for answers.",
    quickStart: "Quick start",
    promptOne: "What is the core conclusion of this document?",
    promptTwo: "Give me a concise answer from the knowledge base.",
    promptThree: "What have we confirmed in this conversation?",
    primaryNav: "Primary",
    systemStatus: "System status",
    apiEndpoint: "API endpoint",
    connected: "Connected",
    disconnected: "Disconnected",
    knowledgeReady: "Knowledge ready",
    noSession: "No session selected",
    startChat: "Start asking",
    openDocuments: "Manage documents",
    configured: "Configured",
    notConfigured: "Needs setup",
    duplicate: "Duplicate",
    processed: "Processed",
    pending: "Processing",
    failed: "Failed",
    clean: "Healthy",
    documentLibrary: "Document library",
    documentLibraryDesc: "Upload, deduplicate, parse, and index into local Chroma.",
    uploadCta: "Choose files",
    uploadBusy: "Processing",
    reindexHint: "Parse again and refresh vector indexes",
    deleteHint: "Delete the document and its vectors",
    sourceStatus: "Source status",
    storageStatus: "Storage status",
    fileId: "Document ID",
    fileType: "Type",
    duplicateOf: "Duplicate of",
    noSelection: "New session",
    composerHint: "Enter to send, Shift + Enter for a new line",
    thinking: "Generating answer",
    quickPrompts: "Quick prompts",
    operational: "Operational",
    settingsActions: "Configuration actions",
    providerSettings: "Providers and models",
    chatSettings: "Chat model",
    embeddingSettings: "Embedding model",
    limitDescription: "Control retrieval count, embedding batches, and local model usage.",
    presetDescription: "Apply recommended settings for the current machine profile.",
    testDescription: "Test model connectivity before saving.",
    accountPlaceholder: "Future sign-in, permissions, and preferences will live here.",
    saveFirst: "Saved settings take effect immediately",
    stableDescription: "Best for local models and everyday machines",
    cloudDescription: "Best for cloud APIs and stable networks",
    lowDescription: "Best for low-memory or low-resource devices",
    refresh: "Refresh",
    retry: "Retry",
    activity: "Workspace overview",
  },
} satisfies Record<Language, Record<string, string>>

const defaultConfig: ModelConfig = {
  chat: { base_url: "", api_key: "", model: "" },
  embedding: {
    provider: "openai-compatible",
    base_url: "",
    api_key: "",
    model: "",
    batch_size: 8,
    max_concurrency: 1,
    batch_interval_seconds: 0,
  },
  retrieval: { top_k: 5 },
}

export function RagWorkspace() {
  const [language, setLanguage] = React.useState<Language>("zh")
  const [view, setView] = React.useState<View>("chat")
  const [conversations, setConversations] = React.useState<ConversationSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = React.useState<string | null>(null)
  const [messages, setMessages] = React.useState<ConversationMessage[]>([])
  const [documents, setDocuments] = React.useState<DocumentRecord[]>([])
  const [config, setConfig] = React.useState<ModelConfig>(defaultConfig)
  const [question, setQuestion] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(true)
  const [isSending, setIsSending] = React.useState(false)
  const [isUploading, setIsUploading] = React.useState(false)
  const [apiError, setApiError] = React.useState<string | null>(null)
  const [isMobileNavOpen, setIsMobileNavOpen] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement | null>(null)
  const t = text[language]

  const selectedSession = conversations.find(
    (session) => session.session_id === selectedSessionId
  )
  const indexedChunks = documents.reduce(
    (total, document) => total + (document.chunk_count || 0),
    0
  )
  const isModelConfigured = Boolean(config.chat.base_url && config.chat.model)
  const readyState = isModelConfigured ? t.configured : t.notConfigured

  const loadWorkspace = React.useCallback(async () => {
    setApiError(null)
    try {
      const [conversationResponse, documentResponse, configResponse] =
        await Promise.all([
          api.listConversations(),
          api.listDocuments(),
          api.getModelConfig(),
        ])
      const nextConversations = conversationResponse.data.conversations
      setConversations(nextConversations)
      setDocuments(documentResponse.data.documents)
      setConfig(configResponse.data.config)
      setSelectedSessionId((current) => {
        if (current && nextConversations.some((item) => item.session_id === current)) {
          return current
        }
        return nextConversations[0]?.session_id ?? null
      })
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsLoading(false)
    }
  }, [])

  const loadConversation = React.useCallback(async (sessionId: string | null) => {
    if (!sessionId) {
      setMessages([])
      return
    }
    try {
      const response = await api.getConversation(sessionId)
      setMessages(response.data.conversation.messages)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }, [])

  React.useEffect(() => {
    queueMicrotask(() => void loadWorkspace())
  }, [loadWorkspace])

  React.useEffect(() => {
    queueMicrotask(() => void loadConversation(selectedSessionId))
  }, [loadConversation, selectedSessionId])

  async function createConversation() {
    try {
      const response = await api.createConversation()
      const session = response.data.conversation
      setConversations((current) => [session, ...current])
      setSelectedSessionId(session.session_id)
      setMessages([])
      setView("chat")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function deleteConversation(sessionId: string) {
    try {
      await api.deleteConversation(sessionId)
      setConversations((current) => current.filter((item) => item.session_id !== sessionId))
      if (selectedSessionId === sessionId) {
        setSelectedSessionId(null)
        setMessages([])
      }
      toast.success("Conversation deleted")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function sendQuestion() {
    const trimmed = question.trim()
    if (!trimmed || isSending) {
      return
    }
    setQuestion("")
    setIsSending(true)
    const optimistic: ConversationMessage = {
      message_id: `local-${Date.now()}`,
      session_id: selectedSessionId ?? "pending",
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    }
    setMessages((current) => [...current, optimistic])
    try {
      const response = await api.chat(trimmed, selectedSessionId)
      const sessionId = response.data.result.session_id
      setSelectedSessionId(sessionId)
      await Promise.all([loadWorkspace(), loadConversation(sessionId)])
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    } finally {
      setIsSending(false)
    }
  }

  function applyPrompt(prompt: string) {
    setQuestion(prompt)
  }

  async function uploadFiles(files: FileList | null) {
    if (!files?.length) {
      return
    }
    setIsUploading(true)
    try {
      const response = await api.uploadDocuments(Array.from(files))
      const failed = response.data.results.filter((item) => item.error)
      if (failed.length) {
        toast.warning(`${failed.length} file(s) failed`)
      } else {
        toast.success("Documents processed")
      }
      const documentsResponse = await api.listDocuments()
      setDocuments(documentsResponse.data.documents)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  async function deleteDocument(documentId: string) {
    try {
      await api.deleteDocument(documentId)
      setDocuments((current) => current.filter((item) => item.document_id !== documentId))
      toast.success("Document deleted")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function reindexDocument(documentId: string) {
    try {
      await api.reindexDocument(documentId)
      const response = await api.listDocuments()
      setDocuments(response.data.documents)
      toast.success("Document reindexed")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function saveConfig() {
    try {
      const response = await api.saveModelConfig(config)
      setConfig(response.data.config)
      toast.success("Configuration saved")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function resetConfig() {
    try {
      const response = await api.resetModelConfig()
      setConfig(response.data.config)
      toast.success("Recommended defaults restored")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function applyPreset(preset: "stable" | "cloud-fast" | "low-resource") {
    try {
      const response = await api.applyPreset(preset)
      setConfig(response.data.config)
      toast.success("Preset applied")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function testModel(kind: "chat" | "embedding") {
    try {
      const response =
        kind === "chat" ? await api.testChatModel() : await api.testEmbeddingModel()
      if (response.data.result.ok) {
        toast.success(response.data.result.message)
      } else {
        toast.error(response.data.result.message)
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  const sidebar = (
    <WorkspaceSidebar
      t={t}
      view={view}
      setView={setView}
      conversations={conversations}
      selectedSessionId={selectedSessionId}
      setSelectedSessionId={setSelectedSessionId}
      isLoading={isLoading}
      createConversation={createConversation}
      deleteConversation={deleteConversation}
      documentCount={documents.length}
    />
  )

  return (
    <SidebarProvider>
      {sidebar}
      <SidebarInset className="rag-workbench-bg">
        <MobileHeader
          t={t}
          view={view}
          setView={(nextView) => {
            setView(nextView)
            setIsMobileNavOpen(false)
          }}
          createConversation={createConversation}
          documentCount={documents.length}
          readyState={readyState}
          open={isMobileNavOpen}
          onOpenChange={setIsMobileNavOpen}
        />
        {apiError ? (
          <main className="flex min-h-svh items-center justify-center p-6">
            <Empty className="rounded-2xl border bg-card/80 p-8 shadow-sm">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <DatabaseIcon />
                </EmptyMedia>
                <EmptyTitle>{t.apiOffline}</EmptyTitle>
                <EmptyDescription>
                  {apiError}. API: {api.baseUrl}
                </EmptyDescription>
              </EmptyHeader>
              <EmptyContent>
                <Button onClick={() => void loadWorkspace()}>
                  <RefreshCwIcon data-icon="inline-start" />
                  Retry
                </Button>
              </EmptyContent>
            </Empty>
          </main>
        ) : (
          <main className="min-h-svh">
            {view === "chat" && (
              <ChatView
                t={t}
                messages={messages}
                question={question}
                setQuestion={setQuestion}
                sendQuestion={sendQuestion}
                isSending={isSending}
                selectedSession={selectedSession}
                conversations={conversations}
                documents={documents}
                indexedChunks={indexedChunks}
                isModelConfigured={isModelConfigured}
                onPromptSelect={applyPrompt}
              />
            )}
            {view === "documents" && (
              <DocumentsView
                t={t}
                documents={documents}
                indexedChunks={indexedChunks}
                isUploading={isUploading}
                fileInputRef={fileInputRef}
                uploadFiles={uploadFiles}
                deleteDocument={deleteDocument}
                reindexDocument={reindexDocument}
                isModelConfigured={isModelConfigured}
              />
            )}
            {view === "settings" && (
              <SettingsView
                t={t}
                language={language}
                setLanguage={setLanguage}
                config={config}
                setConfig={setConfig}
                saveConfig={saveConfig}
                resetConfig={resetConfig}
                applyPreset={applyPreset}
                testModel={testModel}
                documents={documents}
                indexedChunks={indexedChunks}
                isModelConfigured={isModelConfigured}
              />
            )}
          </main>
        )}
      </SidebarInset>
    </SidebarProvider>
  )
}

function WorkspaceSidebar({
  t,
  view,
  setView,
  conversations,
  selectedSessionId,
  setSelectedSessionId,
  isLoading,
  createConversation,
  deleteConversation,
  documentCount,
}: {
  t: Record<string, string>
  view: View
  setView: (view: View) => void
  conversations: ConversationSession[]
  selectedSessionId: string | null
  setSelectedSessionId: (sessionId: string) => void
  isLoading: boolean
  createConversation: () => void
  deleteConversation: (sessionId: string) => void
  documentCount: number
}) {
  const navItems = [
    {
      value: "chat" as const,
      label: t.startChat,
      icon: MessageSquareIcon,
      meta: conversations.length,
    },
    {
      value: "documents" as const,
      label: t.documents,
      icon: FileTextIcon,
      meta: documentCount,
    },
    {
      value: "settings" as const,
      label: t.settings,
      icon: SettingsIcon,
      meta: null,
    },
  ]

  return (
    <Sidebar collapsible="none" className="hidden border-r bg-sidebar/95 md:flex">
      <SidebarHeader className="gap-4 p-4">
        <div className="flex items-start gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-primary text-[0.68rem] font-semibold tracking-wide text-primary-foreground shadow-sm">
            RAG
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">{t.title}</div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="size-1.5 rounded-full bg-chart-2" />
              <span className="truncate">{t.connected}</span>
            </div>
          </div>
        </div>
        <Button
          variant="default"
          size="lg"
          className="w-full justify-start"
          onClick={() => void createConversation()}
        >
            <PlusIcon data-icon="inline-start" />
            {t.newChat}
        </Button>
        <div className="rounded-lg border bg-background/75 p-3 text-xs shadow-sm">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="font-medium text-foreground">{t.systemStatus}</span>
            <StatusPill tone="success" label={t.operational} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <MiniMetric label={t.documentCount} value={documentCount} />
            <MiniMetric label={t.workspace} value="local" />
          </div>
          <div className="mt-3 truncate text-muted-foreground">{api.baseUrl}</div>
        </div>
      </SidebarHeader>
      <SidebarSeparator />
      <SidebarContent>
        <SidebarGroup className="gap-2 p-3">
          <SidebarGroupLabel className="px-1 text-[0.68rem] uppercase tracking-normal">
            {t.primaryNav}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {navItems.map((item) => (
                <SidebarMenuItem key={item.value}>
                  <SidebarMenuButton
                    className="h-10 rounded-lg"
                    isActive={view === item.value}
                    data-testid={`nav-${item.value}`}
                    onClick={() => setView(item.value)}
                  >
                    <item.icon />
                    <span>{item.label}</span>
                    {item.meta !== null && (
                      <Badge variant="secondary" className="ml-auto">
                        {item.meta}
                      </Badge>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarSeparator />
        <SidebarGroup className="gap-2 p-3">
          <SidebarGroupLabel className="px-1 text-[0.68rem] uppercase tracking-normal">
            {t.conversations}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            {isLoading ? (
              <div className="flex flex-col gap-2">
                <Skeleton className="h-10 rounded-xl" />
                <Skeleton className="h-10 rounded-xl" />
                <Skeleton className="h-10 rounded-xl" />
              </div>
            ) : conversations.length ? (
              <SidebarMenu className="gap-1">
                {conversations.map((session) => (
                  <SidebarMenuItem key={session.session_id}>
                    <SidebarMenuButton
                      className="h-11 rounded-lg"
                      isActive={selectedSessionId === session.session_id && view === "chat"}
                      onClick={() => {
                        setSelectedSessionId(session.session_id)
                        setView("chat")
                      }}
                    >
                      <HistoryIcon />
                      <span>{session.title || t.noSelection}</span>
                    </SidebarMenuButton>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <SidebarMenuAction
                          showOnHover
                          className="top-2.5"
                          onClick={() => void deleteConversation(session.session_id)}
                        >
                          <Trash2Icon />
                          <span className="sr-only">{t.delete}</span>
                        </SidebarMenuAction>
                      </TooltipTrigger>
                      <TooltipContent>{t.delete}</TooltipContent>
                    </Tooltip>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            ) : (
              <div className="rounded-lg border border-dashed bg-background/60 p-3 text-xs leading-5 text-muted-foreground">
                {t.emptyDescription}
              </div>
            )}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarSeparator />
      <SidebarFooter className="p-3">
        <SidebarMenu className="gap-1">
          <SidebarMenuItem>
            <SidebarMenuButton className="h-10 rounded-lg">
              <UserIcon />
              <span>{t.account}</span>
              <Badge variant="secondary" className="ml-auto">
                {t.accountHint}
              </Badge>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}

function MobileHeader({
  t,
  view,
  setView,
  createConversation,
  documentCount,
  readyState,
  open,
  onOpenChange,
}: {
  t: Record<string, string>
  view: View
  setView: (view: View) => void
  createConversation: () => void
  documentCount: number
  readyState: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const navItems = [
    { value: "chat" as const, label: t.startChat, icon: MessageSquareIcon },
    { value: "documents" as const, label: t.documents, icon: FileTextIcon },
    { value: "settings" as const, label: t.settings, icon: SettingsIcon },
  ]

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b bg-card/90 px-4 backdrop-blur md:hidden">
      <Button
        size="icon-sm"
        variant="ghost"
        aria-expanded={open}
        onClick={() => onOpenChange(!open)}
      >
        <MenuIcon />
        <span className="sr-only">Menu</span>
      </Button>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{t.title}</div>
        <div className="truncate text-xs text-muted-foreground">{t.subtitle}</div>
      </div>
      <StatusPill tone="success" label={t.connected} />
      {open && (
        <div className="absolute inset-x-3 top-[4.25rem] z-30 rounded-xl border bg-popover p-3 text-popover-foreground shadow-xl">
          <div className="mb-3">
            <div className="truncate text-sm font-semibold">{t.title}</div>
            <div className="truncate text-xs text-muted-foreground">{t.subtitle}</div>
          </div>
          <div className="flex flex-col gap-3">
            <Button
              variant="default"
              className="justify-start"
              onClick={() => {
                void createConversation()
                onOpenChange(false)
              }}
            >
              <PlusIcon data-icon="inline-start" />
              {t.newChat}
            </Button>
            <div className="grid gap-2">
              {navItems.map((item) => (
                <Button
                  key={item.value}
                  variant={view === item.value ? "secondary" : "outline"}
                  className="justify-start"
                  data-testid={`mobile-nav-${item.value}`}
                  onClick={() => setView(item.value)}
                >
                  <item.icon data-icon="inline-start" />
                  {item.label}
                </Button>
              ))}
            </div>
            <div className="rounded-lg border bg-background/70 p-3 text-xs text-muted-foreground">
              <div className="flex items-center justify-between gap-2">
                <span>{t.documentCount}</span>
                <span className="font-medium text-foreground">{documentCount}</span>
              </div>
              <div className="mt-2 flex items-center justify-between gap-2">
                <span>{t.modelSettings}</span>
                <span className="font-medium text-foreground">{readyState}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}

function ChatView({
  t,
  messages,
  question,
  setQuestion,
  sendQuestion,
  isSending,
  selectedSession,
  conversations,
  documents,
  indexedChunks,
  isModelConfigured,
  onPromptSelect,
}: {
  t: Record<string, string>
  messages: ConversationMessage[]
  question: string
  setQuestion: (value: string) => void
  sendQuestion: () => void
  isSending: boolean
  selectedSession?: ConversationSession
  conversations: ConversationSession[]
  documents: DocumentRecord[]
  indexedChunks: number
  isModelConfigured: boolean
  onPromptSelect: (prompt: string) => void
}) {
  const sessionBadge = selectedSession?.session_id.slice(0, 8) ?? t.noSelection

  return (
    <div className="mx-auto flex h-[calc(100svh-4rem)] max-w-6xl flex-col px-4 py-5 md:h-svh lg:px-8">
      <PageHeader
        title={t.title}
        description={t.subtitle}
        badge={sessionBadge}
        actions={
          <div className="flex flex-wrap justify-end gap-2">
            <StatusPill
              tone={isModelConfigured ? "success" : "warning"}
              label={isModelConfigured ? t.configured : t.notConfigured}
            />
            <StatusPill tone={documents.length ? "success" : "neutral"} label={t.knowledgeReady} />
          </div>
        }
      />
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <StatCard icon={MessageSquareIcon} label={t.messageCount} value={messages.length} />
        <StatCard icon={FileTextIcon} label={t.documentCount} value={documents.length} />
        <StatCard icon={Layers3Icon} label={t.indexedChunks} value={indexedChunks} />
      </div>
      <div className="rag-panel rag-soft-border flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-card/70 px-4 py-3">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium">
              {selectedSession?.title || t.noSelection}
            </div>
            <div className="mt-0.5 truncate text-xs text-muted-foreground">
              {t.askHint}
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <CommandIcon />
            <span>{t.composerHint}</span>
          </div>
        </div>
        <ScrollArea className="min-h-0 flex-1">
          {messages.length ? (
            <div className="flex flex-col gap-4 p-4 md:p-6">
              {messages.map((message) => (
                <MessageBubble key={message.message_id} message={message} />
              ))}
              {isSending && (
                <div className="flex w-fit items-center gap-2 rounded-full border bg-background/70 px-3 py-2 text-sm text-muted-foreground">
                  <Loader2Icon className="animate-spin" />
                  {t.thinking}
                </div>
              )}
            </div>
          ) : (
            <EmptyChat
              t={t}
              conversations={conversations.length}
              documents={documents.length}
              onPromptSelect={onPromptSelect}
            />
          )}
        </ScrollArea>
        <div className="border-t bg-card/80 p-3 backdrop-blur">
          <div className="flex items-end gap-2 rounded-xl border bg-background p-2 shadow-sm">
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  void sendQuestion()
                }
              }}
              placeholder={t.inputPlaceholder}
              className="max-h-40 min-h-11 resize-none border-0 bg-transparent px-2 shadow-none focus-visible:ring-0"
            />
            <Button
              size="icon-lg"
              disabled={!question.trim() || isSending}
              onClick={() => void sendQuestion()}
            >
              {isSending ? <Loader2Icon className="animate-spin" /> : <SendIcon />}
              <span className="sr-only">{t.send}</span>
            </Button>
          </div>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2 px-1 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
            <SparklesIcon />
            <span>{t.askHint}</span>
            </div>
            <span>{t.composerHint}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function EmptyChat({
  t,
  conversations,
  documents,
  onPromptSelect,
}: {
  t: Record<string, string>
  conversations: number
  documents: number
  onPromptSelect: (prompt: string) => void
}) {
  return (
    <div className="grid min-h-[28rem] place-items-center p-6">
      <div className="max-w-xl text-center">
        <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-xl bg-accent text-accent-foreground shadow-sm">
          <BotIcon />
        </div>
        <h2 className="text-xl font-semibold tracking-tight">{t.emptyTitle}</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          {t.emptyDescription}
        </p>
        <div className="mt-5 text-xs font-medium text-muted-foreground">
          {t.quickPrompts}
        </div>
        <div className="mt-2 grid gap-2 text-left sm:grid-cols-3">
          {[t.promptOne, t.promptTwo, t.promptThree].map((prompt) => (
            <button
              key={prompt}
              data-testid="quick-prompt"
              className="rounded-lg border bg-background/75 p-3 text-left text-xs leading-5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              onClick={() => onPromptSelect(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
        <div className="mt-5 flex justify-center gap-2">
          <Badge variant="secondary">
            {t.conversations}: {conversations}
          </Badge>
          <Badge variant="secondary">
            {t.documents}: {documents}
          </Badge>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === "user"
  return (
    <div className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="mt-1 flex size-8 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground">
          <BotIcon />
        </div>
      )}
      <div
        className={cn(
          "max-w-[86%] whitespace-pre-wrap rounded-xl px-4 py-3 text-sm leading-6 shadow-sm md:max-w-[78%]",
          isUser
            ? "bg-primary text-primary-foreground"
            : "border bg-card text-card-foreground"
        )}
      >
        {message.content}
      </div>
    </div>
  )
}

function DocumentsView({
  t,
  documents,
  indexedChunks,
  isUploading,
  fileInputRef,
  uploadFiles,
  deleteDocument,
  reindexDocument,
  isModelConfigured,
}: {
  t: Record<string, string>
  documents: DocumentRecord[]
  indexedChunks: number
  isUploading: boolean
  fileInputRef: React.RefObject<HTMLInputElement | null>
  uploadFiles: (files: FileList | null) => void
  deleteDocument: (documentId: string) => void
  reindexDocument: (documentId: string) => void
  isModelConfigured: boolean
}) {
  const duplicateCount = documents.filter(
    (document) => document.status === "duplicate" || document.duplicate_of_document_id
  ).length

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5 px-4 py-5 lg:px-8">
      <PageHeader
        title={t.documents}
        description={t.uploadHint}
        badge={`${documents.length} ${t.documentCount}`}
        actions={
          <StatusPill
            tone={isModelConfigured ? "success" : "warning"}
            label={isModelConfigured ? t.configured : t.notConfigured}
          />
        }
      />
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard icon={FileTextIcon} label={t.documentCount} value={documents.length} />
        <StatCard icon={Layers3Icon} label={t.indexedChunks} value={indexedChunks} />
        <StatCard icon={HardDriveIcon} label={t.duplicate} value={duplicateCount} />
      </div>
      <Card className="rag-panel rag-soft-border overflow-hidden">
        <CardHeader className="gap-3 sm:flex sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <CardTitle>{t.documentLibrary}</CardTitle>
            <CardDescription>{t.documentLibraryDesc}</CardDescription>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.md,.markdown,.txt"
              className="hidden"
              onChange={(event) => void uploadFiles(event.target.files)}
            />
            <Button
              data-testid="documents-upload-button"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
            >
              {isUploading ? (
                <Loader2Icon data-icon="inline-start" className="animate-spin" />
              ) : (
                <UploadIcon data-icon="inline-start" />
              )}
              {isUploading ? t.uploadBusy : t.uploadCta}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {documents.length ? (
            <>
            <div className="hidden overflow-x-auto rounded-lg border bg-background/65 md:block">
              <Table className="min-w-[860px]">
                <TableHeader>
                  <TableRow className="bg-muted/60">
                    <TableHead>{t.filename}</TableHead>
                    <TableHead>{t.status}</TableHead>
                    <TableHead>{t.parse}</TableHead>
                    <TableHead>{t.index}</TableHead>
                    <TableHead>{t.chunks}</TableHead>
                    <TableHead className="text-right">{t.actions}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.map((document) => (
                    <TableRow key={document.document_id}>
                      <TableCell className="max-w-[20rem]">
                        <div className="flex min-w-0 items-center gap-3">
                          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                            <FileTextIcon />
                          </div>
                          <div className="flex min-w-0 flex-col gap-1">
                            <span className="truncate font-medium">
                              {document.original_filename}
                            </span>
                            <DocumentMeta t={t} document={document} />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <StatusBadge value={document.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {document.parse_status}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {document.index_status}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{document.chunk_count}</Badge>
                      </TableCell>
                      <TableCell>
                        <DocumentActions
                          t={t}
                          document={document}
                          deleteDocument={deleteDocument}
                          reindexDocument={reindexDocument}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="grid gap-3 md:hidden">
              {documents.map((document) => (
                <div
                  key={document.document_id}
                  data-testid="mobile-document-card"
                  className="rounded-lg border bg-background/70 p-3 shadow-sm"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                      <FileTextIcon />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        {document.original_filename}
                      </div>
                      <DocumentMeta t={t} document={document} />
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <DocumentMiniStat label={t.status} value={<StatusBadge value={document.status} />} />
                    <DocumentMiniStat label={t.chunks} value={document.chunk_count} />
                    <DocumentMiniStat label={t.parse} value={document.parse_status} />
                    <DocumentMiniStat label={t.index} value={document.index_status} />
                  </div>
                  <div className="mt-3 flex justify-end">
                    <DocumentActions
                      t={t}
                      document={document}
                      deleteDocument={deleteDocument}
                      reindexDocument={reindexDocument}
                    />
                  </div>
                </div>
              ))}
            </div>
            </>
          ) : (
            <div className="grid min-h-[24rem] place-items-center rounded-lg border border-dashed bg-background/55">
              <Empty>
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <FileTextIcon />
                  </EmptyMedia>
                  <EmptyTitle>{t.noDocuments}</EmptyTitle>
                  <EmptyDescription>{t.noDocumentsDesc}</EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                  <Button
                    data-testid="documents-upload-button"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <UploadIcon data-icon="inline-start" />
                    {t.upload}
                  </Button>
                </EmptyContent>
              </Empty>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function SettingsView({
  t,
  language,
  setLanguage,
  config,
  setConfig,
  saveConfig,
  resetConfig,
  applyPreset,
  testModel,
  documents,
  indexedChunks,
  isModelConfigured,
}: {
  t: Record<string, string>
  language: Language
  setLanguage: (language: Language) => void
  config: ModelConfig
  setConfig: React.Dispatch<React.SetStateAction<ModelConfig>>
  saveConfig: () => void
  resetConfig: () => void
  applyPreset: (preset: "stable" | "cloud-fast" | "low-resource") => void
  testModel: (kind: "chat" | "embedding") => void
  documents: DocumentRecord[]
  indexedChunks: number
  isModelConfigured: boolean
}) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5 px-4 py-5 lg:px-8">
      <PageHeader
        title={t.settings}
        description={t.beginnerHint}
        badge={isModelConfigured ? t.configured : t.notConfigured}
        actions={
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="outline" onClick={() => void testModel("chat")}>
              <BotIcon data-icon="inline-start" />
              {t.testChat}
            </Button>
            <Button onClick={() => void saveConfig()}>
              <CheckIcon data-icon="inline-start" />
              {t.save}
            </Button>
          </div>
        }
      />
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard
          icon={DatabaseIcon}
          label={t.providerSettings}
          value={config.embedding.provider}
        />
        <StatCard icon={FileTextIcon} label={t.documentCount} value={documents.length} />
        <StatCard icon={Layers3Icon} label={t.indexedChunks} value={indexedChunks} />
      </div>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <Tabs defaultValue="model" className="min-w-0">
          <TabsList className="mb-3">
            <TabsTrigger value="model">{t.modelSettings}</TabsTrigger>
            <TabsTrigger value="limits">{t.retrievalSettings}</TabsTrigger>
          </TabsList>
          <TabsContent value="model">
            <Card className="rag-panel rag-soft-border">
              <CardHeader>
                <CardTitle>{t.providerSettings}</CardTitle>
                <CardDescription>{t.beginnerHint}</CardDescription>
              </CardHeader>
              <CardContent>
                <FieldGroup className="grid gap-4 md:grid-cols-2">
                  <Field className="rounded-lg border bg-background/65 p-3 md:col-span-2">
                    <div className="mb-3 flex items-center gap-2 text-sm font-medium">
                      <BotIcon />
                      {t.chatSettings}
                    </div>
                    <FieldLabel htmlFor="chat-base-url">{t.chatBaseUrl}</FieldLabel>
                    <Input
                      id="chat-base-url"
                      value={config.chat.base_url}
                      onChange={(event) =>
                        setConfig((current) => ({
                          ...current,
                          chat: { ...current.chat, base_url: event.target.value },
                        }))
                      }
                    />
                  </Field>
                  <Field className="rounded-lg border bg-background/65 p-3">
                    <FieldLabel htmlFor="chat-api-key">{t.chatApiKey}</FieldLabel>
                    <Input
                      id="chat-api-key"
                      type="password"
                      value={config.chat.api_key}
                      onChange={(event) =>
                        setConfig((current) => ({
                          ...current,
                          chat: { ...current.chat, api_key: event.target.value },
                        }))
                      }
                    />
                  </Field>
                  <Field className="rounded-lg border bg-background/65 p-3">
                    <FieldLabel htmlFor="chat-model">{t.chatModel}</FieldLabel>
                    <Input
                      id="chat-model"
                      value={config.chat.model}
                      onChange={(event) =>
                        setConfig((current) => ({
                          ...current,
                          chat: { ...current.chat, model: event.target.value },
                        }))
                      }
                    />
                  </Field>
                  <div className="md:col-span-2">
                    <Separator />
                  </div>
                  <Field className="rounded-lg border bg-background/65 p-3">
                    <FieldLabel>{t.embeddingProvider}</FieldLabel>
                    <Select
                      value={config.embedding.provider}
                      onValueChange={(value) =>
                        setConfig((current) => ({
                          ...current,
                          embedding: {
                            ...current.embedding,
                            provider: value as ModelConfig["embedding"]["provider"],
                          },
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectItem value="openai-compatible">
                            OpenAI-compatible
                          </SelectItem>
                          <SelectItem value="local-api">Local API</SelectItem>
                          <SelectItem value="local-huggingface">
                            Local HuggingFace
                          </SelectItem>
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                  <Field className="rounded-lg border bg-background/65 p-3">
                    <FieldLabel htmlFor="embedding-model">{t.embeddingModel}</FieldLabel>
                    <Input
                      id="embedding-model"
                      value={config.embedding.model}
                      onChange={(event) =>
                        setConfig((current) => ({
                          ...current,
                          embedding: { ...current.embedding, model: event.target.value },
                        }))
                      }
                    />
                  </Field>
                  <Field className="rounded-lg border bg-background/65 p-3">
                    <FieldLabel htmlFor="embedding-base-url">
                      {t.embeddingBaseUrl}
                    </FieldLabel>
                    <Input
                      id="embedding-base-url"
                      value={config.embedding.base_url}
                      onChange={(event) =>
                        setConfig((current) => ({
                          ...current,
                          embedding: {
                            ...current.embedding,
                            base_url: event.target.value,
                          },
                        }))
                      }
                    />
                  </Field>
                  <Field className="rounded-lg border bg-background/65 p-3">
                    <FieldLabel htmlFor="embedding-api-key">
                      {t.embeddingApiKey}
                    </FieldLabel>
                    <Input
                      id="embedding-api-key"
                      type="password"
                      value={config.embedding.api_key}
                      onChange={(event) =>
                        setConfig((current) => ({
                          ...current,
                          embedding: {
                            ...current.embedding,
                            api_key: event.target.value,
                          },
                        }))
                      }
                    />
                  </Field>
                </FieldGroup>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="limits">
            <Card className="rag-panel rag-soft-border">
              <CardHeader>
                <CardTitle>{t.retrievalSettings}</CardTitle>
                <CardDescription>{t.limitDescription}</CardDescription>
              </CardHeader>
              <CardContent>
                <FieldGroup className="grid gap-4 md:grid-cols-2">
                  <NumberField
                    id="top-k"
                    icon={SearchIcon}
                    label={t.topK}
                    description="Controls how many context chunks are retrieved."
                    value={config.retrieval.top_k}
                    min={1}
                    onChange={(value) =>
                      setConfig((current) => ({
                        ...current,
                        retrieval: { top_k: value },
                      }))
                    }
                  />
                  <NumberField
                    id="batch-size"
                    icon={Layers3Icon}
                    label={t.batchSize}
                    description="Controls how many text chunks are embedded per batch."
                    value={config.embedding.batch_size}
                    min={1}
                    onChange={(value) =>
                      setConfig((current) => ({
                        ...current,
                        embedding: { ...current.embedding, batch_size: value },
                      }))
                    }
                  />
                  <NumberField
                    id="max-concurrency"
                    icon={GaugeIcon}
                    label={t.maxConcurrency}
                    description="Local services and low-resource computers should usually stay at 1."
                    value={config.embedding.max_concurrency}
                    min={1}
                    onChange={(value) =>
                      setConfig((current) => ({
                        ...current,
                        embedding: { ...current.embedding, max_concurrency: value },
                      }))
                    }
                  />
                  <NumberField
                    id="interval"
                    icon={Clock3Icon}
                    label={t.interval}
                    description={t.beginnerHint}
                    value={config.embedding.batch_interval_seconds}
                    min={0}
                    step={0.1}
                    onChange={(value) =>
                      setConfig((current) => ({
                        ...current,
                        embedding: {
                          ...current.embedding,
                          batch_interval_seconds: value,
                        },
                      }))
                    }
                  />
                </FieldGroup>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        <div className="flex flex-col gap-4">
          <Card className="rag-panel rag-soft-border">
            <CardHeader>
              <CardTitle>{t.language}</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={language} onValueChange={(value) => setLanguage(value as Language)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="zh">中文</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
          <Card className="rag-panel rag-soft-border">
            <CardHeader>
              <CardTitle>{t.account}</CardTitle>
              <CardDescription>{t.accountHint}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3 rounded-xl border bg-background/70 p-3 text-sm text-muted-foreground">
                <UserIcon />
                {t.accountPlaceholder}
              </div>
            </CardContent>
          </Card>
          <FieldSet className="rounded-xl border bg-card/85 p-3 shadow-sm">
            <div className="mb-1 text-sm font-medium">{t.settingsActions}</div>
            <div className="text-xs leading-5 text-muted-foreground">{t.saveFirst}</div>
            <div className="mt-3 grid gap-2">
              <Button onClick={() => void saveConfig()}>
                <CheckIcon data-icon="inline-start" />
                {t.save}
              </Button>
              <Button variant="outline" onClick={() => void resetConfig()}>
                <RefreshCwIcon data-icon="inline-start" />
                {t.reset}
              </Button>
            </div>
            <Separator className="my-3" />
            <div className="mb-2 text-xs leading-5 text-muted-foreground">
              {t.presetDescription}
            </div>
            <div className="grid grid-cols-1 gap-2">
              <Button variant="outline" onClick={() => void applyPreset("stable")}>
                {t.stable}
              </Button>
              <Button variant="outline" onClick={() => void applyPreset("cloud-fast")}>
                {t.cloud}
              </Button>
              <Button variant="outline" onClick={() => void applyPreset("low-resource")}>
                {t.low}
              </Button>
            </div>
            <Separator className="my-3" />
            <div className="mb-2 text-xs leading-5 text-muted-foreground">
              {t.testDescription}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="secondary" onClick={() => void testModel("chat")}>
                {t.testChat}
              </Button>
              <Button variant="secondary" onClick={() => void testModel("embedding")}>
                {t.testEmbedding}
              </Button>
            </div>
          </FieldSet>
        </div>
      </div>
    </div>
  )
}

function PageHeader({
  title,
  description,
  badge,
  actions,
}: {
  title: string
  description: string
  badge: string
  actions?: React.ReactNode
}) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <h1 className="truncate text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
          {description}
        </p>
      </div>
      <div className="flex flex-wrap items-center justify-end gap-2">
        {actions}
        <Badge variant="secondary" className="mt-1">
          {badge}
        </Badge>
      </div>
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="rag-soft-border flex items-center gap-3 rounded-xl border bg-card/70 p-3 shadow-sm">
      <div className="flex size-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
        <Icon />
      </div>
      <div className="min-w-0">
        <div className="truncate text-xs text-muted-foreground">{label}</div>
        <div className="truncate text-sm font-semibold">{value}</div>
      </div>
    </div>
  )
}

function StatusPill({ tone, label }: { tone: StatusTone; label: string }) {
  const Icon =
    tone === "success"
      ? CheckCircle2Icon
      : tone === "warning"
        ? AlertTriangleIcon
        : tone === "destructive"
          ? XCircleIcon
          : InfoIcon

  return (
    <span
      className={cn(
        "inline-flex h-7 items-center gap-1.5 rounded-full border px-2.5 text-xs font-medium",
        tone === "success" &&
          "border-chart-2/25 bg-chart-2/10 text-[color-mix(in_oklch,var(--chart-2),var(--foreground)_30%)]",
        tone === "warning" &&
          "border-chart-3/30 bg-chart-3/10 text-[color-mix(in_oklch,var(--chart-3),var(--foreground)_42%)]",
        tone === "destructive" &&
          "border-destructive/25 bg-destructive/10 text-destructive",
        tone === "neutral" && "border-border bg-muted text-muted-foreground"
      )}
    >
      <Icon />
      {label}
    </span>
  )
}

function MiniMetric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="truncate text-muted-foreground">{label}</div>
      <div className="truncate font-semibold text-foreground">{value}</div>
    </div>
  )
}

function NumberField({
  id,
  icon: Icon,
  label,
  description,
  value,
  min,
  step = 1,
  onChange,
}: {
  id: string
  icon: React.ElementType
  label: string
  description: string
  value: number
  min: number
  step?: number
  onChange: (value: number) => void
}) {
  return (
    <Field className="rounded-lg border bg-background/70 p-3">
      <div className="flex items-start gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
          <Icon />
        </div>
        <div className="min-w-0 flex-1">
          <FieldLabel htmlFor={id}>{label}</FieldLabel>
          <Input
            id={id}
            type="number"
            min={min}
            step={step}
            value={value}
            onChange={(event) => onChange(Number(event.target.value))}
            className="mt-2"
          />
          <FieldDescription className="mt-2">{description}</FieldDescription>
        </div>
      </div>
    </Field>
  )
}

function DocumentMeta({
  t,
  document,
}: {
  t: Record<string, string>
  document: DocumentRecord
}) {
  return (
    <span
      className="block truncate text-xs text-muted-foreground"
      title={document.document_id}
    >
      {document.file_type || t.fileType} · {document.document_id}
    </span>
  )
}

function DocumentMiniStat({
  label,
  value,
}: {
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="min-w-0 rounded-lg border bg-card/70 p-2">
      <div className="truncate text-muted-foreground">{label}</div>
      <div className="mt-1 truncate font-medium text-foreground">{value}</div>
    </div>
  )
}

function DocumentActions({
  t,
  document,
  deleteDocument,
  reindexDocument,
}: {
  t: Record<string, string>
  document: DocumentRecord
  deleteDocument: (documentId: string) => void
  reindexDocument: (documentId: string) => void
}) {
  return (
    <div className="flex justify-end gap-2">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="icon-sm"
            onClick={() => void reindexDocument(document.document_id)}
          >
            <RefreshCwIcon />
            <span className="sr-only">{t.reindex}</span>
          </Button>
        </TooltipTrigger>
        <TooltipContent>{t.reindexHint}</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="destructive"
            size="icon-sm"
            onClick={() => void deleteDocument(document.document_id)}
          >
            <Trash2Icon />
            <span className="sr-only">{t.delete}</span>
          </Button>
        </TooltipTrigger>
        <TooltipContent>{t.deleteHint}</TooltipContent>
      </Tooltip>
    </div>
  )
}

function StatusBadge({ value }: { value: string }) {
  const variant = value === "duplicate" ? "secondary" : "outline"
  return <Badge variant={variant}>{value}</Badge>
}
