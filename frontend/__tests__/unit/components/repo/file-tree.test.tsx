import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileTree } from '@/components/repo/file-tree'
import { createFileNode, createDirectoryNode } from '@/__tests__/fixtures/repository'

describe('FileTree', () => {
  const mockOnToggle = jest.fn()

  beforeEach(() => {
    mockOnToggle.mockClear()
  })

  it('renders a file node', () => {
    const node = createFileNode({ name: 'test.py', path: 'test.py' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByText('test.py')).toBeInTheDocument()
  })

  it('renders a directory node with expand button', () => {
    const node = createDirectoryNode('src', [])
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByText('src')).toBeInTheDocument()
    expect(screen.getByText('▶')).toBeInTheDocument() // collapsed indicator
  })

  it('expands directory when clicked', async () => {
    const user = userEvent.setup()
    const childNode = createFileNode({ name: 'utils.py', path: 'src/utils.py' })
    const node = createDirectoryNode('src', [childNode])
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    // Initially collapsed, children not visible
    expect(screen.queryByText('utils.py')).not.toBeInTheDocument()

    // Click expand button
    await user.click(screen.getByText('▶'))

    // Now expanded, children visible
    expect(screen.getByText('utils.py')).toBeInTheDocument()
    expect(screen.getByText('▼')).toBeInTheDocument() // expanded indicator
  })

  it('shows directory icon for directories', () => {
    const node = createDirectoryNode('src', [])
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByText('📁')).toBeInTheDocument()
  })

  it('shows appropriate file icon for Python files', () => {
    const node = createFileNode({ name: 'main.py', path: 'main.py' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByText('🐍')).toBeInTheDocument()
  })

  it('shows appropriate file icon for TypeScript files', () => {
    const node = createFileNode({ name: 'app.ts', path: 'app.ts' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByText('📘')).toBeInTheDocument()
  })

  it('shows appropriate file icon for TSX files', () => {
    const node = createFileNode({ name: 'component.tsx', path: 'component.tsx' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByText('⚛️')).toBeInTheDocument()
  })

  it('shows default file icon for unknown extensions', () => {
    const node = createFileNode({ name: 'unknown.xyz', path: 'unknown.xyz' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByText('📄')).toBeInTheDocument()
  })

  it('calls onToggle when file is clicked', async () => {
    const user = userEvent.setup()
    const node = createFileNode({ name: 'main.py', path: 'main.py' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    await user.click(screen.getByText('main.py'))

    expect(mockOnToggle).toHaveBeenCalledWith('main.py')
  })

  it('shows checkbox for selection', () => {
    const node = createFileNode({ name: 'main.py', path: 'main.py' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('checkbox is checked when file is selected', () => {
    const node = createFileNode({ name: 'main.py', path: 'main.py' })
    const selectedFiles = new Set(['main.py'])

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeChecked()
  })

  it('checkbox is unchecked when file is not selected', () => {
    const node = createFileNode({ name: 'main.py', path: 'main.py' })
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} />)

    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).not.toBeChecked()
  })

  it('directories are expanded by default at shallow depth', () => {
    const childNode = createFileNode({ name: 'utils.py', path: 'src/utils.py' })
    const node = createDirectoryNode('src', [childNode])
    const selectedFiles = new Set<string>()

    // depth=0 should be expanded by default
    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} depth={0} />)

    expect(screen.getByText('utils.py')).toBeInTheDocument()
  })

  it('sorts children with directories first', () => {
    const fileNode = createFileNode({ name: 'zebra.py', path: 'zebra.py' })
    const dirNode = createDirectoryNode('aaa', [])
    const node = createDirectoryNode('root', [fileNode, dirNode])
    const selectedFiles = new Set<string>()

    render(<FileTree node={node} selectedFiles={selectedFiles} onToggle={mockOnToggle} depth={0} />)

    const items = screen.getAllByText(/aaa|zebra/)
    // Directory 'aaa' should come before file 'zebra'
    expect(items[0]).toHaveTextContent('aaa')
    expect(items[1]).toHaveTextContent('zebra')
  })
})
