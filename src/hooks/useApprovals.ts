import { useState, useEffect, useCallback, useMemo } from 'react'
import type { Approval, ApprovalMetrics } from '../types/approval'
import {
  approvalService,
  APPROVALS_UPDATED_EVENT,
} from '../services/approvalService'
import { REQUESTS_UPDATED_EVENT } from '../services/requestService'

export function useApprovals() {
  const [approvals, setApprovals] = useState<Approval[]>(() => approvalService.getApprovals())
  const [metrics, setMetrics] = useState<ApprovalMetrics>(() => approvalService.getMetrics())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => {
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
        const res = approvalService.approveRequest(id, actor, comment)
        if (!res.success) {
          throw new Error(res.error || 'Failed to approve request.')
        }
        refresh()
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
        const res = approvalService.rejectRequest(id, actor, reason, comment)
        if (!res.success) {
          throw new Error(res.error || 'Failed to reject request.')
        }
        refresh()
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
        const res = approvalService.requestChanges(id, actor, reason, details)
        if (!res.success) {
          throw new Error(res.error || 'Failed to send changes back to requester.')
        }
        refresh()
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
