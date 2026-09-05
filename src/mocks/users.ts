import type { User } from '../types/user'

export const mockCurrentUser: User = {
  id: 'usr_001',
  name: 'Arjun Sharma',
  email: 'arjun.sharma@dealflow360.io',
  role: 'Sales Director',
  initials: 'AS',
  department: 'Commercial Operations',
  permissions: [
    'request:create',
    'request:read',
    'request:edit',
    'approval:review',
    'approval:action',
    'execution:trigger',
    'analytics:view',
    'audit:view',
  ],
  createdAt: '2025-01-15T09:00:00Z',
}

export const mockCustomerUser: User = {
  id: 'usr_002',
  name: 'Rajesh Kumar',
  email: 'rajesh@acme.com',
  role: 'Customer',
  initials: 'RK',
  department: 'Procurement - Acme Corp',
  permissions: ['request:read'],
  createdAt: '2025-03-10T11:00:00Z',
}

export const mockUsers: User[] = [
  mockCurrentUser,
  mockCustomerUser,
  {
    id: 'usr_003',
    name: 'Priya Mehta',
    email: 'priya.mehta@dealflow360.io',
    role: 'Account Executive',
    initials: 'PM',
    department: 'Enterprise Sales',
    permissions: ['request:create', 'request:read', 'request:edit'],
    createdAt: '2025-02-01T08:30:00Z',
  },
  {
    id: 'usr_004',
    name: 'Deepak Nair',
    email: 'deepak.nair@dealflow360.io',
    role: 'Approver',
    initials: 'DN',
    department: 'Finance & Risk',
    permissions: ['request:read', 'approval:review', 'approval:action'],
    createdAt: '2024-11-20T14:15:00Z',
  },
]
