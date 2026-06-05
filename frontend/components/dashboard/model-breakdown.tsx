import { formatNumber } from '@/lib/utils'

interface ModelBreakdownProps {
  requestsByModel: Record<string, number>
  totalRequests: number
}

const MODEL_COLORS: Record<string, string> = {
  'gpt-4o': '#22c55e',
  'gpt-4o-mini': '#3b82f6',
  'gpt-4-turbo': '#8b5cf6',
  'gpt-3.5-turbo': '#06b6d4',
  'claude-3-5-sonnet-20241022': '#f97316',
  'claude-sonnet-4-6': '#f97316',
  'claude-3-haiku-20240307': '#eab308',
  'claude-3-5-haiku-20241022': '#eab308',
}

function getColor(model: string): string {
  return MODEL_COLORS[model] ?? '#6b7280'
}

export function ModelBreakdown({ requestsByModel, totalRequests }: ModelBreakdownProps) {
  const sorted = Object.entries(requestsByModel).sort(([, a], [, b]) => b - a)

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-5">
      <p className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-4">Requests by Model</p>
      {sorted.length === 0 ? (
        <p className="text-gray-600 text-sm">No data yet</p>
      ) : (
        <div className="space-y-3">
          {sorted.map(([model, count]) => {
            const pct = totalRequests > 0 ? (count / totalRequests) * 100 : 0
            return (
              <div key={model}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white text-sm font-mono truncate max-w-[70%]">{model}</span>
                  <span className="text-gray-400 text-sm">
                    {formatNumber(count)} <span className="text-gray-600">({pct.toFixed(0)}%)</span>
                  </span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${pct}%`, backgroundColor: getColor(model) }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
