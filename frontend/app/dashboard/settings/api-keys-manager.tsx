'use client'

import { useState } from 'react'
import { createApiKey, revokeApiKey, type ApiKeyItem, type ApiKeyCreated } from '@/lib/api'
import { relativeTime } from '@/lib/utils'

interface Props {
  projectId: string
  sessionApiKey: string
  initialKeys: ApiKeyItem[]
}

export function ApiKeysManager({ projectId, sessionApiKey, initialKeys }: Props) {
  const [keys, setKeys] = useState(initialKeys)
  const [creating, setCreating] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [justCreated, setJustCreated] = useState<ApiKeyCreated | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!newKeyName.trim()) return
    setCreating(true)
    setError(null)
    try {
      const created = await createApiKey(sessionApiKey, projectId, newKeyName.trim())
      setJustCreated(created)
      setKeys((prev) => [...prev, created])
      setNewKeyName('')
    } catch (e: any) {
      setError(e?.message ?? 'Failed to create key')
    } finally {
      setCreating(false)
    }
  }

  const handleRevoke = async (keyId: string) => {
    if (!confirm('Revoke this API key? This cannot be undone.')) return
    try {
      await revokeApiKey(sessionApiKey, projectId, keyId)
      setKeys((prev) => prev.filter((k) => k.id !== keyId))
      if (justCreated?.id === keyId) setJustCreated(null)
    } catch (e: any) {
      setError(e?.message ?? 'Failed to revoke key')
    }
  }

  return (
    <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden">
      {/* Just-created key banner */}
      {justCreated && (
        <div className="p-4 bg-brand-900/30 border-b border-brand-700/30">
          <p className="text-brand-400 text-sm font-medium mb-2">
            New API key created — copy it now. It will not be shown again.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-black/50 border border-white/10 rounded px-3 py-2 text-green-400 text-sm font-mono break-all">
              {justCreated.key}
            </code>
            <button
              onClick={() => navigator.clipboard.writeText(justCreated.key)}
              className="px-3 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg transition-colors"
            >
              Copy
            </button>
          </div>
          <button
            onClick={() => setJustCreated(null)}
            className="text-gray-500 text-xs mt-2 hover:text-white"
          >
            I&apos;ve saved it
          </button>
        </div>
      )}

      {/* Existing keys */}
      <div className="divide-y divide-white/5">
        {keys.length === 0 ? (
          <p className="px-5 py-8 text-center text-gray-600 text-sm">No API keys yet.</p>
        ) : (
          keys.map((key) => (
            <div key={key.id} className="flex items-center justify-between px-5 py-3.5">
              <div>
                <p className="text-white text-sm font-medium">{key.name}</p>
                <p className="text-gray-500 text-xs font-mono mt-0.5">
                  nvl_live_{key.key_prefix}••••••••
                  {key.last_used_at && (
                    <span className="ml-2 text-gray-600">· last used {relativeTime(key.last_used_at)}</span>
                  )}
                </p>
              </div>
              <button
                onClick={() => handleRevoke(key.id)}
                className="text-gray-600 hover:text-red-400 text-xs transition-colors"
              >
                Revoke
              </button>
            </div>
          ))
        )}
      </div>

      {/* Create new key form */}
      <div className="px-5 py-4 border-t border-white/10">
        {error && <p className="text-red-400 text-xs mb-2">{error}</p>}
        <div className="flex gap-2">
          <input
            type="text"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            placeholder="Key name (e.g. Production)"
            className="flex-1 bg-black/50 border border-white/10 text-white text-sm rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none focus:border-brand-500"
          />
          <button
            onClick={handleCreate}
            disabled={creating || !newKeyName.trim()}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {creating ? 'Creating...' : 'Create Key'}
          </button>
        </div>
      </div>
    </div>
  )
}
