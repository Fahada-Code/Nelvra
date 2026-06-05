'use client'

import Link from 'next/link'
import type { RequestSummary } from '@/lib/api'
import { cn, formatCost, formatLatency, relativeTime } from '@/lib/utils'

interface EventsTableProps {
  events: RequestSummary[]
  currentPage: number
  totalPages: number
  onPageChange?: (page: number) => void
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'bg-green-900/40 text-green-400',
  anthropic: 'bg-orange-900/40 text-orange-400',
}

const FINISH_COLORS: Record<string, string> = {
  stop: 'text-brand-500',
  end_turn: 'text-brand-500',
  length: 'text-yellow-400',
  content_filter: 'text-red-400',
  error: 'text-red-400',
}

export function EventsTable({ events, currentPage, totalPages, onPageChange }: EventsTableProps) {
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left text-gray-500 text-xs font-medium py-3 px-4 uppercase tracking-wider">Time</th>
              <th className="text-left text-gray-500 text-xs font-medium py-3 px-4 uppercase tracking-wider">Model</th>
              <th className="text-left text-gray-500 text-xs font-medium py-3 px-4 uppercase tracking-wider">Provider</th>
              <th className="text-right text-gray-500 text-xs font-medium py-3 px-4 uppercase tracking-wider">Tokens</th>
              <th className="text-right text-gray-500 text-xs font-medium py-3 px-4 uppercase tracking-wider">Cost</th>
              <th className="text-right text-gray-500 text-xs font-medium py-3 px-4 uppercase tracking-wider">Latency</th>
              <th className="text-left text-gray-500 text-xs font-medium py-3 px-4 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {events.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-16 text-center text-gray-600">
                  No events yet. Instrument your app to start seeing data here.
                </td>
              </tr>
            ) : (
              events.map((e) => (
                <tr key={e.id} className="hover:bg-white/[0.02] group">
                  <td className="py-3 px-4">
                    <Link href={`/dashboard/events/${e.id}`} className="text-gray-400 text-sm group-hover:text-white transition-colors">
                      {relativeTime(e.timestamp)}
                    </Link>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-white text-sm font-mono">{e.model}</span>
                    {e.feature && (
                      <span className="ml-2 text-xs text-gray-600 bg-white/5 px-1.5 py-0.5 rounded">
                        {e.feature}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className={cn('text-xs px-2 py-0.5 rounded font-medium', PROVIDER_COLORS[e.provider] ?? 'bg-white/5 text-gray-400')}>
                      {e.provider}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-gray-400 text-sm tabular-nums">
                    {e.total_tokens.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-sm tabular-nums">
                    <span className={e.cost_usd && e.cost_usd > 0.01 ? 'text-yellow-400' : 'text-gray-400'}>
                      {formatCost(e.cost_usd)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-sm tabular-nums">
                    <span className={e.latency_ms > 3000 ? 'text-yellow-400' : 'text-gray-400'}>
                      {formatLatency(e.latency_ms)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={cn('text-sm', FINISH_COLORS[e.finish_reason] ?? 'text-gray-400')}>
                      {e.finish_reason}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-white/10">
          <p className="text-gray-500 text-sm">Page {currentPage} of {totalPages}</p>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange?.(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-1.5 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed border border-white/10 rounded-lg transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange?.(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-1.5 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed border border-white/10 rounded-lg transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
