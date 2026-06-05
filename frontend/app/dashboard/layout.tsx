import { getServerSession } from 'next-auth'
import { redirect } from 'next/navigation'
import { authOptions } from '@/lib/auth'
import { Sidebar } from '@/components/layout/sidebar'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  return (
    <div className="flex h-screen bg-[#0a0a0a] overflow-hidden">
      <Sidebar session={session} />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
