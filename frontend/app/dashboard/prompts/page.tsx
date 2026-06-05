import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getPrompts } from '@/lib/api'
import { PromptCard } from '@/components/prompts/prompt-card'
import { CreatePromptButton } from './create-prompt-button'

export default async function PromptsPage() {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null

  if (!apiKey) return <div className="p-8 text-yellow-400">Session expired.</div>

  let prompts = []
  let error: string | null = null
  try {
    prompts = await getPrompts(apiKey)
  } catch (e: any) {
    error = e?.message ?? 'Failed to load'
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-white text-2xl font-semibold">Prompts</h1>
          <p className="text-gray-500 text-sm mt-1">
            Track, monitor, and optimize your prompt templates.
          </p>
        </div>
        <CreatePromptButton apiKey={apiKey} />
      </div>

      {error ? (
        <p className="text-red-400">{error}</p>
      ) : prompts.length === 0 ? (
        <div className="bg-[#111] border border-white/10 rounded-xl p-10 text-center">
          <p className="text-gray-400 font-medium mb-2">No prompts tracked yet</p>
          <p className="text-gray-600 text-sm">
            Create a prompt to start tracking drift and optimizing quality.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {prompts.map((p: any) => (
            <PromptCard key={p.id} prompt={p} apiKey={apiKey} />
          ))}
        </div>
      )}
    </div>
  )
}
