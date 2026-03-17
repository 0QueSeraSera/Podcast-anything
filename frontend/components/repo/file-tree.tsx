'use client'

import { useState } from 'react'

interface FileNode {
  name: string
  path: string
  is_dir: boolean
  children?: FileNode[]
}

interface FileTreeProps {
  node: FileNode
  selectedFiles: Set<string>
  onToggle: (path: string) => void
  depth?: number
}

export function FileTree({ node, selectedFiles, onToggle, depth = 0 }: FileTreeProps) {
  const [isExpanded, setIsExpanded] = useState(depth < 2)

  const isDirectory = node.is_dir
  const isSelected = selectedFiles.has(node.path)
  const hasSelectedChildren = isDirectory && node.children?.some((child) =>
    selectedFiles.has(child.path) || (child.is_dir && hasSelectedDescendants(child, selectedFiles))
  )

  function hasSelectedDescendants(n: FileNode, selected: Set<string>): boolean {
    if (selected.has(n.path)) return true
    if (n.children) {
      return n.children.some((child) => hasSelectedDescendants(child, selected))
    }
    return false
  }

  const handleToggle = () => {
    if (!isDirectory) {
      onToggle(node.path)
    } else {
      // Toggle all children
      toggleAllChildren(node, !hasSelectedChildren)
    }
  }

  const toggleAllChildren = (n: FileNode, select: boolean) => {
    if (!n.is_dir) {
      if (select) {
        selectedFiles.add(n.path)
      } else {
        selectedFiles.delete(n.path)
      }
      onToggle(n.path) // Trigger re-render
    } else if (n.children) {
      n.children.forEach((child) => toggleAllChildren(child, select))
    }
  }

  return (
    <div style={{ paddingLeft: depth * 16 }}>
      <div
        className={`flex items-center gap-2 rounded px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 ${
          (isSelected || hasSelectedChildren) ? 'bg-primary-50 dark:bg-primary-900/20' : ''
        }`}
      >
        {isDirectory && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        )}

        <button
          onClick={handleToggle}
          className="flex flex-1 items-center gap-2 text-left"
        >
          <span className={isDirectory ? 'text-amber-500' : 'text-blue-500'}>
            {isDirectory ? '📁' : getFileIcon(node.name)}
          </span>
          <span className="text-slate-700 dark:text-slate-300">{node.name}</span>
        </button>

        <input
          type="checkbox"
          checked={isSelected || hasSelectedChildren}
          onChange={handleToggle}
          className="h-4 w-4 rounded border-slate-300"
        />
      </div>

      {isDirectory && isExpanded && node.children && (
        <div className="mt-1">
          {node.children
            .sort((a, b) => {
              // Directories first, then alphabetically
              if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1
              return a.name.localeCompare(b.name)
            })
            .map((child) => (
              <FileTree
                key={child.path}
                node={child}
                selectedFiles={selectedFiles}
                onToggle={onToggle}
                depth={depth + 1}
              />
            ))}
        </div>
      )}
    </div>
  )
}

function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const icons: Record<string, string> = {
    py: '🐍',
    js: '📜',
    ts: '📘',
    tsx: '⚛️',
    jsx: '⚛️',
    json: '📋',
    md: '📝',
    yaml: '⚙️',
    yml: '⚙️',
    html: '🌐',
    css: '🎨',
    go: '🐹',
    rs: '🦀',
    java: '☕',
    rb: '💎',
    php: '🐘',
  }
  return icons[ext || ''] || '📄'
}
