import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getAlerts, getAlertIncidents } from '@/lib/api'
import { AlertRow } from '@/components/alerts/alert-row'
import { CreateAlertButton } from './create-alert-button'
import { relativeTime } from '@/lib/utils'

export default async function AlertsPage() {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null
  if (!apiKey) return <div className="p-8 text-yellow-400">Session expired.</div>

  const [alerts, incidents] = await Promise.all([
    getAlerts(apiKey).catch(() => []),
    getAlertIncidents(apiKey).catch(() => []),
  ])

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-white text-2xl font-semibold">Alerts</h1>
          <p className="text-gray-500 text-sm mt-1">
            Get notified on Slack or email when thresholds are breached.
          </p>
        </div>
        <CreateAlertButton apiKey={apiKey} />
      </div>

      {/* Active alerts */}
      <section className="mb-8">
        <h2 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">
          Alert Rules ({alerts.length})
        </h2>
        {alerts.length === 0 ? (
          <div className="bg-[#111] border border-white/10 rounded-xl p-8 text-center">
            <p className="text-gray-400">No alerts configured</p>
            <p className="text-gray-600 text-sm mt-1">Create your first alert to get notified about cost spikes, errors, or latency issues.</p>
          </div>
        ) : (
          <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden divide-y divide-white/5">
            {alerts.map((a: any) => (
              <AlertRow key={a.id} alert={a} apiKey={apiKey} />
            ))}
          </div>
        )}
      </section>

      {/* Recent incidents */}
      {incidents.length > 0 && (
        <section>
          <h2 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">
            Recent Incidents
          </h2>
          <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left text-gray-500 text-xs font-medium py-3 px-4 uppercase">Time</th>
                  <th className="text-left text-gray-500 text-xs font-medium py-3 px-4 uppercase">Value</th>
                  <th className="text-left text-gray-500 text-xs font-medium py-3 px-4 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {incidents.slice(0, 20).map((i: any) => (
                  <tr key={i.id}>
                    <td className="py-3 px-4 text-gray-400 text-sm">{relativeTime(i.created_at)}</td>
                    <td className="py-3 px-4 text-white text-sm tabular-nums">{i.triggered_value.toFixed(4)}</td>
                    <td className="py-3 px-4">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${i.resolved_at ? 'text-brand-400 bg-brand-900/30 border-brand-700/40' : 'text-red-400 bg-red-900/30 border-red-700/40'}`}>
                        {i.resolved_at ? 'resolved' : 'active'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
