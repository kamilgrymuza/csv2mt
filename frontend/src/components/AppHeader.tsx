import { useNavigate } from 'react-router-dom'
import { SignedIn, SignedOut, SignOutButton } from '@clerk/clerk-react'
import { Button } from './ui/button'

interface AppHeaderProps {
  showNavLinks?: boolean
}

export default function AppHeader({ showNavLinks = false }: AppHeaderProps) {
  const navigate = useNavigate()

  const scrollToSection = (sectionId: string) => {
    // If we're not on the landing page, navigate there first
    if (window.location.pathname !== '/') {
      navigate('/')
      // Wait for navigation to complete, then scroll
      setTimeout(() => {
        const element = document.getElementById(sectionId)
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' })
        }
      }, 100)
    } else {
      const element = document.getElementById(sectionId)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }
  }

  const handleLogoClick = () => {
    if (window.location.pathname === '/') {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      navigate('/')
    }
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center h-16">
          <button
            onClick={handleLogoClick}
            className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
          >
            <svg className="h-8 w-8 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
            </svg>
            <h1 className="text-xl font-bold text-gray-900">Statement Converter</h1>
          </button>

          <div className="flex items-center space-x-6">
            {showNavLinks && (
              <>
                <button
                  onClick={() => scrollToSection('features')}
                  className="text-gray-600 hover:text-gray-900 font-medium"
                >
                  Features
                </button>
                <button
                  onClick={() => scrollToSection('pricing')}
                  className="text-gray-600 hover:text-gray-900 font-medium"
                >
                  Pricing
                </button>
                <button
                  onClick={() => scrollToSection('testimonials')}
                  className="text-gray-600 hover:text-gray-900 font-medium"
                >
                  Testimonials
                </button>
              </>
            )}

            <SignedOut>
              <Button
                variant="primary"
                onClick={() => navigate('/sign-in')}
              >
                Log in
              </Button>
            </SignedOut>

            <SignedIn>
              <Button
                variant="secondary"
                onClick={() => navigate('/convert')}
              >
                Converter
              </Button>
              <Button
                variant="secondary"
                onClick={() => navigate('/subscription')}
              >
                Subscription
              </Button>
              <SignOutButton>
                <Button variant="danger">
                  Sign Out
                </Button>
              </SignOutButton>
            </SignedIn>
          </div>
        </div>
      </div>
    </header>
  )
}
