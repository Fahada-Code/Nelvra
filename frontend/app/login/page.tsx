import { getServerSession } from 'next-auth'
import { redirect } from 'next/navigation'
import { authOptions } from '@/lib/auth'
import { LoginButton } from './login-button'

export default async function LoginPage() {
  const session = await getServerSession(authOptions)
  if (session) redirect('/dashboard')

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <div className="w-full max-w-md px-8">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">N</span>
            </div>
            <span className="text-white text-xl font-semibold">Nelvra</span>
          </div>
          <h1 className="text-white text-2xl font-semibold">Welcome back</h1>
          <p className="text-gray-400 mt-2 text-sm">
            Monitor, optimize, and understand your LLM app.
          </p>
        </div>

        {/* Card */}
        <div className="bg-[#111] border border-white/10 rounded-xl p-8">
          <LoginButton />
          <p className="text-center text-gray-500 text-xs mt-6">
            By signing in, you agree to our terms of service.
          </p>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-600 text-xs mt-8">
          Free plan includes 50k events/month. No credit card required.
        </p>
      </div>
    </div>
  )
}
