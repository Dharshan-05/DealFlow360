import { useState, useEffect, useCallback, useMemo } from 'react'
import type { Transaction, TransactionMetrics, TransactionStatus } from '../types/transaction'
import { transactionService, TRANSACTIONS_UPDATED_EVENT } from '../services/transactionService'

export function useTransactions() {
  const [transactions, setTransactions] = useState<Transaction[]>(() => transactionService.getTransactions())
  const [metrics, setMetrics] = useState<TransactionMetrics>(() => transactionService.getMetrics())
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<TransactionStatus | 'All'>('All')

  const refresh = useCallback(() => {
    setTransactions(transactionService.getTransactions())
    setMetrics(transactionService.getMetrics())
  }, [])

  useEffect(() => {
    refresh()
    const handleUpdate = () => refresh()
    window.addEventListener(TRANSACTIONS_UPDATED_EVENT, handleUpdate)
    return () => window.removeEventListener(TRANSACTIONS_UPDATED_EVENT, handleUpdate)
  }, [refresh])

  const filteredTransactions = useMemo(() => {
    return transactions.filter((t) => {
      if (statusFilter !== 'All' && t.status !== statusFilter) return false
      if (!searchQuery.trim()) return true
      const q = searchQuery.toLowerCase()
      return (
        t.transactionNumber.toLowerCase().includes(q) ||
        t.customer.toLowerCase().includes(q) ||
        t.requestReference.toLowerCase().includes(q) ||
        t.odooSyncRef.toLowerCase().includes(q) ||
        (t.title && t.title.toLowerCase().includes(q))
      )
    })
  }, [transactions, searchQuery, statusFilter])

  const getTransactionByRequestId = useCallback((requestId: string) => {
    return transactionService.getTransactionByRequestId(requestId)
  }, [])

  const getTransactionById = useCallback((id: string) => {
    return transactionService.getTransactionById(id)
  }, [])

  return {
    transactions: filteredTransactions,
    rawTransactions: transactions,
    metrics,
    selectedTransaction,
    setSelectedTransaction,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    getTransactionByRequestId,
    getTransactionById,
    refresh,
  }
}
