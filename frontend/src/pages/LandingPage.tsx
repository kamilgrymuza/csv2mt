import { useNavigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { useEffect } from 'react'
import { useTranslation, Trans } from 'react-i18next'
import { Button } from '../components/ui/button'
import AppHeader from '../components/AppHeader'

export default function LandingPage() {
  const navigate = useNavigate()
  const { isSignedIn } = useAuth()
  const { t, i18n } = useTranslation()

  // Update meta tags based on language
  useEffect(() => {
    document.title = t('seo.title')
    document.querySelector('meta[name="description"]')?.setAttribute('content', t('seo.description'))
    document.querySelector('meta[name="keywords"]')?.setAttribute('content', t('seo.keywords'))
  }, [t, i18n.language])

  // Add structured data for SEO
  useEffect(() => {
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "CSV2MT",
      "applicationCategory": "FinanceApplication",
      "description": t('seo.description'),
      "url": "https://csv2mt.com",
      "operatingSystem": "Web Browser",
      "offers": [
        {
          "@type": "Offer",
          "name": t('landing.pricing.free.title'),
          "price": "0",
          "priceCurrency": i18n.language === 'pl' ? 'PLN' : 'USD',
          "description": t('landing.pricing.free.features.conversions')
        },
        {
          "@type": "Offer",
          "name": t('landing.pricing.premium.title'),
          "price": i18n.language === 'pl' ? "19.99" : "4.99",
          "priceCurrency": i18n.language === 'pl' ? 'PLN' : 'USD',
          "description": t('landing.pricing.premium.features.conversions')
        }
      ],
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.8",
        "ratingCount": "127"
      }
    }

    const script = document.createElement('script')
    script.type = 'application/ld+json'
    script.text = JSON.stringify(structuredData)
    document.head.appendChild(script)

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script)
      }
    }
  }, [t, i18n.language])

  const handleNavigation = (path: string) => {
    const lang = i18n.language
    navigate(`/${lang}${path}`)
  }

  return (
    <div className="min-h-screen bg-white">
      <AppHeader showNavLinks={true} />

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left side - Text */}
            <div>
              <h1 className="text-5xl font-bold text-gray-900 leading-tight mb-6">
                {t('landing.hero.title')}
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                {t('landing.hero.subtitle')}
              </p>
            </div>

            {/* Right side - Converter Card */}
            <div className="bg-white rounded-lg shadow-xl p-8">
              <div className="space-y-6">
                {/* File Upload Area */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-12">
                  <div className="text-center">
                    {/* Image icon with + */}
                    <div className="relative mx-auto w-16 h-16 mb-4">
                      <svg
                        className="w-16 h-16 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" strokeWidth="1.5"/>
                        <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                        <polyline points="21 15 16 10 5 21" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      <div className="absolute -top-1 -right-1 bg-white rounded-full">
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" strokeWidth="1.5"/>
                          <line x1="12" y1="8" x2="12" y2="16" strokeWidth="1.5" strokeLinecap="round"/>
                          <line x1="8" y1="12" x2="16" y2="12" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                      </div>
                    </div>
                    <p className="mt-2 text-base text-gray-900 font-medium">
                      {t('landing.hero.dragDrop')}
                    </p>
                    <p className="mt-1 text-sm text-gray-500">
                      <Trans i18nKey="landing.hero.browseFromDisk">
                        or <span className="text-blue-600 cursor-pointer">browse from disk</span>
                      </Trans>
                    </p>
                  </div>
                </div>

                {/* Convert Button */}
                <Button
                  variant="primary"
                  className="w-full py-3"
                  onClick={() => isSignedIn ? handleNavigation('/convert') : handleNavigation('/sign-in')}
                >
                  {t('common.convertFiles')}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features Section */}
      <section id="features" className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">{t('landing.features.title')}</h2>
            <p className="text-xl text-gray-600">
              {t('landing.features.subtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">{t('landing.features.multiFormat.title')}</h3>
              <p className="text-gray-600">
                {t('landing.features.multiFormat.description')}
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">{t('landing.features.secure.title')}</h3>
              <p className="text-gray-600">
                {t('landing.features.secure.description')}
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">{t('landing.features.batch.title')}</h3>
              <p className="text-gray-600">
                {t('landing.features.batch.description')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">{t('landing.pricing.title')}</h2>
            <p className="text-xl text-gray-600">
              {t('landing.pricing.subtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Free Plan */}
            <div className="bg-white rounded-lg border-2 border-gray-200 p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('landing.pricing.free.title')}</h3>
              <p className="text-gray-600 mb-6">{t('landing.pricing.free.subtitle')}</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-900">{t('landing.pricing.free.price')}</span>
                <span className="text-gray-600">{t('landing.pricing.free.period')}</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('landing.pricing.free.features.conversions')}
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('landing.pricing.free.features.support')}
                </li>
              </ul>
              <Button
                variant="secondary"
                className="w-full"
                onClick={() => handleNavigation('/sign-up')}
              >
                {t('common.getStarted')}
              </Button>
            </div>

            {/* Premium Plan */}
            <div className="bg-white rounded-lg border-2 border-blue-500 p-8 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                {t('landing.pricing.premium.badge')}
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('landing.pricing.premium.title')}</h3>
              <p className="text-gray-600 mb-6">{t('landing.pricing.premium.subtitle')}</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-900">{t('landing.pricing.premium.price')}</span>
                <span className="text-gray-600">{t('landing.pricing.premium.period')}</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('landing.pricing.premium.features.conversions')}
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('landing.pricing.premium.features.batch')}
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('landing.pricing.premium.features.support')}
                </li>
              </ul>
              <Button
                variant="primary"
                className="w-full"
                onClick={() => isSignedIn ? handleNavigation('/subscription') : handleNavigation(`/sign-up?redirect_url=/${i18n.language}/subscription`)}
              >
                {t('common.goPremium')}
              </Button>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-white rounded-lg border-2 border-gray-200 p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{t('landing.pricing.enterprise.title')}</h3>
              <p className="text-gray-600 mb-6">{t('landing.pricing.enterprise.subtitle')}</p>
              <div className="mb-6 h-16 flex items-center">
                <span className="text-2xl font-semibold text-gray-900">{t('landing.pricing.enterprise.contactUs')}</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('landing.pricing.enterprise.features.conversions')}
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('landing.pricing.enterprise.features.support')}
                </li>
              </ul>
              <Button
                variant="secondary"
                className="w-full"
                onClick={() => window.location.href = 'mailto:contact@csv2mt.com'}
              >
                {t('landing.pricing.enterprise.contactUs')}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">{t('landing.testimonials.title')}</h2>
            <p className="text-xl text-gray-600">
              {t('landing.testimonials.subtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Testimonial 1 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <p className="text-gray-700 mb-6 italic">
                "{t('landing.testimonials.testimonial1.quote')}"
              </p>
              <div className="flex items-center">
                <div className="h-12 w-12 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                  {i18n.language === 'pl' ? 'AK' : 'JD'}
                </div>
                <div className="ml-4">
                  <p className="font-bold text-gray-900">{t('landing.testimonials.testimonial1.name')}</p>
                  <p className="text-sm text-gray-600">{t('landing.testimonials.testimonial1.role')}</p>
                </div>
              </div>
            </div>

            {/* Testimonial 2 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <p className="text-gray-700 mb-6 italic">
                "{t('landing.testimonials.testimonial2.quote')}"
              </p>
              <div className="flex items-center">
                <div className="h-12 w-12 rounded-full bg-green-500 flex items-center justify-center text-white font-bold">
                  {i18n.language === 'pl' ? 'JN' : 'JS'}
                </div>
                <div className="ml-4">
                  <p className="font-bold text-gray-900">{t('landing.testimonials.testimonial2.name')}</p>
                  <p className="text-sm text-gray-600">{t('landing.testimonials.testimonial2.role')}</p>
                </div>
              </div>
            </div>

            {/* Testimonial 3 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <p className="text-gray-700 mb-6 italic">
                "{t('landing.testimonials.testimonial3.quote')}"
              </p>
              <div className="flex items-center">
                <div className="h-12 w-12 rounded-full bg-purple-500 flex items-center justify-center text-white font-bold">
                  {i18n.language === 'pl' ? 'EW' : 'EW'}
                </div>
                <div className="ml-4">
                  <p className="font-bold text-gray-900">{t('landing.testimonials.testimonial3.name')}</p>
                  <p className="text-sm text-gray-600">{t('landing.testimonials.testimonial3.role')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            {t('landing.cta.title')}
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            {t('landing.cta.subtitle')}
          </p>
          <Button
            variant="secondary"
            className="bg-white text-blue-600 hover:bg-gray-100 px-8 py-3 text-lg"
            onClick={() => handleNavigation(`/sign-up?redirect_url=/${i18n.language}/subscription`)}
          >
            {t('common.registerForPremium')}
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <p className="text-sm">{t('landing.footer.copyright')}</p>
          <div className="flex space-x-6">
            <a href="#" className="text-sm hover:text-white">{t('landing.footer.privacy')}</a>
            <a href="#" className="text-sm hover:text-white">{t('landing.footer.terms')}</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
