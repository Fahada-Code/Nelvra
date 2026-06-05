'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createAlert } from '@/lib/api'

const METRIC_OPTIONS = [
  { value: 'cost_usd', label: 'Total cost (USD)', hint: 'e.g. > $5 per hour' },
  { value: 'error_rate', label: 'Error rate', hint: 'e.g. > 0.05 (5%)' },
  { value: 'latency_p95', label: 'P95 latency (ms)', hint: 'e.g. > 5000 ms' },
  { value: 'request_count', label: 'Request count', hint: 'e.g. < 10 (traffic drop)' },
]

export function CreateAlertButton({ apiKey }: { apiKey: string }) {
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    name: '', metric: 'cost_usd', operator: 'gt', threshold: '', window_minutes: '60',
    notify_slack: false, slack_webhook_url: '',
    notify_email: false, email_address: '',
  })
  const router = useRouter()

  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }))

  const handleCreate = async () => {
    if (!form.name || !form.threshold) return
    setSaving(true)
    try {
      await createAlert(apiKey, {
        name: form.name,
        metric: form.metric,
        operator: form.operator,
        threshold: parseFloat(form.threshold),
        window_minutes: parseInt(form.window_minutes),
        notify_slack: form.notify_slack,
        slack_webhook_url: form.notify_slack ? form.slack_webhook_url : undefined,
        notify_email: form.notify_email,
        email_address: form.notify_email ? form.email_address : undefined,
      })
      setOpen(false)
      router.refresh()
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
        + New Alert
      </button>
    )
  }

  const inputCls = "w-full bg-black/50 border border-white/10 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-brand-500"

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#111] border border-white/10 rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-white font-semibold text-lg mb-5">New Alert</h2>

        <label className="block text-gray-400 text-sm mb-1">Alert name</label>
        <input className={`${inputCls} mb-4`} placeholder="Cost spike alert" value={form.name} onChange={(e) => set('name', e.target.value)} />

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="block text-gray-400 text-sm mb-1">Metric</label>
            <select className={inputCls} value={form.metric} onChange={(e) => set('metric', e.target.value)}>
              {METRIC_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Window</label>
            <select className={inputCls} value={form.window_minutes} onChange={(e) => set('window_minutes', e.target.value)}>
              <option value="15">15 min</option>
              <option value="60">1 hour</option>
              <option value="360">6 hours</option>
              <option value="1440">24 hours</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="block text-gray-400 text-sm mb-1">Operator</label>
            <select className={inputCls} value={form.operator} onChange={(e) => set('operator', e.target.value)}>
              <option value="gt">greater than (&gt;)</option>
              <option value="gte">greater or equal (≥)</option>
              <option value="lt">less than (&lt;)</option>
              <option value="lte">less or equal (≤)</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Threshold</label>
            <input className={inputCls} type="number" step="any" placeholder="0.05" value={form.threshold} onChange={(e) => set('threshold', e.target.value)} />
          </div>
        </div>

        <div className="space-y-3 mb-5">
          <label className="flex items-center gap-3">
            <input type="checkbox" checked={form.notify_slack} onChange={(e) => set('notify_slack', e.target.checked)} className="accent-brand-500" />
            <span className="text-gray-300 text-sm">Slack notification</span>
          </label>
          {form.notify_slack && <input className={inputCls} placeholder="https://hooks.slack.com/..." value={form.slack_webhook_url} onChange={(e) => set('slack_webhook_url', e.target.value)} />}

          <label className="flex items-center gap-3">
            <input type="checkbox" checked={form.notify_email} onChange={(e) => set('notify_email', e.target.checked)} className="accent-brand-500" />
            <span className="text-gray-300 text-sm">Email notification</span>
          </label>
          {form.notify_email && <input className={inputCls} type="email" placeholder="you@example.com" value={form.email_address} onChange={(e) => set('email_address', e.target.value)} />}
        </div>

        <div className="flex gap-3 justify-end">
          <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-white px-4 py-2 text-sm">Cancel</button>
          <button onClick={handleCreate} disabled={saving || !form.name || !form.threshold} className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors">
            {saving ? 'Creating...' : 'Create Alert'}
          </button>
        </div>
      </div>
    </div>
  )
}
