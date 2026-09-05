import React, { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  ServerIcon as Server,
  TerminalIcon as Terminal,
  PlayIcon as Play,
  RotateCcwIcon as RotateCcw,
  ExternalLinkIcon as ExternalLink,
  ArrowRightIcon as ArrowRight,
  ShieldCheckIcon as ShieldCheck,
  CheckCircle2Icon as CheckCircle2,
  AlertCircleIcon as AlertCircle,
  ClockIcon as Clock,
  SearchIcon as Search,
} from '../common/Icons'
import type { Execution, ExecutionMetrics } from '../../types/execution'
import type { Transaction, TransactionMetrics, TransactionStatus } from '../../types/transaction'

interface Props {
  executions: Execution[]
  execMetrics: ExecutionMetrics
  transactions: Transaction[]
  txMetrics: TransactionMetrics
  onOpenModal: (exec: Execution) => void
  onOpenExecDrawer: (exec: Execution) => void
  onOpenTxDrawer: (tx: Transaction) => void
  onRetry: (id: string) => Promise<any>
}

export default function ERPExecutionView({
  executions,
  execMetrics,
  transactions,
  txMetrics,
  onOpenModal,
  onOpenExecDrawer,
  onOpenTxDrawer,
  onRetry,
}: Props) {
  const [subTab, setSubTab] = useState<'executions' | 'transactions'>('executions')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')

  // Filtered executions
  const filteredExecutions = useMemo(() => {
    return executions.filter((e) => {
      if (statusFilter !== 'All' && e.status !== statusFilter) return false
      if (!search.trim()) return true
      const q = search.toLowerCase()
      return (
        e.referenceNumber.toLowerCase().includes(q) ||
        e.customer.toLowerCase().includes(q) ||
        e.odooOperation.reference.toLowerCase().includes(q)
      )
    })
  }, [executions, search, statusFilter])

  // Filtered transactions
  const filteredTransactions = useMemo(() => {
    return transactions.filter((t) => {
      if (statusFilter !== 'All' && t.status !== statusFilter) return false
      if (!search.trim()) return true
      const q = search.toLowerCase()
      return (
        t.transactionNumber.toLowerCase().includes(q) ||
        t.customer.toLowerCase().includes(q) ||
        t.requestReference.toLowerCase().includes(q) ||
        t.odooSyncRef.toLowerCase().includes(q)
      )
    })
  }, [transactions, search, statusFilter])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* 5 KPI Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
          gap: 12,
        }}
      >
        <div
          className="df-card"
          style={{ padding: '16px 18px', background: '#09090c', border: '1px solid #1c1c24' }}
        >
          <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase', fontWeight: 600 }}>
            Total Executions
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginTop: 6, fontFamily: 'monospace' }}>
            {execMetrics.total}
          </div>
          <div style={{ fontSize: 11, color: '#a1a1aa', marginTop: 4 }}>Pipeline records tracked</div>
        </div>

        <div
          className="df-card"
          style={{ padding: '16px 18px', background: '#09090c', border: '1px solid #1c1c24' }}
        >
          <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase', fontWeight: 600 }}>
            In-Flight Processing
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#c084fc', marginTop: 6, fontFamily: 'monospace' }}>
            {execMetrics.inProgress}
          </div>
          <div style={{ fontSize: 11, color: '#a78bfa', marginTop: 4 }}>Odoo Sync / Validating</div>
        </div>

        <div
          className="df-card"
          style={{ padding: '16px 18px', background: '#09090c', border: '1px solid #1c1c24' }}
        >
          <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase', fontWeight: 600 }}>
            Completed Executions
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#34d399', marginTop: 6, fontFamily: 'monospace' }}>
            {execMetrics.completed}
          </div>
          <div style={{ fontSize: 11, color: '#10b981', marginTop: 4 }}>ERP sync verified</div>
        </div>

        <div
          className="df-card"
          style={{ padding: '16px 18px', background: '#09090c', border: '1px solid #1c1c24' }}
        >
          <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase', fontWeight: 600 }}>
            Failed / Retry Needed
          </div>
          <div
            style={{
              fontSize: 24,
              fontWeight: 700,
              color: execMetrics.failed > 0 ? '#f87171' : '#71717a',
              marginTop: 6,
              fontFamily: 'monospace',
            }}
          >
            {execMetrics.failed}
          </div>
          <div style={{ fontSize: 11, color: '#ef4444', marginTop: 4 }}>Deterministic retry enabled</div>
        </div>

        <div
          className="df-card"
          style={{ padding: '16px 18px', background: '#09090c', border: '1px solid #1c1c24' }}
        >
          <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase', fontWeight: 600 }}>
            Settled Volume
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#10b981', marginTop: 6, fontFamily: 'monospace' }}>
            {txMetrics.totalValue}
          </div>
          <div style={{ fontSize: 11, color: '#a1a1aa', marginTop: 4 }}>Closed financial records</div>
        </div>
      </div>

      {/* Mandatory ERP Simulation Banner */}
      <div
        style={{
          background: 'linear-gradient(90deg, rgba(234, 179, 8, 0.08), rgba(124, 58, 237, 0.08))',
          border: '1px solid rgba(234, 179, 8, 0.3)',
          borderRadius: 8,
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 6,
              background: 'rgba(234, 179, 8, 0.15)',
              border: '1px solid rgba(234, 179, 8, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#facc15',
            }}
          >
            <Server size={16} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#fff' }}>
                Simulated Odoo ERP Operations
              </span>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  background: '#facc15',
                  color: '#000',
                  padding: '1px 6px',
                  borderRadius: 3,
                }}
              >
                DEMO ENVIRONMENT
              </span>
            </div>
            <div style={{ fontSize: 11.5, color: '#a1a1aa', marginTop: 2 }}>
              Target Odoo models (<code>sale.order</code>, <code>sale.subscription</code>, <code>stock.reservation</code>) are simulated locally in browser state.
            </div>
          </div>
        </div>

        <div style={{ fontSize: 11, color: '#71717a', fontFamily: 'monospace' }}>
          Idempotency: Active · RPC Latency: Simulated (1.2s)
        </div>
      </div>

      {/* Sub-tab Navigation & Filters Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #1c1c24',
          paddingBottom: 12,
          gap: 16,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="button"
            onClick={() => {
              setSubTab('executions')
              setStatusFilter('All')
            }}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              fontSize: 12.5,
              fontWeight: 600,
              background: subTab === 'executions' ? '#1f1f28' : 'transparent',
              color: subTab === 'executions' ? '#fff' : '#71717a',
              border: subTab === 'executions' ? '1px solid #2e2e3a' : '1px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>Simulated Odoo Executions</span>
            <span
              style={{
                fontSize: 11,
                background: subTab === 'executions' ? 'rgba(124, 58, 237, 0.25)' : 'rgba(255, 255, 255, 0.06)',
                color: subTab === 'executions' ? '#c084fc' : '#71717a',
                padding: '1px 6px',
                borderRadius: 4,
                fontFamily: 'monospace',
              }}
            >
              {executions.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => {
              setSubTab('transactions')
              setStatusFilter('All')
            }}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              fontSize: 12.5,
              fontWeight: 600,
              background: subTab === 'transactions' ? '#1f1f28' : 'transparent',
              color: subTab === 'transactions' ? '#fff' : '#71717a',
              border: subTab === 'transactions' ? '1px solid #2e2e3a' : '1px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>Financial Transactions Ledger</span>
            <span
              style={{
                fontSize: 11,
                background: subTab === 'transactions' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(255, 255, 255, 0.06)',
                color: subTab === 'transactions' ? '#34d399' : '#71717a',
                padding: '1px 6px',
                borderRadius: 4,
                fontFamily: 'monospace',
              }}
            >
              {transactions.length}
            </span>
          </button>
        </div>

        {/* Search & Status Filter */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search
              size={14}
              color="#71717a"
              style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              placeholder={subTab === 'executions' ? 'Search executions or ref...' : 'Search transactions or ref...'}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="df-input"
              style={{ paddingLeft: 30, height: 32, fontSize: 12, width: 220 }}
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="df-input"
            style={{ height: 32, fontSize: 12 }}
          >
            <option value="All">All Statuses</option>
            {subTab === 'executions' ? (
              <>
                <option value="Completed">Completed</option>
                <option value="Processing">Processing</option>
                <option value="Validating">Validating</option>
                <option value="Failed">Failed</option>
                <option value="Queued">Queued</option>
              </>
            ) : (
              <>
                <option value="Completed">Completed</option>
                <option value="Processing">Processing</option>
                <option value="Pending">Pending</option>
                <option value="Failed">Failed</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* SUBTAB 1: EXECUTIONS TABLE */}
      {subTab === 'executions' && (
        <div className="df-card" style={{ overflow: 'hidden', background: '#08080a', border: '1px solid #1c1c24' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', minWidth: 900, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#0e0e14', borderBottom: '1px solid #1c1c24' }}>
                  <th style={thStyle}>Request / Deal</th>
                  <th style={thStyle}>Customer</th>
                  <th style={thStyle}>Amount</th>
                  <th style={thStyle}>Simulated Odoo Target</th>
                  <th style={thStyle}>Odoo Reference</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Pipeline</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredExecutions.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ padding: '36px 20px', textAlign: 'center', color: '#71717a', fontSize: 13 }}>
                      No simulated executions found matching query.
                    </td>
                  </tr>
                ) : (
                  filteredExecutions.map((exec) => {
                    const isDone = exec.status === 'Completed'
                    const isFail = exec.status === 'Failed'

                    return (
                      <tr
                        key={exec.id}
                        style={{ borderBottom: '1px solid #14141c' }}
                        className="hover:bg-white/[0.02] transition-colors"
                      >
                        <td style={tdStyle}>
                          <div style={{ fontWeight: 600, color: '#fff', fontSize: 13 }}>
                            {exec.referenceNumber}
                          </div>
                          <div style={{ fontSize: 11, color: '#71717a' }}>{exec.requestType || 'Commercial'}</div>
                        </td>

                        <td style={tdStyle}>
                          <div style={{ color: '#e4e4e7', fontSize: 13, fontWeight: 500 }}>{exec.customer}</div>
                        </td>

                        <td style={tdStyle}>
                          <div className="mono" style={{ color: '#fff', fontWeight: 600, fontSize: 13 }}>
                            {exec.amount}
                          </div>
                        </td>

                        <td style={tdStyle}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span style={{ fontSize: 11, color: '#93c5fd', fontFamily: 'monospace' }}>
                              {exec.odooOperation.model}
                            </span>
                          </div>
                        </td>

                        <td style={tdStyle}>
                          <span
                            className="mono"
                            style={{
                              fontSize: 12,
                              fontWeight: 700,
                              color: '#38bdf8',
                              background: 'rgba(56, 189, 248, 0.1)',
                              padding: '2px 6px',
                              borderRadius: 4,
                              border: '1px solid rgba(56, 189, 248, 0.25)',
                            }}
                          >
                            {exec.odooOperation.reference}
                          </span>
                        </td>

                        <td style={tdStyle}>
                          <span
                            style={{
                              fontSize: 11,
                              fontWeight: 600,
                              padding: '3px 8px',
                              borderRadius: 4,
                              background: isDone
                                ? 'rgba(16, 185, 129, 0.15)'
                                : isFail
                                ? 'rgba(239, 68, 68, 0.15)'
                                : 'rgba(139, 92, 246, 0.15)',
                              color: isDone ? '#34d399' : isFail ? '#f87171' : '#c084fc',
                              border: `1px solid ${
                                isDone
                                  ? 'rgba(16, 185, 129, 0.3)'
                                  : isFail
                                  ? 'rgba(239, 68, 68, 0.3)'
                                  : 'rgba(139, 92, 246, 0.3)'
                              }`,
                            }}
                          >
                            {exec.status}
                          </span>
                        </td>

                        <td style={tdStyle}>
                          <div style={{ width: 100 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#71717a', marginBottom: 2 }}>
                              <span>Progress</span>
                              <span className="mono">{exec.progressPercent}%</span>
                            </div>
                            <div style={{ height: 4, background: '#202028', borderRadius: 2, overflow: 'hidden' }}>
                              <div
                                style={{
                                  height: '100%',
                                  width: `${exec.progressPercent}%`,
                                  background: isDone ? '#10b981' : isFail ? '#ef4444' : '#a855f7',
                                }}
                              />
                            </div>
                          </div>
                        </td>

                        <td style={{ ...tdStyle, textAlign: 'right' }}>
                          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                            {isFail ? (
                              <button
                                onClick={() => onRetry(exec.id)}
                                style={{
                                  padding: '5px 10px',
                                  borderRadius: 4,
                                  background: '#f59e0b',
                                  color: '#000',
                                  fontWeight: 600,
                                  fontSize: 11.5,
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: 4,
                                  border: 'none',
                                }}
                              >
                                <RotateCcw size={12} /> Retry
                              </button>
                            ) : (
                              <button
                                onClick={() => onOpenModal(exec)}
                                style={{
                                  padding: '5px 10px',
                                  borderRadius: 4,
                                  background: isDone ? '#15151c' : '#7c3aed',
                                  color: isDone ? '#d4d4d8' : '#fff',
                                  fontWeight: 500,
                                  fontSize: 11.5,
                                  cursor: 'pointer',
                                  border: isDone ? '1px solid #242430' : 'none',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: 4,
                                }}
                              >
                                {isDone ? 'Simulation Modal' : <><Play size={11} fill="#fff" /> Run</>}
                              </button>
                            )}

                            <button
                              onClick={() => onOpenExecDrawer(exec)}
                              className="df-btn-secondary"
                              style={{ padding: '5px 9px', fontSize: 11.5 }}
                            >
                              Inspect
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUBTAB 2: TRANSACTIONS TABLE */}
      {subTab === 'transactions' && (
        <div className="df-card" style={{ overflow: 'hidden', background: '#08080a', border: '1px solid #1c1c24' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', minWidth: 900, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#0e0e14', borderBottom: '1px solid #1c1c24' }}>
                  <th style={thStyle}>Transaction Number</th>
                  <th style={thStyle}>Request Reference</th>
                  <th style={thStyle}>Customer</th>
                  <th style={thStyle}>Settled Amount</th>
                  <th style={thStyle}>Simulated Odoo SO</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Payment</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>Lifecycle Trace</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ padding: '36px 20px', textAlign: 'center', color: '#71717a', fontSize: 13 }}>
                      No financial transactions found.
                    </td>
                  </tr>
                ) : (
                  filteredTransactions.map((tx) => {
                    const isDone = tx.status === 'Completed'

                    return (
                      <tr
                        key={tx.id}
                        style={{ borderBottom: '1px solid #14141c' }}
                        className="hover:bg-white/[0.02] transition-colors"
                      >
                        <td style={tdStyle}>
                          <div className="mono" style={{ fontWeight: 700, color: '#10b981', fontSize: 13 }}>
                            {tx.transactionNumber}
                          </div>
                          <div style={{ fontSize: 11, color: '#71717a' }}>{tx.executionId}</div>
                        </td>

                        <td style={tdStyle}>
                          <span className="mono" style={{ fontSize: 12.5, color: '#a78bfa' }}>
                            {tx.requestReference}
                          </span>
                        </td>

                        <td style={tdStyle}>
                          <div style={{ color: '#e4e4e7', fontSize: 13, fontWeight: 500 }}>{tx.customer}</div>
                        </td>

                        <td style={tdStyle}>
                          <div className="mono" style={{ color: '#fff', fontWeight: 700, fontSize: 13.5 }}>
                            {tx.amount}
                          </div>
                        </td>

                        <td style={tdStyle}>
                          <span
                            className="mono"
                            style={{
                              fontSize: 12,
                              fontWeight: 600,
                              color: '#38bdf8',
                              background: 'rgba(56, 189, 248, 0.1)',
                              padding: '2px 6px',
                              borderRadius: 4,
                            }}
                          >
                            {tx.odooSyncRef}
                          </span>
                        </td>

                        <td style={tdStyle}>
                          <span
                            style={{
                              fontSize: 11,
                              fontWeight: 600,
                              padding: '3px 8px',
                              borderRadius: 4,
                              background: isDone ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                              color: isDone ? '#34d399' : '#fbbf24',
                            }}
                          >
                            {tx.status}
                          </span>
                        </td>

                        <td style={tdStyle}>
                          <span
                            style={{
                              fontSize: 11,
                              fontWeight: 600,
                              color: tx.paymentStatus === 'Paid' ? '#34d399' : '#fbbf24',
                            }}
                          >
                            {tx.paymentStatus}
                          </span>
                        </td>

                        <td style={{ ...tdStyle, textAlign: 'right' }}>
                          <button
                            onClick={() => onOpenTxDrawer(tx)}
                            style={{
                              padding: '6px 14px',
                              borderRadius: 5,
                              background: '#0d2d1a',
                              border: '1px solid rgba(16, 185, 129, 0.4)',
                              color: '#34d399',
                              fontWeight: 600,
                              fontSize: 12,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 6,
                            }}
                          >
                            Trace Dealflow &rarr;
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

const thStyle: React.CSSProperties = {
  padding: '12px 16px',
  textAlign: 'left',
  fontSize: 11,
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  color: '#71717a',
}

const tdStyle: React.CSSProperties = {
  padding: '13px 16px',
  fontSize: 12.5,
  verticalAlign: 'middle',
}
