'use client'

interface Chapter {
  id: number
  title: string
  start_time: number
  end_time: number
  description?: string
}

interface ChapterListProps {
  chapters: Chapter[]
  currentTime: number
  onSeekToChapter: (startTime: number) => void
}

export function ChapterList({ chapters, currentTime, onSeekToChapter }: ChapterListProps) {
  const currentChapter = chapters.find(
    (ch) => currentTime >= ch.start_time && currentTime < ch.end_time
  )

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-800">
      <h2 className="mb-4 font-semibold text-slate-900 dark:text-white">Chapters</h2>

      <div className="max-h-96 space-y-2 overflow-y-auto">
        {chapters.map((chapter) => {
          const isActive = currentChapter?.id === chapter.id

          return (
            <button
              key={chapter.id}
              onClick={() => onSeekToChapter(chapter.start_time)}
              className={`w-full rounded-lg p-3 text-left transition-colors ${
                isActive
                  ? 'bg-primary-100 dark:bg-primary-900/30'
                  : 'hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${
                      isActive
                        ? 'bg-primary-500 text-white'
                        : 'bg-slate-200 text-slate-600 dark:bg-slate-600 dark:text-slate-300'
                    }`}
                  >
                    {chapter.id}
                  </span>
                  <span
                    className={`font-medium ${
                      isActive ? 'text-primary-700 dark:text-primary-300' : 'text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    {chapter.title}
                  </span>
                </div>
                <span className="text-sm text-slate-500">{formatTime(chapter.start_time)}</span>
              </div>
              {chapter.description && (
                <p className="mt-1 ml-8 text-sm text-slate-500">{chapter.description}</p>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
