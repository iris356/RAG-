"use client"

import * as React from "react"
import {
  BotIcon,
  CheckIcon,
  Clock3Icon,
  DatabaseIcon,
  FileTextIcon,
  GaugeIcon,
  HardDriveIcon,
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
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
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
  const fileInputRef = React.useRef<HTMLInputElement | null>(null)
  const t = text[language]

  const selectedSession = conversations.find(
    (session) => session.session_id === selectedSessionId
  )
  const indexedChunks = documents.reduce(
    (total, document) => total + (document.chunk_count || 0),
    0
  )

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
        <MobileHeader t={t} setView={setView} createConversation={createConversation} />
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
  return (
    <Sidebar collapsible="none" className="hidden border-r bg-sidebar/95 md:flex">
      <SidebarHeader className="gap-4 p-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-[0.68rem] font-semibold tracking-wide text-primary-foreground shadow-sm">
            RAG
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{t.title}</div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="size-1.5 rounded-full bg-chart-2" />
              <span className="truncate">{api.baseUrl}</span>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant={view === "documents" ? "secondary" : "outline"}
            size="sm"
            className="justify-start"
            onClick={() => setView("documents")}
          >
            <FileTextIcon data-icon="inline-start" />
            {t.documents}
          </Button>
          <Button
            variant="default"
            size="sm"
            className="justify-start"
            onClick={() => void createConversation()}
          >
            <PlusIcon data-icon="inline-start" />
            {t.newChat}
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-2 rounded-xl border bg-background/70 p-2 text-xs">
          <MiniMetric label={t.documentCount} value={documentCount} />
          <MiniMetric label={t.workspace} value="local" />
        </div>
      </SidebarHeader>
      <SidebarSeparator />
      <SidebarContent>
        <SidebarGroup className="gap-2 p-3">
          <SidebarGroupLabel className="px-1 text-[0.68rem] uppercase tracking-[0.14em]">
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
                      className="h-10 rounded-xl"
                      isActive={selectedSessionId === session.session_id && view === "chat"}
                      onClick={() => {
                        setSelectedSessionId(session.session_id)
                        setView("chat")
                      }}
                    >
                      <MessageSquareIcon />
                      <span>{session.title}</span>
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
              <div className="rounded-xl border border-dashed bg-background/60 p-3 text-xs leading-5 text-muted-foreground">
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
            <SidebarMenuButton
              className="h-10 rounded-xl"
              isActive={view === "settings"}
              onClick={() => setView("settings")}
            >
              <SettingsIcon />
              <span>{t.settings}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton className="h-10 rounded-xl">
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
  setView,
  createConversation,
}: {
  t: Record<string, string>
  setView: (view: View) => void
  createConversation: () => void
}) {
  return (
    <header className="flex h-14 items-center gap-3 border-b bg-card/85 px-4 backdrop-blur md:hidden">
      <Sheet>
        <SheetTrigger asChild>
          <Button size="icon-sm" variant="ghost">
            <MenuIcon />
            <span className="sr-only">Menu</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left">
          <SheetHeader>
            <SheetTitle>{t.title}</SheetTitle>
            <SheetDescription>{t.subtitle}</SheetDescription>
          </SheetHeader>
          <div className="flex flex-col gap-2 px-4">
            <Button variant="outline" onClick={() => setView("documents")}>
              <FileTextIcon data-icon="inline-start" />
              {t.documents}
            </Button>
            <Button variant="default" onClick={() => void createConversation()}>
              <PlusIcon data-icon="inline-start" />
              {t.newChat}
            </Button>
            <Button variant="outline" onClick={() => setView("settings")}>
              <SettingsIcon data-icon="inline-start" />
              {t.settings}
            </Button>
          </div>
        </SheetContent>
      </Sheet>
      <div className="min-w-0">
        <div className="truncate text-sm font-semibold">{t.title}</div>
        <div className="truncate text-xs text-muted-foreground">{t.subtitle}</div>
      </div>
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
}) {
  return (
    <div className="mx-auto flex h-svh max-w-5xl flex-col px-4 py-5 lg:px-8">
      <PageHeader
        title={t.title}
        description={t.subtitle}
        badge={selectedSession?.session_id.slice(0, 12) ?? t.ready}
      />
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <StatCard icon={MessageSquareIcon} label={t.messageCount} value={messages.length} />
        <StatCard icon={FileTextIcon} label={t.documentCount} value={documents.length} />
        <StatCard icon={Layers3Icon} label={t.indexedChunks} value={indexedChunks} />
      </div>
      <div className="rag-panel rag-soft-border flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border">
        <ScrollArea className="min-h-0 flex-1">
          {messages.length ? (
            <div className="flex flex-col gap-4 p-4 md:p-6">
              {messages.map((message) => (
                <MessageBubble key={message.message_id} message={message} />
              ))}
              {isSending && (
                <div className="flex items-center gap-2 rounded-full border bg-background/70 px-3 py-2 text-sm text-muted-foreground">
                  <Loader2Icon className="animate-spin" />
                  Thinking
                </div>
              )}
            </div>
          ) : (
            <EmptyChat t={t} conversations={conversations.length} documents={documents.length} />
          )}
        </ScrollArea>
        <div className="border-t bg-card/80 p-3 backdrop-blur">
          <div className="flex items-end gap-2 rounded-2xl border bg-background p-2 shadow-sm">
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
          <div className="mt-2 flex items-center gap-2 px-1 text-xs text-muted-foreground">
            <SparklesIcon />
            <span>{t.askHint}</span>
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
}: {
  t: Record<string, string>
  conversations: number
  documents: number
}) {
  return (
    <div className="grid min-h-[28rem] place-items-center p-6">
      <div className="max-w-xl text-center">
        <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-2xl bg-accent text-accent-foreground shadow-sm">
          <BotIcon />
        </div>
        <h2 className="text-xl font-semibold tracking-tight">{t.emptyTitle}</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          {t.emptyDescription}
        </p>
        <div className="mt-5 grid gap-2 text-left sm:grid-cols-3">
          {[t.promptOne, t.promptTwo, t.promptThree].map((prompt) => (
            <div
              key={prompt}
              className="rounded-xl border bg-background/75 p-3 text-xs leading-5 text-muted-foreground"
            >
              {prompt}
            </div>
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
          "max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm",
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
}: {
  t: Record<string, string>
  documents: DocumentRecord[]
  indexedChunks: number
  isUploading: boolean
  fileInputRef: React.RefObject<HTMLInputElement | null>
  uploadFiles: (files: FileList | null) => void
  deleteDocument: (documentId: string) => void
  reindexDocument: (documentId: string) => void
}) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5 px-4 py-5 lg:px-8">
      <PageHeader
        title={t.documents}
        description={t.uploadHint}
        badge={`${documents.length} ${t.documentCount}`}
      />
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard icon={FileTextIcon} label={t.documentCount} value={documents.length} />
        <StatCard icon={Layers3Icon} label={t.indexedChunks} value={indexedChunks} />
        <StatCard icon={HardDriveIcon} label={t.localVector} value="Chroma" />
      </div>
      <Card className="rag-panel rag-soft-border">
        <CardHeader className="gap-3 sm:flex sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{t.documents}</CardTitle>
            <CardDescription>{t.noDocumentsDesc}</CardDescription>
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
            <Button disabled={isUploading} onClick={() => fileInputRef.current?.click()}>
              {isUploading ? (
                <Loader2Icon data-icon="inline-start" className="animate-spin" />
              ) : (
                <UploadIcon data-icon="inline-start" />
              )}
              {t.upload}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {documents.length ? (
            <div className="overflow-hidden rounded-xl border bg-background/65">
              <Table>
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
                      <TableCell>
                        <div className="flex min-w-0 items-center gap-3">
                          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                            <FileTextIcon />
                          </div>
                          <div className="flex min-w-0 flex-col gap-1">
                            <span className="truncate font-medium">
                              {document.original_filename}
                            </span>
                            <span className="truncate text-xs text-muted-foreground">
                              {document.document_id}
                            </span>
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
                            <TooltipContent>{t.reindex}</TooltipContent>
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
                            <TooltipContent>{t.delete}</TooltipContent>
                          </Tooltip>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="grid min-h-[24rem] place-items-center rounded-xl border border-dashed bg-background/55">
              <Empty>
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <FileTextIcon />
                  </EmptyMedia>
                  <EmptyTitle>{t.noDocuments}</EmptyTitle>
                  <EmptyDescription>{t.noDocumentsDesc}</EmptyDescription>
                </EmptyHeader>
                <EmptyContent>
                  <Button onClick={() => fileInputRef.current?.click()}>
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
}) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5 px-4 py-5 lg:px-8">
      <PageHeader title={t.settings} description={t.beginnerHint} badge={t.ready} />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <Tabs defaultValue="model" className="min-w-0">
          <TabsList className="mb-3">
            <TabsTrigger value="model">{t.modelSettings}</TabsTrigger>
            <TabsTrigger value="limits">{t.retrievalSettings}</TabsTrigger>
          </TabsList>
          <TabsContent value="model">
            <Card className="rag-panel rag-soft-border">
              <CardHeader>
                <CardTitle>{t.modelSettings}</CardTitle>
                <CardDescription>{t.beginnerHint}</CardDescription>
              </CardHeader>
              <CardContent>
                <FieldGroup className="grid gap-4 md:grid-cols-2">
                  <Field className="md:col-span-2">
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
                  <Field>
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
                  <Field>
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
                  <Field>
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
                  <Field>
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
                  <Field>
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
                  <Field>
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
                <CardDescription>{t.beginnerHint}</CardDescription>
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
                Future sign-in and account settings will live here.
              </div>
            </CardContent>
          </Card>
          <FieldSet className="rounded-2xl border bg-card/85 p-3 shadow-sm">
            <Button onClick={() => void saveConfig()}>
              <CheckIcon data-icon="inline-start" />
              {t.save}
            </Button>
            <Button variant="outline" onClick={() => void resetConfig()}>
              <RefreshCwIcon data-icon="inline-start" />
              {t.reset}
            </Button>
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
}: {
  title: string
  description: string
  badge: string
}) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <h1 className="truncate text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
          {description}
        </p>
      </div>
      <Badge variant="secondary" className="mt-1">
        {badge}
      </Badge>
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
    <div className="rag-soft-border flex items-center gap-3 rounded-2xl border bg-card/70 p-3 shadow-sm">
      <div className="flex size-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
        <Icon />
      </div>
      <div className="min-w-0">
        <div className="truncate text-xs text-muted-foreground">{label}</div>
        <div className="truncate text-sm font-semibold">{value}</div>
      </div>
    </div>
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
    <Field className="rounded-xl border bg-background/70 p-3">
      <div className="flex items-start gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
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

function StatusBadge({ value }: { value: string }) {
  const variant = value === "duplicate" ? "secondary" : "outline"
  return <Badge variant={variant}>{value}</Badge>
}
