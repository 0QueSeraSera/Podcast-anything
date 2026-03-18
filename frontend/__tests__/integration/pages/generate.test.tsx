import { render, screen, waitFor } from '@testing-library/react'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import GeneratePage from '@/app/generate/page'
import { podcastHandlers } from '@/__tests__/mocks/handlers/podcast'

const server = setupServer(...podcastHandlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// Mock Next.js router
const mockPush = jest.fn()
const mockSearchParams = new URLSearchParams({ podcast_id: 'pod1234' })

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => mockSearchParams,
}))

describe('Generate Page', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('renders progress indicator', () => {
    render(<GeneratePage />)

    expect(screen.getByText(/generating/i)).toBeInTheDocument()
  })

  it('shows current step', async () => {
    render(<GeneratePage />)

    await waitFor(() => {
      expect(screen.getByText(/pending|generating|synthesizing/i)).toBeInTheDocument()
    })
  })

  it('polls for status updates', async () => {
    let callCount = 0
    server.use(
      rest.get('/api/v1/podcast/:podcastId/status', (req, res, ctx) => {
        callCount++
        const statuses = ['pending', 'generating_script', 'synthesizing', 'completed']
        const status = statuses[Math.min(callCount - 1, 3)]

        return res(ctx.json({
          podcast_id: 'pod1234',
          status,
          progress: callCount * 25,
          current_step: status.replace('_', ' ').toUpperCase(),
        }))
      })
    )

    render(<GeneratePage />)

    // Wait for multiple status calls
    await waitFor(() => {
      expect(callCount).toBeGreaterThan(1)
    }, { timeout: 10000 })
  })

  it('redirects to podcast page when completed', async () => {
    server.use(
      rest.get('/api/v1/podcast/:podcastId/status', (req, res, ctx) => {
        return res(ctx.json({
          podcast_id: 'pod1234',
          status: 'completed',
          progress: 100,
          current_step: 'Completed',
        }))
      })
    )

    render(<GeneratePage />)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/podcast/pod1234')
    }, { timeout: 5000 })
  })

  it('shows error state on failure', async () => {
    server.use(
      rest.get('/api/v1/podcast/:podcastId/status', (req, res, ctx) => {
        return res(ctx.json({
          podcast_id: 'pod1234',
          status: 'failed',
          progress: 0,
          error: 'Script generation failed',
        }))
      })
    )

    render(<GeneratePage />)

    await waitFor(() => {
      expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
    })
  })

  it('handles missing podcast_id', async () => {
    jest.mock('next/navigation', () => ({
      useRouter: () => ({ push: mockPush }),
      useSearchParams: () => new URLSearchParams(),
    }))

    render(<GeneratePage />)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('displays progress percentage', async () => {
    server.use(
      rest.get('/api/v1/podcast/:podcastId/status', (req, res, ctx) => {
        return res(ctx.json({
          podcast_id: 'pod1234',
          status: 'synthesizing',
          progress: 60,
          current_step: 'Synthesizing',
        }))
      })
    )

    render(<GeneratePage />)

    await waitFor(() => {
      expect(screen.getByText(/60%/)).toBeInTheDocument()
    })
  })
})
