import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import GeneratePage from '@/app/generate/page'

const mockPush = jest.fn()
const mockRouter = { push: mockPush }
let currentSearchParams = new URLSearchParams({ podcast_id: 'pod1234' })

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  useSearchParams: () => currentSearchParams,
}))

const mockFetch = jest.fn()

function mockStatusResponse(status: string, progress: number, error: string | null = null) {
  return {
    ok: true,
    json: async () => ({
      podcast_id: 'pod1234',
      status,
      progress,
      current_step: status.replace('_', ' '),
      error,
    }),
  }
}

describe('Generate Page', () => {
  beforeEach(() => {
    mockPush.mockClear()
    currentSearchParams = new URLSearchParams({ podcast_id: 'pod1234' })
    mockFetch.mockReset()
    ;(global as any).fetch = mockFetch
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders progress indicator', async () => {
    mockFetch.mockResolvedValue(mockStatusResponse('pending', 0))
    render(<GeneratePage />)

    expect(await screen.findByText(/starting|loading/i)).toBeInTheDocument()
  })

  it('redirects to podcast page when completed', async () => {
    mockFetch.mockResolvedValue(mockStatusResponse('completed', 100))
    render(<GeneratePage />)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/podcast/pod1234')
    })
  })

  it('shows failed fallback action', async () => {
    const user = userEvent.setup()
    mockFetch.mockResolvedValue(
      mockStatusResponse('failed', 70, 'Script generation failed')
    )
    render(<GeneratePage />)

    expect(await screen.findByRole('button', { name: /return home/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /return home/i }))
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('stops polling after terminal status', async () => {
    mockFetch
      .mockResolvedValueOnce(mockStatusResponse('pending', 10))
      .mockResolvedValueOnce(mockStatusResponse('completed', 100))
      .mockResolvedValue(mockStatusResponse('completed', 100))

    render(<GeneratePage />)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2)
    }, { timeout: 7000 })

    expect(mockPush).toHaveBeenCalledWith('/podcast/pod1234')

    const terminalCallCount = mockFetch.mock.calls.length

    await new Promise((resolve) => setTimeout(resolve, 2500))
    expect(mockFetch).toHaveBeenCalledTimes(terminalCallCount)
  }, 15000)

  it('handles missing podcast_id', async () => {
    currentSearchParams = new URLSearchParams()
    mockFetch.mockResolvedValue(mockStatusResponse('pending', 0))
    render(<GeneratePage />)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })
})
