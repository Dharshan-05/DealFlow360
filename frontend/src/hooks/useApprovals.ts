import { useState, useEffect, useCallback, useMemo } from 'react'
import type { Approval, ApprovalMetrics } from '../types/approval'
import {
  approvalService,
  APPROVALS_UPDATED_EVENT,
} from '../services/approvalService'
import { REQUESTS_UPDATED_EVENT } from '../services/requestService'
import { api } from '../lib/api'

function transformBackendApproval(r: any): Approval {
  const statusMap: Record<string, any> = {
    PENDING: 'Pending',
    IN_PROGRESS: 'Pending',
    APPROVED: 'Approved',
    REJECTED: 'Rejected',
    RETURNED_FOR_REVISION: 'Changes Requested',
  }

  const riskMap: Record<string, any> = {
    LOW: 'Low',
    MEDIUM: 'Medium',
    HIGH: 'High',
    CRITICAL: 'Critical',
  }

  return {
    id: r.id,
    requestId: r.id,
    requestReference: r.deal_reference || `REQ-${r.id.slice(0, 8)}`,
    title: `Deal Approval: ${r.deal_reference || r.id.slice(0, 8)}`,
    customer: r.customer_id ? `Account #${r.customer_id.slice(0, 8)}` : 'Enterprise Client',
    amount: `₹${Number(r.deal_value || 0).toLocaleString('en-IN')}`,
    amountValue: Number(r.deal_value || 0),
    priority: Number(r.requested_discount_pct || 0) > 20 ? 'Critical' : 'High',
    requestType: 'Pricing Exception',
    requestedValue: `${r.requested_discount_pct || 0}%`,
    policyLimit: '10%',
    aiRecommended: `${Math.max(0, Number(r.requested_discount_pct || 0) - 5)}%`,
    aiConfidenceScore: 92,
    riskScore: Math.round((r.blended_risk_score || 0.4) * 100),
    riskLevel: riskMap[r.blended_risk_classification] || 'Medium',
    status: statusMap[r.status] || 'Pending',
    submittedBy: 'Commercial Team',
    submittedByRole: 'Sales Representative',
    submittedAt: r.created_at,
    timeAgo: 'Recently',
    slaDeadline: '48h SLA',
    slaStatus: 'normal',
    assignedApprover: {
      name: 'Commercial Director',
      role: r.required_level || 'Tier 2 Approver',
      level: r.required_level || 'Commercial',
    },
    description: `Approval evaluation for proposal ${r.deal_reference || ''}`,
    businessJustification: r.routing_metadata?.justification || 'Strategic customer deal exception.',
    expectedOutcome: 'Win deal with approved commercial margin.',
    lineItems: [],
    history: (r.steps || []).map((s: any) => ({
      id: s.id,
      event: s.step_name || 'Workflow Step',
      actor: s.assigned_role || 'Approver',
      timestamp: s.actioned_at || s.created_at,
      isCompleted: s.status === 'APPROVED',
      comment: s.decision_reason,
    })),
  }
}

export function useApprovals() {
  const [approvals, setApprovals] = useState<Approval[]>(() => approvalService.getApprovals())
  const [metrics, setMetrics] = useState<ApprovalMetrics>(() => approvalService.getMetrics())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      // Attempt live backend fetch
      const res = await api.approvals.list()
      const rawList = Array.isArray(res) ? res : (res as any)?.data || []
      if (Array.isArray(rawList) && rawList.length > 0) {
        const transformed = rawList.map(transformBackendApproval)
        setApprovals(transformed)
        const total = transformed.length
        const pending = transformed.filter(a => a.status === 'Pending').length
        const approved = transformed.filter(a => a.status === 'Approved').length
        const rejected = transformed.filter(a => a.status === 'Rejected').length
        const changesRequested = transformed.filter(a => a.status === 'Changes Requested').length
        const highRisk = transformed.filter(a => a.status === 'Pending' && (a.riskLevel === 'High' || a.riskLevel === 'Critical')).length
        setMetrics({
          total,
          pending,
          approved,
          rejected,
          changesRequested,
          highRisk,
          avgTurnaroundHours: 1.8,
        })
        setError(null)
        return
      }
    } catch (e: any) {
      console.warn('Backend approvals fetch warning, falling back to local service:', e?.message)
    }

    // Fallback to local approvalService
    try {
      const data = approvalService.getApprovals()
      setApprovals(data)
      setMetrics(approvalService.getMetrics())
      setError(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to load approvals.')
    }
  }, [])

  useEffect(() => {
    refresh()

    const handleUpdate = () => {
      refresh()
    }

    window.addEventListener(APPROVALS_UPDATED_EVENT, handleUpdate)
    window.addEventListener(REQUESTS_UPDATED_EVENT, handleUpdate)
    window.addEventListener('storage', handleUpdate)

    return () => {
      window.removeEventListener(APPROVALS_UPDATED_EVENT, handleUpdate)
      window.removeEventListener(REQUESTS_UPDATED_EVENT, handleUpdate)
      window.removeEventListener('storage', handleUpdate)
    }
  }, [refresh])

  const pendingApprovals = useMemo(
    () => approvals.filter((a) => a.status === 'Pending'),
    [approvals]
  )

  const historyApprovals = useMemo(
    () => approvals.filter((a) => a.status !== 'Pending'),
    [approvals]
  )

  const approve = useCallback(
    async (id: string, actor = 'Arjun Sharma', comment?: string) => {
      setIsLoading(true)
      setError(null)
      try {
        // Attempt backend approve first if id looks like UUID
        if (id.length > 20) {
          try {
            await api.approvals.approve(id, comment)
          } catch (apiErr: any) {
            console.warn('Backend approve failed, falling back:', apiErr)
          }
        }
        const res = approvalService.approveRequest(id, actor, comment)
        if (!res.success && id.length <= 20) {
          throw new Error(res.error || 'Failed to approve request.')
        }
        await refresh()
        return res.approval
      } catch (err: any) {
        setError(err?.message || 'Error occurred while approving request.')
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [refresh]
  )

  const reject = useCallback(
    async (id: string, actor = 'Arjun Sharma', reason: string, comment?: string) => {
      setIsLoading(true)
      setError(null)
      try {
        if (id.length > 20) {
          try {
            await api.approvals.reject(id, reason)
          } catch (apiErr: any) {
            console.warn('Backend reject failed, falling back:', apiErr)
          }
        }
        const res = approvalService.rejectRequest(id, actor, reason, comment)
        if (!res.success && id.length <= 20) {
          throw new Error(res.error || 'Failed to reject request.')
        }
        await refresh()
        return res.approval
      } catch (err: any) {
        setError(err?.message || 'Error occurred while rejecting request.')
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [refresh]
  )

  const requestChanges = useCallback(
    async (id: string, actor = 'Arjun Sharma', reason: string, details?: string) => {
      setIsLoading(true)
      setError(null)
      try {
        if (id.length > 20) {
          try {
            await api.approvals.escalate(id, `${reason}: ${details || ''}`)
          } catch (apiErr: any) {
            console.warn('Backend escalate/changes failed, falling back:', apiErr)
          }
        }
        const res = approvalService.requestChanges(id, actor, reason, details)
        if (!res.success && id.length <= 20) {
          throw new Error(res.error || 'Failed to send changes back to requester.')
        }
        await refresh()
        return res.approval
      } catch (err: any) {
        setError(err?.message || 'Error occurred while requesting changes.')
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [refresh]
  )

  const addComment = useCallback(
    async (id: string, actor = 'Arjun Sharma', comment: string) => {
      try {
        const res = approvalService.addApprovalComment(id, actor, comment)
        if (res.success) {
          refresh()
        }
        return res.approval
      } catch (err: any) {
        console.error(err)
      }
    },
    [refresh]
  )

  return {
    approvals,
    pendingApprovals,
    historyApprovals,
    metrics,
    isLoading,
    error,
    refresh,
    approve,
    reject,
    requestChanges,
    addComment,
    clearError: () => setError(null),
  }
}


export default useApprovals
