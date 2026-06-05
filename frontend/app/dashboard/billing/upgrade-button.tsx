'use client'

import { useState } from 'react'
import { createCheckout, createBillingPortal } from '@/lib/api'

interface Props {
  apiKey: string
  plan?: 'pro' | 'team'
  mode: 'checkout' | 'portal'
}

export function UpgradeButton({ apiKey, plan, mode }: Props) {
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    setLoading(true)
    try {
      if (mode === 'checkout' && plan) {
        const { checkout_url } = await createCheckout(apiKey, plan)
        window.location.href = checkout_url
      } else {
        const { portal_url } = await createBillingPortal(apiKey)
        window.location.href = portal_url
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
    >
      {loading ? 'Redirecting...' : mode === 'portal' ? 'Manage billing' : `Upgrade to ${plan}`}
    </button>
  )
}
