/**
 * DealFlow360 Centralized Application Constants
 * Authoritative constants across workflow, status, risk, and roles.
 */

// Request Workflow Statuses
export const REQUEST_STATUS = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  IN_REVIEW: 'In Review',
  PENDING_APPROVAL: 'Pending Approval',
  READY_FOR_APPROVAL: 'Ready for Approval',
  APPROVED: 'Approved',
  EXECUTING: 'Executing',
  ODOO_PROCESSING: 'Odoo Processing',
  COMPLETED: 'Completed',
  REJECTED: 'Rejected',
  CANCELLED: 'Cancelled',
} as const

// Request Priorities
export const REQUEST_PRIORITY = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  CRITICAL: 'Critical',
} as const

// Risk Levels
export const RISK_LEVEL = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  CRITICAL: 'Critical',
} as const

// Approval Decisions & Statuses
export const APPROVAL_STATUS = {
  PENDING: 'Pending',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  CHANGES_REQUESTED: 'Changes Requested',
} as const

// Execution & Odoo Engine Statuses
export const EXECUTION_STATUS = {
  IDLE: 'Idle',
  QUEUED: 'Queued',
  VALIDATING: 'Validating',
  PROCESSING: 'Processing',
  ODOO_SYNC: 'Odoo Processing',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
} as const

// Transaction History Statuses
export const TRANSACTION_STATUS = {
  COMPLETED: 'Completed',
  PROCESSING: 'Processing',
  PENDING: 'Pending',
  FAILED: 'Failed',
} as const

// System User Roles
export const USER_ROLE = {
  ADMIN: 'Admin',
  SALES_DIRECTOR: 'Sales Director',
  ACCOUNT_EXECUTIVE: 'Account Executive',
  APPROVER: 'Approver',
  OPERATIONS: 'Operations',
  CUSTOMER: 'Customer',
} as const

// Figma Design System Color Palette for Badges & Statuses
export const STATUS_COLORS = {
  // Risk colors
  Critical: {
    text: '#EF4444',
    bg: 'rgba(239, 68, 68, 0.08)',
    border: 'rgba(239, 68, 68, 0.22)',
  },
  High: {
    text: '#F97316',
    bg: 'rgba(249, 115, 22, 0.08)',
    border: 'rgba(249, 115, 22, 0.22)',
  },
  Medium: {
    text: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.08)',
    border: 'rgba(245, 158, 11, 0.22)',
  },
  Low: {
    text: '#10B981',
    bg: 'rgba(16, 185, 129, 0.08)',
    border: 'rgba(16, 185, 129, 0.22)',
  },
  // Workflow states
  Draft: {
    text: '#A1A1AA',
    bg: '#141414',
    border: '#242424',
  },
  Submitted: {
    text: '#60A5FA',
    bg: 'rgba(96, 165, 250, 0.10)',
    border: 'rgba(96, 165, 250, 0.22)',
  },
  'Under Review': {
    text: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.10)',
    border: 'rgba(245, 158, 11, 0.20)',
  },
  'In Review': {
    text: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.10)',
    border: 'rgba(245, 158, 11, 0.20)',
  },
  'Changes Requested': {
    text: '#F97316',
    bg: 'rgba(249, 115, 22, 0.10)',
    border: 'rgba(249, 115, 22, 0.22)',
  },
  'Pending Approval': {
    text: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.10)',
    border: 'rgba(245, 158, 11, 0.20)',
  },
  'Ready for Approval': {
    text: '#A78BFA',
    bg: 'rgba(124, 58, 237, 0.10)',
    border: 'rgba(124, 58, 237, 0.22)',
  },
  Approved: {
    text: '#10B981',
    bg: 'rgba(16, 185, 129, 0.10)',
    border: 'rgba(16, 185, 129, 0.20)',
  },
  Completed: {
    text: '#10B981',
    bg: 'rgba(16, 185, 129, 0.10)',
    border: 'rgba(16, 185, 129, 0.20)',
  },
  Processing: {
    text: '#93C5FD',
    bg: 'rgba(59, 130, 246, 0.10)',
    border: 'rgba(59, 130, 246, 0.20)',
  },
  'Odoo Processing': {
    text: '#A78BFA',
    bg: 'rgba(124, 58, 237, 0.10)',
    border: 'rgba(124, 58, 237, 0.22)',
  },
  Rejected: {
    text: '#EF4444',
    bg: 'rgba(239, 68, 68, 0.10)',
    border: 'rgba(239, 68, 68, 0.22)',
  },
} as const

export const BRAND = {
  name: 'DealFlow360',
  tagline: 'Enterprise Transaction & Request Intelligence Platform',
  version: '1.0.0',
} as const
