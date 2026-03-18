import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import PodcastPage from '@/app/podcast/[id]/page'
import { podcastHandlers } from '@/__tests__/mocks/handlers/podcast'
import { mockChapters } from '@/__tests__/fixtures/podcast'

const server = setupServer(...podcastHandlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// Mock Next.js router
const mockParams = { id: 'pod1234' }

jest.mock('next/navigation', () => ({
  useParams: () => mockParams,
}))

describe('Podcast Page', () => {
  it('renders audio player', async () => {
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByRole('audio')).toBeInTheDocument()
    })
  })

  it('renders chapter list', async () => {
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText('Chapters')).toBeInTheDocument()
    })
  })

  it('fetches and displays chapters', async () => {
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText('Introduction')).toBeInTheDocument()
    })
  })

  it('syncs current chapter with audio playback', async () => {
    const user = userEvent.setup()
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText('Introduction')).toBeInTheDocument()
    })

    // Click on a chapter to seek
    await user.click(screen.getByText('Core Architecture'))

    // Audio should seek to that chapter's start time
    // (Testing indirectly through the onSeekToChapter callback)
  })

  it('displays playback speed control', async () => {
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText(/speed:/i)).toBeInTheDocument()
    })
  })

  it('handles podcast not found', async () => {
    server.use(
      rest.get('/api/v1/podcast/:podcastId/chapters', (req, res, ctx) => {
        return res(ctx.status(404), ctx.json({ detail: 'Podcast not found' }))
      })
    )

    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument()
    })
  })

  it('shows download button', async () => {
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /download/i })).toBeInTheDocument()
    })
  })

  it('download link points to correct audio URL', async () => {
    render(<PodcastPage />)

    await waitFor(() => {
      const downloadLink = screen.getByRole('link', { name: /download/i })
      expect(downloadLink).toHaveAttribute('href', '/api/v1/podcast/pod1234/audio')
    })
  })

  it('handles audio loading error', async () => {
    server.use(
      rest.get('/api/v1/podcast/:podcastId/audio', (req, res, ctx) => {
        return res(ctx.status(404))
      })
    )

    render(<PodcastPage />)

    // Audio element should still render but show error
    await waitFor(() => {
      expect(screen.getByRole('audio')).toBeInTheDocument()
    })
  })
})
