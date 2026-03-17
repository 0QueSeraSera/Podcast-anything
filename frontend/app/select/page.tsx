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

export default function SelectPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const repoId = searchParams.get('repo_id')
  const repoName = searchParams.get('name')

  const [fileTree, setFileTree] = useState<FileNode | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

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
        if (response.ok) {
          const data = await response.json()
          setFileTree(data.root)
        }
      } catch (error) {
        console.error('Failed to fetch structure:', error)
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
            Choose which files and folders to include in your podcast. Leave empty to include all.
          </p>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
          {fileTree ? (
            <FileTree
              node={fileTree}
              selectedFiles={selectedFiles}
              onToggle={handleToggleFile}
            />
          ) : (
            <p className="text-slate-500">No files found</p>
          )}
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
