import { mockRequests } from '../mocks/requests'
import { mockApprovals } from '../mocks/approvals'
import { mockExecutions } from '../mocks/executions'
import { mockTransactions } from '../mocks/transactions'
import { mockAuditEvents } from '../mocks/audit'
import { mockNotifications } from '../mocks/notifications'
import { defaultSystemSettings } from '../mocks/settings'

/**
 * Resets all demo data in localStorage to initial pristine demo state.
 * PRESERVES the current authentication session (`dealflow360_auth_session`).
 */
export function resetAllDemoData(): { success: boolean; message: string; timestamp: string } {
  try {
    // 1. Reset all operational mock tables
    localStorage.setItem('dealflow360_requests', JSON.stringify(mockRequests))
    localStorage.setItem('dealflow360_approvals', JSON.stringify(mockApprovals))
    localStorage.setItem('dealflow360_executions', JSON.stringify(mockExecutions))
    localStorage.setItem('dealflow360_transactions', JSON.stringify(mockTransactions))
    localStorage.setItem('dealflow360_audit_logs', JSON.stringify(mockAuditEvents))
    localStorage.setItem('dealflow360_notifications', JSON.stringify(mockNotifications))
    localStorage.setItem('dealflow360_settings', JSON.stringify(defaultSystemSettings))

    // 2. Clear volatile caches (re-calculated on demand)
    localStorage.removeItem('dealflow360_ai_analysis')
    localStorage.removeItem('dealflow360_ai_history')
    localStorage.removeItem('dealflow360_report_history')

    // 3. Dispatch reactive bus events to notify all active subscribers immediately
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('dealflow_requests_updated', { detail: mockRequests }))
      window.dispatchEvent(new CustomEvent('dealflow_approval_updated', { detail: mockApprovals }))
      window.dispatchEvent(new CustomEvent('dealflow_execution_updated', { detail: mockExecutions }))
      window.dispatchEvent(new CustomEvent('dealflow_transaction_updated', { detail: mockTransactions }))
      window.dispatchEvent(new CustomEvent('dealflow_audit_updated', { detail: mockAuditEvents }))
      window.dispatchEvent(new CustomEvent('dealflow_notifications_updated', { detail: mockNotifications }))
      window.dispatchEvent(new CustomEvent('dealflow_settings_updated', { detail: defaultSystemSettings }))
      window.dispatchEvent(new CustomEvent('dealflow_ai_updated', { detail: {} }))
    }

    return {
      success: true,
      message: 'All demo data has been reset to baseline defaults.',
      timestamp: new Date().toISOString(),
    }
  } catch (error) {
    console.error('Failed to reset demo data', error)
    return {
      success: false,
      message: 'Failed to reset demo data due to local storage error.',
      timestamp: new Date().toISOString(),
    }
  }
}
