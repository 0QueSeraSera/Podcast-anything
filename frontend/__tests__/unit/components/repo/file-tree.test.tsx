import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileTree } from '@/components/repo/file-tree'
import { createFileNode, createDirectoryNode } from '@/__tests__/fixtures/repository'

describe('FileTree', () => {
  const mockOnToggleFile = jest.fn()
  const mockOnToggleDirectory = jest.fn()

  const renderTree = (
    node: any,
    selectedFiles = new Set<string>(),
    depth?: number
  ) =>
    render(
      <FileTree
        node={node}
        selectedFiles={selectedFiles}
        onToggleFile={mockOnToggleFile}
        onToggleDirectory={mockOnToggleDirectory}
        depth={depth}
      />
    )

  beforeEach(() => {
    mockOnToggleFile.mockClear()
    mockOnToggleDirectory.mockClear()
  })

  it('renders a file node', () => {
    renderTree(createFileNode({ name: 'test.py', path: 'test.py' }))

    expect(screen.getByText('test.py')).toBeInTheDocument()
  })

  it('renders a directory node with expand button', () => {
    renderTree(createDirectoryNode('src', []), new Set<string>(), 2)

    expect(screen.getByText('src')).toBeInTheDocument()
    expect(screen.getByText('▶')).toBeInTheDocument()
  })

  it('expands directory when clicked', async () => {
    const user = userEvent.setup()
    const childNode = createFileNode({ name: 'utils.py', path: 'src/utils.py' })
    const node = createDirectoryNode('src', [childNode])
    renderTree(node, new Set<string>(), 2)

    expect(screen.queryByText('utils.py')).not.toBeInTheDocument()

    await user.click(screen.getByText('▶'))

    expect(screen.getByText('utils.py')).toBeInTheDocument()
    expect(screen.getByText('▼')).toBeInTheDocument()
  })

  it('shows directory icon for directories', () => {
    renderTree(createDirectoryNode('src', []))

    expect(screen.getByText('📁')).toBeInTheDocument()
  })

  it('shows appropriate file icon for known file types', () => {
    renderTree(createFileNode({ name: 'main.py', path: 'main.py' }))
    expect(screen.getByText('🐍')).toBeInTheDocument()
  })

  it('shows default file icon for unknown extensions', () => {
    renderTree(createFileNode({ name: 'unknown.xyz', path: 'unknown.xyz' }))

    expect(screen.getByText('📄')).toBeInTheDocument()
  })

  it('calls onToggleFile when file is clicked', async () => {
    const user = userEvent.setup()
    renderTree(createFileNode({ name: 'main.py', path: 'main.py' }))

    await user.click(screen.getByText('main.py'))

    expect(mockOnToggleFile).toHaveBeenCalledWith('main.py')
  })

  it('directory toggle selects all descendant files deterministically', async () => {
    const user = userEvent.setup()
    const node = createDirectoryNode('src', [
      createDirectoryNode('models', [
        createFileNode({ name: 'user.py', path: 'src/models/user.py' }),
      ]),
      createFileNode({ name: 'main.py', path: 'src/main.py' }),
    ])
    renderTree(node)

    await user.click(screen.getByRole('checkbox', { name: 'Select src' }))

    expect(mockOnToggleDirectory).toHaveBeenCalledWith(
      ['src/models/user.py', 'src/main.py'],
      true
    )
  })

  it('directory toggle deselects when all descendants are already selected', async () => {
    const user = userEvent.setup()
    const node = createDirectoryNode('src', [
      createFileNode({ name: 'a.py', path: 'src/a.py' }),
      createFileNode({ name: 'b.py', path: 'src/b.py' }),
    ])
    renderTree(node, new Set(['src/a.py', 'src/b.py']))

    await user.click(screen.getByRole('checkbox', { name: 'Select src' }))

    expect(mockOnToggleDirectory).toHaveBeenCalledWith(['src/a.py', 'src/b.py'], false)
  })

  it('uses checked state only when all descendants are selected', () => {
    const node = createDirectoryNode('src', [
      createFileNode({ name: 'a.py', path: 'src/a.py' }),
      createFileNode({ name: 'b.py', path: 'src/b.py' }),
    ])
    renderTree(node, new Set(['src/a.py']))

    expect(screen.getByRole('checkbox', { name: 'Select src' })).not.toBeChecked()
  })

  it('sorts children with directories first', () => {
    const fileNode = createFileNode({ name: 'zebra.py', path: 'zebra.py' })
    const dirNode = createDirectoryNode('aaa', [])
    renderTree(createDirectoryNode('root', [fileNode, dirNode]), new Set<string>(), 0)

    const items = screen.getAllByText(/aaa|zebra/)
    expect(items[0]).toHaveTextContent('aaa')
    expect(items[1]).toHaveTextContent('zebra')
  })
})
