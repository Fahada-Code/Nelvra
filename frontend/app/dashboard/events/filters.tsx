'use client'

import { useRouter, useSearchParams } from 'next/navigation'

interface Props {
  currentModel?: string
  currentProvider?: string
  currentEnvironment?: string
}

export function EventsFilters({ currentModel, currentProvider, currentEnvironment }: Props) {
  const router = useRouter()
  const params = useSearchParams()

  const update = (key: string, value: string | undefined) => {
    const next = new URLSearchParams(params.toString())
    if (value) {
      next.set(key, value)
    } else {
      next.delete(key)
    }
    next.delete('page')
    router.push(`/dashboard/events?${next}`)
  }

  return (
    <div className="flex flex-wrap gap-2">
      <select
        value={currentProvider ?? ''}
        onChange={(e) => update('provider', e.target.value || undefined)}
        className="bg-[#111] border border-white/10 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-brand-500"
      >
        <option value="">All providers</option>
        <option value="openai">OpenAI</option>
        <option value="anthropic">Anthropic</option>
      </select>

      <select
        value={currentEnvironment ?? ''}
        onChange={(e) => update('environment', e.target.value || undefined)}
        className="bg-[#111] border border-white/10 text-gray-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-brand-500"
      >
        <option value="">All environments</option>
        <option value="production">Production</option>
        <option value="staging">Staging</option>
        <option value="development">Development</option>
      </select>

      {(currentProvider || currentEnvironment || currentModel) && (
        <button
          onClick={() => router.push('/dashboard/events')}
          className="text-gray-500 hover:text-white text-sm border border-white/10 rounded-lg px-3 py-2 transition-colors"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
