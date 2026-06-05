import Link from 'next/link'

export function Hero({ isLoggedIn }: { isLoggedIn: boolean }) {
  return (
    <section className="pt-24 pb-20 px-6 text-center">
      <div className="max-w-4xl mx-auto">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-brand-900/40 border border-brand-700/40 rounded-full px-4 py-1.5 text-brand-400 text-sm mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
          Open-source LLM observability
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-6xl font-bold text-white leading-tight mb-6">
          Know when your AI breaks{' '}
          <span className="text-brand-500">before your users do</span>
        </h1>

        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Monitor every LLM call, detect silent prompt degradation, and automatically
          optimize underperforming prompts — with a 3-line SDK integration.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Link
            href={isLoggedIn ? '/dashboard' : '/login'}
            className="bg-brand-600 hover:bg-brand-700 text-white font-medium px-8 py-3.5 rounded-xl text-lg transition-colors"
          >
            {isLoggedIn ? 'Open Dashboard →' : 'Start free — 50k events/mo'}
          </Link>
          <a
            href="https://github.com/Fahadada-code/Nelvra"
            target="_blank"
            rel="noreferrer"
            className="border border-white/20 hover:border-white/40 text-white font-medium px-8 py-3.5 rounded-xl text-lg transition-colors flex items-center gap-2 justify-center"
          >
            <GitHubIcon className="w-5 h-5" />
            View on GitHub
          </a>
        </div>

        {/* Code snippet */}
        <div className="max-w-lg mx-auto">
          <div className="bg-[#111] border border-white/10 rounded-xl overflow-hidden text-left">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-white/10">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-green-500/60" />
              <span className="ml-2 text-gray-500 text-xs">your_app.py</span>
            </div>
            <pre className="px-5 py-4 text-sm font-mono leading-relaxed">
              <span className="text-gray-500">1  </span>
              <span className="text-blue-400">from </span>
              <span className="text-white">nelvra </span>
              <span className="text-blue-400">import </span>
              <span className="text-white">Nelvra{'\n'}</span>
              <span className="text-gray-500">2  </span>
              <span className="text-white">nelvra </span>
              <span className="text-gray-400">= </span>
              <span className="text-yellow-400">Nelvra</span>
              <span className="text-white">(api_key</span>
              <span className="text-gray-400">=</span>
              <span className="text-green-400">"nvl_live_..."</span>
              <span className="text-white">){'\n'}</span>
              <span className="text-gray-500">3  </span>
              <span className="text-white">nelvra.</span>
              <span className="text-yellow-400">instrument</span>
              <span className="text-white">()  </span>
              <span className="text-gray-600"># done ✓</span>
            </pre>
          </div>
          <p className="text-gray-600 text-sm mt-3">Works with OpenAI and Anthropic. No config required.</p>
        </div>
      </div>
    </section>
  )
}

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  )
}
