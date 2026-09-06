import type { RiskLevel } from './ai'

export type RequestStatus =
  | 'Draft'
  | 'Submitted'
  | 'In Review'
  | 'Under Review'
  | 'Pending Approval'
  | 'Ready for Approval'
  | 'Approved'
  | 'Executing'
  | 'Odoo Processing'
  | 'Processing'
  | 'Completed'
  | 'Rejected'
  | 'Changes Requested'
  | 'Cancelled'

export type RequestPriority = 'Low' | 'Medium' | 'High' | 'Critical'

export type RequestType =
  | 'Commercial Exception'
  | 'Hardware Bundle'
  | 'Software License'
  | 'Custom SLA'
  | 'Standard Procurement'
  | 'Enterprise Expansion'

export interface RequestItem {
  id: string | number
  name: string
  code?: string
  sku?: string
  quantity: number
  unitPrice: number
  discountPercent?: number
  policyLimitPercent?: number
  subtotal: number
  notes?: string
}

export interface RequestTimelineEvent {
  id: string
  event: string
  title: string
  actor: string
  timestamp: string
  note?: string
  status?: RequestStatus
}

export interface RequestActivity {
  id: string
  action: string
  actor: string
  timestamp: string
  description?: string
}

export interface RequestDocument {
  id: string
  name: string
  type: string
  size: string
  uploadedBy: string
  uploadedAt: string
  status: 'Verified' | 'Pending Review' | 'Uploaded'
}

export interface Request {
  id: string
  title: string
  referenceNumber: string
  requestType: RequestType
  customer: string
  customerContact?: string
  owner: string
  ownerRole?: string
  priority: RequestPriority
  status: RequestStatus
  amount: number
  formattedAmount: string
  dueDate?: string
  description?: string
  businessJustification?: string
  expectedOutcome?: string
  riskLevel: RiskLevel
  healthScore?: number
  items: RequestItem[]
  timeline?: RequestTimelineEvent[]
  activity?: RequestActivity[]
  documents?: RequestDocument[]
  requiresApproval: boolean
  approvalReason?: string
  odooReference?: string
  odooSynced?: boolean
  notes?: string
  createdAt: string
  updatedAt: string
}
