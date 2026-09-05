import { useState, useCallback, useEffect } from 'react'
import type { User, Role, Permission } from '../types/user'
import {
  authService,
  type LoginCredentials,
  type SignupData,
} from '../services/authService'

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => {
    const session = authService.getSession()
    return session ? session.user : null
  })
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return !!authService.getSession()
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Listen for storage changes in other tabs
  useEffect(() => {
    const handleStorage = () => {
      const session = authService.getSession()
      setUser(session ? session.user : null)
      setIsAuthenticated(!!session)
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await authService.login(credentials)
      setUser(response.user)
      setIsAuthenticated(true)
      return response.user
    } catch (err: any) {
      const msg = err?.message || 'Authentication failed. Please check your credentials.'
      setError(msg)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const signup = useCallback(async (data: SignupData) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await authService.signup(data)
      setUser(response.user)
      setIsAuthenticated(true)
      return response.user
    } catch (err: any) {
      const msg = err?.message || 'Registration failed.'
      setError(msg)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    setIsLoading(true)
    try {
      await authService.logout()
      setUser(null)
      setIsAuthenticated(false)
      setError(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const requestPasswordReset = useCallback(async (email: string) => {
    setIsLoading(true)
    setError(null)
    try {
      return await authService.requestPasswordReset(email)
    } catch (err: any) {
      setError(err?.message || 'Password reset request failed.')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const resetPassword = useCallback(async (newPassword: string) => {
    setIsLoading(true)
    setError(null)
    try {
      return await authService.resetPassword(newPassword)
    } catch (err: any) {
      setError(err?.message || 'Failed to update password.')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      setIsLoading(true)
      setError(null)
      try {
        return await authService.changePassword(currentPassword, newPassword)
      } catch (err: any) {
        setError(err?.message || 'Password update failed.')
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  const hasRole = useCallback(
    (allowedRoles: Role[]) => {
      return authService.hasRole(user, allowedRoles)
    },
    [user]
  )

  const hasPermission = useCallback(
    (permission: Permission) => {
      return authService.hasPermission(user, permission)
    },
    [user]
  )

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    signup,
    logout,
    requestPasswordReset,
    resetPassword,
    changePassword,
    hasRole,
    hasPermission,
    clearError: () => setError(null),
  }
}

export default useAuth
