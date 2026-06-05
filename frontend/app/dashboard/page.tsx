import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getOverview } from '@/lib/api'
import { StatsCard } from '@/components/dashboard/stats-card'
import { OverviewChart } from '@/components/dashboard/overview-chart'
import { ModelBreakdown } from '@/components/dashboard/model-breakdown'
import { formatCost, formatLatency, formatNumber } from '@/lib/utils'
import { PeriodSelector } from './period-selector'

interface Props {
  searchParams: { period?: string }
}

export default async function DashboardPage({ searchParams }: Props) {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null
  const periodHours = Number(searchParams.period ?? 24)

  if (!apiKey) {
    return (
      <div className="p-8">
        <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-5">
          <p className="text-yellow-400 font-medium">API key not found in session.</p>
          <p className="text-yellow-600 text-sm mt-1">
            Sign out and sign back in to refresh your credentials.
          </p>
        </div>
      </div>
    )
  }

  let overview = null
  let fetchError: string | null = null

  try {
    overview = await getOverview(apiKey, periodHours)
  } catch (e: any) {
    fetchError = e?.message ?? 'Failed to load data'
  }

  if (fetchError || !overview) {
    return (
      <div className="p-8">
        <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-5">
          <p className="text-red-400 font-medium">Could not load dashboard data.</p>
          <p className="text-red-600 text-sm mt-1">{fetchError}</p>
          <p className="text-gray-500 text-xs mt-2">Is the API running at {process.env.NEXT_PUBLIC_API_URL}?</p>
        </div>
      </div>
    )
  }

  const errorPct =
    overview.total_requests > 0
      ? `${(overview.error_rate * 100).toFixed(1)}%`
      : '0%'

  return (
    <div className="p-8 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-white text-2xl font-semibold">Overview</h1>
          <p className="text-gray-500 text-sm mt-1">
            Last {periodHours === 24 ? '24 hours' : `${periodHours} hours`}
          </p>
        </div>
        <PeriodSelector current={periodHours} />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatsCard
          label="Total Requests"
          value={formatNumber(overview.total_requests)}
          icon={<RequestIcon />}
        />
        <StatsCard
          label="Total Cost"
          value={formatCost(overview.total_cost_usd)}
          subValue="USD"
          icon={<CostIcon />}
        />
        <StatsCard
          label="Avg Latency"
          value={formatLatency(Math.round(overview.avg_latency_ms))}
          icon={<LatencyIcon />}
        />
        <StatsCard
          label="Error Rate"
          value={errorPct}
          subValue={`${overview.error_count} errors`}
          trend={overview.error_rate > 0.05 ? 'up' : 'neutral'}
          trendLabel={overview.error_rate > 0.05 ? 'Above threshold' : 'Healthy'}
          icon={<ErrorIcon />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
        <OverviewChart data={overview.hourly_requests} dataKey="requests" label="Requests over time" />
        <OverviewChart
          data={overview.hourly_requests}
          dataKey="cost_usd"
          color="#3b82f6"
          label="Cost over time"
        />
      </div>

      {/* Model breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ModelBreakdown
          requestsByModel={overview.requests_by_model}
          totalRequests={overview.total_requests}
        />
        <div className="bg-[#111] border border-white/10 rounded-xl p-5">
          <p className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-4">Cost by Model</p>
          {Object.keys(overview.cost_by_model).length === 0 ? (
            <p className="text-gray-600 text-sm">No data yet</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(overview.cost_by_model)
                .sort(([, a], [, b]) => b - a)
                .map(([model, cost]) => (
                  <div key={model} className="flex justify-between items-center py-1">
                    <span className="text-white text-sm font-mono truncate">{model}</span>
                    <span className="text-brand-500 text-sm font-medium">{formatCost(cost)}</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function RequestIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  )
}

function CostIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function LatencyIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function ErrorIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  )
}
