import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div style={{
      minHeight: '100vh',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <header style={{
        padding: '1rem 2rem',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e5e5e5',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ margin: 0 }}>CSV2MT</h1>
        <div>
          <SignedOut>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Link
                to="/convert"
                style={{
                  textDecoration: 'none',
                  color: '#007bff',
                  fontWeight: 500
                }}
              >
                Converter
              </Link>
              <SignInButton mode="modal">
                <button style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'transparent',
                  border: '1px solid #007bff',
                  color: '#007bff',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}>
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}>
                  Sign Up
                </button>
              </SignUpButton>
            </div>
          </SignedOut>
          <SignedIn>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Link
                to="/convert"
                style={{
                  textDecoration: 'none',
                  color: '#007bff',
                  fontWeight: 500
                }}
              >
                Converter
              </Link>
              <Link
                to="/dashboard"
                style={{
                  textDecoration: 'none',
                  color: '#007bff',
                  fontWeight: 500
                }}
              >
                Dashboard
              </Link>
              <UserButton />
            </div>
          </SignedIn>
        </div>
      </header>

      <main style={{
        padding: '4rem 2rem',
        textAlign: 'center',
        maxWidth: '800px',
        margin: '0 auto'
      }}>
        <SignedOut>
          <div>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>
              CSV to MT940 Converter
            </h2>
            <p style={{
              fontSize: '1.2rem',
              color: '#666',
              marginBottom: '3rem',
              lineHeight: 1.6
            }}>
              Transform your bank statement CSV files into standard MT940 format
              for seamless integration with accounting software.
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '2rem',
              marginBottom: '3rem'
            }}>
              <div style={{
                padding: '1.5rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
              }}>
                <h3>📊 Multiple Banks</h3>
                <p>Support for various bank CSV formats including Santander</p>
              </div>
              <div style={{
                padding: '1.5rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
              }}>
                <h3>⚡ Instant Conversion</h3>
                <p>Fast and accurate conversion to standard MT940 format</p>
              </div>
              <div style={{
                padding: '1.5rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
              }}>
                <h3>🔒 Secure & Private</h3>
                <p>No data stored - files processed in memory only</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <Link to="/convert">
                <button style={{
                  padding: '0.75rem 2rem',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 500
                }}>
                  Try Converter
                </button>
              </Link>
              <Link to="/sign-up">
                <button style={{
                  padding: '0.75rem 2rem',
                  backgroundColor: 'transparent',
                  border: '1px solid #007bff',
                  color: '#007bff',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 500
                }}>
                  Sign Up
                </button>
              </Link>
            </div>
          </div>
        </SignedOut>

        <SignedIn>
          <div>
            <h2 style={{ fontSize: '2rem', marginBottom: '1rem' }}>
              Welcome back! 👋
            </h2>
            <p style={{
              fontSize: '1.1rem',
              color: '#666',
              marginBottom: '2rem'
            }}>
              You're successfully authenticated. Ready to build something amazing?
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <Link to="/convert">
                <button style={{
                  padding: '0.75rem 2rem',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 500
                }}>
                  Convert Files
                </button>
              </Link>
              <Link to="/dashboard">
                <button style={{
                  padding: '0.75rem 2rem',
                  backgroundColor: 'transparent',
                  border: '1px solid #007bff',
                  color: '#007bff',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 500
                }}>
                  Dashboard
                </button>
              </Link>
            </div>
          </div>
        </SignedIn>
      </main>
    </div>
  )
}