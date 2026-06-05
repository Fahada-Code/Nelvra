'use client'

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { HourlyBucket } from '@/lib/api'

interface OverviewChartProps {
  data: HourlyBucket[]
  dataKey: 'requests' | 'cost_usd'
  color?: string
  label?: string
}

function formatHour(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function OverviewChart({ data, dataKey, color = '#22c55e', label }: OverviewChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    hour: formatHour(d.hour),
  }))

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl p-5">
      {label && <p className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-4">{label}</p>}
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
          <XAxis
            dataKey="hour"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => (dataKey === 'cost_usd' ? `$${v.toFixed(2)}` : String(v))}
          />
          <Tooltip
            contentStyle={{
              background: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
              color: '#fff',
              fontSize: 12,
            }}
            formatter={(val: number) =>
              dataKey === 'cost_usd' ? [`$${val.toFixed(4)}`, 'Cost'] : [val, 'Requests']
            }
          />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            fill={`url(#grad-${dataKey})`}
            strokeWidth={2}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
