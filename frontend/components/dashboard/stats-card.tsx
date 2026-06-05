import { cn } from '@/lib/utils'

interface StatsCardProps {
  label: string
  value: string
  subValue?: string
  trend?: 'up' | 'down' | 'neutral'
  trendLabel?: string
  icon?: React.ReactNode
  className?: string
}

export function StatsCard({
  label,
  value,
  subValue,
  trend,
  trendLabel,
  icon,
  className,
}: StatsCardProps) {
  return (
    <div
      className={cn(
        'bg-[#111] border border-white/10 rounded-xl p-5',
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-xs font-medium uppercase tracking-wider">{label}</p>
          <p className="text-white text-2xl font-semibold mt-1">{value}</p>
          {subValue && <p className="text-gray-500 text-sm mt-0.5">{subValue}</p>}
          {trendLabel && trend && (
            <p
              className={cn(
                'text-xs mt-1.5',
                trend === 'up' && 'text-red-400',
                trend === 'down' && 'text-brand-500',
                trend === 'neutral' && 'text-gray-400',
              )}
            >
              {trendLabel}
            </p>
          )}
        </div>
        {icon && (
          <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-gray-400">
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
