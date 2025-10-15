import { BrowserRouter as Router, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/react'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import LandingPage from './pages/LandingPage'
import SignInPage from './pages/SignInPage'
import SignUpPage from './pages/SignUpPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import Dashboard from './pages/Dashboard'
import SimpleConverter from './pages/SimpleConverter'
import SubscriptionPage from './pages/SubscriptionPage'
import ProtectedRoute from './components/ProtectedRoute'
import SEOHead from './components/SEOHead'
import './App.css'

// Component to handle language detection and redirect
function LanguageRedirect() {
  const navigate = useNavigate()

  useEffect(() => {
    // Detect browser language
    const browserLang = navigator.language.split('-')[0]
    const defaultLang = ['en', 'pl'].includes(browserLang) ? browserLang : 'en'

    // Check if user has a stored preference
    const storedLang = localStorage.getItem('i18nextLng')
    const targetLang = storedLang && ['en', 'pl'].includes(storedLang) ? storedLang : defaultLang

    // Redirect to language-specific home
    navigate(`/${targetLang}/`, { replace: true })
  }, [navigate])

  return null
}

// Wrapper component to sync URL language with i18n
function LanguageWrapper({ children }: { children: React.ReactNode }) {
  const { lang } = useParams<{ lang: string }>()
  const { i18n } = useTranslation()

  useEffect(() => {
    if (lang && ['en', 'pl'].includes(lang) && i18n.language !== lang) {
      i18n.changeLanguage(lang)
    }
  }, [lang, i18n])

  return (
    <>
      <SEOHead />
      {children}
    </>
  )
}

function App() {
  return (
    <>
      <Router>
        <Routes>
          {/* Root redirect to language-specific home */}
          <Route path="/" element={<LanguageRedirect />} />

          {/* Language-specific routes */}
          <Route path="/:lang/*" element={
            <LanguageWrapper>
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route
                  path="/convert"
                  element={
                    <ProtectedRoute>
                      <SimpleConverter />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/subscription"
                  element={
                    <ProtectedRoute>
                      <SubscriptionPage />
                    </ProtectedRoute>
                  }
                />
                <Route path="/sign-in/*" element={<SignInPage />} />
                <Route path="/sign-up/*" element={<SignUpPage />} />
                <Route path="/forgot-password/*" element={<ForgotPasswordPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </LanguageWrapper>
          } />

          {/* Fallback redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>

      {/* Vercel Analytics - tracks page views and custom events */}
      <Analytics />

      {/* Vercel Speed Insights - monitors real-user performance metrics */}
      <SpeedInsights />
    </>
  )
}

export default App
