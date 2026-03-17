'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams } from 'next/navigation'
import { AudioPlayer } from '@/components/podcast/audio-player'
import { ChapterList } from '@/components/podcast/chapter-list'

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

export default function PodcastPage() {
  const params = useParams()
  const podcastId = params.id as string

  const [podcast, setPodcast] = useState<PodcastData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(0)
  const [playbackRate, setPlaybackRate] = useState(1)
  const audioRef = useRef<HTMLAudioElement>(null)

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
      </div>
    </div>
  )
}
