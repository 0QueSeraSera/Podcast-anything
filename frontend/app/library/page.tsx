'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Chapter {
  id: number
  title: string
  start_time: number
  end_time: number
  description?: string
}

interface SavedPodcast {
  podcast_id: string
  title: string
  repo_name: string | null
  created_at: string
  saved_at: string
  duration: number | null
  chapters: Chapter[]
}

export default function LibraryPage() {
  const [podcasts, setPodcasts] = useState<SavedPodcast[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSavedPodcasts = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/saved`)
        if (!res.ok) throw new Error('Failed to fetch saved podcasts')
        const data = await res.json()
        setPodcasts(data.podcasts)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load library')
      } finally {
        setIsLoading(false)
      }
    }

    fetchSavedPodcasts()
  }, [])

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '--:--'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
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
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <Link href="/" className="text-sm text-primary-500 hover:underline">
            &larr; Back to Home
          </Link>
          <h1 className="mt-4 text-3xl font-bold text-slate-900 dark:text-white">
            Your Library
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Saved podcasts stored locally at ~/.podcast_anything
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 p-4 text-red-600 dark:bg-red-900/20 dark:text-red-400">
            {error}
          </div>
        )}

        {podcasts.length === 0 ? (
          <div className="rounded-xl bg-white p-12 text-center shadow-sm dark:bg-slate-800">
            <svg
              className="mx-auto h-12 w-12 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <p className="mt-4 text-slate-600 dark:text-slate-400">
              No saved podcasts yet
            </p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600"
            >
              Create a Podcast
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {podcasts.map((podcast) => (
              <div
                key={podcast.podcast_id}
                className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                      {podcast.title}
                    </h2>
                    {podcast.repo_name && (
                      <p className="text-sm text-slate-500">{podcast.repo_name}</p>
                    )}
                    <div className="mt-2 flex items-center gap-4 text-sm text-slate-500">
                      <span>{formatDuration(podcast.duration)}</span>
                      <span>Saved {formatDate(podcast.saved_at)}</span>
                      <span>{podcast.chapters.length} chapters</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <a
                      href={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/saved/${podcast.podcast_id}/audio`}
                      download
                      className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
                    >
                      Audio
                    </a>
                    <a
                      href={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/saved/${podcast.podcast_id}/script`}
                      download
                      className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
                    >
                      Script
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
