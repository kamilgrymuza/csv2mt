import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as Sentry from '@sentry/react'
import App from './App.tsx'
import './index.css'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN
const ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT || 'development'

if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key")
}

// Initialize Sentry only for staging and production environments
if (['staging', 'production'].includes(ENVIRONMENT) && SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: ENVIRONMENT,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: ENVIRONMENT === 'staging' ? 1.0 : 0.1,
    // Session Replay
    replaysSessionSampleRate: ENVIRONMENT === 'staging' ? 1.0 : 0.1,
    replaysOnErrorSampleRate: 1.0,
  })
}

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClerkProvider
      publishableKey={PUBLISHABLE_KEY}
      signInFallbackRedirectUrl="/convert"
      signUpFallbackRedirectUrl="/convert"
      signInForceRedirectUrl="/convert"
      signUpForceRedirectUrl="/convert"
    >
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ClerkProvider>
  </StrictMode>,
)

// Signal to prerenderer that the app is ready
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    document.dispatchEvent(new Event('app-rendered'))
  })
}
