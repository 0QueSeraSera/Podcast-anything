'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'

interface UrlInputProps {
  onSubmit: (url: string) => void
  isLoading?: boolean
}

export function UrlInput({ onSubmit, isLoading }: UrlInputProps) {
  const [url, setUrl] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      onSubmit(url.trim())
    }
  }

  const isValidGitHubUrl = (value: string) => {
    return /^https?:\/\/github\.com\/[\w-]+\/[\w.-]+/.test(value)
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col gap-4 sm:flex-row">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/user/repository"
          className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder-slate-500"
          disabled={isLoading}
        />
        <Button
          type="submit"
          isLoading={isLoading}
          disabled={!url.trim() || !isValidGitHubUrl(url)}
        >
          Analyze
        </Button>
      </div>
      {url && !isValidGitHubUrl(url) && (
        <p className="mt-2 text-sm text-amber-600 dark:text-amber-400">
          Please enter a valid GitHub repository URL
        </p>
      )}
    </form>
  )
}
