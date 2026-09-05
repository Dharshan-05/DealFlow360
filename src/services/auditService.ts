import type {
  AuditEvent,
  UserActivityLog,
  SystemEvent,
  SecurityEvent,
  LoginHistoryItem,
  DataChangeRecord,
  AuditMetrics,
  AuditFilters,
} from '../types/audit'
import {
  mockAuditEvents,
  mockUserActivities,
  mockSystemEvents,
  mockSecurityEvents,
  mockLoginHistory,
  mockDataChanges,
} from '../mocks/audit'
import { REQUESTS_UPDATED_EVENT } from './requestService'
import { APPROVALS_UPDATED_EVENT } from './approvalService'
import { EXECUTION_UPDATED_EVENT } from './executionService'
import { TRANSACTIONS_UPDATED_EVENT } from './transactionService'

export const AUDIT_STORAGE_KEY = 'dealflow360_audit_logs'
export const AUDIT_UPDATED_EVENT = 'dealflow_audit_updated'

class AuditService {
  private listeners: (() => void)[] = []
  private recentLogSignatures: Set<string> = new Set()

  constructor() {
    if (typeof window !== 'undefined') {
      // Auto-listen to lifecycle events across DealFlow360
      window.addEventListener(REQUESTS_UPDATED_EVENT, () => {
        this.captureWorkflowEvent('REQUEST', 'REQUEST_UPDATED', 'Request modified or advanced in lifecycle')
      })
      window.addEventListener(APPROVALS_UPDATED_EVENT, () => {
        this.captureWorkflowEvent('APPROVAL', 'APPROVAL_APPROVED', 'Governance decision registered')
      })
      window.addEventListener(EXECUTION_UPDATED_EVENT, () => {
        this.captureWorkflowEvent('EXECUTION', 'EXECUTION_COMPLETED', 'Simulated Odoo ERP dispatch updated')
      })
      window.addEventListener(TRANSACTIONS_UPDATED_EVENT, () => {
        this.captureWorkflowEvent('TRANSACTION', 'TRANSACTION_CREATED', 'Financial ledger settlement transaction generated')
      })
      window.addEventListener('dealflow_settings_updated', () => {
        this.captureWorkflowEvent('SETTINGS', 'SETTINGS_UPDATED', 'System workspace settings updated')
      })
    }
  }

  public subscribe(callback: () => void): () => void {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback)
    }
  }

  private notify(): void {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(AUDIT_UPDATED_EVENT))
      this.listeners.forEach((cb) => cb())
    }
  }

  private captureWorkflowEvent(category: any, eventType: any, description: string) {
    const signature = `${category}_${eventType}_${Date.now().toString().slice(0, -3)}`
    if (this.recentLogSignatures.has(signature)) return
    this.recentLogSignatures.add(signature)
    setTimeout(() => this.recentLogSignatures.delete(signature), 3000)

    this.logEvent({
      category,
      eventType,
      actor: 'Active User Session',
      actorRole: 'Sales Director',
      action: description,
      resource: category.charAt(0) + category.slice(1).toLowerCase(),
      severity: 'LOW',
      result: 'SUCCESS',
      description,
      ipAddress: '127.0.0.1 (Localhost)',
    })
  }

  public getAuditEvents(filters?: AuditFilters): AuditEvent[] {
    try {
      const raw = localStorage.getItem(AUDIT_STORAGE_KEY)
      let events: AuditEvent[] = raw ? JSON.parse(raw) : mockAuditEvents
      if (!raw) {
        this.saveAuditEvents(mockAuditEvents)
      }

      if (!filters) return events

      return events.filter((evt) => {
        if (filters.search) {
          const q = filters.search.toLowerCase()
          const matches =
            evt.id.toLowerCase().includes(q) ||
            evt.action.toLowerCase().includes(q) ||
            evt.description.toLowerCase().includes(q) ||
            evt.actor.toLowerCase().includes(q) ||
            (evt.resourceId && evt.resourceId.toLowerCase().includes(q))
          if (!matches) return false
        }
        if (filters.category && filters.category !== 'All' && evt.category !== filters.category) return false
        if (filters.eventType && filters.eventType !== 'All' && evt.eventType !== filters.eventType) return false
        if (filters.severity && filters.severity !== 'All' && evt.severity !== filters.severity) return false
        if (filters.actor && filters.actor !== 'All' && evt.actor !== filters.actor) return false
        if (filters.result && filters.result !== 'All' && evt.result !== filters.result) return false
        if (filters.resource && filters.resource !== 'All' && evt.resource !== filters.resource) return false
        return true
      })
    } catch {
      return mockAuditEvents
    }
  }

  private saveAuditEvents(events: AuditEvent[]): void {
    try {
      localStorage.setItem(AUDIT_STORAGE_KEY, JSON.stringify(events))
      this.notify()
    } catch (e) {
      console.error('Failed to persist audit events', e)
    }
  }

  public logEvent(event: Partial<AuditEvent>): AuditEvent {
    const existing = this.getAuditEvents()
    const newEvent: AuditEvent = {
      id: `EVT-2026-${(existing.length + 9001).toString()}`,
      timestamp: new Date().toISOString(),
      category: event.category || 'SYSTEM',
      eventType: event.eventType || 'SYSTEM',
      actor: event.actor || 'System',
      actorRole: event.actorRole || 'System Agent',
      actorEmail: event.actorEmail,
      action: event.action || 'System Action Executed',
      resource: event.resource || 'System',
      resourceId: event.resourceId,
      severity: event.severity || 'INFO',
      result: event.result || 'SUCCESS',
      description: event.description || 'System event triggered locally.',
      ipAddress: event.ipAddress || '127.0.0.1 (Localhost)',
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      details: event.details,
      metadata: event.metadata,
      before: event.before,
      after: event.after,
    }

    const updated = [newEvent, ...existing]
    if (updated.length > 300) updated.pop()
    this.saveAuditEvents(updated)
    return newEvent
  }

  public getUserActivity(filters?: any): UserActivityLog[] {
    const auditEvents = this.getAuditEvents()
    const userEvents: UserActivityLog[] = auditEvents
      .filter((e) => e.category === 'USER' || e.actor !== 'System Agent' && e.actor !== 'DealFlow360 Copilot Engine')
      .map((e) => ({
        id: `ACT-${e.id.slice(-4)}`,
        timestamp: e.timestamp,
        user: e.actor,
        role: e.actorRole,
        action: e.action,
        resource: e.resource,
        resourceId: e.resourceId,
        result: e.result,
        details: e.description,
      }))

    return userEvents.length > 0 ? userEvents : mockUserActivities
  }

  public getSystemEvents(filters?: any): SystemEvent[] {
    const auditEvents = this.getAuditEvents()
    const sysEvents: SystemEvent[] = auditEvents
      .filter((e) => ['SYSTEM', 'EXECUTION', 'AI', 'TRANSACTION'].includes(e.category))
      .map((e) => ({
        id: `SYS-${e.id.slice(-4)}`,
        timestamp: e.timestamp,
        module: e.category === 'EXECUTION' ? 'Odoo Gateway (Simulated)' : e.category === 'AI' ? 'AI Intelligence Copilot' : 'Core Platform',
        event: e.eventType,
        status: e.result === 'SUCCESS' ? 'SUCCESS' : e.result === 'FAILURE' ? 'FAILED' : 'RUNNING',
        reference: e.resourceId || e.resource,
        duration: e.metadata?.duration || '120ms',
        details: e.description,
      }))

    return sysEvents.length > 0 ? sysEvents : mockSystemEvents
  }

  public getSecurityEvents(filters?: any): SecurityEvent[] {
    const auditEvents = this.getAuditEvents()
    const secEvents: SecurityEvent[] = auditEvents
      .filter((e) => e.category === 'SECURITY' || e.eventType.includes('LOGIN') || e.eventType.includes('PASSWORD') || e.eventType.includes('UNAUTHORIZED'))
      .map((e) => ({
        id: `SEC-${e.id.slice(-4)}`,
        timestamp: e.timestamp,
        event: e.action,
        user: e.actor,
        role: e.actorRole,
        result: e.result === 'SUCCESS' ? 'SUCCESS' : 'FAILED',
        severity: e.severity,
        sessionStatus: e.result === 'SUCCESS' ? 'ACTIVE' : 'BLOCKED',
        ipAddress: e.ipAddress,
        device: e.userAgent ? 'Desktop Browser' : 'Chrome / Windows',
        details: e.description,
      }))

    return secEvents.length > 0 ? secEvents : mockSecurityEvents
  }

  public getLoginHistory(): LoginHistoryItem[] {
    return mockLoginHistory
  }

  public getDataChangeHistory(filters?: any): DataChangeRecord[] {
    const auditEvents = this.getAuditEvents()
    const changes: DataChangeRecord[] = []

    for (const e of auditEvents) {
      if (e.before && e.after) {
        const fields = Object.keys(e.after)
        for (const field of fields) {
          changes.push({
            id: `CHG-${e.id.slice(-4)}`,
            timestamp: e.timestamp,
            actor: e.actor,
            actorRole: e.actorRole,
            resource: e.resource as any,
            resourceId: e.resourceId || e.resource,
            field,
            previousValue: String(e.before[field] ?? 'None'),
            newValue: String(e.after[field] ?? 'None'),
            changeReason: e.description,
            fullDiff: { before: e.before, after: e.after },
          })
        }
      }
    }

    return changes.length > 0 ? [...changes, ...mockDataChanges] : mockDataChanges
  }

  public getAuditMetrics(): AuditMetrics {
    const events = this.getAuditEvents()
    const userActions = events.filter((e) => e.category === 'USER' || (e.actor !== 'System Agent' && e.actor !== 'DealFlow360 Copilot Engine')).length
    const systemEvents = events.filter((e) => ['SYSTEM', 'EXECUTION', 'AI', 'TRANSACTION'].includes(e.category)).length
    const securityEvents = events.filter((e) => e.category === 'SECURITY' || e.eventType.includes('LOGIN')).length
    const dataChanges = events.filter((e) => e.before && e.after).length + mockDataChanges.length
    const loginEvents = events.filter((e) => e.eventType.includes('LOGIN')).length + mockLoginHistory.length
    const failedLogins = events.filter((e) => e.result === 'FAILURE' && e.eventType.includes('LOGIN')).length + 1
    const highRiskEvents = events.filter((e) => e.severity === 'HIGH' || e.severity === 'CRITICAL').length

    const recentCritical = events.filter((e) => e.severity === 'HIGH' || e.severity === 'CRITICAL').slice(0, 5)

    const catCounts: Record<string, number> = {}
    events.forEach((e) => {
      catCounts[e.category] = (catCounts[e.category] || 0) + 1
    })

    const catColors: Record<string, string> = {
      REQUEST: '#6366F1',
      APPROVAL: '#10B981',
      AI: '#8B5CF6',
      EXECUTION: '#3B82F6',
      TRANSACTION: '#06B6D4',
      SECURITY: '#EF4444',
      SETTINGS: '#F59E0B',
      SYSTEM: '#71717A',
      USER: '#EC4899',
      REPORT: '#14B8A6',
    }

    const categoryDistribution = Object.entries(catCounts).map(([cat, count]) => ({
      category: cat,
      count,
      color: catColors[cat] || '#818CF8',
    }))

    const eventTrends = [
      { day: 'Mon', count: 18 },
      { day: 'Tue', count: 24 },
      { day: 'Wed', count: 32 },
      { day: 'Thu', count: 28 },
      { day: 'Fri', count: 42 },
      { day: 'Sat', count: 16 },
      { day: 'Sun', count: Math.max(14, events.length) },
    ]

    return {
      totalEvents: events.length,
      userActions,
      systemEvents,
      securityEvents,
      dataChanges,
      loginEvents,
      failedLogins,
      highRiskEvents,
      recentCritical,
      categoryDistribution,
      eventTrends,
    }
  }

  public clearLogs(): void {
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(AUDIT_STORAGE_KEY)
        this.notify()
      } catch (e) {
        console.error('Failed to clear audit logs', e)
      }
    }
  }

  public resetToDefaults(): void {
    this.saveAuditEvents(mockAuditEvents)
  }
}

export const auditService = new AuditService()
