import Link from 'next/link'

export function Footer() {
  return (
    <footer className="border-t border-white/10 py-12 px-6 mt-8">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-brand-500 flex items-center justify-center">
            <span className="text-white font-bold text-xs">N</span>
          </div>
          <span className="text-white font-semibold">Nelvra</span>
          <span className="text-gray-600 text-sm ml-2">Open-core LLM observability</span>
        </div>

        <div className="flex items-center gap-6 text-sm text-gray-500">
          <a
            href="https://github.com/Fahadada-code/Nelvra"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white transition-colors"
          >
            GitHub
          </a>
          <Link href="/login" className="hover:text-white transition-colors">
            Sign in
          </Link>
          <span>Apache 2.0 License</span>
        </div>
      </div>
    </footer>
  )
}
