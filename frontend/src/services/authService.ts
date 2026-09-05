import type { User, Role, Permission } from '../types/user'
import { mockCurrentUser, mockCustomerUser, mockUsers } from '../mocks/users'

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
   * Reads persistent mock session from localStorage.
   */
  getSession(): AuthSession | null {
    try {
      const raw = localStorage.getItem(SESSION_STORAGE_KEY)
      if (!raw) return null
      const parsed = JSON.parse(raw) as AuthSession
      // Check expiration if set (default 7 days)
      if (parsed.expiresAt && Date.now() > parsed.expiresAt) {
        this.clearSession()
        return null
      }
      return parsed
    } catch {
      this.clearSession()
      return null
    }
  }

  /**
   * Stores mock session in localStorage.
   */
  setSession(session: AuthSession): void {
    try {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
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
    } catch {
      // Ignore
    }
  }

  /**
   * Mock login authenticating against mock users.
   * Resolves in a realistic 500ms delay.
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    await new Promise((resolve) => setTimeout(resolve, 500))

    const emailLower = credentials.email.trim().toLowerCase()

    // Validate email format
    if (!emailLower || !emailLower.includes('@')) {
      throw new Error('Please enter a valid work email address.')
    }

    // Match against mock users or create session matching accountType
    let matchedUser = mockUsers.find((u) => u.email.toLowerCase() === emailLower)

    if (!matchedUser) {
      if (credentials.accountType === 'customer') {
        matchedUser = mockCustomerUser
      } else {
        // Allow login with demo default if credentials match demo or standard format
        matchedUser = mockCurrentUser
      }
    }

    const session: AuthSession = {
      user: matchedUser,
      token: `mock-jwt-${Date.now()}-${matchedUser.id}`,
      expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000, // 7 days
    }

    this.setSession(session)
    return { user: session.user, token: session.token }
  }

  /**
   * Mock signup creating a new user and session.
   */
  async signup(data: SignupData): Promise<AuthResponse> {
    await new Promise((resolve) => setTimeout(resolve, 600))

    const emailLower = data.email.trim().toLowerCase()
    if (!emailLower || !emailLower.includes('@')) {
      throw new Error('Please enter a valid work email address.')
    }

    const role: Role = data.accountType === 'customer' ? 'Customer' : 'Account Executive'
    const permissions: Permission[] =
      data.accountType === 'customer'
        ? ['request:read']
        : ['request:create', 'request:read', 'request:edit']

    const initials = data.name
      .split(' ')
      .map((part) => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'DF'

    const newUser: User = {
      id: `usr_${Date.now()}`,
      name: data.name.trim(),
      email: emailLower,
      role,
      initials,
      department: data.accountType === 'customer' ? 'Client Organization' : 'Sales & Commercial',
      permissions,
      createdAt: new Date().toISOString(),
    }

    const session: AuthSession = {
      user: newUser,
      token: `mock-jwt-${Date.now()}-${newUser.id}`,
      expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000,
    }

    this.setSession(session)
    return { user: session.user, token: session.token }
  }

  /**
   * Mock logout clearing session.
   */
  async logout(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 200))
    this.clearSession()
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
