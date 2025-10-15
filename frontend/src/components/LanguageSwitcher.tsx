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
      className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-gray-100 transition-colors"
      aria-label={ariaLabel}
      title={ariaLabel}
    >
      {targetLang === 'en' ? (
        // US Flag (switch to English)
        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none">
          <g clipPath="url(#clip0)">
            <rect width="24" height="24" rx="12" fill="#B22234"/>
            <path d="M0 2.769h24M0 5.538h24M0 8.308h24M0 11.077h24M0 13.846h24M0 16.615h24M0 19.385h24M0 22.154h24" stroke="white" strokeWidth="1.846"/>
            <rect width="10.154" height="11.077" fill="#3C3B6E"/>
            <g fill="white">
              <circle cx="2.077" cy="2.077" r="0.462"/>
              <circle cx="4.154" cy="2.077" r="0.462"/>
              <circle cx="6.231" cy="2.077" r="0.462"/>
              <circle cx="8.308" cy="2.077" r="0.462"/>
              <circle cx="3.115" cy="3.462" r="0.462"/>
              <circle cx="5.192" cy="3.462" r="0.462"/>
              <circle cx="7.269" cy="3.462" r="0.462"/>
              <circle cx="2.077" cy="4.846" r="0.462"/>
              <circle cx="4.154" cy="4.846" r="0.462"/>
              <circle cx="6.231" cy="4.846" r="0.462"/>
              <circle cx="8.308" cy="4.846" r="0.462"/>
              <circle cx="3.115" cy="6.231" r="0.462"/>
              <circle cx="5.192" cy="6.231" r="0.462"/>
              <circle cx="7.269" cy="6.231" r="0.462"/>
              <circle cx="2.077" cy="7.615" r="0.462"/>
              <circle cx="4.154" cy="7.615" r="0.462"/>
              <circle cx="6.231" cy="7.615" r="0.462"/>
              <circle cx="8.308" cy="7.615" r="0.462"/>
              <circle cx="3.115" cy="9" r="0.462"/>
              <circle cx="5.192" cy="9" r="0.462"/>
              <circle cx="7.269" cy="9" r="0.462"/>
            </g>
          </g>
          <defs>
            <clipPath id="clip0">
              <rect width="24" height="24" rx="12" fill="white"/>
            </clipPath>
          </defs>
        </svg>
      ) : (
        // Polish Flag (switch to Polish)
        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none">
          <g clipPath="url(#clip1)">
            <circle cx="12" cy="12" r="12" fill="white"/>
            <path d="M12 12C12 17.5228 12 24 12 24C18.6274 24 24 18.6274 24 12H12Z" fill="#DC143C"/>
            <path d="M12 12C12 17.5228 12 24 12 24C5.37258 24 0 18.6274 0 12H12Z" fill="#DC143C"/>
            <rect y="12" width="24" height="12" fill="#DC143C"/>
          </g>
          <defs>
            <clipPath id="clip1">
              <rect width="24" height="24" rx="12" fill="white"/>
            </clipPath>
          </defs>
        </svg>
      )}
    </button>
  )
}
