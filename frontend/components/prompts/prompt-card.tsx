'use client'

import Link from 'next/link'
import { useState } from 'react'
import { requestOptimization } from '@/lib/api'
import { cn, formatCost, formatLatency } from '@/lib/utils'

interface PromptData {
  id: string
  name: string
  content: string
  version: number
  avg_quality_score: number | null
  avg_tokens: number | null
  avg_cost_usd: number | null
  avg_latency_ms: number | null
  request_count: number
  quality_trend: string
  drift_detected_at: string | null
  drift_explanation: string | null
  optimization_status: string
  optimization_savings: number | null
}

const TREND_STYLES: Record<string, string> = {
  degrading: 'text-red-400 bg-red-900/30 border-red-700/40',
  improving: 'text-brand-400 bg-brand-900/30 border-brand-700/40',
  stable: 'text-gray-400 bg-white/5 border-white/10',
}

const TREND_LABELS: Record<string, string> = {
  degrading: '↘ Degrading',
  improving: '↗ Improving',
  stable: '→ Stable',
}

export function PromptCard({ prompt, apiKey }: { prompt: PromptData; apiKey: string }) {
  const [optimizing, setOptimizing] = useState(false)

  const handleOptimize = async () => {
    setOptimizing(true)
    try {
      await requestOptimization(apiKey, prompt.id)
    } finally {
      setOptimizing(false)
    }
  }

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-5 hover:border-white/20 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <Link
              href={`/dashboard/prompts/${prompt.id}`}
              className="text-white font-medium hover:text-brand-400 transition-colors"
            >
              {prompt.name}
            </Link>
            <span className="text-gray-600 text-xs">v{prompt.version}</span>
            <span className={cn('text-xs px-2 py-0.5 rounded-full border', TREND_STYLES[prompt.quality_trend])}>
              {TREND_LABELS[prompt.quality_trend]}
            </span>
          </div>
          <p className="text-gray-600 text-sm font-mono truncate">{prompt.content.slice(0, 80)}...</p>
        </div>

        <div className="flex items-center gap-2 ml-4 flex-shrink-0">
          {prompt.optimization_status === 'suggested' && (
            <Link
              href={`/dashboard/prompts/${prompt.id}`}
              className="bg-brand-600/20 hover:bg-brand-600/30 border border-brand-600/40 text-brand-400 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
            >
              ✨ Optimization ready
            </Link>
          )}
          {prompt.optimization_status === 'none' && prompt.quality_trend !== 'degrading' && (
            <button
              onClick={handleOptimize}
              disabled={optimizing}
              className="text-gray-500 hover:text-white text-xs border border-white/10 hover:border-white/20 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
            >
              {optimizing ? 'Queued...' : 'Optimize'}
            </button>
          )}
        </div>
      </div>

      {/* Drift alert */}
      {prompt.quality_trend === 'degrading' && prompt.drift_explanation && (
        <div className="bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-2.5 mb-3">
          <p className="text-red-300 text-sm leading-relaxed">{prompt.drift_explanation}</p>
        </div>
      )}

      {/* Stats */}
      <div className="flex flex-wrap gap-5 text-sm">
        {prompt.avg_quality_score !== null && (
          <div>
            <span className="text-gray-500 text-xs">Quality</span>
            <p className={cn('font-medium', prompt.avg_quality_score >= 0.8 ? 'text-brand-400' : prompt.avg_quality_score >= 0.6 ? 'text-yellow-400' : 'text-red-400')}>
              {(prompt.avg_quality_score * 100).toFixed(0)}%
            </p>
          </div>
        )}
        {prompt.avg_tokens && (
          <div>
            <span className="text-gray-500 text-xs">Avg tokens</span>
            <p className="text-white font-medium">{prompt.avg_tokens.toLocaleString()}</p>
          </div>
        )}
        {prompt.avg_cost_usd !== null && (
          <div>
            <span className="text-gray-500 text-xs">Avg cost</span>
            <p className="text-white font-medium">{formatCost(prompt.avg_cost_usd)}</p>
          </div>
        )}
        {prompt.avg_latency_ms && (
          <div>
            <span className="text-gray-500 text-xs">Avg latency</span>
            <p className="text-white font-medium">{formatLatency(prompt.avg_latency_ms)}</p>
          </div>
        )}
        <div>
          <span className="text-gray-500 text-xs">Requests</span>
          <p className="text-white font-medium">{prompt.request_count.toLocaleString()}</p>
        </div>
        {prompt.optimization_savings && (
          <div>
            <span className="text-gray-500 text-xs">Est. savings</span>
            <p className="text-brand-400 font-medium">{prompt.optimization_savings.toFixed(0)}% tokens</p>
          </div>
        )}
      </div>
    </div>
  )
}
