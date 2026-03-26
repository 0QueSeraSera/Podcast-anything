import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SelectPage from '@/app/select/page'

const mockPush = jest.fn()
const mockRouter = { push: mockPush }
let currentSearchParams = new URLSearchParams({ repo_id: 'test1234', name: 'sample-project' })
const mockFetch = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  useSearchParams: () => currentSearchParams,
}))

const structurePayload = {
  repo_id: 'test1234',
  root: {
    name: 'sample-project',
    path: '.',
    is_dir: true,
    children: [
      { name: 'README.md', path: 'README.md', is_dir: false, children: null },
      {
        name: 'src',
        path: 'src',
        is_dir: true,
        children: [
          { name: 'main.py', path: 'src/main.py', is_dir: false, children: null },
        ],
      },
    ],
  },
}

describe('Select Page', () => {
  beforeEach(() => {
    currentSearchParams = new URLSearchParams({ repo_id: 'test1234', name: 'sample-project' })
    mockPush.mockReset()
    mockFetch.mockReset()
    ;(global as any).fetch = mockFetch
  })

  function setupSuccessFetches() {
    mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/structure')) {
        return { ok: true, json: async () => structurePayload }
      }
      if (url.endsWith('/api/v1/podcast/create')) {
        return {
          ok: true,
          json: async () => ({ podcast_id: 'pod1234', status: 'pending' }),
        }
      }
      throw new Error(`Unexpected URL: ${url}`)
    })
  }

  it('renders and loads repository structure', async () => {
    setupSuccessFetches()
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByText(/select files for sample-project/i)).toBeInTheDocument()
      expect(screen.getByText('README.md')).toBeInTheDocument()
    })
  })

  it('allows selecting a file', async () => {
    const user = userEvent.setup()
    setupSuccessFetches()
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByText('README.md')).toBeInTheDocument()
    })

    await user.click(screen.getByText('README.md'))
    expect(screen.getByRole('checkbox', { name: /select readme.md/i })).toBeChecked()
  })

  it('creates podcast and navigates to generate page', async () => {
    const user = userEvent.setup()
    setupSuccessFetches()
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /generate podcast/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /generate podcast/i }))
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/generate?podcast_id=pod1234')
    })
  })

  it('redirects home when repo_id is missing', async () => {
    currentSearchParams = new URLSearchParams()
    render(<SelectPage />)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('shows repository load error from API', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Repository not found' }),
    })
    render(<SelectPage />)

    await waitFor(() => {
      expect(screen.getByText(/repository not found/i)).toBeInTheDocument()
    })
  })
})
