'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { UrlInput } from '@/components/repo/url-input'

export default function Home() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (url: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/repository/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to analyze repository')
      }

      const data = await response.json()
      router.push(`/select?repo_id=${data.repo_id}&name=${encodeURIComponent(data.name)}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-2xl space-y-8 text-center">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-5xl">
            Podcast-Anything
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Transform any GitHub repository into an educational audio explanation.
            Listen while you commute, exercise, or relax.
          </p>
        </div>

        <div className="space-y-4">
          <UrlInput onSubmit={handleSubmit} isLoading={isLoading} />

          {error && (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
              {error}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <FeatureCard
            icon="🎙️"
            title="AI-Powered Analysis"
            description="Claude analyzes your codebase structure and key components"
          />
          <FeatureCard
            icon="📚"
            title="Educational Content"
            description="Generates tutorial-style explanations you can learn from"
          />
          <FeatureCard
            icon="🎧"
            title="Listen Anywhere"
            description="PWA support for offline listening on mobile devices"
          />
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
      <div className="text-3xl">{icon}</div>
      <h3 className="mt-3 font-semibold text-slate-900 dark:text-white">{title}</h3>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{description}</p>
    </div>
  )
}
