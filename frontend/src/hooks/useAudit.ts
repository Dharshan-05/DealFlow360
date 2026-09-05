import { useState, useEffect, useCallback } from 'react'
import { auditService } from '../services/auditService'
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

export function useAudit(initialFilters?: AuditFilters) {
  const [filters, setFilters] = useState<AuditFilters>(initialFilters || {})
  const [events, setEvents] = useState<AuditEvent[]>(() => auditService.getAuditEvents(initialFilters))
  const [metrics, setMetrics] = useState<AuditMetrics>(() => auditService.getAuditMetrics())
  const [userActivities, setUserActivities] = useState<UserActivityLog[]>(() => auditService.getUserActivity())
  const [systemEvents, setSystemEvents] = useState<SystemEvent[]>(() => auditService.getSystemEvents())
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>(() => auditService.getSecurityEvents())
  const [loginHistory, setLoginHistory] = useState<LoginHistoryItem[]>(() => auditService.getLoginHistory())
  const [dataChanges, setDataChanges] = useState<DataChangeRecord[]>(() => auditService.getDataChangeHistory())
  const [isLoading, setIsLoading] = useState(false)

  const reload = useCallback(() => {
    setIsLoading(true)
    setEvents(auditService.getAuditEvents(filters))
    setMetrics(auditService.getAuditMetrics())
    setUserActivities(auditService.getUserActivity())
    setSystemEvents(auditService.getSystemEvents())
    setSecurityEvents(auditService.getSecurityEvents())
    setLoginHistory(auditService.getLoginHistory())
    setDataChanges(auditService.getDataChangeHistory())
    setIsLoading(false)
  }, [filters])

  useEffect(() => {
    reload()
    const unsubscribe = auditService.subscribe(reload)
    return () => unsubscribe()
  }, [reload])

  const logCustomEvent = useCallback((evt: Partial<AuditEvent>) => {
    const created = auditService.logEvent(evt)
    reload()
    return created
  }, [reload])

  const clearAllLogs = useCallback(() => {
    auditService.clearLogs()
    reload()
  }, [reload])

  const resetLogs = useCallback(() => {
    auditService.resetToDefaults()
    reload()
  }, [reload])

  return {
    events,
    metrics,
    userActivities,
    systemEvents,
    securityEvents,
    loginHistory,
    dataChanges,
    filters,
    setFilters,
    isLoading,
    reload,
    logCustomEvent,
    clearAllLogs,
    resetLogs,
  }
}
