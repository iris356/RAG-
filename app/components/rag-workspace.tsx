"use client"

import * as React from "react"
import {
  BellIcon,
  BoxesIcon,
  CheckCircle2Icon,
  ChevronDownIcon,
  CircleHelpIcon,
  DatabaseIcon,
  FileArchiveIcon,
  FileTextIcon,
  GaugeIcon,
  HomeIcon,
  KeyRoundIcon,
  Layers3Icon,
  Loader2Icon,
  MenuIcon,
  MessageSquareTextIcon,
  NetworkIcon,
  PlusIcon,
  RefreshCwIcon,
  SearchIcon,
  SendIcon,
  SettingsIcon,
  SparklesIcon,
  TargetIcon,
  Trash2Icon,
  UploadIcon,
  UserCircleIcon,
  XIcon,
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"

type View = "overview" | "documents" | "chat" | "settings"
type Tone = "success" | "warning" | "danger" | "neutral"

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

const navItems = [
  { key: "overview", label: "知识库总览", icon: HomeIcon },
  { key: "documents", label: "文档管理", icon: FileTextIcon },
  { key: "chat", label: "向量检索", icon: NetworkIcon },
  { key: "chat", label: "对话测试", icon: MessageSquareTextIcon },
  { key: "settings", label: "系统设置", icon: SettingsIcon },
] satisfies Array<{ key: View; label: string; icon: React.ElementType }>

export function RagWorkspace() {
  const [view, setView] = React.useState<View>("overview")
  const [conversations, setConversations] = React.useState<ConversationSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = React.useState<string | null>(null)
  const [messages, setMessages] = React.useState<ConversationMessage[]>([])
  const [documents, setDocuments] = React.useState<DocumentRecord[]>([])
  const [config, setConfig] = React.useState<ModelConfig>(defaultConfig)
  const [question, setQuestion] = React.useState("")
  const [search, setSearch] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(true)
  const [isSending, setIsSending] = React.useState(false)
  const [isUploading, setIsUploading] = React.useState(false)
  const [apiError, setApiError] = React.useState<string | null>(null)
  const [isMobileNavOpen, setIsMobileNavOpen] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement | null>(null)

  const selectedSession = conversations.find(
    (session) => session.session_id === selectedSessionId
  )
  const indexedChunks = documents.reduce(
    (total, document) => total + (document.chunk_count || 0),
    0
  )
  const answeredMessages = messages.filter((item) => item.role === "assistant").length
  const isConfigured = Boolean(config.chat.base_url && config.chat.model)
  const latestAnswer =
    [...messages].reverse().find((item) => item.role === "assistant")?.content ??
    "RAGFlow 支持将本地文档解析、切分并写入向量库。配置模型后，可以在当前会话中结合知识片段与会话记忆生成回答。"

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
      setIsMobileNavOpen(false)
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
      toast.success("会话已删除")
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
    setMessages((current) => [
      ...current,
      {
        message_id: `local-${Date.now()}`,
        session_id: selectedSessionId ?? "pending",
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      },
    ])
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
      toast[failed.length ? "warning" : "success"](
        failed.length ? `${failed.length} 个文件处理失败` : "文档已处理"
      )
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
      toast.success("文档已删除")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function reindexDocument(documentId: string) {
    try {
      await api.reindexDocument(documentId)
      const response = await api.listDocuments()
      setDocuments(response.data.documents)
      toast.success("索引已重建")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function saveConfig() {
    try {
      const response = await api.saveModelConfig(config)
      setConfig(response.data.config)
      toast.success("配置已保存")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function resetConfig() {
    try {
      const response = await api.resetModelConfig()
      setConfig(response.data.config)
      toast.success("已恢复推荐默认值")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  async function applyPreset(preset: "stable" | "cloud-fast" | "low-resource") {
    try {
      const response = await api.applyPreset(preset)
      setConfig(response.data.config)
      toast.success("预设已应用")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error))
    }
  }

  const sidebarProps = {
    activeView: view,
    conversations,
    documents,
    indexedChunks,
    selectedSessionId,
    setActiveView: setView,
    setIsMobileNavOpen,
    setSelectedSessionId,
    createConversation,
  }

  return (
    <div className="min-h-screen bg-[var(--rag-bg)] text-[var(--rag-ink)]">
      <Sidebar {...sidebarProps} variant="desktop" />
      <main className="min-h-screen min-w-0 bg-[var(--rag-bg)] md:pl-[270px]">
        <Topbar
          apiError={apiError}
          isConfigured={isConfigured}
          search={search}
          setSearch={setSearch}
          setIsMobileNavOpen={setIsMobileNavOpen}
          loadWorkspace={loadWorkspace}
        />
        <div className="mx-auto max-w-[1600px] px-4 py-5 lg:px-7">
          {isLoading ? (
            <LoadingState />
          ) : view === "overview" ? (
            <Overview
              apiError={apiError}
              answeredMessages={answeredMessages}
              config={config}
              conversations={conversations}
              documents={documents}
              indexedChunks={indexedChunks}
              isConfigured={isConfigured}
              isSending={isSending}
              latestAnswer={latestAnswer}
              question={question}
              selectedSession={selectedSession}
              setQuestion={setQuestion}
              sendQuestion={sendQuestion}
            />
          ) : view === "documents" ? (
            <DocumentsView
              documents={documents}
              indexedChunks={indexedChunks}
              isUploading={isUploading}
              fileInputRef={fileInputRef}
              uploadFiles={uploadFiles}
              deleteDocument={deleteDocument}
              reindexDocument={reindexDocument}
            />
          ) : view === "chat" ? (
            <ChatView
              conversations={conversations}
              createConversation={createConversation}
              deleteConversation={deleteConversation}
              isSending={isSending}
              messages={messages}
              question={question}
              selectedSessionId={selectedSessionId}
              sendQuestion={sendQuestion}
              setQuestion={setQuestion}
              setSelectedSessionId={setSelectedSessionId}
            />
          ) : (
            <SettingsView
              config={config}
              documents={documents}
              indexedChunks={indexedChunks}
              setConfig={setConfig}
              saveConfig={saveConfig}
              resetConfig={resetConfig}
              applyPreset={applyPreset}
            />
          )}
        </div>
      </main>
      {isMobileNavOpen ? (
        <div className="fixed inset-0 z-50 bg-black/30 md:hidden">
          <Sidebar {...sidebarProps} variant="mobile" />
          <button
            className="absolute right-4 top-4 flex size-9 items-center justify-center rounded-full bg-white text-stone-700 shadow"
            type="button"
            onClick={() => setIsMobileNavOpen(false)}
          >
            <XIcon className="size-4" />
            <span className="sr-only">关闭导航</span>
          </button>
        </div>
      ) : null}
    </div>
  )
}

function Sidebar({
  activeView,
  conversations,
  documents,
  indexedChunks,
  selectedSessionId,
  setActiveView,
  setIsMobileNavOpen,
  setSelectedSessionId,
  createConversation,
  variant = "desktop",
}: {
  activeView: View
  conversations: ConversationSession[]
  documents: DocumentRecord[]
  indexedChunks: number
  selectedSessionId: string | null
  setActiveView: (view: View) => void
  setIsMobileNavOpen: (open: boolean) => void
  setSelectedSessionId: (sessionId: string) => void
  createConversation: () => void
  variant?: "desktop" | "mobile"
}) {
  function openView(nextView: View) {
    setActiveView(nextView)
    setIsMobileNavOpen(false)
  }

  return (
    <aside
      className={cn(
        "w-[270px] border-r border-[var(--rag-line)] bg-[var(--rag-sidebar)]",
        variant === "desktop"
          ? "fixed inset-y-0 left-0 z-40 hidden md:flex md:flex-col"
          : "flex h-full flex-col shadow-2xl"
      )}
    >
      <div className="flex h-[76px] items-center gap-3 border-b border-[var(--rag-line)] px-6">
        <div className="rag-logo-mark">
          <BoxesIcon className="size-5" />
        </div>
        <div>
          <div className="text-2xl font-semibold leading-none tracking-tight">RAGFlow</div>
          <div className="mt-1 text-xs text-[var(--rag-muted)]">企业级知识库平台</div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-5">
        <nav className="space-y-1">
          {navItems.map((item, index) => {
            const Icon = item.icon
            const active =
              item.key === activeView && (activeView !== "chat" || index === 2)
            return (
              <button
                key={`${item.label}-${index}`}
                type="button"
                className={cn("rag-nav-item", active && "is-active")}
                onClick={() => openView(item.key)}
              >
                <Icon className="size-4" />
                <span>{item.label}</span>
                {index > 0 ? <ChevronDownIcon className="ml-auto size-3.5" /> : null}
              </button>
            )
          })}
        </nav>
        <div className="mt-6 rounded-lg border border-orange-200/80 bg-orange-50/80 p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold">知识库状态</span>
            <Badge className="bg-emerald-100 text-emerald-700">正常</Badge>
          </div>
          <UsageBar label="存储空间" value={`${documents.length} 个文档`} percent={42} />
          <UsageBar label="向量数据" value={`${indexedChunks} 块`} percent={58} />
          <UsageBar label="API 调用额度" value="本地运行" percent={36} />
          <Button className="mt-4 h-10 w-full rounded-md bg-[var(--rag-orange)] text-white hover:bg-[var(--rag-orange-dark)]">
            升级套餐
          </Button>
        </div>
      </div>
      <div className="border-t border-[var(--rag-line)] p-4">
        <Button
          className="h-10 w-full rounded-md bg-stone-900 text-white hover:bg-stone-800"
          onClick={() => void createConversation()}
        >
          <PlusIcon data-icon="inline-start" />
          新建对话
        </Button>
        <div className="mt-3 max-h-28 space-y-1 overflow-y-auto">
          {conversations.slice(0, 3).map((session) => (
            <button
              key={session.session_id}
              className={cn(
                "w-full truncate rounded-md px-2 py-1.5 text-left text-xs text-[var(--rag-muted)] hover:bg-orange-50",
                selectedSessionId === session.session_id && "bg-orange-50 text-[var(--rag-orange)]"
              )}
              type="button"
              onClick={() => {
                setSelectedSessionId(session.session_id)
                openView("chat")
              }}
            >
              {session.title}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}

function Topbar({
  apiError,
  isConfigured,
  search,
  setSearch,
  setIsMobileNavOpen,
  loadWorkspace,
}: {
  apiError: string | null
  isConfigured: boolean
  search: string
  setSearch: (value: string) => void
  setIsMobileNavOpen: (open: boolean) => void
  loadWorkspace: () => Promise<void>
}) {
  return (
    <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-[var(--rag-line)] bg-[var(--rag-topbar)] px-4 backdrop-blur md:px-7">
      <div className="flex min-w-0 items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          className="md:hidden"
          onClick={() => setIsMobileNavOpen(true)}
        >
          <MenuIcon />
          <span className="sr-only">打开导航</span>
        </Button>
        <div className="hidden text-sm font-semibold lg:block">
          <span className="text-[var(--rag-orange)]">控制台</span>
          <span className="mx-2 text-[var(--rag-muted)]">/</span>
          总览
        </div>
      </div>
      <div className="mx-3 hidden w-full max-w-[430px] items-center rounded-md border border-[var(--rag-line)] bg-white px-3 shadow-sm sm:flex">
        <SearchIcon className="size-4 text-[var(--rag-muted)]" />
        <Input
          className="h-10 border-0 bg-transparent shadow-none focus-visible:ring-0"
          placeholder="搜索知识库、文档、问题或功能..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <kbd className="rounded bg-stone-100 px-1.5 py-0.5 text-xs text-stone-400">⌘K</kbd>
      </div>
      <div className="flex items-center gap-2">
        <StatusDot tone={apiError ? "danger" : isConfigured ? "success" : "warning"} />
        <IconButton label="刷新" onClick={() => void loadWorkspace()}>
          <RefreshCwIcon />
        </IconButton>
        <IconButton label="通知">
          <BellIcon />
        </IconButton>
        <IconButton label="帮助">
          <CircleHelpIcon />
        </IconButton>
        <IconButton label="设置">
          <SettingsIcon />
        </IconButton>
        <div className="ml-2 hidden items-center gap-2 lg:flex">
          <UserCircleIcon className="size-9 text-stone-700" />
          <span className="text-sm font-semibold">张伟</span>
          <ChevronDownIcon className="size-3.5 text-[var(--rag-muted)]" />
        </div>
      </div>
    </header>
  )
}

function Overview(props: {
  apiError: string | null
  answeredMessages: number
  config: ModelConfig
  conversations: ConversationSession[]
  documents: DocumentRecord[]
  indexedChunks: number
  isConfigured: boolean
  isSending: boolean
  latestAnswer: string
  question: string
  selectedSession: ConversationSession | undefined
  setQuestion: (value: string) => void
  sendQuestion: () => Promise<void>
}) {
  const {
    apiError,
    answeredMessages,
    config,
    conversations,
    documents,
    indexedChunks,
    isConfigured,
    isSending,
    latestAnswer,
    question,
    selectedSession,
    setQuestion,
    sendQuestion,
  } = props
  const averageRecall = documents.length ? Math.min(96, 78 + documents.length * 2) : 0
  const accuracy = indexedChunks ? Math.min(94, 82 + Math.floor(indexedChunks / 25)) : 0

  return (
    <div className="space-y-4">
      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard icon={HomeIcon} label="知识库数量" value="1" delta="+2" tone="orange" />
        <MetricCard icon={FileTextIcon} label="文档总数" value={documents.length} delta={`+${documents.slice(0, 3).length}`} tone="amber" />
        <MetricCard icon={BoxesIcon} label="向量总数" value={indexedChunks.toLocaleString()} delta="+12.5%" tone="orange" />
        <MetricCard icon={TargetIcon} label="平均召回率" value={`${averageRecall}%`} delta="+3.4%" tone="coral" />
        <MetricCard icon={GaugeIcon} label="问答准确率" value={`${accuracy}%`} delta="+2.1%" tone="gold" />
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="rag-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">智能问答测试</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1fr)]">
            <div className="rounded-lg border border-[var(--rag-line)] bg-white p-4">
              <div className="mb-3 text-sm font-semibold">问题输入</div>
              <div className="flex gap-2">
                <Input
                  className="h-11"
                  placeholder="RAGFlow 支持哪些文档格式？如何保证检索效果？"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault()
                      void sendQuestion()
                    }
                  }}
                />
                <Button
                  className="h-11 rounded-md bg-[var(--rag-orange)] px-4 text-white hover:bg-[var(--rag-orange-dark)]"
                  disabled={isSending}
                  onClick={() => void sendQuestion()}
                >
                  {isSending ? <Loader2Icon className="animate-spin" /> : <SendIcon />}
                  发送
                </Button>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--rag-muted)]">
                <span>选择知识库</span>
                <Badge variant="outline" className="h-7 rounded-md px-3">全部知识库</Badge>
                <span>混合检索</span>
              </div>
              <div className="mt-4 text-sm font-semibold">检索到的片段（Top 4）</div>
              <div className="mt-2 space-y-2">
                {(documents.length ? documents.slice(0, 4) : sampleDocuments).map((document, index) => (
                  <SnippetRow key={document.document_id} document={document} index={index} />
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-[var(--rag-line)] bg-white p-4">
              <div className="mb-3 text-sm font-semibold">生成答案</div>
              <p className="max-h-44 overflow-hidden text-sm leading-7 text-stone-700">
                {apiError
                  ? `Python API 暂不可用：${apiError}`
                  : latestAnswer}
              </p>
              <div className="mt-4 text-sm font-semibold">参考来源</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {(documents.length ? documents.slice(0, 4) : sampleDocuments).map((document, index) => (
                  <Badge key={document.document_id} variant="outline" className="h-7 rounded-md border-orange-200 bg-orange-50 text-orange-700">
                    {index + 1} {shortName(document.original_filename)}
                  </Badge>
                ))}
              </div>
              <div className="mt-7 flex items-center justify-between text-xs text-[var(--rag-muted)]">
                <span>当前会话：{selectedSession?.title ?? "新会话"}</span>
                <Button variant="outline" size="sm" onClick={() => setQuestion("请基于知识库总结最近上传文档的核心内容")}>
                  重新生成
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <SidePanel title="最近导入任务" action="全部任务">
            {(documents.length ? documents.slice(0, 5) : sampleDocuments).map((document, index) => (
              <TaskRow key={document.document_id} document={document} index={index} />
            ))}
          </SidePanel>
          <SidePanel title="最近活动" action="查看更多活动">
            {(conversations.length ? conversations.slice(0, 4) : sampleConversations).map((session, index) => (
              <ActivityRow key={session.session_id} session={session} index={index} />
            ))}
          </SidePanel>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_320px_1fr_360px]">
        <ChartPanel title="文档增长趋势">
          <BarChart />
        </ChartPanel>
        <ChartPanel title="文档类型分布">
          <DonutChart total={documents.length || 8942} />
        </ChartPanel>
        <ChartPanel title="请求量趋势">
          <LineAreaChart />
        </ChartPanel>
        <ChartPanel title="检索效果趋势">
          <TrendChart />
        </ChartPanel>
      </section>

      <div className="sr-only">
        模型状态：{isConfigured ? "已配置" : "待配置"}，聊天模型：{config.chat.model}
        ，已回答消息：{answeredMessages}
      </div>
    </div>
  )
}

function DocumentsView({
  documents,
  indexedChunks,
  isUploading,
  fileInputRef,
  uploadFiles,
  deleteDocument,
  reindexDocument,
}: {
  documents: DocumentRecord[]
  indexedChunks: number
  isUploading: boolean
  fileInputRef: React.RefObject<HTMLInputElement | null>
  uploadFiles: (files: FileList | null) => Promise<void>
  deleteDocument: (documentId: string) => Promise<void>
  reindexDocument: (documentId: string) => Promise<void>
}) {
  return (
    <div className="space-y-4">
      <SectionHeader
        title="文档管理"
        description="上传、去重、解析并写入本地 Chroma 向量库。"
        action={
          <>
            <input
              ref={fileInputRef}
              className="hidden"
              type="file"
              multiple
              onChange={(event) => void uploadFiles(event.target.files)}
            />
            <Button
              className="rounded-md bg-[var(--rag-orange)] text-white hover:bg-[var(--rag-orange-dark)]"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
            >
              {isUploading ? <Loader2Icon className="animate-spin" /> : <UploadIcon />}
              选择文件
            </Button>
          </>
        }
      />
      <div className="grid gap-3 md:grid-cols-3">
        <MetricCard icon={FileTextIcon} label="文档总数" value={documents.length} delta="实时" tone="orange" />
        <MetricCard icon={Layers3Icon} label="索引块数" value={indexedChunks.toLocaleString()} delta="Chroma" tone="amber" />
        <MetricCard icon={DatabaseIcon} label="重复资料" value={documents.filter((item) => item.status === "duplicate").length} delta="MD5" tone="gold" />
      </div>
      <Card className="rag-card">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>文件名</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>解析</TableHead>
                <TableHead>索引</TableHead>
                <TableHead>分块</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((document) => (
                <TableRow key={document.document_id}>
                  <TableCell className="max-w-[280px] truncate font-medium">
                    {document.original_filename}
                    <div className="truncate text-xs text-[var(--rag-muted)]">
                      {document.file_type} · {document.document_id}
                    </div>
                  </TableCell>
                  <TableCell><StatusBadge value={document.status} /></TableCell>
                  <TableCell>{document.parse_status}</TableCell>
                  <TableCell>{document.index_status}</TableCell>
                  <TableCell>{document.chunk_count}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="icon-sm" onClick={() => void reindexDocument(document.document_id)}>
                        <RefreshCwIcon />
                        <span className="sr-only">重建索引</span>
                      </Button>
                      <Button variant="destructive" size="icon-sm" onClick={() => void deleteDocument(document.document_id)}>
                        <Trash2Icon />
                        <span className="sr-only">删除文档</span>
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {!documents.length ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center text-[var(--rag-muted)]">
                    还没有文档，点击右上角选择文件开始导入。
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

function ChatView({
  conversations,
  createConversation,
  deleteConversation,
  isSending,
  messages,
  question,
  selectedSessionId,
  sendQuestion,
  setQuestion,
  setSelectedSessionId,
}: {
  conversations: ConversationSession[]
  createConversation: () => Promise<void>
  deleteConversation: (sessionId: string) => Promise<void>
  isSending: boolean
  messages: ConversationMessage[]
  question: string
  selectedSessionId: string | null
  sendQuestion: () => Promise<void>
  setQuestion: (value: string) => void
  setSelectedSessionId: (sessionId: string) => void
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
      <Card className="rag-card">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>会话记录</CardTitle>
          <Button size="icon-sm" onClick={() => void createConversation()}>
            <PlusIcon />
            <span className="sr-only">新建会话</span>
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {conversations.map((session) => (
            <div
              key={session.session_id}
              className={cn(
                "group flex items-center gap-2 rounded-md border p-2 text-sm",
                selectedSessionId === session.session_id
                  ? "border-orange-200 bg-orange-50"
                  : "border-[var(--rag-line)] bg-white"
              )}
            >
              <button className="min-w-0 flex-1 truncate text-left" type="button" onClick={() => setSelectedSessionId(session.session_id)}>
                {session.title}
                <div className="truncate text-xs text-[var(--rag-muted)]">{formatDate(session.updated_at)}</div>
              </button>
              <Button variant="ghost" size="icon-xs" onClick={() => void deleteConversation(session.session_id)}>
                <Trash2Icon />
                <span className="sr-only">删除会话</span>
              </Button>
            </div>
          ))}
          {!conversations.length ? <p className="text-sm text-[var(--rag-muted)]">还没有会话。</p> : null}
        </CardContent>
      </Card>
      <Card className="rag-card min-h-[620px]">
        <CardHeader>
          <CardTitle>对话测试</CardTitle>
        </CardHeader>
        <CardContent className="flex min-h-[520px] flex-col">
          <div className="flex-1 space-y-3 overflow-y-auto rounded-lg border border-[var(--rag-line)] bg-white p-4">
            {messages.map((message) => (
              <div
                key={message.message_id}
                className={cn(
                  "max-w-[82%] rounded-lg px-3 py-2 text-sm leading-6",
                  message.role === "user"
                    ? "ml-auto bg-[var(--rag-orange)] text-white"
                    : "bg-orange-50 text-stone-700"
                )}
              >
                {message.content}
              </div>
            ))}
            {!messages.length ? (
              <div className="flex h-full min-h-72 items-center justify-center text-sm text-[var(--rag-muted)]">
                选择或新建会话后开始提问。
              </div>
            ) : null}
          </div>
          <div className="mt-3 flex gap-2">
            <Textarea
              className="min-h-12 resize-none"
              placeholder="向知识库提问..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  void sendQuestion()
                }
              }}
            />
            <Button
              className="h-12 rounded-md bg-[var(--rag-orange)] px-4 text-white hover:bg-[var(--rag-orange-dark)]"
              disabled={isSending}
              onClick={() => void sendQuestion()}
            >
              {isSending ? <Loader2Icon className="animate-spin" /> : <SendIcon />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function SettingsView({
  config,
  documents,
  indexedChunks,
  setConfig,
  saveConfig,
  resetConfig,
  applyPreset,
}: {
  config: ModelConfig
  documents: DocumentRecord[]
  indexedChunks: number
  setConfig: React.Dispatch<React.SetStateAction<ModelConfig>>
  saveConfig: () => Promise<void>
  resetConfig: () => Promise<void>
  applyPreset: (preset: "stable" | "cloud-fast" | "low-resource") => Promise<void>
}) {
  return (
    <div className="space-y-4">
      <SectionHeader
        title="系统设置"
        description="配置聊天模型、向量模型、检索数量和本地向量限速。"
        action={
          <Button className="rounded-md bg-[var(--rag-orange)] text-white hover:bg-[var(--rag-orange-dark)]" onClick={() => void saveConfig()}>
            <CheckCircle2Icon />
            保存配置
          </Button>
        }
      />
      <div className="grid gap-3 md:grid-cols-3">
        <MetricCard icon={KeyRoundIcon} label="聊天模型" value={config.chat.model || "未配置"} delta="Chat" tone="orange" />
        <MetricCard icon={DatabaseIcon} label="文档总数" value={documents.length} delta="Docs" tone="amber" />
        <MetricCard icon={Layers3Icon} label="索引块数" value={indexedChunks.toLocaleString()} delta="Vector" tone="gold" />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <Card className="rag-card">
          <CardHeader>
            <CardTitle>Provider 与模型</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <Field label="聊天 Base URL">
              <Input value={config.chat.base_url} onChange={(event) => setConfig((current) => ({ ...current, chat: { ...current.chat, base_url: event.target.value } }))} />
            </Field>
            <Field label="聊天 API Key">
              <Input type="password" value={config.chat.api_key} onChange={(event) => setConfig((current) => ({ ...current, chat: { ...current.chat, api_key: event.target.value } }))} />
            </Field>
            <Field label="聊天模型">
              <Input value={config.chat.model} onChange={(event) => setConfig((current) => ({ ...current, chat: { ...current.chat, model: event.target.value } }))} />
            </Field>
            <Field label="向量 Provider">
              <Select
                value={config.embedding.provider}
                onValueChange={(value) => setConfig((current) => ({ ...current, embedding: { ...current.embedding, provider: value as ModelConfig["embedding"]["provider"] } }))}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="openai-compatible">OpenAI-compatible</SelectItem>
                    <SelectItem value="local-api">Local API</SelectItem>
                    <SelectItem value="local-huggingface">Local HuggingFace</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>
            <Field label="向量 Base URL">
              <Input value={config.embedding.base_url} onChange={(event) => setConfig((current) => ({ ...current, embedding: { ...current.embedding, base_url: event.target.value } }))} />
            </Field>
            <Field label="向量 API Key">
              <Input type="password" value={config.embedding.api_key} onChange={(event) => setConfig((current) => ({ ...current, embedding: { ...current.embedding, api_key: event.target.value } }))} />
            </Field>
            <Field label="向量模型">
              <Input value={config.embedding.model} onChange={(event) => setConfig((current) => ({ ...current, embedding: { ...current.embedding, model: event.target.value } }))} />
            </Field>
          </CardContent>
        </Card>
        <Card className="rag-card">
          <CardHeader>
            <CardTitle>检索与限速</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <NumberInput label="Top K" value={config.retrieval.top_k} min={1} onChange={(value) => setConfig((current) => ({ ...current, retrieval: { top_k: value } }))} />
            <NumberInput label="向量批量大小" value={config.embedding.batch_size} min={1} onChange={(value) => setConfig((current) => ({ ...current, embedding: { ...current.embedding, batch_size: value } }))} />
            <NumberInput label="最大并发数" value={config.embedding.max_concurrency} min={1} onChange={(value) => setConfig((current) => ({ ...current, embedding: { ...current.embedding, max_concurrency: value } }))} />
            <NumberInput label="批次间隔秒数" value={config.embedding.batch_interval_seconds} min={0} step={0.1} onChange={(value) => setConfig((current) => ({ ...current, embedding: { ...current.embedding, batch_interval_seconds: value } }))} />
            <div className="grid gap-2 pt-2">
              <Button variant="outline" onClick={() => void resetConfig()}>恢复推荐默认值</Button>
              <Button variant="outline" onClick={() => void applyPreset("stable")}>稳定模式</Button>
              <Button variant="outline" onClick={() => void applyPreset("cloud-fast")}>云端加速模式</Button>
              <Button variant="outline" onClick={() => void applyPreset("low-resource")}>低性能电脑模式</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function SectionHeader({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-[var(--rag-muted)]">{description}</p>
      </div>
      {action}
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, delta, tone }: { icon: React.ElementType; label: string; value: React.ReactNode; delta: string; tone: "orange" | "amber" | "coral" | "gold" }) {
  return (
    <Card className="rag-metric-card">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className={cn("rag-metric-icon", `tone-${tone}`)}>
            <Icon className="size-5" />
          </div>
          <MiniSparkline />
        </div>
        <div className="mt-3 text-sm text-[var(--rag-muted)]">{label}</div>
        <div className="mt-1 flex items-end gap-2">
          <div className="text-2xl font-semibold tracking-tight">{value}</div>
          <div className="pb-1 text-xs font-semibold text-emerald-600">{delta}</div>
        </div>
      </CardContent>
    </Card>
  )
}

function SidePanel({ title, action, children }: { title: string; action: string; children: React.ReactNode }) {
  return (
    <Card className="rag-card">
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <button className="text-xs font-semibold text-[var(--rag-orange)]" type="button">
          {action} ›
        </button>
      </CardHeader>
      <CardContent className="space-y-3">{children}</CardContent>
    </Card>
  )
}

function ChartPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="rag-card min-h-[210px]">
      <CardHeader className="flex-row items-center justify-between pb-1">
        <CardTitle className="text-base">{title}</CardTitle>
        <Badge variant="outline" className="h-7 rounded-md">近7天</Badge>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}

function TaskRow({ document, index }: { document: DocumentRecord; index: number }) {
  const tone: Tone = document.status === "duplicate" ? "warning" : document.status === "failed" ? "danger" : "success"
  return (
    <div className="flex items-center gap-3">
      <div className={cn("rag-file-icon", index % 3 === 0 && "blue", index % 3 === 1 && "red", index % 3 === 2 && "yellow")}>
        {document.file_type === "zip" ? <FileArchiveIcon /> : <FileTextIcon />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{document.original_filename}</div>
        <div className="text-xs text-[var(--rag-muted)]">{document.chunk_count || 0} 条文档</div>
      </div>
      <StatusLabel tone={tone} label={statusText(document.status)} />
    </div>
  )
}

function ActivityRow({ session, index }: { session: ConversationSession; index: number }) {
  const icons = [UserCircleIcon, SparklesIcon, CheckCircle2Icon, SettingsIcon]
  const Icon = icons[index % icons.length]
  return (
    <div className="flex items-center gap-3 border-b border-[var(--rag-line)] pb-2 last:border-0 last:pb-0">
      <div className="flex size-7 items-center justify-center rounded-full bg-orange-100 text-[var(--rag-orange)]">
        <Icon className="size-4" />
      </div>
      <div className="min-w-0 flex-1 truncate text-sm">{session.title}</div>
      <div className="text-xs text-[var(--rag-muted)]">{formatDate(session.updated_at)}</div>
    </div>
  )
}

function SnippetRow({ document, index }: { document: DocumentRecord; index: number }) {
  return (
    <div className="grid grid-cols-[44px_24px_minmax(0,1fr)_42px] items-center gap-2 rounded-md border border-[var(--rag-line)] bg-[var(--rag-warm)] p-2">
      <div className="rounded bg-orange-100 px-2 py-1 text-xs font-semibold text-[var(--rag-orange)]">
        {(0.92 - index * 0.03).toFixed(2)}
      </div>
      <FileTextIcon className="size-4 text-blue-500" />
      <div className="min-w-0 truncate text-xs text-stone-700">
        {document.original_filename}：{document.status === "duplicate" ? "重复资料已识别，未重复入库。" : "已解析并写入知识库索引。"}
      </div>
      <Badge variant="outline" className="h-6 rounded-md text-[10px]">P.{12 - index}</Badge>
    </div>
  )
}

function UsageBar({ label, value, percent }: { label: string; value: string; percent: number }) {
  return (
    <div className="mb-3 last:mb-0">
      <div className="mb-1 flex justify-between text-xs text-stone-600">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-orange-100">
        <div className="h-full rounded-full bg-[var(--rag-orange)]" style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}

function IconButton({ label, children, onClick }: { label: string; children: React.ReactNode; onClick?: () => void }) {
  return (
    <Button variant="ghost" size="icon" className="rounded-full text-stone-700" onClick={onClick}>
      {children}
      <span className="sr-only">{label}</span>
    </Button>
  )
}

function StatusDot({ tone }: { tone: Tone }) {
  return (
    <span className={cn("size-2.5 rounded-full", tone === "success" && "bg-emerald-500", tone === "warning" && "bg-amber-500", tone === "danger" && "bg-red-500", tone === "neutral" && "bg-stone-300")} />
  )
}

function StatusLabel({ tone, label }: { tone: Tone; label: string }) {
  return (
    <span className={cn("rounded px-2 py-1 text-xs font-semibold", tone === "success" && "bg-emerald-100 text-emerald-700", tone === "warning" && "bg-amber-100 text-amber-700", tone === "danger" && "bg-red-100 text-red-700", tone === "neutral" && "bg-stone-100 text-stone-600")}>
      {label}
    </span>
  )
}

function StatusBadge({ value }: { value: string }) {
  const tone: Tone = value === "duplicate" ? "warning" : value === "failed" ? "danger" : "success"
  return <StatusLabel tone={tone} label={statusText(value)} />
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      {label}
      {children}
    </label>
  )
}

function NumberInput({ label, value, min, step = 1, onChange }: { label: string; value: number; min: number; step?: number; onChange: (value: number) => void }) {
  return (
    <Field label={label}>
      <Input type="number" min={min} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </Field>
  )
}

function LoadingState() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <div className="flex items-center gap-3 rounded-lg border border-[var(--rag-line)] bg-white px-4 py-3 text-sm text-[var(--rag-muted)] shadow-sm">
        <Loader2Icon className="size-4 animate-spin text-[var(--rag-orange)]" />
        正在加载知识库工作台...
      </div>
    </div>
  )
}

function MiniSparkline() {
  return (
    <svg className="h-7 w-24 text-[var(--rag-orange)]" viewBox="0 0 96 28" aria-hidden>
      <path d="M2 22 C12 20 14 23 22 18 S34 18 40 14 50 16 58 11 70 15 78 9 88 12 94 7" fill="none" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  )
}

function BarChart() {
  const values = [28, 46, 22, 62, 38, 75, 34, 28, 52, 44, 86, 48, 31, 63, 56, 42, 74, 39, 58, 67]
  return (
    <div className="flex h-32 items-end gap-1.5 border-b border-dashed border-stone-200 px-2">
      {values.map((value, index) => (
        <div key={index} className="flex-1 rounded-t bg-orange-300/85" style={{ height: `${value}%` }} />
      ))}
    </div>
  )
}

function LineAreaChart() {
  return (
    <svg className="h-32 w-full" viewBox="0 0 420 130" aria-hidden>
      <defs>
        <linearGradient id="area" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#ff8a2a" stopOpacity="0.32" />
          <stop offset="100%" stopColor="#ff8a2a" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M0 90 L58 72 L116 82 L174 58 L232 34 L290 42 L348 31 L420 20 L420 128 L0 128 Z" fill="url(#area)" />
      <path d="M0 90 L58 72 L116 82 L174 58 L232 34 L290 42 L348 31 L420 20" fill="none" stroke="#ff7420" strokeWidth="3" />
    </svg>
  )
}

function TrendChart() {
  return (
    <svg className="h-32 w-full" viewBox="0 0 360 130" aria-hidden>
      {[25, 50, 75, 100].map((line) => (
        <line key={line} x1="0" x2="360" y1={line} y2={line} stroke="#eadfd4" strokeDasharray="4 4" />
      ))}
      <path d="M0 72 L52 58 L104 57 L156 70 L208 50 L260 56 L312 48 L360 40" fill="none" stroke="#ff6b1a" strokeWidth="3" />
      <path d="M0 86 L52 70 L104 73 L156 78 L208 64 L260 68 L312 66 L360 62" fill="none" stroke="#f6a20a" strokeWidth="3" />
    </svg>
  )
}

function DonutChart({ total }: { total: number }) {
  return (
    <div className="flex items-center justify-center gap-4">
      <div className="rag-donut">
        <div>
          <span>总计</span>
          <strong>{total.toLocaleString()}</strong>
        </div>
      </div>
      <div className="space-y-2 text-xs text-stone-600">
        {["PDF 41.2%", "DOCX 24.7%", "TXT 12.1%", "MD 8.6%"].map((item) => (
          <div key={item} className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-[var(--rag-orange)]" />
            {item}
          </div>
        ))}
      </div>
    </div>
  )
}

function statusText(value: string) {
  if (value === "duplicate") return "重复"
  if (value === "failed") return "已失败"
  if (value === "processing") return "处理中"
  return "已完成"
}

function shortName(value: string) {
  return value.length > 18 ? `${value.slice(0, 15)}...` : value
}

function formatDate(value: string) {
  if (!value) return "--"
  return value.slice(5, 16).replace("T", " ")
}

const sampleDocuments: DocumentRecord[] = [
  makeSampleDocument("sample-1", "产品手册_2024Q1.pdf", "pdf", 2341),
  makeSampleDocument("sample-2", "公司财报_2023.pdf", "pdf", 1598),
  makeSampleDocument("sample-3", "技术方案汇总（内部）.docx", "docx", 856),
  makeSampleDocument("sample-4", "市场调研报告合集.zip", "zip", 3204),
]

const sampleConversations: ConversationSession[] = [
  { session_id: "sample-c1", title: "系统完成了向量化任务", created_at: "", updated_at: "2026-06-27T10:24:00" },
  { session_id: "sample-c2", title: "李明导入了文档", created_at: "", updated_at: "2026-06-27T09:18:00" },
  { session_id: "sample-c3", title: "张伟更新了系统设置", created_at: "", updated_at: "2026-06-26T15:30:00" },
]

function makeSampleDocument(
  id: string,
  filename: string,
  type: string,
  chunks: number
): DocumentRecord {
  return {
    document_id: id,
    original_filename: filename,
    stored_filename: filename,
    file_path: "",
    file_type: type,
    file_size: 0,
    file_md5: id,
    text_md5: id,
    duplicate_of_document_id: null,
    status: "processed",
    parse_status: "parsed",
    index_status: "indexed",
    chunk_count: chunks,
    created_at: "",
    updated_at: "2026-06-27T10:24:00",
  }
}
