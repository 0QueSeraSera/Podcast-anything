'use client'

import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'

interface SourceCitation {
  path: string
  chunk_id: string
  source_type: string
  snippet?: string | null
  score?: number | null
}

interface ChatMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sources: SourceCitation[]
  created_at: string
}

interface ChatSession {
  session_id: string
  title: string
  repo_id: string | null
  podcast_id: string | null
  selected_files: string[]
  script_path: string | null
  created_at: string
  updated_at: string
}

interface ChatHistoryResponse {
  session: ChatSession
  messages: ChatMessage[]
}

interface ChatMessageResponse {
  session_id: string
  user_message: ChatMessage
  assistant_message: ChatMessage
}

interface ChatPanelProps {
  podcastId: string
}

const QUICK_ACTIONS = [
  'Explain the architecture',
  'Find entry points',
  'Summarize selected modules',
]

const SESSION_KEY_PREFIX = 'podcast-anything:chat-session:'

function sessionStorageKey(podcastId: string): string {
  return `${SESSION_KEY_PREFIX}${podcastId}`
}

function parseError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback
  const body = payload as {
    detail?: string | { code?: string; message?: string }
  }
  if (typeof body.detail === 'string') return body.detail
  if (body.detail?.message) return body.detail.message
  return fallback
}

function parseFilename(contentDisposition: string | null, fallback: string): string {
  if (!contentDisposition) return fallback
  const match = contentDisposition.match(/filename="([^"]+)"/)
  return match?.[1] || fallback
}

export function ChatPanel({ podcastId }: ChatPanelProps) {
  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamEnabled, setStreamEnabled] = useState(true)
  const [isExporting, setIsExporting] = useState(false)
  const [lastQuestion, setLastQuestion] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const apiBase = process.env.NEXT_PUBLIC_API_URL
  const supportsStreaming = typeof window !== 'undefined' && typeof window.EventSource !== 'undefined'
  const hasActiveStream = isStreaming && Boolean(eventSourceRef.current)

  const exportDisabled = !session || isExporting || isSending || isStreaming
  const sendDisabled = !session || !input.trim() || isSending || hasActiveStream

  const quickActions = useMemo(() => QUICK_ACTIONS, [])

  useEffect(() => {
    let cancelled = false

    const updateSessionInUrl = (sessionId: string) => {
      const url = new URL(window.location.href)
      url.searchParams.set('chat_session', sessionId)
      window.history.replaceState({}, '', url.toString())
    }

    const persistSessionId = (sessionId: string) => {
      localStorage.setItem(sessionStorageKey(podcastId), sessionId)
      updateSessionInUrl(sessionId)
    }

    const fetchHistory = async (sessionId: string): Promise<ChatHistoryResponse | null> => {
      const response = await fetch(`${apiBase}/api/v1/chat/${sessionId}/messages`)
      if (!response.ok) return null
      return (await response.json()) as ChatHistoryResponse
    }

    const createSession = async (): Promise<ChatSession> => {
      const create = async (payload: Record<string, unknown>) =>
        fetch(`${apiBase}/api/v1/chat/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

      let response = await create({ podcast_id: podcastId })
      if (!response.ok && response.status === 404) {
        // Recovery path for missing podcast state after server restart.
        response = await create({ title: `Podcast ${podcastId} chat` })
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(parseError(payload, 'Failed to create chat session'))
      }
      return (await response.json()) as ChatSession
    }

    const bootstrap = async () => {
      setIsInitializing(true)
      setError(null)
      try {
        const currentUrl = new URL(window.location.href)
        const fromUrl = currentUrl.searchParams.get('chat_session')
        const fromStorage = localStorage.getItem(sessionStorageKey(podcastId))
        const preferredSessionId = fromUrl || fromStorage

        if (preferredSessionId) {
          const history = await fetchHistory(preferredSessionId)
          if (history) {
            if (cancelled) return
            setSession(history.session)
            setMessages(history.messages)
            persistSessionId(history.session.session_id)
            return
          }
        }

        const newSession = await createSession()
        if (cancelled) return
        persistSessionId(newSession.session_id)
        setSession(newSession)
        setMessages([])
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to initialize chat')
      } finally {
        if (!cancelled) {
          setIsInitializing(false)
        }
      }
    }

    bootstrap()

    return () => {
      cancelled = true
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [apiBase, podcastId])

  const sendMessage = async (question: string) => {
    if (!session) return
    const trimmed = question.trim()
    if (!trimmed) return
    setError(null)
    setLastQuestion(trimmed)

    if (streamEnabled && supportsStreaming) {
      const tempUserId = `temp-user-${Date.now()}`
      const tempAssistantId = `temp-assistant-${Date.now()}`
      const optimisticUser: ChatMessage = {
        message_id: tempUserId,
        session_id: session.session_id,
        role: 'user',
        content: trimmed,
        sources: [],
        created_at: new Date().toISOString(),
      }
      const optimisticAssistant: ChatMessage = {
        message_id: tempAssistantId,
        session_id: session.session_id,
        role: 'assistant',
        content: '',
        sources: [],
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, optimisticUser, optimisticAssistant])
      setInput('')
      setIsSending(true)
      setIsStreaming(true)

      const streamUrl = `${apiBase}/api/v1/chat/${session.session_id}/stream?question=${encodeURIComponent(trimmed)}`
      const source = new EventSource(streamUrl)
      eventSourceRef.current = source

      source.addEventListener('chunk', (event) => {
        const payload = JSON.parse((event as MessageEvent).data) as { delta?: string }
        if (!payload.delta) return
        setMessages((prev) =>
          prev.map((message) =>
            message.message_id === tempAssistantId
              ? { ...message, content: `${message.content}${payload.delta}` }
              : message
          )
        )
      })

      source.addEventListener('done', (event) => {
        const payload = JSON.parse((event as MessageEvent).data) as {
          user_message?: ChatMessage
          assistant_message?: ChatMessage
        }
        setMessages((prev) => {
          const withoutOptimistic = prev.filter(
            (message) => message.message_id !== tempUserId && message.message_id !== tempAssistantId
          )
          if (payload.user_message) {
            withoutOptimistic.push(payload.user_message)
          }
          if (payload.assistant_message) {
            withoutOptimistic.push(payload.assistant_message)
          }
          return withoutOptimistic
        })
        source.close()
        eventSourceRef.current = null
        setIsStreaming(false)
        setIsSending(false)
      })

      source.addEventListener('error', () => {
        source.close()
        eventSourceRef.current = null
        setIsStreaming(false)
        setIsSending(false)
        setError('Streaming failed. You can retry the same question.')
      })
      return
    }

    setIsSending(true)
    try {
      const response = await fetch(`${apiBase}/api/v1/chat/${session.session_id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: trimmed }),
      })
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(parseError(payload, 'Failed to send message'))
      }
      const data = (await response.json()) as ChatMessageResponse
      setMessages((prev) => [...prev, data.user_message, data.assistant_message])
      setInput('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setIsSending(false)
    }
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    await sendMessage(input)
  }

  const handleCancelStream = () => {
    if (!eventSourceRef.current) return
    eventSourceRef.current.close()
    eventSourceRef.current = null
    setIsStreaming(false)
    setIsSending(false)
    setError('Streaming canceled.')
  }

  const handleExport = async (format: 'markdown' | 'json') => {
    if (!session) return
    setIsExporting(true)
    setError(null)
    try {
      const response = await fetch(
        `${apiBase}/api/v1/chat/${session.session_id}/export?format=${format}`
      )
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(parseError(payload, 'Failed to export transcript'))
      }
      const content = await response.text()
      const mediaType = format === 'json' ? 'application/json' : 'text/markdown'
      const filename = parseFilename(
        response.headers.get('content-disposition'),
        format === 'json' ? `chat-${session.session_id}.json` : `chat-${session.session_id}.md`
      )
      const blob = new Blob([content], { type: mediaType })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export transcript')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-800 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Ask Follow-up Questions</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Responses are grounded in selected files and generated script context.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => handleExport('markdown')}
            disabled={exportDisabled}
            className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200 disabled:opacity-50 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600"
          >
            Export .md
          </button>
          <button
            type="button"
            onClick={() => handleExport('json')}
            disabled={exportDisabled}
            className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200 disabled:opacity-50 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600"
          >
            Export .json
          </button>
          {supportsStreaming && (
            <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-700 dark:border-slate-600 dark:text-slate-200">
              <input
                type="checkbox"
                checked={streamEnabled}
                onChange={(event) => setStreamEnabled(event.target.checked)}
                className="h-3.5 w-3.5"
              />
              Stream answers
            </label>
          )}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {quickActions.map((action) => (
          <button
            key={action}
            type="button"
            onClick={() => void sendMessage(action)}
            disabled={!session || isSending || hasActiveStream}
            className="rounded-full border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700 hover:bg-primary-100 disabled:opacity-50 dark:border-primary-500/30 dark:bg-primary-500/10 dark:text-primary-300"
          >
            {action}
          </button>
        ))}
      </div>

      <div className="mt-4 max-h-[380px] space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/40">
        {isInitializing && (
          <p className="text-sm text-slate-500 dark:text-slate-400">Initializing chat session...</p>
        )}

        {!isInitializing && messages.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Start with a question about architecture, entry points, or module behavior.
          </p>
        )}

        {messages.map((message) => (
          <div key={message.message_id} className="space-y-1">
            <div
              className={`max-w-[92%] rounded-lg px-3 py-2 text-sm ${
                message.role === 'user'
                  ? 'ml-auto bg-primary-500 text-white'
                  : 'bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-100'
              }`}
            >
              {message.content || (message.role === 'assistant' ? '...' : '')}
            </div>
            {message.role === 'assistant' && message.sources.length > 0 && (
              <div className="space-y-1 pl-1 text-xs text-slate-600 dark:text-slate-400">
                {message.sources.map((source) => (
                  <p key={`${message.message_id}-${source.path}-${source.chunk_id}`}>
                    source: {source.path} [{source.chunk_id}]
                  </p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 mt-3 space-y-2 border-t border-slate-200 bg-white/95 pt-3 backdrop-blur dark:border-slate-700 dark:bg-slate-800/95"
      >
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about architecture, modules, or call flow..."
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white dark:placeholder-slate-500"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={sendDisabled}
              className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 disabled:opacity-50"
            >
              {isSending ? 'Sending...' : 'Send'}
            </button>
            {hasActiveStream && (
              <button
                type="button"
                onClick={handleCancelStream}
                className="rounded-lg bg-slate-200 px-3 py-2 text-sm text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600"
              >
                Cancel
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-300">
            <span>{error}</span>
            {lastQuestion && !isSending && (
              <button
                type="button"
                onClick={() => void sendMessage(lastQuestion)}
                className="rounded-md bg-red-100 px-2 py-1 font-medium text-red-700 hover:bg-red-200 dark:bg-red-900/40 dark:text-red-300 dark:hover:bg-red-900/60"
              >
                Retry
              </button>
            )}
          </div>
        )}
      </form>
    </section>
  )
}
