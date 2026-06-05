import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getBillingSubscription, getBillingUsage } from '@/lib/api'
import { UpgradeButton } from './upgrade-button'
import { formatNumber } from '@/lib/utils'

export default async function BillingPage() {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null
  if (!apiKey) return <div className="p-8 text-yellow-400">Session expired.</div>

  const [sub, usage] = await Promise.all([
    getBillingSubscription(apiKey).catch(() => null),
    getBillingUsage(apiKey).catch(() => null),
  ])

  const planColors: Record<string, string> = {
    free: 'text-gray-400',
    pro: 'text-brand-400',
    team: 'text-blue-400',
  }

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-white text-2xl font-semibold mb-8">Billing</h1>

      {/* Current plan */}
      <section className="mb-8">
        <h2 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">Current Plan</h2>
        <div className="bg-[#111] border border-white/10 rounded-xl p-6">
          {sub ? (
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <span className={`text-2xl font-bold capitalize ${planColors[sub.plan] ?? 'text-white'}`}>
                    {sub.plan}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${
                    sub.status === 'active' ? 'text-brand-400 bg-brand-900/30 border-brand-700/40' :
                    'text-red-400 bg-red-900/30 border-red-700/40'
                  }`}>
                    {sub.status}
                  </span>
                </div>
                <p className="text-gray-500 text-sm mt-1">
                  {formatNumber(sub.events_limit)} events/month · {sub.retention_days}-day retention
                </p>
                {sub.current_period_end && (
                  <p className="text-gray-600 text-xs mt-1">
                    Renews {new Date(sub.current_period_end).toLocaleDateString()}
                  </p>
                )}
              </div>
              {sub.plan !== 'free' && (
                <UpgradeButton apiKey={apiKey} mode="portal" />
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Free plan · unlimited time</p>
          )}
        </div>
      </section>

      {/* Usage */}
      {usage && (
        <section className="mb-8">
          <h2 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">This Month</h2>
          <div className="bg-[#111] border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-white text-lg font-semibold">{formatNumber(usage.events_this_month)}</p>
                <p className="text-gray-500 text-sm">of {formatNumber(usage.events_limit)} events used</p>
              </div>
              <p className={`text-lg font-semibold ${usage.pct_used >= 90 ? 'text-red-400' : usage.pct_used >= 70 ? 'text-yellow-400' : 'text-brand-400'}`}>
                {usage.pct_used}%
              </p>
            </div>
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${usage.pct_used >= 90 ? 'bg-red-500' : usage.pct_used >= 70 ? 'bg-yellow-500' : 'bg-brand-500'}`}
                style={{ width: `${Math.min(usage.pct_used, 100)}%` }}
              />
            </div>
          </div>
        </section>
      )}

      {/* Upgrade */}
      {(!sub || sub.plan === 'free') && (
        <section>
          <h2 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">Upgrade</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#111] border border-white/10 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-1">Pro</h3>
              <p className="text-brand-400 text-2xl font-bold mb-2">$29<span className="text-gray-500 text-sm font-normal">/mo</span></p>
              <ul className="text-gray-400 text-sm space-y-1 mb-5">
                <li>✓ 500k events/month</li>
                <li>✓ Prompt drift detection</li>
                <li>✓ Quality scoring</li>
                <li>✓ Slack + email alerts</li>
              </ul>
              <UpgradeButton apiKey={apiKey} plan="pro" mode="checkout" />
            </div>
            <div className="bg-[#111] border border-white/10 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-1">Team</h3>
              <p className="text-blue-400 text-2xl font-bold mb-2">$99<span className="text-gray-500 text-sm font-normal">/mo</span></p>
              <ul className="text-gray-400 text-sm space-y-1 mb-5">
                <li>✓ 5M events/month</li>
                <li>✓ Prompt optimization</li>
                <li>✓ Team members (5)</li>
                <li>✓ CSV export</li>
              </ul>
              <UpgradeButton apiKey={apiKey} plan="team" mode="checkout" />
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
