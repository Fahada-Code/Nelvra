const features = [
  {
    icon: '📉',
    title: 'Prompt Drift Detection',
    description:
      'Automatically detects when your prompts silently degrade in production. Get plain-English alerts like "Your support prompt quality dropped 23% in the last 48 hours."',
    badge: 'Hero feature',
    badgeColor: 'bg-brand-900/50 text-brand-400 border-brand-700/50',
  },
  {
    icon: '⚡',
    title: 'Automatic Prompt Optimization',
    description:
      'Detects underperforming prompts, generates an optimized version using Claude, and shows a side-by-side diff with estimated token savings. One-click deploy with auto-rollback.',
    badge: 'Phase 2',
    badgeColor: 'bg-blue-900/50 text-blue-400 border-blue-700/50',
  },
  {
    icon: '📊',
    title: 'Real-Time Cost Intelligence',
    description:
      'See your LLM spend by model, feature, and environment in real time. Set monthly budget thresholds and get Slack or email alerts before you overspend.',
    badge: 'Core',
    badgeColor: 'bg-gray-800 text-gray-400 border-gray-700',
  },
  {
    icon: '🔍',
    title: 'Full Request Logging',
    description:
      'Every prompt, response, latency, token count, and cost captured automatically. Search, filter, and inspect any call — no sampling, no data loss.',
    badge: 'Core',
    badgeColor: 'bg-gray-800 text-gray-400 border-gray-700',
  },
  {
    icon: '✨',
    title: 'LLM-as-Judge Quality Scoring',
    description:
      'Each response is scored 0–1 by Claude acting as a neutral judge. Track quality trends over time and get alerted the moment scores start slipping.',
    badge: 'Phase 2',
    badgeColor: 'bg-blue-900/50 text-blue-400 border-blue-700/50',
  },
  {
    icon: '⏱️',
    title: '60-Second Setup',
    description:
      'Three lines of code. Works immediately. Auto-patches your existing OpenAI and Anthropic clients — no middleware, no proxy, no config required.',
    badge: 'Core',
    badgeColor: 'bg-gray-800 text-gray-400 border-gray-700',
  },
]

export function Features() {
  return (
    <section id="features" className="py-20 px-6 border-t border-white/5">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Every competitor shows dashboards.
            <br />
            <span className="text-brand-500">Nelvra tells you what's wrong and fixes it.</span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Purpose-built for developers shipping AI products — not MLOps teams with dedicated tooling.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <div
              key={f.title}
              className="bg-[#111] border border-white/10 rounded-xl p-6 hover:border-white/20 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-3xl">{f.icon}</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${f.badgeColor}`}>
                  {f.badge}
                </span>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
