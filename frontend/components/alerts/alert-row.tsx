'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { deleteAlert, toggleAlert } from '@/lib/api'
import { relativeTime } from '@/lib/utils'

const METRIC_LABELS: Record<string, string> = {
  cost_usd: 'Total cost',
  error_rate: 'Error rate',
  latency_p95: 'P95 latency',
  request_count: 'Request count',
  quality_drift: 'Quality drift',
}

export function AlertRow({ alert, apiKey }: { alert: any; apiKey: string }) {
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleToggle = async () => {
    setLoading(true)
    try {
      await toggleAlert(apiKey, alert.id, !alert.enabled)
      router.refresh()
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Delete alert "${alert.name}"?`)) return
    setLoading(true)
    try {
      await deleteAlert(apiKey, alert.id)
      router.refresh()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-between px-5 py-3.5">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-white text-sm font-medium">{alert.name}</span>
          {!alert.enabled && (
            <span className="text-xs text-gray-600 border border-white/10 px-1.5 py-0.5 rounded">Paused</span>
          )}
          {alert.consecutive_breaches > 0 && (
            <span className="text-xs text-red-400 bg-red-900/30 border border-red-700/40 px-1.5 py-0.5 rounded">
              Firing
            </span>
          )}
        </div>
        <p className="text-gray-500 text-xs">
          {METRIC_LABELS[alert.metric] ?? alert.metric} {alert.operator} {alert.threshold} over {alert.window_minutes}m
          {alert.last_triggered_at && (
            <span className="ml-2 text-gray-600">· last fired {relativeTime(alert.last_triggered_at)}</span>
          )}
        </p>
      </div>

      <div className="flex items-center gap-2 ml-4">
        <div className="flex gap-1">
          {alert.notify_slack && <span className="text-xs text-gray-500 bg-white/5 px-1.5 py-0.5 rounded">Slack</span>}
          {alert.notify_email && <span className="text-xs text-gray-500 bg-white/5 px-1.5 py-0.5 rounded">Email</span>}
        </div>
        <button
          onClick={handleToggle}
          disabled={loading}
          className="text-gray-500 hover:text-white text-xs border border-white/10 px-2.5 py-1 rounded-lg transition-colors disabled:opacity-40"
        >
          {alert.enabled ? 'Pause' : 'Enable'}
        </button>
        <button
          onClick={handleDelete}
          disabled={loading}
          className="text-gray-600 hover:text-red-400 text-xs transition-colors disabled:opacity-40"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
