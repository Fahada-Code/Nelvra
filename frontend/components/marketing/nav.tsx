import Link from 'next/link'

export function MarketingNav({ isLoggedIn }: { isLoggedIn: boolean }) {
  return (
    <nav className="border-b border-white/10 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-brand-500 flex items-center justify-center">
            <span className="text-white font-bold text-xs">N</span>
          </div>
          <span className="text-white font-semibold text-lg">Nelvra</span>
        </div>

        <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
          <Link href="#features" className="hover:text-white transition-colors">Features</Link>
          <Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link>
          <a
            href="https://github.com/Fahadada-code/Nelvra"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white transition-colors"
          >
            GitHub
          </a>
        </div>

        <div className="flex items-center gap-3">
          {isLoggedIn ? (
            <Link
              href="/dashboard"
              className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Open Dashboard →
            </Link>
          ) : (
            <>
              <Link href="/login" className="text-gray-400 hover:text-white text-sm transition-colors">
                Sign in
              </Link>
              <Link
                href="/login"
                className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                Get started free
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
