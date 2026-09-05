import { useState, useEffect } from 'react'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import AppShell from './components/AppShell'
import { useAuth } from './hooks/useAuth'

export type AppPage = 'landing' | 'login' | 'app'

export default function App() {
  const { user, isAuthenticated, logout } = useAuth()
  const [page, setPage] = useState<AppPage>(() => {
    // If already authenticated via restored session, go directly to app
    return isAuthenticated ? 'app' : 'landing'
  })
  const [initialView, setInitialView] = useState<'command' | 'portal'>('command')

  // Keep page in sync with authentication status
  useEffect(() => {
    if (isAuthenticated) {
      setPage('app')
      setInitialView(user?.role === 'Customer' ? 'portal' : 'command')
    }
  }, [isAuthenticated, user?.role])

  const handleLoginSuccess = (accountType: 'internal' | 'customer') => {
    setInitialView(accountType === 'customer' ? 'portal' : 'command')
    setPage('app')
  }

  const handleLogout = async () => {
    await logout()
    setPage('login')
  }

  // Unauthenticated states
  if (!isAuthenticated && page === 'landing') {
    return (
      <LandingPage
        onLogin={() => setPage('login')}
        onGetStarted={() => setPage('login')}
      />
    )
  }

  if (!isAuthenticated && page === 'login') {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        onBack={() => setPage('landing')}
      />
    )
  }

  // Protected application state
  return (
    <AppShell
      currentUser={user || undefined}
      initialView={initialView}
      onLogout={handleLogout}
    />
  )
}
