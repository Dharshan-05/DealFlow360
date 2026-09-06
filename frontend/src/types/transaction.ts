export type TransactionStatus = 'Completed' | 'Processing' | 'Pending' | 'Failed' | 'Cancelled'

export interface TransactionTraceEvent {
  id: string
  stage: string
  actor: string
  timestamp: string
  status: 'Completed' | 'Pending' | 'Failed'
  note?: string
}

export interface Transaction {
  id: string
  transactionNumber: string
  requestId: string
  requestReference: string
  executionId: string
  customer: string
  title?: string
  amount: string
  numericAmount: number
  currency: string
  status: TransactionStatus
  transactionType: string
  odooSyncRef: string
  paymentStatus: 'Paid' | 'Pending' | 'Overdue'
  initiatedDate: string
  completedDate?: string
  settledBy?: string
  timeline: TransactionTraceEvent[]
  failureReason?: string
}

export interface TransactionMetrics {
  total: number
  completed: number
  processing: number
  pending: number
  failed: number
  totalValue: string
  totalValueNumeric: number
}
