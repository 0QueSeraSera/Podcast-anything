'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { FileTree } from '@/components/repo/file-tree'
import { Button } from '@/components/ui/button'

interface FileNode {
  name: string
  path: string
  is_dir: boolean
  children?: FileNode[]
}

interface ScopeMessage {
  id: string
  role: 'assistant' | 'user'
  content: string
}

export default function SelectPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const repoId = searchParams.get('repo_id')
  const repoName = searchParams.get('name')

  const [fileTree, setFileTree] = useState<FileNode | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [scopeInput, setScopeInput] = useState('')
  const [scopeMessages, setScopeMessages] = useState<ScopeMessage[]>([
    {
      id: 'assistant-welcome',
      role: 'assistant',
      content:
        'Describe what you want to learn and what to skip. Example: "Focus on backend architecture, skip CI/CD details."',
    },
  ])

  useEffect(() => {
    if (!repoId) {
      router.push('/')
      return
    }

    const fetchStructure = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/repository/${repoId}/structure`
        )
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || 'Failed to load repository structure')
        }

        const data = await response.json()
        setFileTree(data.root)
        setLoadError(null)
      } catch (error) {
        console.error('Failed to fetch structure:', error)
        setLoadError(error instanceof Error ? error.message : 'Failed to load repository structure')
      } finally {
        setIsLoading(false)
      }
    }

    fetchStructure()
  }, [repoId, router])

  const handleToggleFile = (path: string) => {
    setSelectedFiles((prev) => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  const handleSendScopeMessage = () => {
    const trimmed = scopeInput.trim()
    if (!trimmed) return

    setScopeMessages((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${prev.length}`,
        role: 'user',
        content: trimmed,
      },
    ])
    setScopeInput('')
  }

  const learningPreferences = scopeMessages
    .filter((message) => message.role === 'user')
    .map((message, index) => `${index + 1}. ${message.content}`)
    .join('\n')

  const handleCreatePodcast = async () => {
    if (!repoId) return

    setIsSubmitting(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_id: repoId,
          selected_files: Array.from(selectedFiles),
          title: `Understanding ${repoName}`,
          learning_preferences: learningPreferences || undefined,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        router.push(`/generate?podcast_id=${data.podcast_id}`)
      }
    } catch (error) {
      console.error('Failed to create podcast:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Select Files for {repoName}
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Step 1: choose files/folders to focus on. Leave empty to include all files.
          </p>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
          {loadError ? (
            <p className="text-red-600 dark:text-red-400">{loadError}</p>
          ) : fileTree ? (
            <FileTree
              node={fileTree}
              selectedFiles={selectedFiles}
              onToggle={handleToggleFile}
            />
          ) : (
            <p className="text-slate-500">No files found</p>
          )}
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            Step 2: Scope Chat (Optional)
          </h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Tell the assistant what you want to learn and what to skip.
          </p>

          <div className="mt-4 h-56 space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/40">
            {scopeMessages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[90%] rounded-lg px-3 py-2 text-sm ${
                  message.role === 'assistant'
                    ? 'bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-100'
                    : 'ml-auto bg-primary-500 text-white'
                }`}
              >
                {message.content}
              </div>
            ))}
          </div>

          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input
              value={scopeInput}
              onChange={(e) => setScopeInput(e.target.value)}
              placeholder="e.g. Focus on API flow, avoid deployment details"
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder-slate-500"
            />
            <Button
              variant="secondary"
              onClick={handleSendScopeMessage}
              disabled={!scopeInput.trim()}
            >
              Send
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">
            {selectedFiles.size} file{selectedFiles.size !== 1 ? 's' : ''} selected
          </p>
          <div className="space-x-4">
            <Button variant="secondary" onClick={() => router.push('/')}>
              Back
            </Button>
            <Button onClick={handleCreatePodcast} isLoading={isSubmitting}>
              Generate Podcast
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
