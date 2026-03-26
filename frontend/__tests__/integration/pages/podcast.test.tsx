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

describe('Podcast Page', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    ;(global as any).fetch = mockFetch
  })

  it('renders audio player and chapter list', async () => {
    mockFetch.mockResolvedValue(chaptersResponse(true))
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByLabelText(/podcast audio/i)).toBeInTheDocument()
      expect(screen.getByText('Chapters')).toBeInTheDocument()
      expect(screen.getByText('Introduction')).toBeInTheDocument()
    })
  })

  it('supports selecting a chapter', async () => {
    const user = userEvent.setup()
    mockFetch.mockResolvedValue(chaptersResponse(true))
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText('Core Architecture')).toBeInTheDocument()
    })
    await user.click(screen.getByText('Core Architecture'))

    expect(screen.getByText('Core Architecture')).toBeInTheDocument()
  })

  it('renders playback speed controls and action buttons', async () => {
    mockFetch.mockResolvedValue(chaptersResponse(true))
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText(/speed:/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /download audio/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /download script/i })).toBeInTheDocument()
    })
  })

  it('shows not found when chapter API fails', async () => {
    mockFetch.mockResolvedValue(chaptersResponse(false))
    render(<PodcastPage />)

    await waitFor(() => {
      expect(screen.getByText(/podcast not found/i)).toBeInTheDocument()
    })
  })
})
