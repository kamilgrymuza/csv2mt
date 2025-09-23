import { SignedIn, SignedOut, SignInButton, SignUpButton } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import SimpleConverter from './SimpleConverter'
import { Button } from '../components/ui/button'
import { Card, CardContent } from '../components/ui/card'

export default function Home() {
  return (
    <>
      <SignedOut>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <h1 className="text-xl font-semibold text-gray-900">CSV2MT</h1>
                <div className="flex items-center space-x-4">
                  <SignInButton mode="modal">
                    <Button variant="ghost">
                      Sign In
                    </Button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <Button variant="primary">
                      Sign Up
                    </Button>
                  </SignUpButton>
                </div>
              </div>
            </div>
          </header>

          <main className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                CSV to MT940 Converter
              </h2>
              <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
                Transform your bank statement CSV files into standard MT940 format
                for seamless integration with accounting software.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">📊 Multiple Banks</h3>
                    <p className="text-gray-600">Support for various bank CSV formats including Santander</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">⚡ Instant Conversion</h3>
                    <p className="text-gray-600">Fast and accurate conversion to standard MT940 format</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">🔒 Secure & Private</h3>
                    <p className="text-gray-600">No data stored - files processed in memory only</p>
                  </CardContent>
                </Card>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <SignInButton mode="redirect" forceRedirectUrl="/convert">
                  <Button variant="primary" size="lg">
                    Sign In
                  </Button>
                </SignInButton>
                <Link to="/sign-up">
                  <Button variant="secondary" size="lg">
                    Sign Up
                  </Button>
                </Link>
              </div>
            </div>
          </main>
        </div>
      </SignedOut>

      <SignedIn>
        <SimpleConverter />
      </SignedIn>
    </>
  )
}