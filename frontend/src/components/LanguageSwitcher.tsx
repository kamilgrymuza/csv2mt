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

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={() => changeLanguage('en')}
        className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
          currentLang === 'en'
            ? 'bg-blue-600 text-white'
            : 'text-gray-700 hover:bg-gray-100'
        }`}
        aria-label="Switch to English"
      >
        EN
      </button>
      <button
        onClick={() => changeLanguage('pl')}
        className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
          currentLang === 'pl'
            ? 'bg-blue-600 text-white'
            : 'text-gray-700 hover:bg-gray-100'
        }`}
        aria-label="Przełącz na polski"
      >
        PL
      </button>
    </div>
  )
}
