import type { Approval, ApprovalHistoryItem, ApprovalMetrics, ApprovalStatus } from '../types/approval'
import { mockApprovals } from '../mocks/approvals'
import { requestService, REQUESTS_UPDATED_EVENT } from './requestService'
import { aiService } from './aiService'
import type { Request } from '../types/request'
import { api } from '../lib/api'

const STORAGE_KEY = 'dealflow360_approvals'
export const APPROVALS_UPDATED_EVENT = 'dealflow_approval_updated'

class ApprovalService {
  private getStorage(): Approval[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      let list: Approval[] = []
      if (!raw) {
        list = [...mockApprovals]
      } else {
        const parsed = JSON.parse(raw)
        list = Array.isArray(parsed) && parsed.length > 0 ? parsed : [...mockApprovals]
      }

      // Automatically synchronize with requests in "Ready for Approval" or "Pending Approval"
      const requests = requestService.getRequests()
      let modified = false

      for (const req of requests) {
        if (req.status === 'Ready for Approval' || req.status === 'Pending Approval') {
          const exists = list.find((a) => a.requestId === req.id || a.requestReference === req.referenceNumber)
          if (!exists) {
            const aiData = aiService.getAnalysis(req.id)
            const newApproval: Approval = {
              id: 'appr_' + req.id.replace('req_', ''),
              requestId: req.id,
              requestReference: req.referenceNumber,
              title: req.title,
              customer: req.customer,
              amount: req.formattedAmount,
              amountValue: req.amount,
              priority: req.priority,
              requestType: req.requestType,
              requestedValue: '15%',
              policyLimit: '10%',
              aiRecommended: aiData?.recommendation?.title.includes('Approve') ? '12%' : '10%',
              aiConfidenceScore: aiData?.confidenceScore || 92,
              riskScore: aiData?.riskScore || 45,
              riskLevel: aiData?.overallRisk || req.riskLevel || 'Medium',
              status: 'Pending',
              submittedBy: req.owner || 'Sales Team',
              submittedByRole: req.ownerRole || 'Sales Director',
              submittedAt: req.createdAt,
              timeAgo: 'Just now',
              slaDeadline: '3h 45m remaining',
              slaStatus: 'normal',
              assignedApprover: {
                name: 'Arjun Sharma',
                role: 'Commercial Director',
                level: 'Level 2 Commercial Sign-off',
              },
              description: req.description,
              businessJustification: req.businessJustification,
              expectedOutcome: req.expectedOutcome,
              lineItems: req.items,
              aiSummary: aiData?.recommendation?.rationale || 'AI evaluation complete and pending commercial authorization.',
              fullAiAnalysis: aiData || undefined,
              history: [
                {
                  id: 'h_init_' + Date.now(),
                  event: 'Request submitted for approval',
                  actor: req.owner,
                  timestamp: 'Just now',
                  isCompleted: true,
                },
                {
                  id: 'h_ai_' + Date.now(),
                  event: 'AI Intelligence completed & accepted',
                  actor: 'AI Engine',
                  timestamp: 'Just now',
                  isCompleted: true,
                },
                {
                  id: 'h_rev_' + Date.now(),
                  event: 'Commercial Director Review',
                  actor: 'Arjun Sharma',
                  timestamp: 'Pending review',
                  isCompleted: false,
                },
              ],
            }
            list.unshift(newApproval)
            modified = true
          }
        }
      }

      if (modified || !raw) {
        this.setStorage(list, false)
      }

      return list
    } catch {
      return [...mockApprovals]
    }
  }

  private setStorage(approvals: Approval[], notify = true): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(approvals))
      if (notify && typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(APPROVALS_UPDATED_EVENT, { detail: approvals }))
      }
    } catch (e) {
      console.error('Failed to save approvals to localStorage', e)
    }
  }

  public getApprovals(): Approval[] {
    return this.getStorage()
  }

  public getApprovalById(id: string): Approval | undefined {
    const list = this.getStorage()
    return list.find(
      (a) =>
        a.id === id ||
        a.requestId === id ||
        a.requestReference.toLowerCase() === id.toLowerCase()
    )
  }

  public getPendingApprovals(): Approval[] {
    return this.getStorage().filter((a) => a.status === 'Pending')
  }

  public getApprovalHistory(): Approval[] {
    return this.getStorage().filter((a) => a.status !== 'Pending')
  }

  public getMetrics(): ApprovalMetrics {
    const list = this.getStorage()
    const total = list.length
    const pending = list.filter((a) => a.status === 'Pending').length
    const approved = list.filter((a) => a.status === 'Approved').length
    const rejected = list.filter((a) => a.status === 'Rejected').length
    const changesRequested = list.filter((a) => a.status === 'Changes Requested').length
    const highRisk = list.filter((a) => a.status === 'Pending' && (a.riskLevel === 'High' || a.riskLevel === 'Critical')).length

    return {
      total,
      pending,
      approved,
      rejected,
      changesRequested,
      highRisk,
      avgTurnaroundHours: 1.8,
    }
  }

  public approveRequest(
    approvalId: string,
    actor = 'Arjun Sharma',
    comment?: string
  ): { approval?: Approval; success: boolean; error?: string } {
    const list = this.getStorage()
    const index = list.findIndex((a) => a.id === approvalId || a.requestId === approvalId)
    if (index < 0) {
      return { success: false, error: 'Approval item not found.' }
    }

    const current = list[index]
    if (current.status !== 'Pending') {
      return {
        success: false,
        error: `Request has already been decided (${current.status}) and cannot be approved again.`,
      }
    }

    const now = new Date().toISOString()
    const newHistory: ApprovalHistoryItem[] = [
      ...current.history.map((h) => ({ ...h, isCompleted: true })),
      {
        id: 'h_appr_' + Date.now(),
        event: 'Commercial Approval Confirmed',
        actor,
        timestamp: 'Just now',
        isCompleted: true,
        comment: comment || 'Terms verified. Ready for execution.',
      },
    ]

    const updated: Approval = {
      ...current,
      status: 'Approved',
      reviewedBy: actor,
      decidedAt: now,
      decisionComment: comment || 'Approved for execution handoff.',
      history: newHistory,
      slaStatus: 'normal',
      slaDeadline: 'Approved',
    }

    list[index] = updated
    this.setStorage(list)

    // Synchronize request state to 'Approved'
    requestService.transitionStatus(
      current.requestId,
      'Approved',
      actor,
      'Commercial Approval Granted',
      comment || 'Request approved. Ready for execution handoff.'
    )

    return { approval: updated, success: true }
  }

  public rejectRequest(
    approvalId: string,
    actor = 'Arjun Sharma',
    reason: string,
    comment?: string
  ): { approval?: Approval; success: boolean; error?: string } {
    if (!reason || !reason.trim()) {
      return { success: false, error: 'Rejection reason is mandatory.' }
    }

    const list = this.getStorage()
    const index = list.findIndex((a) => a.id === approvalId || a.requestId === approvalId)
    if (index < 0) {
      return { success: false, error: 'Approval item not found.' }
    }

    const current = list[index]
    if (current.status !== 'Pending') {
      return {
        success: false,
        error: `Request has already been decided (${current.status}) and cannot be rejected again.`,
      }
    }

    const now = new Date().toISOString()
    const fullReason = comment ? `${reason}: ${comment}` : reason

    const newHistory: ApprovalHistoryItem[] = [
      ...current.history.map((h) => ({ ...h, isCompleted: true })),
      {
        id: 'h_rej_' + Date.now(),
        event: 'Commercial Request Rejected',
        actor,
        timestamp: 'Just now',
        isCompleted: true,
        comment: fullReason,
      },
    ]

    const updated: Approval = {
      ...current,
      status: 'Rejected',
      reviewedBy: actor,
      decidedAt: now,
      decisionReason: reason,
      decisionComment: comment,
      history: newHistory,
      slaStatus: 'normal',
      slaDeadline: 'Rejected',
    }

    list[index] = updated
    this.setStorage(list)

    // Synchronize request state to 'Rejected'
    requestService.transitionStatus(
      current.requestId,
      'Rejected',
      actor,
      'Commercial Request Rejected',
      fullReason
    )

    return { approval: updated, success: true }
  }

  public requestChanges(
    approvalId: string,
    actor = 'Arjun Sharma',
    reason: string,
    details?: string
  ): { approval?: Approval; success: boolean; error?: string } {
    if (!reason || !reason.trim()) {
      return { success: false, error: 'Change reason / instructions are mandatory.' }
    }

    const list = this.getStorage()
    const index = list.findIndex((a) => a.id === approvalId || a.requestId === approvalId)
    if (index < 0) {
      return { success: false, error: 'Approval item not found.' }
    }

    const current = list[index]
    if (current.status !== 'Pending') {
      return {
        success: false,
        error: `Request has already been decided (${current.status}) and cannot be sent back for changes.`,
      }
    }

    const now = new Date().toISOString()
    const fullChangeNote = details ? `${reason} — ${details}` : reason

    const newHistory: ApprovalHistoryItem[] = [
      ...current.history.map((h) => ({ ...h, isCompleted: true })),
      {
        id: 'h_chg_' + Date.now(),
        event: 'Changes Requested from Submitter',
        actor,
        timestamp: 'Just now',
        isCompleted: true,
        comment: fullChangeNote,
      },
    ]

    const updated: Approval = {
      ...current,
      status: 'Changes Requested',
      reviewedBy: actor,
      decidedAt: now,
      changeNotes: fullChangeNote,
      history: newHistory,
      slaStatus: 'normal',
      slaDeadline: 'Changes Pending',
    }

    list[index] = updated
    this.setStorage(list)

    // Synchronize request state to 'Changes Requested'
    requestService.transitionStatus(
      current.requestId,
      'Changes Requested',
      actor,
      'Changes Requested by Commercial Approver',
      fullChangeNote
    )

    return { approval: updated, success: true }
  }

  public addApprovalComment(
    approvalId: string,
    actor: string,
    comment: string
  ): { approval?: Approval; success: boolean } {
    if (!comment || !comment.trim()) return { success: false }

    const list = this.getStorage()
    const index = list.findIndex((a) => a.id === approvalId || a.requestId === approvalId)
    if (index < 0) return { success: false }

    const current = list[index]
    const updated: Approval = {
      ...current,
      history: [
        ...current.history,
        {
          id: 'h_comm_' + Date.now(),
          event: 'Reviewer Note Added',
          actor,
          timestamp: 'Just now',
          isCompleted: true,
          comment,
        },
      ],
    }

    list[index] = updated
    this.setStorage(list)
    return { approval: updated, success: true }
  }

  public resetToMockData(): void {
    this.setStorage(mockApprovals)
  }
}

export const approvalService = new ApprovalService()
