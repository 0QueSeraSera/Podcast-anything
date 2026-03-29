'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams } from 'next/navigation'
import { AudioPlayer } from '@/components/podcast/audio-player'
import { ChapterList } from '@/components/podcast/chapter-list'
import { ChatPanel } from '@/components/podcast/chat-panel'

interface Chapter {
  id: number
  title: string
  start_time: number
  end_time: number
  description?: string
}

interface PodcastData {
  audio_url: string
  chapters: Chapter[]
  title: string
  duration: number
}

interface SaveStatus {
  isSaved: boolean
  isSaving: boolean
  savedPath: string | null
  error: string | null
}

export default function PodcastPage() {
  const params = useParams()
  const podcastId = params.id as string

  const [podcast, setPodcast] = useState<PodcastData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(0)
  const [playbackRate, setPlaybackRate] = useState(1)
  const audioRef = useRef<HTMLAudioElement>(null)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>({
    isSaved: false,
    isSaving: false,
    savedPath: null,
    error: null,
  })

  useEffect(() => {
    const fetchPodcast = async () => {
      try {
        const [chaptersRes] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/${podcastId}/chapters`),
        ])

        if (chaptersRes.ok) {
          const chaptersData = await chaptersRes.json()
          setPodcast({
            audio_url: `${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/${podcastId}/audio`,
            chapters: chaptersData.chapters,
            title: 'Understanding Repository',
            duration: 0,
          })
        }
      } catch (error) {
        console.error('Failed to fetch podcast:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchPodcast()
  }, [podcastId])

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time)
  }

  const handleSeekToChapter = (startTime: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = startTime
      audioRef.current.play()
    }
  }

  const handleSpeedChange = (rate: number) => {
    setPlaybackRate(rate)
    if (audioRef.current) {
      audioRef.current.playbackRate = rate
    }
  }

  const handleSaveToLibrary = async () => {
    setSaveStatus(prev => ({ ...prev, isSaving: true, error: null }))
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/${podcastId}/save`, {
        method: 'POST',
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to save')
      }
      const data = await res.json()
      setSaveStatus({
        isSaved: true,
        isSaving: false,
        savedPath: data.saved_path,
        error: null,
      })
    } catch (err) {
      setSaveStatus(prev => ({
        ...prev,
        isSaving: false,
        error: err instanceof Error ? err.message : 'Failed to save',
      }))
    }
  }

  const handleDownloadAudio = () => {
    const link = document.createElement('a')
    link.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/${podcastId}/audio`
    link.download = `podcast-${podcastId}.mp3`
    link.click()
  }

  const handleDownloadScript = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/podcast/${podcastId}/script`)
      if (!res.ok) throw new Error('Script not available')
      const data = await res.json()
      const blob = new Blob([data.content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `podcast-${podcastId}-script.md`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download script:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    )
  }

  if (!podcast) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">Podcast not found</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            {podcast.title}
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Your AI-generated podcast is ready
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap justify-center gap-3">
          <button
            onClick={handleSaveToLibrary}
            disabled={saveStatus.isSaving || saveStatus.isSaved}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              saveStatus.isSaved
                ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                : 'bg-primary-500 text-white hover:bg-primary-600'
            } disabled:opacity-50`}
          >
            {saveStatus.isSaving ? (
              <>
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Saving...
              </>
            ) : saveStatus.isSaved ? (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Saved to Library
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                Save to Library
              </>
            )}
          </button>

          <button
            onClick={handleDownloadAudio}
            className="flex items-center gap-2 rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download Audio
          </button>

          <button
            onClick={handleDownloadScript}
            className="flex items-center gap-2 rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download Script
          </button>
        </div>

        {saveStatus.error && (
          <div className="rounded-lg bg-red-50 p-3 text-center text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
            {saveStatus.error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <AudioPlayer
              ref={audioRef}
              audioUrl={podcast.audio_url}
              onTimeUpdate={handleTimeUpdate}
              playbackRate={playbackRate}
              onSpeedChange={handleSpeedChange}
            />
          </div>

          <div>
            <ChapterList
              chapters={podcast.chapters}
              currentTime={currentTime}
              onSeekToChapter={handleSeekToChapter}
            />
          </div>
        </div>

        <ChatPanel podcastId={podcastId} />
      </div>
    </div>
  )
}
