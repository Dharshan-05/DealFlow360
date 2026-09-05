import type { Execution, ExecutionMetrics, ExecutionStatus, ExecutionStep, OdooOperation } from '../types/execution'
import type { Request } from '../types/request'
import type { Approval } from '../types/approval'
import { mockExecutions } from '../mocks/executions'
import { requestService } from './requestService'
import { transactionService } from './transactionService'

const STORAGE_KEY = 'dealflow360_executions'
export const EXECUTION_UPDATED_EVENT = 'dealflow_execution_updated'

const INITIAL_STEPS: Omit<ExecutionStep, 'startedAt' | 'completedAt' | 'duration'>[] = [
  {
    id: 'step_1',
    name: 'Validation & Parameter Check',
    status: 'pending',
    details: 'Verify commercial approval signature, discount limits, and client credit status.',
  },
  {
    id: 'step_2',
    name: 'ERP Payload Preparation',
    status: 'pending',
    details: 'Compile simulated Odoo sale.order schema, item tax matrices, and partner IDs.',
  },
  {
    id: 'step_3',
    name: 'Simulated Odoo ERP Sync',
    status: 'pending',
    details: 'Transmit mock RPC dispatch to demo Odoo instance with idempotency key.',
  },
  {
    id: 'step_4',
    name: 'Inventory & Resource Allocation',
    status: 'pending',
    details: 'Simulate warehouse allocation picking slips and licensing key reservations.',
  },
  {
    id: 'step_5',
    name: 'Transaction Finalization',
    status: 'pending',
    details: 'Generate audit-ready transaction record, close execution loop, and mark complete.',
  },
]

class ExecutionService {
  private getStorage(): Execution[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) {
        this.setStorage(mockExecutions, false)
        return [...mockExecutions]
      }
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : [...mockExecutions]
    } catch {
      return [...mockExecutions]
    }
  }

  private setStorage(executions: Execution[], notify = true): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(executions))
      if (notify && typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(EXECUTION_UPDATED_EVENT, { detail: executions }))
      }
    } catch (e) {
      console.error('Failed to save executions to localStorage', e)
    }
  }

  public getExecutions(): Execution[] {
    return this.getStorage()
  }

  public getExecutionById(id: string): Execution | undefined {
    const list = this.getStorage()
    return list.find(
      (e) =>
        e.id === id ||
        e.requestId === id ||
        e.referenceNumber.toLowerCase() === id.toLowerCase()
    )
  }

  public getExecutionByRequestId(requestId: string): Execution | undefined {
    const list = this.getStorage()
    return list.find((e) => e.requestId === requestId || e.referenceNumber === requestId)
  }

  public getMetrics(): ExecutionMetrics {
    const list = this.getStorage()
    const total = list.length
    const completed = list.filter((e) => e.status === 'Completed').length
    const failed = list.filter((e) => e.status === 'Failed').length
    const inProgress = list.filter(
      (e) => e.status === 'Processing' || e.status === 'Validating' || e.status === 'Odoo Sync'
    ).length
    const pendingExecution = list.filter((e) => e.status === 'Queued' || e.status === 'Idle').length

    return {
      total,
      completed,
      failed,
      inProgress,
      pendingExecution,
      avgProcessingTimeSec: 64,
    }
  }

  public createOrGetExecution(request: Request, approval?: Approval): Execution {
    const list = this.getStorage()
    const existing = list.find((e) => e.requestId === request.id || e.referenceNumber === request.referenceNumber)
    if (existing) {
      return existing
    }

    const odooRef = request.odooReference || `SO-2026-${Math.floor(1000 + Math.random() * 8999)}`
    const now = new Date().toISOString()

    const odooOp: OdooOperation = {
      operationType: request.requestType === 'Software License' ? 'Create Subscription' : 'Create Sales Order',
      target: 'Odoo ERP',
      model: request.requestType === 'Software License' ? 'sale.subscription' : 'sale.order',
      reference: odooRef,
      status: 'Processing',
      environment: 'Demo / Simulated',
      details: `Simulated Odoo ERP record generation queued for ${request.customer}.`,
    }

    const newExec: Execution = {
      id: 'exec_' + request.id.replace('req_', ''),
      requestId: request.id,
      referenceNumber: request.referenceNumber,
      title: request.title,
      customer: request.customer,
      amount: request.formattedAmount,
      numericAmount: request.amount,
      requestType: request.requestType,
      priority: request.priority,
      approvalId: approval?.id || ('appr_' + request.id.replace('req_', '')),
      approverName: approval?.reviewedBy || 'Arjun Sharma',
      status: 'Queued',
      progressPercent: 0,
      currentStep: 'Validation & Parameter Check',
      currentStepIndex: 0,
      steps: INITIAL_STEPS.map((s) => ({ ...s, status: 'pending' })),
      odooOperation: odooOp,
      logs: [
        `[${new Date().toLocaleTimeString()}] [QUEUE] Execution created for request ${request.referenceNumber}`,
        `[${new Date().toLocaleTimeString()}] [AUTH] Linked to approval sign-off by ${approval?.reviewedBy || 'Arjun Sharma'}`,
        `[${new Date().toLocaleTimeString()}] [SIM] Simulated target set to Odoo ERP (Demo environment)`,
      ],
      startedAt: now,
      retryCount: 0,
    }

    list.unshift(newExec)
    this.setStorage(list)
    return newExec
  }

  public async runExecution(
    executionId: string,
    options?: {
      simulateFailure?: boolean
      onStepUpdate?: (exec: Execution) => void
    }
  ): Promise<Execution> {
    const list = this.getStorage()
    const index = list.findIndex((e) => e.id === executionId || e.requestId === executionId)
    if (index < 0) {
      throw new Error(`Execution ${executionId} not found`)
    }

    let exec = { ...list[index] }

    // Mark as started
    const startTime = Date.now()
    exec.status = 'Validating'
    exec.startedAt = new Date().toISOString()
    exec.progressPercent = 10
    exec.currentStepIndex = 0
    exec.currentStep = exec.steps[0].name
    exec.steps = exec.steps.map((s, i) =>
      i === 0
        ? { ...s, status: 'in_progress', startedAt: new Date().toISOString() }
        : { ...s, status: 'pending' }
    )
    exec.logs = [
      ...exec.logs,
      `[${new Date().toLocaleTimeString()}] [START] Execution started by user action`,
    ]

    list[index] = exec
    this.setStorage(list)
    options?.onStepUpdate?.(exec)

    // Helper to pause
    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

    // Step 1: Validation (1000ms)
    await sleep(1000)
    exec.steps[0] = {
      ...exec.steps[0],
      status: 'completed',
      completedAt: new Date().toISOString(),
      duration: '1.0s',
      details: 'Validation checks passed. Authorized discount within SLA quota.',
    }
    exec.logs.push(`[${new Date().toLocaleTimeString()}] [VALIDATION] Passed: All commercial rules confirmed`)
    exec.status = 'Processing'
    exec.progressPercent = 25
    exec.currentStepIndex = 1
    exec.currentStep = exec.steps[1].name
    exec.steps[1] = {
      ...exec.steps[1],
      status: 'in_progress',
      startedAt: new Date().toISOString(),
    }
    list[index] = { ...exec }
    this.setStorage(list)
    options?.onStepUpdate?.(exec)

    // Step 2: ERP Payload Preparation (1000ms)
    await sleep(1000)
    exec.steps[1] = {
      ...exec.steps[1],
      status: 'completed',
      completedAt: new Date().toISOString(),
      duration: '1.0s',
      details: `Generated simulated payload: model ${exec.odooOperation.model}, currency INR, lines ${exec.amount}.`,
    }
    exec.logs.push(`[${new Date().toLocaleTimeString()}] [PREPARATION] Simulated Odoo payload prepared`)
    exec.status = 'Odoo Sync'
    exec.progressPercent = 50
    exec.currentStepIndex = 2
    exec.currentStep = exec.steps[2].name
    exec.steps[2] = {
      ...exec.steps[2],
      status: 'in_progress',
      startedAt: new Date().toISOString(),
    }
    list[index] = { ...exec }
    this.setStorage(list)
    options?.onStepUpdate?.(exec)

    // Step 3: Simulated Odoo ERP Sync (1200ms)
    await sleep(1200)

    // Check for simulated failure trigger
    if (options?.simulateFailure) {
      exec.steps[2] = {
        ...exec.steps[2],
        status: 'failed',
        completedAt: new Date().toISOString(),
        duration: '1.2s',
        details: 'Simulated ERP connection timeout / resource lock error on demo node.',
      }
      exec.status = 'Failed'
      exec.failureStep = exec.steps[2].name
      exec.failureReason = 'Simulated Odoo ERP operation could not be completed on demo environment.'
      exec.odooOperation.status = 'Failed'
      exec.odooOperation.details = 'Simulated ERP call failed during RPC sync.'
      exec.logs.push(`[${new Date().toLocaleTimeString()}] [ERROR] Simulated Odoo ERP sync failed on step 3`)
      exec.logs.push(`[${new Date().toLocaleTimeString()}] [HALT] Execution paused in Failed state. Retry available.`)

      list[index] = { ...exec }
      this.setStorage(list)
      options?.onStepUpdate?.(exec)
      return exec
    }

    exec.steps[2] = {
      ...exec.steps[2],
      status: 'completed',
      completedAt: new Date().toISOString(),
      duration: '1.2s',
      details: `Successfully dispatched to demo Odoo: Reference ${exec.odooOperation.reference} created.`,
    }
    exec.odooOperation.status = 'Completed'
    exec.odooOperation.processedAt = new Date().toISOString()
    exec.logs.push(`[${new Date().toLocaleTimeString()}] [ERP-SIM] Simulated Odoo record created: ${exec.odooOperation.reference}`)
    exec.status = 'Processing'
    exec.progressPercent = 75
    exec.currentStepIndex = 3
    exec.currentStep = exec.steps[3].name
    exec.steps[3] = {
      ...exec.steps[3],
      status: 'in_progress',
      startedAt: new Date().toISOString(),
    }
    list[index] = { ...exec }
    this.setStorage(list)
    options?.onStepUpdate?.(exec)

    // Step 4: Inventory & Resource Allocation (1000ms)
    await sleep(1000)
    exec.steps[3] = {
      ...exec.steps[3],
      status: 'completed',
      completedAt: new Date().toISOString(),
      duration: '1.0s',
      details: 'Simulated warehouse picking slip confirmed and inventory reserved.',
    }
    exec.logs.push(`[${new Date().toLocaleTimeString()}] [INVENTORY] Simulated inventory allocation confirmed`)
    exec.progressPercent = 90
    exec.currentStepIndex = 4
    exec.currentStep = exec.steps[4].name
    exec.steps[4] = {
      ...exec.steps[4],
      status: 'in_progress',
      startedAt: new Date().toISOString(),
    }
    list[index] = { ...exec }
    this.setStorage(list)
    options?.onStepUpdate?.(exec)

    // Step 5: Transaction Finalization (1000ms)
    await sleep(1000)
    exec.steps[4] = {
      ...exec.steps[4],
      status: 'completed',
      completedAt: new Date().toISOString(),
      duration: '1.0s',
      details: 'Audit trail registered, transaction posted, execution complete.',
    }

    const durationSec = Math.round((Date.now() - startTime) / 1000)
    exec.status = 'Completed'
    exec.progressPercent = 100
    exec.currentStep = 'Execution Completed'
    exec.completedAt = new Date().toISOString()
    exec.duration = `${durationSec}s`
    exec.failureReason = undefined
    exec.failureStep = undefined

    // Generate transaction linked to this execution
    const request = requestService.getRequestById(exec.requestId)
    const tx = transactionService.createTransactionFromExecution(exec, request)
    exec.transactionId = tx.id

    exec.logs.push(`[${new Date().toLocaleTimeString()}] [TRANSACTION] Transaction record generated: ${tx.transactionNumber}`)
    exec.logs.push(`[${new Date().toLocaleTimeString()}] [COMPLETE] Full execution pipeline completed successfully in ${durationSec}s`)

    list[index] = { ...exec }
    this.setStorage(list)

    // Transition underlying request to Completed with odoo reference
    requestService.transitionStatus(
      exec.requestId,
      'Completed',
      exec.approverName || 'Execution Engine',
      'Execution & ERP Fulfillment Completed',
      `Fulfillment completed. Simulated Odoo Ref: ${exec.odooOperation.reference}, Transaction: ${tx.transactionNumber}.`
    )

    // Update request with odoo details
    const currentReq = requestService.getRequestById(exec.requestId)
    if (currentReq) {
      requestService.updateRequest(exec.requestId, {
        odooReference: exec.odooOperation.reference,
        odooSynced: true,
      })
    }

    options?.onStepUpdate?.(exec)
    return exec
  }

  public async retryExecution(
    executionId: string,
    options?: { onStepUpdate?: (exec: Execution) => void }
  ): Promise<Execution> {
    const list = this.getStorage()
    const index = list.findIndex((e) => e.id === executionId || e.requestId === executionId)
    if (index < 0) {
      throw new Error(`Execution ${executionId} not found`)
    }

    const current = list[index]
    const retried: Execution = {
      ...current,
      status: 'Queued',
      retryCount: (current.retryCount || 0) + 1,
      failureReason: undefined,
      failureStep: undefined,
      logs: [
        ...current.logs,
        `[${new Date().toLocaleTimeString()}] [RETRY] User triggered retry attempt #${(current.retryCount || 0) + 1}`,
      ],
    }

    list[index] = retried
    this.setStorage(list)
    options?.onStepUpdate?.(retried)

    return this.runExecution(executionId, { simulateFailure: false, onStepUpdate: options?.onStepUpdate })
  }

  public resetToMockData(): void {
    this.setStorage(mockExecutions)
  }
}

export const executionService = new ExecutionService()
