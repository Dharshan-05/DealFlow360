export type AuditCategory =
  | 'USER'
  | 'REQUEST'
  | 'AI'
  | 'APPROVAL'
  | 'EXECUTION'
  | 'TRANSACTION'
  | 'SYSTEM'
  | 'SECURITY'
  | 'SETTINGS'
  | 'REPORT'

export type AuditSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type AuditResult = 'SUCCESS' | 'FAILURE' | 'WARNING' | 'DENIED'

export type AuditEventType =
  | 'REQUEST_CREATED'
  | 'REQUEST_SUBMITTED'
  | 'REQUEST_UPDATED'
  | 'VALIDATION_PASSED'
  | 'VALIDATION_FAILED'
  | 'AI_ANALYSIS_COMPLETED'
  | 'AI_RECOMMENDATION_GENERATED'
  | 'APPROVAL_REQUESTED'
  | 'APPROVAL_APPROVED'
  | 'APPROVAL_REJECTED'
  | 'CHANGES_REQUESTED'
  | 'EXECUTION_STARTED'
  | 'EXECUTION_COMPLETED'
  | 'EXECUTION_FAILED'
  | 'ODOO_SYNC_COMPLETED'
  | 'TRANSACTION_CREATED'
  | 'REPORT_GENERATED'
  | 'USER_LOGIN'
  | 'USER_LOGOUT'
  | 'PASSWORD_CHANGED'
  | 'PASSWORD_RESET_REQUESTED'
  | 'SETTINGS_UPDATED'
  | 'PERMISSION_CHECK'
  | 'UNAUTHORIZED_ATTEMPT'
  | 'SYSTEM'
  | 'request_created'
  | 'request_updated'
  | 'validation_passed'
  | 'validation_failed'
  | 'ai_analyzed'
  | 'approval_requested'
  | 'approval_granted'
  | 'approval_rejected'
  | 'execution_started'
  | 'odoo_synced'
  | 'execution_completed'

export interface AuditEvent {
  id: string
  timestamp: string
  category: AuditCategory
  eventType: AuditEventType
  actor: string
  actorRole: string
  actorEmail?: string
  action: string
  resource: string
  resourceId?: string
  severity: AuditSeverity
  result: AuditResult
  description: string
  ipAddress?: string
  userAgent?: string
  details?: string
  metadata?: Record<string, any>
  before?: Record<string, any>
  after?: Record<string, any>
}

// Backwards-compatible alias with Phase 2
export interface AuditLog extends AuditEvent {
  title?: string
  details: string
  actorName?: string
  requestId?: string
}

export interface UserActivityLog {
  id: string
  timestamp: string
  user: string
  role: string
  action: string
  resource: string
  resourceId?: string
  result: AuditResult
  details?: string
}

export interface SystemEvent {
  id: string
  timestamp: string
  module: string
  event: string
  status: 'SUCCESS' | 'RUNNING' | 'FAILED' | 'PENDING'
  reference: string
  duration?: string
  details: string
}

export interface SecurityEvent {
  id: string
  timestamp: string
  event: string
  user: string
  role?: string
  result: 'SUCCESS' | 'FAILED' | 'WARNING'
  severity: AuditSeverity
  sessionStatus: 'ACTIVE' | 'TERMINATED' | 'EXPIRED' | 'BLOCKED'
  ipAddress?: string
  device?: string
  details?: string
}

export interface LoginHistoryItem {
  id: string
  user: string
  role: string
  email: string
  loginTime: string
  logoutTime?: string
  sessionDuration: string
  loginResult: 'SUCCESS' | 'FAILED' | 'BLOCKED'
  device: string
  browser: string
  sessionId: string
  simulatedIp: string
}

export interface DataChangeRecord {
  id: string
  timestamp: string
  actor: string
  actorRole: string
  resource: 'Request' | 'Approval' | 'Transaction' | 'User' | 'Settings'
  resourceId: string
  field: string
  previousValue: string
  newValue: string
  changeReason?: string
  fullDiff?: {
    before: Record<string, any>
    after: Record<string, any>
  }
}

export interface AuditMetrics {
  totalEvents: number
  userActions: number
  systemEvents: number
  securityEvents: number
  dataChanges: number
  loginEvents: number
  failedLogins: number
  highRiskEvents: number
  recentCritical: AuditEvent[]
  categoryDistribution: { category: string; count: number; color: string }[]
  eventTrends: { day: string; count: number }[]
}

export interface AuditFilters {
  search?: string
  category?: string
  eventType?: string
  severity?: string
  actor?: string
  result?: string
  period?: string
  resource?: string
}

