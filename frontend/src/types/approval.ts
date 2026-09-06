import type { RiskLevel, AIAnalysis } from './ai'
import type { RequestPriority, RequestType, RequestItem } from './request'

export type ApprovalStatus =
  | 'Pending'
  | 'Approved'
  | 'Rejected'
  | 'Changes Requested'

export interface ApprovalHistoryItem {
  id: string
  event: string
  actor: string
  timestamp: string
  isCompleted: boolean
  comment?: string
}

export interface AssignedApprover {
  name: string
  role: string
  level: string
  avatarUrl?: string
}

export interface Approval {
  id: string
  requestId: string
  requestReference: string
  title?: string
  customer: string
  amount: string
  amountValue?: number
  priority: RequestPriority
  requestType: RequestType
  requestedValue: string // e.g. "18%" discount or custom pricing
  policyLimit: string   // e.g. "10%"
  aiRecommended: string // e.g. "9%"
  aiConfidenceScore?: number // e.g. 92
  riskScore?: number     // e.g. 45
  riskLevel: RiskLevel
  status: ApprovalStatus
  submittedBy: string
  submittedByRole: string
  submittedAt?: string
  reviewedBy?: string
  assignedApprover?: AssignedApprover
  slaDeadline?: string
  slaStatus?: 'normal' | 'warning' | 'urgent' | 'overdue'
  timeAgo: string
  description?: string
  businessJustification?: string
  expectedOutcome?: string
  lineItems?: RequestItem[]
  history: ApprovalHistoryItem[]
  aiSummary?: string
  fullAiAnalysis?: AIAnalysis | null
  decisionReason?: string
  decisionComment?: string
  decidedAt?: string
  changeNotes?: string
}

export interface ApprovalMetrics {
  total: number
  pending: number
  approved: number
  rejected: number
  changesRequested: number
  highRisk: number
  avgTurnaroundHours: number
}
