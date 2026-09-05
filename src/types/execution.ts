export type ExecutionStatus =
  | 'Idle'
  | 'Queued'
  | 'Validating'
  | 'Processing'
  | 'Odoo Sync'
  | 'Completed'
  | 'Failed'

export interface ExecutionStep {
  id: string
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped'
  startedAt?: string
  completedAt?: string
  duration?: string
  details?: string
}

export interface OdooOperation {
  operationType:
    | 'Create Sales Order'
    | 'Reserve Inventory'
    | 'Create Invoice'
    | 'Create Subscription'
  target: 'Odoo ERP'
  model: string
  reference: string
  status: 'Processing' | 'Completed' | 'Failed'
  environment: 'Demo / Simulated'
  details: string
  processedAt?: string
}

export interface Execution {
  id: string
  requestId: string
  referenceNumber: string
  title?: string
  customer: string
  amount: string
  numericAmount?: number
  requestType?: string
  priority?: string
  approvalId?: string
  approverName?: string
  transactionId?: string
  status: ExecutionStatus
  progressPercent: number
  currentStep: string
  currentStepIndex: number
  steps: ExecutionStep[]
  odooOperation: OdooOperation
  logs: string[]
  startedAt: string
  completedAt?: string
  duration?: string
  failureReason?: string
  failureStep?: string
  retryCount: number
}

export interface ExecutionMetrics {
  total: number
  inProgress: number
  completed: number
  failed: number
  pendingExecution: number
  avgProcessingTimeSec: number
}
