import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Home from '@/app/page'

const mockPush = jest.fn()
const mockRouter = { push: mockPush }
const mockFetch = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
}))

describe('Home Page', () => {
  beforeEach(() => {
    mockPush.mockReset()
    mockFetch.mockReset()
    ;(global as any).fetch = mockFetch
  })

  it('renders heading and URL input', () => {
    render(<Home />)

    expect(screen.getByText(/podcast-anything/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/github.com\/user\/repository/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument()
  })

  it('navigates to select page after successful analysis', async () => {
    const user = userEvent.setup()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ repo_id: 'test1234', name: 'test-repo' }),
    })

    render(<Home />)

    await user.type(
      screen.getByPlaceholderText(/github.com\/user\/repository/i),
      'https://github.com/user/repo'
    )
    await user.click(screen.getByRole('button', { name: /analyze/i }))

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/select?repo_id=test1234&name=test-repo')
    })
  })

  it('disables analyze button for non-github URL', async () => {
    const user = userEvent.setup()
    render(<Home />)

    await user.type(
      screen.getByPlaceholderText(/github.com\/user\/repository/i),
      'https://gitlab.com/user/repo'
    )

    expect(screen.getByRole('button', { name: /analyze/i })).toBeDisabled()
  })

  it('shows loading state while analyzing', async () => {
    const user = userEvent.setup()
    let resolveFetch: ((value: unknown) => void) | null = null
    mockFetch.mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve
      })
    )

    render(<Home />)

    await user.type(
      screen.getByPlaceholderText(/github.com\/user\/repository/i),
      'https://github.com/user/repo'
    )
    const button = screen.getByRole('button', { name: /analyze/i })
    await user.click(button)
    expect(button).toBeDisabled()

    resolveFetch?.({
      ok: true,
      json: async () => ({ repo_id: 'test1234', name: 'test-repo' }),
    })
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalled()
    })
  })

  it('shows API errors and does not navigate', async () => {
    const user = userEvent.setup()
    mockFetch.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Server error' }),
    })

    render(<Home />)

    await user.type(
      screen.getByPlaceholderText(/github.com\/user\/repository/i),
      'https://github.com/user/repo'
    )
    await user.click(screen.getByRole('button', { name: /analyze/i }))

    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument()
      expect(mockPush).not.toHaveBeenCalled()
    })
  })
})
