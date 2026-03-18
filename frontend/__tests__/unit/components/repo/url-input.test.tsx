import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UrlInput } from '@/components/repo/url-input'

describe('UrlInput', () => {
  const mockOnSubmit = jest.fn()

  beforeEach(() => {
    mockOnSubmit.mockClear()
  })

  it('renders input field with placeholder', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    expect(screen.getByPlaceholderText('https://github.com/user/repository')).toBeInTheDocument()
  })

  it('renders analyze button', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument()
  })

  it('button is disabled when input is empty', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).toBeDisabled()
  })

  it('button is disabled for invalid GitHub URL', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'invalid-url' } })

    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).toBeDisabled()
  })

  it('button is enabled for valid GitHub URL', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'https://github.com/user/repo' } })

    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).not.toBeDisabled()
  })

  it('shows error message for invalid URL', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'invalid-url' } })

    expect(screen.getByText(/please enter a valid github repository url/i)).toBeInTheDocument()
  })

  it('does not show error for valid URL', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'https://github.com/user/repo' } })

    expect(screen.queryByText(/please enter a valid github repository url/i)).not.toBeInTheDocument()
  })

  it('calls onSubmit with URL when form is submitted', async () => {
    const user = userEvent.setup()
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    await user.type(input, 'https://github.com/user/repo')

    const button = screen.getByRole('button', { name: /analyze/i })
    await user.click(button)

    expect(mockOnSubmit).toHaveBeenCalledWith('https://github.com/user/repo')
  })

  it('trims whitespace from URL before submitting', async () => {
    const user = userEvent.setup()
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    await user.type(input, '  https://github.com/user/repo  ')

    const button = screen.getByRole('button', { name: /analyze/i })
    await user.click(button)

    expect(mockOnSubmit).toHaveBeenCalledWith('https://github.com/user/repo')
  })

  it('disables input when loading', () => {
    render(<UrlInput onSubmit={mockOnSubmit} isLoading />)

    const input = screen.getByRole('textbox')
    expect(input).toBeDisabled()
  })

  it('disables button when loading', () => {
    render(<UrlInput onSubmit={mockOnSubmit} isLoading />)

    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).toBeDisabled()
  })

  it('accepts http protocol', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'http://github.com/user/repo' } })

    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).not.toBeDisabled()
  })

  it('accepts URLs with .git extension', () => {
    render(<UrlInput onSubmit={mockOnSubmit} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'https://github.com/user/repo.git' } })

    const button = screen.getByRole('button', { name: /analyze/i })
    expect(button).not.toBeDisabled()
  })
})
