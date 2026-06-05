import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getApiKeys, getProjects } from '@/lib/api'
import { ApiKeysManager } from './api-keys-manager'

export default async function SettingsPage() {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null
  const projectId = (session as any)?.projectId as string | null

  if (!apiKey || !projectId) {
    return (
      <div className="p-8">
        <p className="text-yellow-400">Session expired. Please sign in again.</p>
      </div>
    )
  }

  const [keys, projects] = await Promise.all([
    getApiKeys(apiKey, projectId).catch(() => []),
    getProjects(apiKey).catch(() => []),
  ])

  const project = projects.find((p) => p.id === projectId)

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-white text-2xl font-semibold mb-8">Settings</h1>

      {/* Project info */}
      <section className="mb-8">
        <h2 className="text-white text-sm font-medium uppercase tracking-wider mb-4">Project</h2>
        <div className="bg-[#111] border border-white/10 rounded-xl p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white font-medium">{project?.name ?? 'Unknown project'}</p>
              <p className="text-gray-500 text-xs mt-1 font-mono">{projectId}</p>
            </div>
          </div>
        </div>
      </section>

      {/* SDK quickstart */}
      <section className="mb-8">
        <h2 className="text-white text-sm font-medium uppercase tracking-wider mb-4">Quickstart</h2>
        <div className="bg-[#111] border border-white/10 rounded-xl p-5 space-y-4">
          <div>
            <p className="text-gray-400 text-sm mb-2">Python</p>
            <pre className="bg-black/50 rounded-lg p-3 text-green-400 text-sm font-mono overflow-x-auto">
{`pip install nelvra

from nelvra import Nelvra
nelvra = Nelvra(api_key="nvl_live_...")
nelvra.instrument()  # auto-patches openai, anthropic`}
            </pre>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">JavaScript / TypeScript</p>
            <pre className="bg-black/50 rounded-lg p-3 text-green-400 text-sm font-mono overflow-x-auto">
{`npm install @nelvra/sdk

import { Nelvra } from '@nelvra/sdk'
const nelvra = new Nelvra({ apiKey: 'nvl_live_...' })
nelvra.instrument()`}
            </pre>
          </div>
        </div>
      </section>

      {/* API Keys */}
      <section>
        <h2 className="text-white text-sm font-medium uppercase tracking-wider mb-4">API Keys</h2>
        <ApiKeysManager
          projectId={projectId}
          sessionApiKey={apiKey}
          initialKeys={keys}
        />
      </section>
    </div>
  )
}
