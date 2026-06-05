import Link from 'next/link'

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'For indie hackers and prototypes.',
    events: '50,000 events/mo',
    retention: '7-day retention',
    features: [
      'Core monitoring (latency, cost, errors)',
      'Full request logging',
      'Real-time dashboard',
      'Python + JS SDKs',
      'Self-hosted option',
    ],
    cta: 'Start free',
    ctaHref: '/login',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$29',
    period: '/month',
    description: 'For production AI apps with real traffic.',
    events: '500,000 events/mo',
    retention: '30-day retention',
    features: [
      'Everything in Free',
      'Prompt drift detection',
      'LLM-as-judge quality scoring',
      'Cost spike + error rate alerts',
      'Slack + email notifications',
    ],
    cta: 'Start Pro',
    ctaHref: '/login',
    highlighted: true,
  },
  {
    name: 'Team',
    price: '$99',
    period: '/month',
    description: 'For teams shipping multiple AI features.',
    events: '5,000,000 events/mo',
    retention: '90-day retention',
    features: [
      'Everything in Pro',
      'Automatic prompt optimization',
      'One-click deploy + auto-rollback',
      'Team members (up to 5)',
      'CSV export + audit logs',
    ],
    cta: 'Start Team',
    ctaHref: '/login',
    highlighted: false,
  },
]

export function PricingSection() {
  return (
    <section id="pricing" className="py-20 px-6 border-t border-white/5">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Simple, honest pricing</h2>
          <p className="text-gray-400 text-lg">
            Start free. Upgrade when you need more. Cancel anytime.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-2xl p-7 border ${
                plan.highlighted
                  ? 'bg-brand-900/20 border-brand-600/60 ring-1 ring-brand-600/40'
                  : 'bg-[#111] border-white/10'
              }`}
            >
              {plan.highlighted && (
                <div className="text-xs text-brand-400 font-medium mb-3 uppercase tracking-wider">
                  Most popular
                </div>
              )}
              <div className="mb-5">
                <h3 className="text-white font-bold text-xl">{plan.name}</h3>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-white text-3xl font-bold">{plan.price}</span>
                  <span className="text-gray-500 text-sm">{plan.period}</span>
                </div>
                <p className="text-gray-500 text-sm mt-1">{plan.description}</p>
              </div>

              <div className="space-y-1 mb-6">
                <p className="text-brand-400 text-sm font-medium">{plan.events}</p>
                <p className="text-gray-500 text-sm">{plan.retention}</p>
              </div>

              <ul className="space-y-2.5 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-brand-500 mt-0.5 flex-shrink-0">✓</span>
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href={plan.ctaHref}
                className={`block w-full text-center py-3 rounded-xl font-medium transition-colors ${
                  plan.highlighted
                    ? 'bg-brand-600 hover:bg-brand-700 text-white'
                    : 'border border-white/20 hover:border-white/40 text-white'
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <p className="text-center text-gray-600 text-sm mt-8">
          All plans include Apache 2.0 licensed self-hosting. No credit card required for Free.
        </p>
      </div>
    </section>
  )
}
