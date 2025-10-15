import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'

export default function SEOHead() {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const currentLang = i18n.language

  useEffect(() => {
    // Update document title
    document.title = t('seo.title')

    // Update meta tags
    const metaDescription = document.querySelector('meta[name="description"]')
    if (metaDescription) {
      metaDescription.setAttribute('content', t('seo.description'))
    }

    const metaKeywords = document.querySelector('meta[name="keywords"]')
    if (metaKeywords) {
      metaKeywords.setAttribute('content', t('seo.keywords'))
    }

    // Update Open Graph tags
    const ogTitle = document.querySelector('meta[property="og:title"]')
    if (ogTitle) {
      ogTitle.setAttribute('content', t('seo.title'))
    }

    const ogDescription = document.querySelector('meta[property="og:description"]')
    if (ogDescription) {
      ogDescription.setAttribute('content', t('seo.description'))
    }

    // Update Twitter Card tags
    const twitterTitle = document.querySelector('meta[property="twitter:title"]')
    if (twitterTitle) {
      twitterTitle.setAttribute('content', t('seo.title'))
    }

    const twitterDescription = document.querySelector('meta[property="twitter:description"]')
    if (twitterDescription) {
      twitterDescription.setAttribute('content', t('seo.description'))
    }

    // Remove existing hreflang links
    const existingHreflangs = document.querySelectorAll('link[hreflang]')
    existingHreflangs.forEach(link => link.remove())

    // Add hreflang links for SEO
    const baseUrl = 'https://csv2mt.com'
    const path = location.pathname.replace(/^\/(en|pl)/, '') || '/'

    // Add hreflang for English
    const enLink = document.createElement('link')
    enLink.rel = 'alternate'
    enLink.hreflang = 'en'
    enLink.href = `${baseUrl}/en${path}`
    document.head.appendChild(enLink)

    // Add hreflang for Polish
    const plLink = document.createElement('link')
    plLink.rel = 'alternate'
    plLink.hreflang = 'pl'
    plLink.href = `${baseUrl}/pl${path}`
    document.head.appendChild(plLink)

    // Add x-default for international/fallback
    const defaultLink = document.createElement('link')
    defaultLink.rel = 'alternate'
    defaultLink.hreflang = 'x-default'
    defaultLink.href = `${baseUrl}/en${path}`
    document.head.appendChild(defaultLink)

    // Update canonical URL
    const canonicalLink = document.querySelector('link[rel="canonical"]')
    if (canonicalLink) {
      canonicalLink.setAttribute('href', `${baseUrl}/${currentLang}${path}`)
    } else {
      const newCanonical = document.createElement('link')
      newCanonical.rel = 'canonical'
      newCanonical.href = `${baseUrl}/${currentLang}${path}`
      document.head.appendChild(newCanonical)
    }

  }, [t, i18n.language, location.pathname, currentLang])

  return null // This component doesn't render anything
}
