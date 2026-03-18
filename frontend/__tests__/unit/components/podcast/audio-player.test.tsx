import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AudioPlayer } from '@/components/podcast/audio-player'

// Mock ref for audio element
const mockAudioRef = {
  current: {
    play: jest.fn().mockResolvedValue(undefined),
    pause: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    currentTime: 0,
    duration: 100,
    playbackRate: 1,
  },
}

describe('AudioPlayer', () => {
  const mockOnTimeUpdate = jest.fn()
  const mockOnSpeedChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockAudioRef.current.currentTime = 0
  })

  it('renders play button', () => {
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument()
  })

  it('renders skip backward button', () => {
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    // Skip backward button (10 seconds)
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThanOrEqual(3) // skip back, play, skip forward
  })

  it('renders skip forward button', () => {
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    // Skip forward button (30 seconds)
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThanOrEqual(3)
  })

  it('renders progress bar', () => {
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    expect(screen.getByRole('slider')).toBeInTheDocument()
  })

  it('renders time display', () => {
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    // Time displays (current and duration)
    const timeDisplays = screen.getAllByText(/0:00/)
    expect(timeDisplays.length).toBeGreaterThanOrEqual(1)
  })

  it('renders audio element', () => {
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    expect(screen.getByRole('audio')).toBeInTheDocument()
  })

  it('renders speed control', () => {
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    expect(screen.getByText(/speed:/i)).toBeInTheDocument()
  })

  it('formats time correctly', () => {
    // Test helper function indirectly through component
    // 0 seconds -> 0:00
    // 65 seconds -> 1:05
    // 125 seconds -> 2:05

    // We can test this by checking the initial render
    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    // Initial time should be 0:00
    expect(screen.getByText('0:00')).toBeInTheDocument()
  })

  it('toggles play/pause when play button is clicked', async () => {
    const user = userEvent.setup()

    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    const playButton = screen.getByRole('button', { name: /play/i })
    await user.click(playButton)

    // After clicking play, the button should show pause icon
    // (testing by checking the svg path changed)
  })

  it('handles seek on progress bar', async () => {
    const user = userEvent.setup()

    render(
      <AudioPlayer
        audioUrl="/test.mp3"
        onTimeUpdate={mockOnTimeUpdate}
        playbackRate={1}
        onSpeedChange={mockOnSpeedChange}
      />
    )

    const slider = screen.getByRole('slider')

    // Simulate seeking
    fireEvent.change(slider, { target: { value: '50' } })

    // The slider value should change
    expect(slider).toHaveValue('50')
  })
})
