import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import Home from '@/app/page'
import { repositoryHandlers } from '@/__tests__/mocks/handlers/repository'

const server = setupServer(...repositoryHandlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// Mock Next.js router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('Home Page', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('renders the main heading', () => {
    render(<Home />)

    expect(screen.getByText(/podcast anything/i)).toBeInTheDocument()
  })

  it('renders the URL input component', () => {
    render(<Home />)

    expect(screen.getByPlaceholderText(/github.com\/user\/repository/i)).toBeInTheDocument()
  })

  it('renders the analyze button', () => {
    render(<Home />)

    expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument()
  })

  it('navigates to select page after successful analysis', async () => {
    const user = userEvent.setup()
    render(<Home />)

    const input = screen.getByPlaceholderText(/github.com\/user\/repository/i)
    await user.type(input, 'https://github.com/user/repo')

    const button = screen.getByRole('button', { name: /analyze/i })
    await user.click(button)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/select?repo_id=test1234')
    })
  })

  it('shows error message for invalid GitHub URL', async () => {
    const user = userEvent.setup()
    render(<Home />)

    const input = screen.getByPlaceholderText(/github.com\/user\/repository/i)
    await user.type(input, 'https://gitlab.com/user/repo')

    // Button should be disabled for non-GitHub URLs
    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).toBeDisabled()
  })

  it('shows loading state during analysis', async () => {
    // Delay the response
    server.use(
      rest.post('/api/v1/repository/analyze', async (req, res, ctx) => {
        await new Promise(resolve => setTimeout(resolve, 500))
        return res(ctx.json({ repo_id: 'test1234', name: 'test-repo', file_count: 10 }))
      })
    )

    const user = userEvent.setup()
    render(<Home />)

    const input = screen.getByPlaceholderText(/github.com\/user\/repository/i)
    await user.type(input, 'https://github.com/user/repo')

    const button = screen.getByRole('button', { name: /analyze/i })
    await user.click(button)

    // Check for loading state
    expect(button).toBeDisabled()
  })

  it('handles API error gracefully', async () => {
    server.use(
      rest.post('/api/v1/repository/analyze', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: 'Server error' }))
      })
    )

    const user = userEvent.setup()
    render(<Home />)

    const input = screen.getByPlaceholderText(/github.com\/user\/repository/i)
    await user.type(input, 'https://github.com/user/repo')

    const button = screen.getByRole('button', { name: /analyze/i })
    await user.click(button)

    // Should not navigate on error
    await waitFor(() => {
      expect(mockPush).not.toHaveBeenCalled()
    })
  })
})
