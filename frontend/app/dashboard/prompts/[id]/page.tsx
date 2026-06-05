import { getServerSession } from 'next-auth'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { authOptions } from '@/lib/auth'
import { getPrompt, getPromptVersions } from '@/lib/api'
import { DeployPanel } from './deploy-panel'

interface Props {
  params: { id: string }
}

export default async function PromptDetailPage({ params }: Props) {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null
  if (!apiKey) notFound()

  let prompt: any = null
  let versions: any[] = []
  try {
    ;[prompt, versions] = await Promise.all([
      getPrompt(apiKey, params.id),
      getPromptVersions(apiKey, params.id),
    ])
  } catch {
    notFound()
  }

  const qualityPct = prompt.avg_quality_score ? (prompt.avg_quality_score * 100).toFixed(1) : null

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center gap-2 text-gray-500 text-sm mb-6">
        <Link href="/dashboard/prompts" className="hover:text-white">Prompts</Link>
        <span>/</span>
        <span className="text-gray-300">{prompt.name}</span>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-white text-2xl font-semibold">{prompt.name}</h1>
          <p className="text-gray-500 text-sm mt-1">v{prompt.version} · {prompt.request_count.toLocaleString()} requests</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
          prompt.quality_trend === 'degrading' ? 'text-red-400 bg-red-900/30 border-red-700/40' :
          prompt.quality_trend === 'improving' ? 'text-brand-400 bg-brand-900/30 border-brand-700/40' :
          'text-gray-400 bg-white/5 border-white/10'
        }`}>
          {prompt.quality_trend}
        </span>
      </div>

      {/* Drift alert */}
      {prompt.quality_trend === 'degrading' && prompt.drift_explanation && (
        <div className="bg-red-900/20 border border-red-700/30 rounded-xl px-5 py-4 mb-6">
          <p className="text-red-400 font-medium text-sm mb-1">⚠ Drift Detected</p>
          <p className="text-red-300 text-sm leading-relaxed">{prompt.drift_explanation}</p>
          {prompt.drift_detected_at && (
            <p className="text-red-600 text-xs mt-1.5">
              Detected {new Date(prompt.drift_detected_at).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {/* Optimization panel */}
      {(prompt.optimization_status === 'suggested' || prompt.optimized_version) && (
        <DeployPanel prompt={prompt} apiKey={apiKey} />
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {qualityPct && (
          <div className="bg-[#111] border border-white/10 rounded-lg p-3">
            <p className="text-gray-500 text-xs">Quality Score</p>
            <p className={`font-semibold text-lg ${parseFloat(qualityPct) >= 80 ? 'text-brand-400' : parseFloat(qualityPct) >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>{qualityPct}%</p>
          </div>
        )}
        {prompt.avg_tokens && (
          <div className="bg-[#111] border border-white/10 rounded-lg p-3">
            <p className="text-gray-500 text-xs">Avg Tokens</p>
            <p className="text-white font-semibold text-lg">{prompt.avg_tokens.toLocaleString()}</p>
          </div>
        )}
        {prompt.avg_cost_usd && (
          <div className="bg-[#111] border border-white/10 rounded-lg p-3">
            <p className="text-gray-500 text-xs">Avg Cost</p>
            <p className="text-white font-semibold text-lg">${prompt.avg_cost_usd.toFixed(4)}</p>
          </div>
        )}
        {prompt.avg_latency_ms && (
          <div className="bg-[#111] border border-white/10 rounded-lg p-3">
            <p className="text-gray-500 text-xs">Avg Latency</p>
            <p className="text-white font-semibold text-lg">{prompt.avg_latency_ms}ms</p>
          </div>
        )}
      </div>

      {/* Current prompt */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-5 mb-4">
        <p className="text-gray-400 text-xs uppercase tracking-wider mb-3">Current Prompt (v{prompt.version})</p>
        <pre className="text-gray-200 text-sm whitespace-pre-wrap font-mono leading-relaxed">{prompt.content}</pre>
      </div>

      {/* Version history */}
      {versions.length > 1 && (
        <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden">
          <p className="text-gray-400 text-xs uppercase tracking-wider px-5 py-3 border-b border-white/10">
            Version History
          </p>
          <div className="divide-y divide-white/5">
            {versions.map((v: any) => (
              <div key={v.id} className="px-5 py-3 flex items-center justify-between">
                <div>
                  <span className="text-white text-sm font-medium">v{v.version}</span>
                  {v.change_note && (
                    <span className="text-gray-500 text-sm ml-3">{v.change_note}</span>
                  )}
                </div>
                <span className="text-gray-600 text-xs">
                  {new Date(v.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
