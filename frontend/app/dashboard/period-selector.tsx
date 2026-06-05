'use client'

import { useRouter, useSearchParams } from 'next/navigation'

const PERIODS = [
  { label: '1h', hours: 1 },
  { label: '24h', hours: 24 },
  { label: '7d', hours: 168 },
  { label: '30d', hours: 720 },
]

export function PeriodSelector({ current }: { current: number }) {
  const router = useRouter()

  return (
    <div className="flex gap-1 bg-[#1a1a1a] border border-white/10 rounded-lg p-1">
      {PERIODS.map(({ label, hours }) => (
        <button
          key={hours}
          onClick={() => router.push(`/dashboard?period=${hours}`)}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            current === hours
              ? 'bg-white/10 text-white'
              : 'text-gray-500 hover:text-white'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
