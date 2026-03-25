'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

interface PodcastStatus {
  podcast_id: string
  status: string
  progress: number
  current_step: string | null
  error: string | null
}

const statusMessages: Record<string, string> = {
  pending: 'Starting...',
  analyzing: 'Analyzing repository...',
  generating_script: 'Generating educational script...',
  synthesizing: 'Converting to audio...',
  completed: 'Complete!',
  failed: 'Generation failed',
}

export default function GeneratePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const podcastId = searchParams.get('podcast_id')

  const [status, setStatus] = useState<PodcastStatus | null>(null)

  useEffect(() => {
    if (!podcastId) {
      router.push('/')
      return
    }

    let pollInterval: ReturnType<typeof setInterval> | null = null
    let isUnmounted = false

    const stopPolling = () => {
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
    }

    const pollStatus = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/${podcastId}/status`
        )
        if (response.ok) {
          const data = await response.json()
          if (isUnmounted) return
          setStatus(data)

          if (data.status === 'completed') {
            stopPolling()
            router.push(`/podcast/${podcastId}`)
            return
          }
          if (data.status === 'failed') {
            stopPolling()
          }
        }
      } catch (error) {
        console.error('Failed to fetch status:', error)
      }
    }

    pollStatus()
    pollInterval = setInterval(pollStatus, 2000)

    return () => {
      isUnmounted = true
      stopPolling()
    }
  }, [podcastId, router])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-md space-y-8 text-center">
        <div className="space-y-4">
          <div className="mx-auto h-16 w-16 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {status ? statusMessages[status.status] || 'Processing...' : 'Loading...'}
          </h1>
          {status?.current_step && (
            <p className="text-slate-600 dark:text-slate-400">{status.current_step}</p>
          )}
        </div>

        {status && (
          <div className="space-y-2">
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
              <div
                className="h-full bg-primary-500 transition-all duration-500"
                style={{ width: `${status.progress}%` }}
              />
            </div>
            <p className="text-sm text-slate-500">{Math.round(status.progress)}%</p>
          </div>
        )}

        {status?.error && (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
            {status.error}
          </div>
        )}

        {status?.status === 'failed' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Generation ended with an error.
            </p>
            <button
              onClick={() => router.push('/')}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
            >
              Return Home
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
