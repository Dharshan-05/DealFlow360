export type Role =
  | 'Admin'
  | 'Sales Director'
  | 'Account Executive'
  | 'Approver'
  | 'Operations'
  | 'Customer'

export type Permission =
  | 'request:create'
  | 'request:read'
  | 'request:edit'
  | 'request:delete'
  | 'approval:review'
  | 'approval:action'
  | 'execution:trigger'
  | 'analytics:view'
  | 'audit:view'
  | 'audit:read'
  | 'audit:read_security'
  | 'notification:read'
  | 'notification:manage'
  | 'settings:read'
  | 'settings:update'


export interface User {
  id: string
  name: string
  email: string
  role: Role
  initials: string
  avatarUrl?: string
  department?: string
  permissions: Permission[]
  createdAt?: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  token: string | null
  isLoading: boolean
  error: string | null
}
