import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SpeedControl } from '@/components/podcast/speed-control'

describe('SpeedControl', () => {
  const mockOnSpeedChange = jest.fn()

  beforeEach(() => {
    mockOnSpeedChange.mockClear()
  })

  it('renders speed label', () => {
    render(<SpeedControl currentSpeed={1} onSpeedChange={mockOnSpeedChange} />)

    expect(screen.getByText('Speed:')).toBeInTheDocument()
  })

  it('renders all speed options', () => {
    render(<SpeedControl currentSpeed={1} onSpeedChange={mockOnSpeedChange} />)

    expect(screen.getByText('0.5x')).toBeInTheDocument()
    expect(screen.getByText('0.75x')).toBeInTheDocument()
    expect(screen.getByText('1x')).toBeInTheDocument()
    expect(screen.getByText('1.25x')).toBeInTheDocument()
    expect(screen.getByText('1.5x')).toBeInTheDocument()
    expect(screen.getByText('1.75x')).toBeInTheDocument()
    expect(screen.getByText('2x')).toBeInTheDocument()
  })

  it('highlights current speed', () => {
    render(<SpeedControl currentSpeed={1.5} onSpeedChange={mockOnSpeedChange} />)

    const activeButton = screen.getByText('1.5x')
    expect(activeButton).toHaveClass('bg-white')
  })

  it('calls onSpeedChange when speed is clicked', async () => {
    const user = userEvent.setup()

    render(<SpeedControl currentSpeed={1} onSpeedChange={mockOnSpeedChange} />)

    await user.click(screen.getByText('1.5x'))

    expect(mockOnSpeedChange).toHaveBeenCalledWith(1.5)
  })

  it('calls onSpeedChange with correct values for all speeds', async () => {
    const user = userEvent.setup()

    render(<SpeedControl currentSpeed={1} onSpeedChange={mockOnSpeedChange} />)

    const speeds = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]

    for (const speed of speeds) {
      await user.click(screen.getByText(`${speed}x`))
      expect(mockOnSpeedChange).toHaveBeenCalledWith(speed)
    }

    expect(mockOnSpeedChange).toHaveBeenCalledTimes(speeds.length)
  })

  it('has correct number of speed buttons', () => {
    render(<SpeedControl currentSpeed={1} onSpeedChange={mockOnSpeedChange} />)

    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(7) // 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2
  })

  it('updates highlighted speed when currentSpeed changes', () => {
    const { rerender } = render(
      <SpeedControl currentSpeed={1} onSpeedChange={mockOnSpeedChange} />
    )

    // Initially 1x is highlighted
    expect(screen.getByText('1x')).toHaveClass('bg-white')

    // Rerender with new speed
    rerender(<SpeedControl currentSpeed={2} onSpeedChange={mockOnSpeedChange} />)

    // Now 2x should be highlighted
    expect(screen.getByText('2x')).toHaveClass('bg-white')
    expect(screen.getByText('1x')).not.toHaveClass('bg-white')
  })
})
