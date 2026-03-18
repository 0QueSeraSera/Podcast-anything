import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChapterList } from '@/components/podcast/chapter-list'
import { mockChapters, createChapter } from '@/__tests__/fixtures/podcast'

describe('ChapterList', () => {
  const mockOnSeekToChapter = jest.fn()

  beforeEach(() => {
    mockOnSeekToChapter.mockClear()
  })

  it('renders chapters title', () => {
    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    expect(screen.getByText('Chapters')).toBeInTheDocument()
  })

  it('renders all chapters', () => {
    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    expect(screen.getByText('Introduction')).toBeInTheDocument()
    expect(screen.getByText('Core Architecture')).toBeInTheDocument()
    expect(screen.getByText('Key Features')).toBeInTheDocument()
    expect(screen.getByText('Conclusion')).toBeInTheDocument()
  })

  it('renders chapter IDs', () => {
    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
  })

  it('renders chapter start times', () => {
    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    // Times are formatted as m:ss
    expect(screen.getByText('0:00')).toBeInTheDocument() // Chapter 1
    expect(screen.getByText('1:00')).toBeInTheDocument() // Chapter 2
    expect(screen.getByText('3:00')).toBeInTheDocument() // Chapter 3
    expect(screen.getByText('5:00')).toBeInTheDocument() // Chapter 4
  })

  it('highlights current chapter', () => {
    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={90} // Within Core Architecture (60-180)
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    // Current chapter should have active styling
    const activeChapter = screen.getByText('Core Architecture').closest('button')
    expect(activeChapter).toHaveClass('bg-primary-100')
  })

  it('calls onSeekToChapter when chapter is clicked', async () => {
    const user = userEvent.setup()

    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    await user.click(screen.getByText('Core Architecture'))

    expect(mockOnSeekToChapter).toHaveBeenCalledWith(60) // start_time of chapter 2
  })

  it('renders chapter descriptions', () => {
    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    expect(screen.getByText('Welcome and overview of the project')).toBeInTheDocument()
    expect(screen.getByText('Understanding the main components')).toBeInTheDocument()
  })

  it('handles empty chapters list', () => {
    render(
      <ChapterList
        chapters={[]}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    expect(screen.getByText('Chapters')).toBeInTheDocument()
    // Should not crash with empty list
  })

  it('correctly identifies chapter at boundary times', () => {
    // Test that chapter is highlighted at exact start time
    render(
      <ChapterList
        chapters={mockChapters}
        currentTime={60} // Exact start of Core Architecture
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    const activeChapter = screen.getByText('Core Architecture').closest('button')
    expect(activeChapter).toHaveClass('bg-primary-100')
  })

  it('formats times correctly for long durations', () => {
    const longChapter = createChapter({
      id: 1,
      title: 'Long Chapter',
      start_time: 3661, // 1 hour, 1 minute, 1 second
      end_time: 7200,
    })

    render(
      <ChapterList
        chapters={[longChapter]}
        currentTime={0}
        onSeekToChapter={mockOnSeekToChapter}
      />
    )

    // Time formatting: 3661 seconds = 61:01
    expect(screen.getByText('61:01')).toBeInTheDocument()
  })
})
