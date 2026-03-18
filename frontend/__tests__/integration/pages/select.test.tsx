import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import SelectPage from '@/app/select/page'
import { repositoryHandlers } from '@/__tests__/mocks/handlers/repository'
import { podcastHandlers } from '@/__tests__/mocks/handlers/podcast'

const server = setupServer(...repositoryHandlers, ...podcastHandlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// Mock Next.js router
const mockPush = jest.fn()
const mockSearchParams = new URLSearchParams({ repo_id: 'test1234' })

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => mockSearchParams,
}))

describe('Select Page', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('renders the file tree', async () => {
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByText(/select files/i)).toBeInTheDocument()
    })
  })

  it('fetches and displays repository structure', async () => {
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByText('sample-project')).toBeInTheDocument()
    })
  })

  it('allows file selection', async () => {
    const user = userEvent.setup()
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByText('README.md')).toBeInTheDocument()
    })

    // Click on a file to select it
    await user.click(screen.getByText('README.md'))

    // File should be selected (checkbox checked)
    const checkbox = screen.getByRole('checkbox', { name: /readme/i })
    expect(checkbox).toBeChecked()
  })

  it('shows generate button', async () => {
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /generate podcast/i })).toBeInTheDocument()
    })
  })

  it('generates podcast and navigates on button click', async () => {
    const user = userEvent.setup()
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /generate podcast/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /generate podcast/i }))

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalled()
    })
  })

  it('handles missing repo_id in URL', async () => {
    // Override search params to be empty
    jest.mock('next/navigation', () => ({
      useRouter: () => ({ push: mockPush }),
      useSearchParams: () => new URLSearchParams(),
    }))

    render(<SelectPage />)

    // Should show error or redirect
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('handles repository not found error', async () => {
    server.use(
      rest.get('/api/v1/repository/:repoId/structure', (req, res, ctx) => {
        return res(ctx.status(404), ctx.json({ detail: 'Repository not found' }))
      })
    )

    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument()
    })
  })
})
