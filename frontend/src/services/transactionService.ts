import type { Transaction, TransactionMetrics, TransactionStatus, TransactionTraceEvent } from '../types/transaction'
import type { Execution } from '../types/execution'
import type { Request } from '../types/request'
import { mockTransactions } from '../mocks/transactions'

const STORAGE_KEY = 'dealflow360_transactions'
export const TRANSACTIONS_UPDATED_EVENT = 'dealflow_transaction_updated'

class TransactionService {
  private getStorage(): Transaction[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) {
        this.setStorage(mockTransactions, false)
        return [...mockTransactions]
      }
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : [...mockTransactions]
    } catch {
      return [...mockTransactions]
    }
  }

  private setStorage(transactions: Transaction[], notify = true): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(transactions))
      if (notify && typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(TRANSACTIONS_UPDATED_EVENT, { detail: transactions }))
      }
    } catch (e) {
      console.error('Failed to save transactions to localStorage', e)
    }
  }

  public getTransactions(): Transaction[] {
    return this.getStorage()
  }

  public getTransactionById(id: string): Transaction | undefined {
    const list = this.getStorage()
    return list.find(
      (t) =>
        t.id === id ||
        t.transactionNumber.toLowerCase() === id.toLowerCase() ||
        t.requestId === id ||
        t.executionId === id
    )
  }

  public getTransactionByRequestId(requestId: string): Transaction | undefined {
    const list = this.getStorage()
    return list.find((t) => t.requestId === requestId || t.requestReference === requestId)
  }

  public getTransactionByExecutionId(executionId: string): Transaction | undefined {
    const list = this.getStorage()
    return list.find((t) => t.executionId === executionId)
  }

  public getMetrics(): TransactionMetrics {
    const list = this.getStorage()
    const total = list.length
    const completed = list.filter((t) => t.status === 'Completed').length
    const processing = list.filter((t) => t.status === 'Processing').length
    const pending = list.filter((t) => t.status === 'Pending').length
    const failed = list.filter((t) => t.status === 'Failed').length

    const totalValueNumeric = list
      .filter((t) => t.status === 'Completed')
      .reduce((sum, t) => sum + (t.numericAmount || 0), 0)

    const formatted = '₹' + totalValueNumeric.toLocaleString('en-IN')

    return {
      total,
      completed,
      processing,
      pending,
      failed,
      totalValue: formatted,
      totalValueNumeric,
    }
  }

  public createTransactionFromExecution(execution: Execution, request?: Request): Transaction {
    const list = this.getStorage()

    // Prevent duplicate transactions for the same execution
    const existing = list.find((t) => t.executionId === execution.id || t.requestId === execution.requestId)
    if (existing) {
      // If already exists and now completed, update status
      if (existing.status !== 'Completed' && execution.status === 'Completed') {
        const updated: Transaction = {
          ...existing,
          status: 'Completed',
          completedDate: new Date().toISOString(),
          paymentStatus: 'Paid',
          odooSyncRef: execution.odooOperation.reference,
        }
        const updatedList = list.map((t) => (t.id === existing.id ? updated : t))
        this.setStorage(updatedList)
        return updated
      }
      return existing
    }

    const nextNumber = 3015 + list.length
    const now = new Date().toISOString()

    const timeline: TransactionTraceEvent[] = [
      {
        id: 'trace_' + Date.now() + '_1',
        stage: 'Request Creation',
        actor: request?.owner || 'Sales Team',
        timestamp: request?.createdAt || now,
        status: 'Completed',
        note: `Contract initial request created: ${execution.referenceNumber}`,
      },
      {
        id: 'trace_' + Date.now() + '_2',
        stage: 'AI Analysis & Margin Verification',
        actor: 'AI Intelligence Engine',
        timestamp: now,
        status: 'Completed',
        note: 'AI evaluation verified commercial viability',
      },
      {
        id: 'trace_' + Date.now() + '_3',
        stage: 'Commercial Approval',
        actor: execution.approverName || 'Arjun Sharma',
        timestamp: now,
        status: 'Completed',
        note: 'Approved for automated ERP execution',
      },
      {
        id: 'trace_' + Date.now() + '_4',
        stage: 'Execution & Odoo Sync',
        actor: 'DealFlow Execution Engine',
        timestamp: now,
        status: execution.status === 'Completed' ? 'Completed' : 'Pending',
        note: `Simulated Odoo ERP reference: ${execution.odooOperation.reference} (${execution.odooOperation.model})`,
      },
      {
        id: 'trace_' + Date.now() + '_5',
        stage: 'Transaction Finalization',
        actor: 'Automated Settlement Engine',
        timestamp: now,
        status: execution.status === 'Completed' ? 'Completed' : 'Pending',
        note: 'Transaction posted to simulated general ledger',
      },
    ]

    const newTx: Transaction = {
      id: 'tx_' + (Date.now().toString().slice(-4)),
      transactionNumber: `TX-2026-${nextNumber}`,
      requestId: execution.requestId,
      requestReference: execution.referenceNumber,
      executionId: execution.id,
      customer: execution.customer,
      title: execution.title || `${execution.customer} Enterprise Fulfillment`,
      amount: execution.amount,
      numericAmount: execution.numericAmount || 0,
      currency: 'INR',
      status: execution.status === 'Completed' ? 'Completed' : 'Processing',
      transactionType: execution.requestType || 'Commercial Contract',
      odooSyncRef: execution.odooOperation.reference,
      paymentStatus: execution.status === 'Completed' ? 'Paid' : 'Pending',
      initiatedDate: execution.startedAt || now,
      completedDate: execution.status === 'Completed' ? (execution.completedAt || now) : undefined,
      settledBy: 'Automated ERP Settlement',
      timeline,
    }

    list.unshift(newTx)
    this.setStorage(list)
    return newTx
  }

  public updateTransactionStatus(id: string, status: TransactionStatus): boolean {
    const list = this.getStorage()
    const index = list.findIndex((t) => t.id === id || t.transactionNumber === id)
    if (index < 0) return false

    list[index] = {
      ...list[index],
      status,
      completedDate: status === 'Completed' ? new Date().toISOString() : list[index].completedDate,
      paymentStatus: status === 'Completed' ? 'Paid' : list[index].paymentStatus,
    }

    this.setStorage(list)
    return true
  }

  public resetToMockData(): void {
    this.setStorage(mockTransactions)
  }
}

export const transactionService = new TransactionService()
