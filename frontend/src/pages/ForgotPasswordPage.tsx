import { SignIn } from '@clerk/clerk-react'

export default function ForgotPasswordPage() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5'
    }}>
      <SignIn
        routing="path"
        path="/forgot-password"
        signUpUrl="/sign-up"
        initialValues={{ emailAddress: '' }}
        appearance={{
          elements: {
            headerTitle: 'Reset your password',
            headerSubtitle: 'Enter your email address and we\'ll send you a link to reset your password.'
          }
        }}
      />
    </div>
  )
}