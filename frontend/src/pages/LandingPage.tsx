import { useNavigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { Button } from '../components/ui/button'
import AppHeader from '../components/AppHeader'

export default function LandingPage() {
  const navigate = useNavigate()
  const { isSignedIn } = useAuth()

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
                Convert Bank Statements to MT940 Instantly
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                Seamlessly convert your bank statements from CSV or PDF format to the standard MT940 format. Our tool simplifies your financial data processing.
              </p>
            </div>

            {/* Right side - Converter Card */}
            <div className="bg-white rounded-lg shadow-xl p-8">
              <div className="space-y-6">
                {/* Bank Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select your bank
                  </label>
                  <select
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled
                  >
                    <option>Alior Bank</option>
                  </select>
                </div>

                {/* File Upload Area */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
                  <div className="text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <p className="mt-2 text-base text-gray-900 font-medium">
                      Drag and drop your files here
                    </p>
                    <p className="mt-1 text-sm text-gray-500">
                      or <span className="text-blue-600 cursor-pointer">browse from disk</span>
                    </p>
                  </div>
                </div>

                {/* Convert Button */}
                <Button
                  variant="primary"
                  className="w-full py-3"
                  onClick={() => isSignedIn ? navigate('/convert') : navigate('/sign-in')}
                >
                  Convert Files
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
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Key Features</h2>
            <p className="text-xl text-gray-600">
              Our platform is designed to make your financial data management as simple and efficient as possible.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Multi-Format Support</h3>
              <p className="text-gray-600">
                Convert both CSV and PDF bank statements effortlessly.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Secure & Private</h3>
              <p className="text-gray-600">
                Your data is processed securely and never stored on our servers.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Batch Conversion</h3>
              <p className="text-gray-600">
                Convert multiple files at once with our premium plan.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-gray-600">
              Choose the plan that's right for you. Get started for free.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Free Plan */}
            <div className="bg-white rounded-lg border-2 border-gray-200 p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Free</h3>
              <p className="text-gray-600 mb-6">Perfect for occasional conversions.</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-900">$0</span>
                <span className="text-gray-600"> / month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Up to 5 conversions
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Basic support
                </li>
              </ul>
              <Button
                variant="secondary"
                className="w-full"
                onClick={() => navigate('/sign-up')}
              >
                Get Started
              </Button>
            </div>

            {/* Premium Plan */}
            <div className="bg-white rounded-lg border-2 border-blue-500 p-8 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                MOST POPULAR
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Premium</h3>
              <p className="text-gray-600 mb-6">For professionals and businesses.</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-900">$4.99</span>
                <span className="text-gray-600"> / month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Unlimited conversions
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Batch processing
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Priority support
                </li>
              </ul>
              <Button
                variant="primary"
                className="w-full"
                onClick={() => isSignedIn ? navigate('/subscription') : navigate('/sign-up')}
              >
                Go Premium
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Loved by Accountants & Businesses</h2>
            <p className="text-xl text-gray-600">
              Don't just take our word for it. Here's what our users say.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Testimonial 1 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <p className="text-gray-700 mb-6 italic">
                "This tool is a lifesaver! It saves me hours of manual data entry every month. Highly recommended for any accountant."
              </p>
              <div className="flex items-center">
                <div className="h-12 w-12 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                  JD
                </div>
                <div className="ml-4">
                  <p className="font-bold text-gray-900">Jane Doe</p>
                  <p className="text-sm text-gray-600">Certified Accountant</p>
                </div>
              </div>
            </div>

            {/* Testimonial 2 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <p className="text-gray-700 mb-6 italic">
                "Simple, fast, and does exactly what it promises. The premium plan is a no-brainer for the price."
              </p>
              <div className="flex items-center">
                <div className="h-12 w-12 rounded-full bg-green-500 flex items-center justify-center text-white font-bold">
                  JS
                </div>
                <div className="ml-4">
                  <p className="font-bold text-gray-900">John Smith</p>
                  <p className="text-sm text-gray-600">Small Business Owner</p>
                </div>
              </div>
            </div>

            {/* Testimonial 3 */}
            <div className="bg-white rounded-lg p-8 shadow-sm">
              <p className="text-gray-700 mb-6 italic">
                "I was skeptical at first, but the accuracy of the PDF conversion is impressive. It handles complex statements with ease."
              </p>
              <div className="flex items-center">
                <div className="h-12 w-12 rounded-full bg-purple-500 flex items-center justify-center text-white font-bold">
                  EW
                </div>
                <div className="ml-4">
                  <p className="font-bold text-gray-900">Emily White</p>
                  <p className="text-sm text-gray-600">Freelance Bookkeeper</p>
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
            Ready for unlimited conversions?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Register now and unlock unlimited file conversions, batch processing, and priority support with our premium plan.
          </p>
          <Button
            variant="secondary"
            className="bg-white text-blue-600 hover:bg-gray-100 px-8 py-3 text-lg"
            onClick={() => navigate('/sign-up')}
          >
            Register for Premium
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <p className="text-sm">© 2024 Statement Converter. All rights reserved.</p>
          <div className="flex space-x-6">
            <a href="#" className="text-sm hover:text-white">Privacy Policy</a>
            <a href="#" className="text-sm hover:text-white">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
