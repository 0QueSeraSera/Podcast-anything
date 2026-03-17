'use client'

interface SpeedControlProps {
  currentSpeed: number
  onSpeedChange: (rate: number) => void
}

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]

export function SpeedControl({ currentSpeed, onSpeedChange }: SpeedControlProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-slate-500">Speed:</span>
      <div className="flex rounded-lg bg-slate-100 p-1 dark:bg-slate-700">
        {SPEEDS.map((speed) => (
          <button
            key={speed}
            onClick={() => onSpeedChange(speed)}
            className={`rounded px-2 py-1 text-sm font-medium transition-colors ${
              currentSpeed === speed
                ? 'bg-white text-primary-600 shadow dark:bg-slate-600 dark:text-primary-300'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
            }`}
          >
            {speed}x
          </button>
        ))}
      </div>
    </div>
  )
}
