'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createPrompt } from '@/lib/api'

export function CreatePromptButton({ apiKey }: { apiKey: string }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const router = useRouter()

  const handleCreate = async () => {
    if (!name.trim() || !content.trim()) return
    setSaving(true)
    try {
      await createPrompt(apiKey, { name: name.trim(), content: content.trim() })
      setOpen(false)
      setName('')
      setContent('')
      router.refresh()
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
      >
        + New Prompt
      </button>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#111] border border-white/10 rounded-2xl p-6 w-full max-w-xl">
        <h2 className="text-white font-semibold text-lg mb-5">New Prompt</h2>
        <label className="block text-gray-400 text-sm mb-1">Name</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Customer Support System Prompt"
          className="w-full bg-black/50 border border-white/10 text-white text-sm rounded-lg px-3 py-2 mb-4 focus:outline-none focus:border-brand-500"
        />
        <label className="block text-gray-400 text-sm mb-1">Prompt Content</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={8}
          placeholder="You are a helpful assistant..."
          className="w-full bg-black/50 border border-white/10 text-white text-sm rounded-lg px-3 py-2 mb-4 font-mono focus:outline-none focus:border-brand-500 resize-none"
        />
        <div className="flex gap-3 justify-end">
          <button
            onClick={() => setOpen(false)}
            className="text-gray-400 hover:text-white px-4 py-2 text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={saving || !name.trim() || !content.trim()}
            className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
          >
            {saving ? 'Creating...' : 'Create Prompt'}
          </button>
        </div>
      </div>
    </div>
  )
}
