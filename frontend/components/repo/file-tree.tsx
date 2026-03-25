'use client'

import { useEffect, useMemo, useRef, useState } from 'react'

interface FileNode {
  name: string
  path: string
  is_dir: boolean
  children?: FileNode[]
}

interface FileTreeProps {
  node: FileNode
  selectedFiles: Set<string>
  onToggleFile: (path: string) => void
  onToggleDirectory: (paths: string[], select: boolean) => void
  depth?: number
}

export function FileTree({
  node,
  selectedFiles,
  onToggleFile,
  onToggleDirectory,
  depth = 0,
}: FileTreeProps) {
  const [isExpanded, setIsExpanded] = useState(depth < 2)
  const checkboxRef = useRef<HTMLInputElement>(null)

  const isDirectory = node.is_dir
  const descendantFilePaths = useMemo(
    () => (isDirectory ? getDescendantFilePaths(node) : []),
    [isDirectory, node]
  )
  const selectedDescendantCount = descendantFilePaths.filter((path) => selectedFiles.has(path)).length
  const isPartiallySelected =
    isDirectory &&
    selectedDescendantCount > 0 &&
    selectedDescendantCount < descendantFilePaths.length
  const isFullySelected =
    isDirectory &&
    descendantFilePaths.length > 0 &&
    selectedDescendantCount === descendantFilePaths.length
  const isSelected = isDirectory ? isFullySelected : selectedFiles.has(node.path)

  useEffect(() => {
    if (checkboxRef.current) {
      checkboxRef.current.indeterminate = isPartiallySelected
    }
  }, [isPartiallySelected])

  const handleToggle = () => {
    if (!isDirectory) {
      onToggleFile(node.path)
    } else {
      onToggleDirectory(descendantFilePaths, !isFullySelected)
    }
  }

  return (
    <div style={{ paddingLeft: depth * 16 }}>
      <div
        className={`flex items-center gap-2 rounded px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 ${
          (isSelected || isPartiallySelected) ? 'bg-primary-50 dark:bg-primary-900/20' : ''
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
          ref={checkboxRef}
          type="checkbox"
          aria-label={`Select ${node.path}`}
          checked={isSelected}
          onChange={handleToggle}
          className="h-4 w-4 rounded border-slate-300"
        />
      </div>

      {isDirectory && isExpanded && node.children && (
        <div className="mt-1">
          {[...node.children]
            .sort(sortNodes)
            .map((child) => (
              <FileTree
                key={child.path}
                node={child}
                selectedFiles={selectedFiles}
                onToggleFile={onToggleFile}
                onToggleDirectory={onToggleDirectory}
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

function sortNodes(a: FileNode, b: FileNode): number {
  if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1
  return a.name.localeCompare(b.name)
}

function getDescendantFilePaths(node: FileNode): string[] {
  if (!node.is_dir) return [node.path]
  if (!node.children || node.children.length === 0) return []
  return [...node.children]
    .sort(sortNodes)
    .flatMap((child) => getDescendantFilePaths(child))
}
