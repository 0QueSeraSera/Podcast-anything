import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PodcastPage from '@/app/podcast/[id]/page'

const mockParams = { id: 'pod1234' }
const mockFetch = jest.fn()

jest.mock('next/navigation', () => ({
  useParams: () => mockParams,
}))

function chaptersResponse(ok = true) {
  if (!ok) {
    return {
      ok: false,
      json: async () => ({ detail: 'Podcast not found' }),
    }
  }
  return {
    ok: true,
    json: async () => ({
      podcast_id: 'pod1234',
      chapters: [
        { id: 1, title: 'Introduction', start_time: 0, end_time: 60 },
        { id: 2, title: 'Core Architecture', start_time: 60, end_time: 120 },
      ],
    }),
  }
}

function createResponse() {
  return {
    ok: true,
    json: async () => ({
      session_id: 'ses1234567890',
      title: 'Podcast chat',
      repo_id: 'repo1234',
      podcast_id: 'pod1234',
      selected_files: [],
      script_path: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }),
  }
}

function historyResponse() {
  return {
    ok: true,
    json: async () => ({
      session: {
        session_id: 'ses1234567890',
        title: 'Podcast chat',
        repo_id: 'repo1234',
        podcast_id: 'pod1234',
        selected_files: [],
        script_path: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      messages: [],
    }),
  }
}

function sendMessageResponse() {
  return {
    ok: true,
    json: async () => ({
      session_id: 'ses1234567890',
      user_message: {
        message_id: 'msg-user-1',
        session_id: 'ses1234567890',
        role: 'user',
        content: 'Explain architecture',
        sources: [],
        created_at: new Date().toISOString(),
      },
      assistant_message: {
        message_id: 'msg-assistant-1',
        session_id: 'ses1234567890',
        role: 'assistant',
        content: 'The backend orchestrates analysis, script generation, and synthesis.',
        sources: [
          {
            path: 'README.md',
            chunk_id: 'file-0',
            source_type: 'file',
            snippet: 'Podcast-Anything overview',
            score: 1.1,
          },
        ],
        created_at: new Date().toISOString(),
      },
    }),
  }
}

function setupFetch({ chaptersOk = true }: { chaptersOk?: boolean } = {}) {
  mockFetch.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = input.toString()
    const method = (init?.method || 'GET').toUpperCase()

    if (url.includes('/api/v1/podcast/pod1234/chapters')) {
      return chaptersResponse(chaptersOk)
    }
    if (url.endsWith('/api/v1/chat/sessions') && method === 'POST') {
      return createResponse()
    }
    if (url.includes('/api/v1/chat/ses1234567890/messages') && method === 'GET') {
      return historyResponse()
    }
    if (url.includes('/api/v1/chat/ses1234567890/messages') && method === 'POST') {
      return sendMessageResponse()
    }
    if (url.includes('/api/v1/podcast/pod1234/script')) {
      return {
        ok: true,
        json: async () => ({
          content: '## Introduction\nMock content',
        }),
      }
    }

    return {
      ok: false,
      json: async () => ({ detail: 'Unhandled route' }),
    }
  })
}

describe('Podcast Page', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    ;(global as any).fetch = mockFetch
    window.localStorage.clear()
  })

  it('renders audio player and chapter list', async () => {
    setupFetch()
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByLabelText(/podcast audio/i)).toBeInTheDocument()
      expect(screen.getByText('Chapters')).toBeInTheDocument()
      expect(screen.getByText('Introduction')).toBeInTheDocument()
    })
  })

  it('supports selecting a chapter', async () => {
    const user = userEvent.setup()
    setupFetch()
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText('Core Architecture')).toBeInTheDocument()
    })
    await user.click(screen.getByText('Core Architecture'))

    expect(screen.getByText('Core Architecture')).toBeInTheDocument()
  })

  it('renders playback speed controls and action buttons', async () => {
    setupFetch()
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText(/speed:/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /download audio/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /download script/i })).toBeInTheDocument()
    })
  })

  it('shows not found when chapter API fails', async () => {
    setupFetch({ chaptersOk: false })
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText(/podcast not found/i)).toBeInTheDocument()
    })
  })

  it('loads chat panel and sends a follow-up question', async () => {
    const user = userEvent.setup()
    setupFetch()
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText(/ask follow-up questions/i)).toBeInTheDocument()
    })

    await user.type(screen.getByPlaceholderText(/ask about architecture/i), 'Explain architecture')
    await user.click(screen.getByRole('button', { name: /^send$/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/backend orchestrates analysis, script generation, and synthesis/i)
      ).toBeInTheDocument()
      expect(screen.getByText(/source: README.md/i)).toBeInTheDocument()
    })
  })
})
