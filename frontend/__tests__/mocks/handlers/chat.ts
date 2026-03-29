import { http, HttpResponse } from 'msw'

const API_BASE = '/api/v1'

const chatSessions = new Map<string, { session_id: string; title: string; messages: any[] }>()

export const chatHandlers = [
  http.post(`${API_BASE}/chat/sessions`, async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as {
      title?: string
      podcast_id?: string
    }
    const sessionId = `ses${Date.now().toString(36)}`
    const session = {
      session_id: sessionId,
      title: body.title || 'Podcast chat',
      repo_id: 'repo1234',
      podcast_id: body.podcast_id || null,
      selected_files: [],
      script_path: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    chatSessions.set(sessionId, { session_id: sessionId, title: session.title, messages: [] })
    return HttpResponse.json(session, { status: 201 })
  }),

  http.get(`${API_BASE}/chat/:sessionId/messages`, ({ params }) => {
    const { sessionId } = params
    const state = chatSessions.get(sessionId as string)
    if (!state) {
      return HttpResponse.json(
        {
          detail: { code: 'SESSION_NOT_FOUND', message: 'Chat session not found.' },
        },
        { status: 404 }
      )
    }
    return HttpResponse.json({
      session: {
        session_id: state.session_id,
        title: state.title,
        repo_id: 'repo1234',
        podcast_id: 'pod1234',
        selected_files: [],
        script_path: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      messages: state.messages,
    })
  }),

  http.post(`${API_BASE}/chat/:sessionId/messages`, async ({ params, request }) => {
    const { sessionId } = params
    const state = chatSessions.get(sessionId as string)
    if (!state) {
      return HttpResponse.json(
        {
          detail: { code: 'SESSION_NOT_FOUND', message: 'Chat session not found.' },
        },
        { status: 404 }
      )
    }
    const body = (await request.json()) as { content: string }
    const now = new Date().toISOString()
    const userMessage = {
      message_id: `msg-user-${Date.now().toString(36)}`,
      session_id: sessionId,
      role: 'user',
      content: body.content,
      sources: [],
      created_at: now,
    }
    const assistantMessage = {
      message_id: `msg-assistant-${Date.now().toString(36)}`,
      session_id: sessionId,
      role: 'assistant',
      content: `Mock answer for: ${body.content}`,
      sources: [
        {
          path: 'README.md',
          chunk_id: 'file-0',
          source_type: 'file',
          snippet: 'Mock snippet',
        },
      ],
      created_at: now,
    }
    state.messages.push(userMessage, assistantMessage)
    return HttpResponse.json({
      session_id: sessionId,
      user_message: userMessage,
      assistant_message: assistantMessage,
    })
  }),

  http.get(`${API_BASE}/chat/:sessionId/export`, ({ params, request }) => {
    const { sessionId } = params
    const format = new URL(request.url).searchParams.get('format') || 'markdown'
    const filename = format === 'json' ? `chat-${sessionId}.json` : `chat-${sessionId}.md`
    const body =
      format === 'json'
        ? JSON.stringify({ session_id: sessionId, messages: [] }, null, 2)
        : `# Chat ${sessionId}\n`
    return new HttpResponse(body, {
      headers: {
        'Content-Type': format === 'json' ? 'application/json' : 'text/markdown',
        'Content-Disposition': `attachment; filename="${filename}"`,
      },
    })
  }),
]

export function resetChatStates() {
  chatSessions.clear()
}
