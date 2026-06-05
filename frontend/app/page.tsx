import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { MarketingNav } from '@/components/marketing/nav'
import { Hero } from '@/components/marketing/hero'
import { Features } from '@/components/marketing/features'
import { PricingSection } from '@/components/marketing/pricing-section'
import { Footer } from '@/components/marketing/footer'

export default async function LandingPage() {
  const session = await getServerSession(authOptions)

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <MarketingNav isLoggedIn={!!session} />
      <Hero isLoggedIn={!!session} />
      <Features />
      <PricingSection />
      <Footer />
    </div>
  )
}
