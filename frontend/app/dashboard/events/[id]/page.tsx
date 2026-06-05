import { getServerSession } from 'next-auth'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { authOptions } from '@/lib/auth'
import { getEventDetail } from '@/lib/api'
import { formatCost, formatLatency, relativeTime } from '@/lib/utils'

interface Props {
  params: { id: string }
}

export default async function EventDetailPage({ params }: Props) {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null
  if (!apiKey) notFound()

  let event = null
  try {
    event = await getEventDetail(apiKey, params.id)
  } catch {
    notFound()
  }

  return (
    <div className="p-8 max-w-4xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-gray-500 text-sm mb-6">
        <Link href="/dashboard/events" className="hover:text-white transition-colors">Events</Link>
        <span>/</span>
        <span className="text-gray-300 font-mono text-xs">{event.id}</span>
      </div>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-white text-xl font-semibold font-mono">{event.model}</h1>
          <p className="text-gray-500 text-sm mt-1">{new Date(event.timestamp).toLocaleString()}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          ['stop', 'end_turn'].includes(event.finish_reason)
            ? 'bg-brand-900/40 text-brand-500 border border-brand-700/40'
            : 'bg-red-900/40 text-red-400 border border-red-700/40'
        }`}>
          {event.finish_reason}
        </span>
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        {[
          { label: 'Latency', value: formatLatency(event.latency_ms) },
          { label: 'Total Tokens', value: event.total_tokens.toLocaleString() },
          { label: 'Cost', value: formatCost(event.cost_usd) },
          { label: 'Environment', value: event.environment },
        ].map(({ label, value }) => (
          <div key={label} className="bg-[#111] border border-white/10 rounded-lg p-3">
            <p className="text-gray-500 text-xs">{label}</p>
            <p className="text-white font-medium mt-0.5">{value}</p>
          </div>
        ))}
      </div>

      {/* Token breakdown */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-5 mb-4">
        <p className="text-gray-400 text-xs uppercase tracking-wider mb-3">Token Usage</p>
        <div className="flex gap-6">
          <div>
            <p className="text-gray-500 text-xs">Prompt</p>
            <p className="text-white tabular-nums">{event.prompt_tokens.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs">Completion</p>
            <p className="text-white tabular-nums">{event.completion_tokens.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs">Total</p>
            <p className="text-white tabular-nums">{event.total_tokens.toLocaleString()}</p>
          </div>
        </div>
        {/* Visual bar */}
        <div className="mt-3 h-1.5 bg-white/5 rounded-full overflow-hidden flex">
          <div
            className="bg-brand-500/60 h-full"
            style={{ width: `${(event.prompt_tokens / event.total_tokens) * 100}%` }}
          />
          <div
            className="bg-blue-500/60 h-full"
            style={{ width: `${(event.completion_tokens / event.total_tokens) * 100}%` }}
          />
        </div>
        <div className="flex gap-4 mt-1.5">
          <span className="text-xs text-gray-500 flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-brand-500/60 inline-block" /> Prompt</span>
          <span className="text-xs text-gray-500 flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-blue-500/60 inline-block" /> Completion</span>
        </div>
      </div>

      {/* System prompt */}
      {event.system_prompt && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-5 mb-4">
          <p className="text-gray-400 text-xs uppercase tracking-wider mb-3">System Prompt</p>
          <pre className="text-gray-300 text-sm whitespace-pre-wrap font-mono leading-relaxed">
            {event.system_prompt}
          </pre>
        </div>
      )}

      {/* Messages */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-5 mb-4">
        <p className="text-gray-400 text-xs uppercase tracking-wider mb-4">Conversation</p>
        <div className="space-y-4">
          {(event.messages as Array<{ role: string; content: string }>).map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'assistant' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-medium ${
                msg.role === 'user' ? 'bg-blue-600 text-white' :
                msg.role === 'assistant' ? 'bg-brand-600 text-white' :
                'bg-gray-700 text-gray-300'
              }`}>
                {msg.role[0].toUpperCase()}
              </div>
              <div className={`max-w-[85%] rounded-xl px-4 py-2.5 ${
                msg.role === 'user' ? 'bg-blue-900/30 border border-blue-800/40' :
                msg.role === 'assistant' ? 'bg-brand-900/30 border border-brand-800/40' :
                'bg-white/5 border border-white/10'
              }`}>
                <p className="text-xs text-gray-500 mb-1 capitalize">{msg.role}</p>
                <p className="text-gray-200 text-sm whitespace-pre-wrap leading-relaxed">
                  {typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content, null, 2)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Response */}
      <div className="bg-[#111] border border-white/10 rounded-xl p-5 mb-4">
        <p className="text-gray-400 text-xs uppercase tracking-wider mb-3">Response</p>
        <pre className="text-gray-200 text-sm whitespace-pre-wrap font-mono leading-relaxed">
          {event.response_text}
        </pre>
      </div>

      {/* Optional metadata */}
      {Object.keys(event.custom_metadata ?? {}).length > 0 && (
        <div className="bg-[#111] border border-white/10 rounded-xl p-5">
          <p className="text-gray-400 text-xs uppercase tracking-wider mb-3">Custom Metadata</p>
          <pre className="text-gray-400 text-sm font-mono">
            {JSON.stringify(event.custom_metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
