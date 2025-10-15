import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import enTranslations from './locales/en.json'
import plTranslations from './locales/pl.json'

// Initialize i18next
i18n
  .use(LanguageDetector) // Detects user language
  .use(initReactI18next) // Passes i18n down to react-i18next
  .init({
    resources: {
      en: {
        translation: enTranslations
      },
      pl: {
        translation: plTranslations
      }
    },
    fallbackLng: 'en', // Fallback language
    supportedLngs: ['en', 'pl'], // Supported languages

    // Language detection options
    detection: {
      // Order of detection methods
      order: ['path', 'localStorage', 'navigator'],
      // Cache user language selection
      caches: ['localStorage'],
      // Look for language in URL path
      lookupFromPathIndex: 0,
    },

    interpolation: {
      escapeValue: false // React already escapes values
    },

    // React options
    react: {
      useSuspense: false // Don't use Suspense for i18n
    }
  })

export default i18n
