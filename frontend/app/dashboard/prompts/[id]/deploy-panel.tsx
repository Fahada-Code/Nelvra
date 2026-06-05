'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { deployOptimization } from '@/lib/api'

export function DeployPanel({ prompt, apiKey }: { prompt: any; apiKey: string }) {
  const [deploying, setDeploying] = useState(false)
  const [showDiff, setShowDiff] = useState(false)
  const router = useRouter()

  const handleDeploy = async () => {
    if (!confirm('Deploy this optimized version? The current version will be saved in history.')) return
    setDeploying(true)
    try {
      await deployOptimization(apiKey, prompt.id)
      router.refresh()
    } finally {
      setDeploying(false)
    }
  }

  return (
    <div className="bg-brand-900/20 border border-brand-700/30 rounded-xl p-5 mb-6">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-brand-400 font-medium text-sm mb-1">✨ Optimized version ready</p>
          {prompt.optimization_savings && (
            <p className="text-gray-400 text-sm">
              Estimated {prompt.optimization_savings.toFixed(0)}% fewer tokens
              {prompt.avg_cost_usd && (
                <span className="text-brand-400">
                  {' '}(~${(prompt.avg_cost_usd * prompt.request_count * 30 * (prompt.optimization_savings / 100)).toFixed(0)}/mo savings)
                </span>
              )}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="text-gray-400 hover:text-white text-xs border border-white/10 px-3 py-1.5 rounded-lg transition-colors"
          >
            {showDiff ? 'Hide diff' : 'View diff'}
          </button>
          <button
            onClick={handleDeploy}
            disabled={deploying}
            className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-xs font-medium px-4 py-1.5 rounded-lg transition-colors"
          >
            {deploying ? 'Deploying...' : 'Deploy'}
          </button>
        </div>
      </div>

      {showDiff && prompt.optimized_version && (
        <div className="grid grid-cols-2 gap-3 mt-3">
          <div>
            <p className="text-gray-500 text-xs mb-1.5">Current</p>
            <pre className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3 text-red-300 text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
              {prompt.content}
            </pre>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1.5">Optimized</p>
            <pre className="bg-brand-900/20 border border-brand-800/40 rounded-lg px-4 py-3 text-brand-300 text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
              {prompt.optimized_version}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
