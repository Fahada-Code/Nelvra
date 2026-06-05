import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getRequests } from '@/lib/api'
import { EventsTable } from '@/components/events/events-table'
import { EventsFilters } from './filters'

interface Props {
  searchParams: {
    page?: string
    model?: string
    provider?: string
    environment?: string
  }
}

export default async function EventsPage({ searchParams }: Props) {
  const session = await getServerSession(authOptions)
  const apiKey = (session as any)?.apiKey as string | null

  const page = Number(searchParams.page ?? 1)
  const perPage = 50

  if (!apiKey) {
    return (
      <div className="p-8">
        <p className="text-yellow-400">Session expired. Please sign in again.</p>
      </div>
    )
  }

  let data = null
  let fetchError: string | null = null

  try {
    data = await getRequests(apiKey, {
      page,
      per_page: perPage,
      model: searchParams.model,
      provider: searchParams.provider,
      environment: searchParams.environment,
    })
  } catch (e: any) {
    fetchError = e?.message ?? 'Failed to load'
  }

  const totalPages = data ? Math.ceil(data.total / perPage) : 0

  return (
    <div className="p-8 max-w-7xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-white text-2xl font-semibold">Events</h1>
          {data && (
            <p className="text-gray-500 text-sm mt-1">
              {data.total.toLocaleString()} total events
            </p>
          )}
        </div>
      </div>

      <EventsFilters
        currentModel={searchParams.model}
        currentProvider={searchParams.provider}
        currentEnvironment={searchParams.environment}
      />

      <div className="bg-[#111] border border-white/10 rounded-xl mt-4 overflow-hidden">
        {fetchError ? (
          <div className="p-8 text-center">
            <p className="text-red-400">{fetchError}</p>
          </div>
        ) : (
          <EventsTable
            events={data?.items ?? []}
            currentPage={page}
            totalPages={totalPages}
          />
        )}
      </div>
    </div>
  )
}
