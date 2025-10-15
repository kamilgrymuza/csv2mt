import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'

export default function LanguageSwitcher() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  const changeLanguage = (lng: string) => {
    // Get current path without language prefix
    const pathWithoutLang = location.pathname.replace(/^\/(en|pl)/, '')

    // Change language in i18n
    i18n.changeLanguage(lng)

    // Navigate to new language path
    const newPath = `/${lng}${pathWithoutLang || '/'}`
    navigate(newPath)
  }

  const currentLang = i18n.language

  // Show the flag of the OTHER language (the one to switch to)
  const targetLang = currentLang === 'en' ? 'pl' : 'en'
  const ariaLabel = targetLang === 'en' ? 'Switch to English' : 'Przełącz na polski'

  return (
    <button
      onClick={() => changeLanguage(targetLang)}
      className="flex items-center justify-center hover:opacity-80 transition-opacity"
      aria-label={ariaLabel}
      title={ariaLabel}
    >
      {targetLang === 'en' ? (
        // US Flag (switch to English)
        <svg className="w-8 h-6 border border-gray-300 rounded" viewBox="0 0 32 24" fill="none">
          <rect width="32" height="24" fill="#B22234" rx="2"/>
          <path d="M0 2.769h32M0 5.538h32M0 8.308h32M0 11.077h32M0 13.846h32M0 16.615h32M0 19.385h32M0 22.154h32" stroke="white" strokeWidth="1.846"/>
          <rect width="13.538" height="11.077" fill="#3C3B6E" rx="1"/>
          <g fill="white">
            <circle cx="2.769" cy="2.077" r="0.5"/>
            <circle cx="5.538" cy="2.077" r="0.5"/>
            <circle cx="8.308" cy="2.077" r="0.5"/>
            <circle cx="11.077" cy="2.077" r="0.5"/>
            <circle cx="4.154" cy="3.692" r="0.5"/>
            <circle cx="6.923" cy="3.692" r="0.5"/>
            <circle cx="9.692" cy="3.692" r="0.5"/>
            <circle cx="2.769" cy="5.308" r="0.5"/>
            <circle cx="5.538" cy="5.308" r="0.5"/>
            <circle cx="8.308" cy="5.308" r="0.5"/>
            <circle cx="11.077" cy="5.308" r="0.5"/>
            <circle cx="4.154" cy="6.923" r="0.5"/>
            <circle cx="6.923" cy="6.923" r="0.5"/>
            <circle cx="9.692" cy="6.923" r="0.5"/>
            <circle cx="2.769" cy="8.538" r="0.5"/>
            <circle cx="5.538" cy="8.538" r="0.5"/>
            <circle cx="8.308" cy="8.538" r="0.5"/>
            <circle cx="11.077" cy="8.538" r="0.5"/>
          </g>
        </svg>
      ) : (
        // Polish Flag (switch to Polish)
        <svg className="w-8 h-6 border border-gray-300 rounded" viewBox="0 0 32 24" fill="none">
          <rect width="32" height="24" fill="white" rx="2"/>
          <rect y="12" width="32" height="12" fill="#DC143C"/>
        </svg>
      )}
    </button>
  )
}
