import { SignUp } from '@clerk/clerk-react'
import AppHeader from '../components/AppHeader'

export default function SignUpPage() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      <AppHeader showNavLinks={true} />

      <div style={{
        maxWidth: '500px',
        margin: '0 auto',
        padding: '60px 20px 20px 20px'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{
            fontSize: '36px',
            fontWeight: 'bold',
            color: '#1a1a1a',
            marginBottom: '12px'
          }}>
            Create your account
          </h1>
          <p style={{
            fontSize: '16px',
            color: '#666',
            margin: 0
          }}>
            Join us to start converting your bank statements effortlessly.
          </p>
        </div>

        <SignUp
          routing="path"
          path="/sign-up"
          signInUrl="/sign-in"
          forceRedirectUrl="/convert"
          fallbackRedirectUrl="/convert"
          appearance={{
            elements: {
              rootBox: {
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
              },
              card: {
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                border: 'none',
              },
              headerTitle: {
                display: 'none',
              },
              headerSubtitle: {
                display: 'none',
              },
              socialButtonsBlockButton: {
                border: '1px solid #e5e7eb',
                backgroundColor: 'white',
                color: '#374151',
                '&:hover': {
                  backgroundColor: '#f9fafb',
                },
              },
              formButtonPrimary: {
                backgroundColor: '#2563eb',
                fontSize: '16px',
                padding: '12px',
                '&:hover': {
                  backgroundColor: '#1d4ed8',
                },
              },
              formFieldInput: {
                borderColor: '#e5e7eb',
                '&:focus': {
                  borderColor: '#2563eb',
                  boxShadow: '0 0 0 3px rgba(37, 99, 235, 0.1)',
                },
              },
              footerActionLink: {
                color: '#2563eb',
                '&:hover': {
                  color: '#1d4ed8',
                },
              },
            },
          }}
        />
      </div>
    </div>
  )
}
