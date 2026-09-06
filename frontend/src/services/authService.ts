import type { User, Role, Permission } from '../types/user'
import { api, ApiError } from '../lib/api'

export interface LoginCredentials {
  email: string
  password?: string
  accountType?: 'internal' | 'customer'
  remember?: boolean
}

export interface SignupData {
  name: string
  email: string
  password?: string
  accountType?: 'internal' | 'customer'
}

export interface AuthSession {
  user: User
  token: string
  expiresAt: number
}

export interface AuthResponse {
  user: User
  token: string
}

const SESSION_STORAGE_KEY = 'dealflow360_auth_session'

export class AuthService {
  /**
   * Reads persistent authenticated session from localStorage.
   */
  getSession(): AuthSession | null {
    try {
      const raw = localStorage.getItem(SESSION_STORAGE_KEY)
      if (!raw) return null
      const parsed = JSON.parse(raw) as AuthSession
      if (parsed.expiresAt && Date.now() > parsed.expiresAt) {
        this.clearSession()
        return null
      }
      if (parsed.token) {
        api.setToken(parsed.token)
      }
      return parsed
    } catch {
      this.clearSession()
      return null
    }
  }

  /**
   * Stores authenticated session in localStorage.
   */
  setSession(session: AuthSession): void {
    try {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
      api.setToken(session.token)
    } catch {
      // Storage unavailable or quota exceeded
    }
  }

  /**
   * Clears session from localStorage.
   */
  clearSession(): void {
    try {
      localStorage.removeItem(SESSION_STORAGE_KEY)
      api.setToken(null)
    } catch {
      // Ignore
    }
  }

  /**
   * Authenticate user with live FastAPI backend.
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const emailLower = credentials.email.trim().toLowerCase()
    if (!emailLower || !emailLower.includes('@')) {
      throw new Error('Please enter a valid work email address.')
    }
    if (!credentials.password) {
      throw new Error('Please enter your password.')
    }

    try {
      // 1. Authenticate with backend /api/v1/auth/login
      const tokenResp = await api.auth.login({
        email: emailLower,
        password: credentials.password,
      })

      const accessToken = tokenResp.access_token
      api.setToken(accessToken)

      // 2. Fetch authenticated user profile from /api/v1/auth/me
      const profile = await api.auth.me()

      const roleNames: string[] = profile.roles || []
      const isCustomer =
        credentials.accountType === 'customer' ||
        roleNames.some((r) => r.toLowerCase().includes('customer'))

      const role: Role = isCustomer ? 'Customer' : 'Account Executive'
      const permissions: Permission[] = isCustomer
        ? ['request:read']
        : ['request:create', 'request:read', 'request:edit', 'request:approve', 'analytics:read']

      const firstName = profile.first_name || ''
      const lastName = profile.last_name || ''
      const fullName = `${firstName} ${lastName}`.trim() || emailLower.split('@')[0]
      const initials = `${firstName[0] || 'D'}${lastName[0] || 'F'}`.toUpperCase()

      const user: User = {
        id: String(profile.id),
        name: fullName,
        email: profile.email,
        role,
        initials,
        department: isCustomer ? 'Client Organization' : 'Commercial Operations',
        permissions,
        createdAt: profile.created_at || new Date().toISOString(),
      }

      const session: AuthSession = {
        user,
        token: accessToken,
        expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000,
      }

      this.setSession(session)
      return { user, token: accessToken }
    } catch (err: any) {
      this.clearSession()
      if (err instanceof ApiError) {
        throw new Error(err.detail || 'Invalid email or password.')
      }
      throw new Error(err?.message || 'Login failed. Please verify credentials.')
    }
  }

  /**
   * Register a new user with live FastAPI backend.
   */
  async signup(data: SignupData): Promise<AuthResponse> {
    const emailLower = data.email.trim().toLowerCase()
    if (!emailLower || !emailLower.includes('@')) {
      throw new Error('Please enter a valid work email address.')
    }
    if (!data.password || data.password.length < 8) {
      throw new Error('Password must be at least 8 characters.')
    }

    const parts = data.name.trim().split(' ')
    const firstName = parts[0] || 'New'
    const lastName = parts.slice(1).join(' ') || 'User'

    try {
      await api.auth.register({
        email: emailLower,
        password: data.password,
        first_name: firstName,
        last_name: lastName,
      })

      // Automatically log in after registration
      return await this.login({
        email: emailLower,
        password: data.password,
        accountType: data.accountType,
      })
    } catch (err: any) {
      if (err instanceof ApiError) {
        throw new Error(err.detail || 'Registration failed.')
      }
      throw new Error(err?.message || 'Registration failed. Please try again.')
    }
  }

  /**
   * Terminate session on backend and clear local state.
   */
  async logout(): Promise<void> {
    try {
      await api.auth.logout()
    } catch {
      // Ignore network errors on logout
    } finally {
      this.clearSession()
    }
  }

  /**
   * Mock password reset request.
   */
  async requestPasswordReset(email: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 500))
    const emailLower = email.trim().toLowerCase()
    if (!emailLower || !emailLower.includes('@')) {
      throw new Error('Please enter a valid work email address.')
    }
    return true
  }

  /**
   * Mock password reset completion.
   */
  async resetPassword(newPassword: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 500))
    if (!newPassword || newPassword.length < 6) {
      throw new Error('Password must be at least 6 characters.')
    }
    return true
  }

  /**
   * Mock change password for active profile.
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 500))
    if (!currentPassword) {
      throw new Error('Current password is required.')
    }
    if (!newPassword || newPassword.length < 6) {
      throw new Error('New password must be at least 6 characters.')
    }
    return true
  }

  /**
   * Role check helper.
   */
  hasRole(user: User | null, allowedRoles: Role[]): boolean {
    if (!user) return false
    return allowedRoles.includes(user.role)
  }

  /**
   * Permission check helper.
   */
  hasPermission(user: User | null, permission: Permission): boolean {
    if (!user) return false
    return user.permissions.includes(permission)
  }
}

export const authService = new AuthService()
export default authService
