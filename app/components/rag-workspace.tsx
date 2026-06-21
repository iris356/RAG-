"use client"

import * as React from "react"
import {
  BotIcon,
  CheckIcon,
  DatabaseIcon,
  FileTextIcon,
  Loader2Icon,
  MenuIcon,
  MessageSquareIcon,
  PlusIcon,
  RefreshCwIcon,
  SendIcon,
  SettingsIcon,
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
    files: "文件",
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
  },
  en: {
    title: "RAG Knowledge App",
    subtitle: "Local knowledge-base Q&A with Python and LangChain",
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
    files: "Files",
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

  return (
    <SidebarProvider>
      <Sidebar collapsible="none">
        <SidebarHeader className="gap-3 p-3">
          <div className="flex items-center gap-2 px-1">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-xs font-semibold text-primary-foreground">
              RAG
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{t.title}</div>
              <div className="truncate text-xs text-muted-foreground">
                {api.baseUrl}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={view === "documents" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setView("documents")}
            >
              <FileTextIcon data-icon="inline-start" />
              {t.documents}
            </Button>
            <Button variant="outline" size="sm" onClick={() => void createConversation()}>
              <PlusIcon data-icon="inline-start" />
              {t.newChat}
            </Button>
          </div>
        </SidebarHeader>
        <SidebarSeparator />
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>{t.conversations}</SidebarGroupLabel>
            <SidebarGroupContent>
              {isLoading ? (
                <div className="flex flex-col gap-2 px-2">
                  <Skeleton className="h-8" />
                  <Skeleton className="h-8" />
                  <Skeleton className="h-8" />
                </div>
              ) : (
                <SidebarMenu>
                  {conversations.map((session) => (
                    <SidebarMenuItem key={session.session_id}>
                      <SidebarMenuButton
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
              )}
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarSeparator />
        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                isActive={view === "settings"}
                onClick={() => setView("settings")}
              >
                <SettingsIcon />
                <span>{t.settings}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton>
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
      <SidebarInset>
        <header className="flex h-14 items-center gap-3 border-b px-4 md:hidden">
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
                <Button variant="outline" onClick={() => void createConversation()}>
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
            <div className="truncate text-sm font-medium">{t.title}</div>
            <div className="truncate text-xs text-muted-foreground">{t.subtitle}</div>
          </div>
        </header>
        {apiError ? (
          <main className="flex min-h-svh items-center justify-center p-6">
            <Empty>
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
          <main className="min-h-svh bg-background">
            {view === "chat" && (
              <ChatView
                t={t}
                messages={messages}
                question={question}
                setQuestion={setQuestion}
                sendQuestion={sendQuestion}
                isSending={isSending}
                selectedSessionId={selectedSessionId}
              />
            )}
            {view === "documents" && (
              <DocumentsView
                t={t}
                documents={documents}
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

function ChatView({
  t,
  messages,
  question,
  setQuestion,
  sendQuestion,
  isSending,
  selectedSessionId,
}: {
  t: Record<string, string>
  messages: ConversationMessage[]
  question: string
  setQuestion: (value: string) => void
  sendQuestion: () => void
  isSending: boolean
  selectedSessionId: string | null
}) {
  return (
    <div className="mx-auto flex h-svh max-w-4xl flex-col px-4 py-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-medium">{t.title}</h1>
          <p className="truncate text-sm text-muted-foreground">{t.subtitle}</p>
        </div>
        {selectedSessionId && (
          <Badge variant="secondary" className="hidden sm:inline-flex">
            {selectedSessionId.slice(0, 12)}
          </Badge>
        )}
      </div>
      <ScrollArea className="min-h-0 flex-1 pr-2">
        {messages.length ? (
          <div className="flex flex-col gap-4 pb-4">
            {messages.map((message) => (
              <MessageBubble key={message.message_id} message={message} />
            ))}
            {isSending && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2Icon className="animate-spin" />
                Thinking
              </div>
            )}
          </div>
        ) : (
          <div className="flex h-[60svh] items-center justify-center">
            <Empty>
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <BotIcon />
                </EmptyMedia>
                <EmptyTitle>{t.emptyTitle}</EmptyTitle>
                <EmptyDescription>{t.emptyDescription}</EmptyDescription>
              </EmptyHeader>
            </Empty>
          </div>
        )}
      </ScrollArea>
      <div className="border-t pt-3">
        <div className="flex items-end gap-2 rounded-xl border bg-card p-2 shadow-sm">
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
            className="max-h-40 min-h-11 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0"
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
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === "user"
  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          isUser
            ? "max-w-[82%] rounded-xl bg-primary px-3 py-2 text-sm leading-6 text-primary-foreground"
            : "max-w-[82%] rounded-xl border bg-card px-3 py-2 text-sm leading-6 shadow-sm"
        }
      >
        {message.content}
      </div>
    </div>
  )
}

function DocumentsView({
  t,
  documents,
  isUploading,
  fileInputRef,
  uploadFiles,
  deleteDocument,
  reindexDocument,
}: {
  t: Record<string, string>
  documents: DocumentRecord[]
  isUploading: boolean
  fileInputRef: React.RefObject<HTMLInputElement | null>
  uploadFiles: (files: FileList | null) => void
  deleteDocument: (documentId: string) => void
  reindexDocument: (documentId: string) => void
}) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-5 px-4 py-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-medium">{t.documents}</h1>
          <p className="text-sm text-muted-foreground">{t.noDocumentsDesc}</p>
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
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {isUploading ? (
              <Loader2Icon data-icon="inline-start" className="animate-spin" />
            ) : (
              <UploadIcon data-icon="inline-start" />
            )}
            {t.upload}
          </Button>
        </div>
      </div>
      {documents.length ? (
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
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
                    <div className="flex min-w-0 flex-col gap-1">
                      <span className="truncate font-medium">
                        {document.original_filename}
                      </span>
                      <span className="truncate text-xs text-muted-foreground">
                        {document.document_id}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge value={document.status} />
                  </TableCell>
                  <TableCell>{document.parse_status}</TableCell>
                  <TableCell>{document.index_status}</TableCell>
                  <TableCell>{document.chunk_count}</TableCell>
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
        <div className="flex h-[60svh] items-center justify-center rounded-lg border">
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
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-4 py-5">
      <div>
        <h1 className="text-lg font-medium">{t.settings}</h1>
        <p className="text-sm text-muted-foreground">{t.beginnerHint}</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-[1fr_18rem]">
        <Tabs defaultValue="model" className="min-w-0">
          <TabsList>
            <TabsTrigger value="model">{t.modelSettings}</TabsTrigger>
            <TabsTrigger value="limits">{t.retrievalSettings}</TabsTrigger>
          </TabsList>
          <TabsContent value="model">
            <Card>
              <CardHeader>
                <CardTitle>{t.modelSettings}</CardTitle>
                <CardDescription>{t.beginnerHint}</CardDescription>
              </CardHeader>
              <CardContent>
                <FieldGroup>
                  <Field>
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
                  <Separator />
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
                </FieldGroup>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="limits">
            <Card>
              <CardHeader>
                <CardTitle>{t.retrievalSettings}</CardTitle>
                <CardDescription>{t.beginnerHint}</CardDescription>
              </CardHeader>
              <CardContent>
                <FieldGroup>
                  <NumberField
                    id="top-k"
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
          <Card>
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
          <Card>
            <CardHeader>
              <CardTitle>{t.account}</CardTitle>
              <CardDescription>{t.accountHint}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <UserIcon />
                Future sign-in and account settings will live here.
              </div>
            </CardContent>
          </Card>
          <FieldSet>
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

function NumberField({
  id,
  label,
  description,
  value,
  min,
  step = 1,
  onChange,
}: {
  id: string
  label: string
  description: string
  value: number
  min: number
  step?: number
  onChange: (value: number) => void
}) {
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Input
        id={id}
        type="number"
        min={min}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <FieldDescription>{description}</FieldDescription>
    </Field>
  )
}

function StatusBadge({ value }: { value: string }) {
  const variant = value === "duplicate" ? "secondary" : "outline"
  return <Badge variant={variant}>{value}</Badge>
}
