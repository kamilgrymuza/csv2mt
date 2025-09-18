import { SignedIn, SignOutButton, useAuth, useUser } from '@clerk/clerk-react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL

export default function Dashboard() {
  const { getToken } = useAuth()
  const { user } = useUser()

  const { data: userData, isLoading, error } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const token = await getToken()
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return response.data
    },
    enabled: !!getToken
  })

  // Test public endpoint to verify backend connectivity
  const { data: publicTest } = useQuery({
    queryKey: ['publicTest'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/test/public`)
      return response.data
    }
  })

  // Get setup instructions
  const { data: authInfo } = useQuery({
    queryKey: ['authInfo'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/test/auth-info`)
      return response.data
    }
  })

  return (
    <div style={{
      padding: '2rem',
      maxWidth: '800px',
      margin: '0 auto',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <SignedIn>
        <header style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2rem',
          borderBottom: '1px solid #e5e5e5',
          paddingBottom: '1rem'
        }}>
          <h1>Dashboard</h1>
          <SignOutButton>
            <button style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}>
              Sign Out
            </button>
          </SignOutButton>
        </header>

        <div style={{
          display: 'grid',
          gap: '2rem'
        }}>
          <div style={{
            padding: '1.5rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <h3 style={{ marginTop: 0 }}>Welcome back!</h3>
            <p>You're successfully signed in with Clerk.</p>
          </div>

          <div style={{
            padding: '1.5rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <h3 style={{ marginTop: 0 }}>Clerk User Info</h3>
            <p><strong>ID:</strong> {user?.id}</p>
            <p><strong>Email:</strong> {user?.primaryEmailAddress?.emailAddress}</p>
            <p><strong>First Name:</strong> {user?.firstName || 'Not provided'}</p>
            <p><strong>Last Name:</strong> {user?.lastName || 'Not provided'}</p>
            <p><strong>Created:</strong> {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Unknown'}</p>
          </div>

          <div style={{
            padding: '1.5rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <h3 style={{ marginTop: 0 }}>Backend API Integration</h3>
            {isLoading ? (
              <p>Loading user data from backend...</p>
            ) : error ? (
              <div style={{ color: '#dc3545' }}>
                <p><strong>Error connecting to backend:</strong></p>
                <pre style={{
                  backgroundColor: '#f8d7da',
                  padding: '1rem',
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '0.875rem'
                }}>
                  {error.message}
                </pre>
              </div>
            ) : userData ? (
              <div style={{ color: '#198754' }}>
                <p><strong>✓ Successfully connected to backend!</strong></p>
                <p><strong>Backend User ID:</strong> {userData.id}</p>
                <p><strong>Backend Email:</strong> {userData.email}</p>
                <p><strong>Backend Created:</strong> {new Date(userData.created_at).toLocaleDateString()}</p>
              </div>
            ) : (
              <p>No data received from backend</p>
            )}
          </div>

          <div style={{
            padding: '1.5rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <h3 style={{ marginTop: 0 }}>Backend Connectivity Test</h3>
            {publicTest ? (
              <div style={{ color: '#198754' }}>
                <p><strong>✓ Backend is reachable!</strong></p>
                <p>{publicTest.message}</p>
              </div>
            ) : (
              <p>Testing backend connectivity...</p>
            )}
          </div>

          {error && authInfo && (
            <div style={{
              padding: '1.5rem',
              backgroundColor: '#fff3cd',
              borderRadius: '8px',
              border: '1px solid #ffeaa7'
            }}>
              <h3 style={{ marginTop: 0, color: '#856404' }}>🔧 Setup Required</h3>
              <p style={{ color: '#856404' }}>{authInfo.message}</p>
              <ol style={{ color: '#856404', paddingLeft: '1.5rem' }}>
                {authInfo.steps?.map((step: string, index: number) => (
                  <li key={index} style={{ marginBottom: '0.5rem' }}>{step}</li>
                ))}
              </ol>
              <p style={{
                marginTop: '1rem',
                padding: '0.75rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                color: '#495057',
                fontSize: '0.9rem'
              }}>
                <strong>Note:</strong> The authentication system is fully configured and working.
                You just need to add your real Clerk credentials to test the protected endpoints.
              </p>
            </div>
          )}
        </div>
      </SignedIn>
    </div>
  )
}