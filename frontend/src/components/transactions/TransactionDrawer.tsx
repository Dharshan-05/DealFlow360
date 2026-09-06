import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  XIcon as X,
  CreditCardIcon as CreditCard,
  FileCheck2Icon as FileCheck2,
  ServerIcon as Server,
  ArrowRightIcon as ArrowRight,
  ShieldCheckIcon as ShieldCheck,
  CheckCircle2Icon as CheckCircle2,
  ClockIcon as Clock,
  ExternalLinkIcon as ExternalLink,
  LayersIcon as Layers,
} from '../common/Icons'
import type { Transaction } from '../../types/transaction'

interface Props {
  isOpen: boolean
  transaction: Transaction | null
  onClose: () => void
  onNavigateToRequest?: (reqId: string) => void
  onViewExecution?: (execId: string) => void
}

export default function TransactionDrawer({
  isOpen,
  transaction,
  onClose,
  onNavigateToRequest,
  onViewExecution,
}: Props) {
  if (!isOpen || !transaction) return null

  const isCompleted = transaction.status === 'Completed'

  return (
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9990,
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(3px)',
          }}
        />

        {/* Drawer Panel */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 280 }}
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 560,
            height: '100%',
            background: '#09090c',
            borderLeft: '1px solid #1f1f28',
            boxShadow: '-10px 0 40px rgba(0, 0, 0, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid #1c1c24',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: '#0e0e14',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: '#10b981',
                    letterSpacing: '0.04em',
                  }}
                >
                  Transaction Record
                </span>
                <span
                  style={{
                    fontSize: 10.5,
                    background: isCompleted
                      ? 'rgba(16, 185, 129, 0.15)'
                      : 'rgba(245, 158, 11, 0.15)',
                    border: `1px solid ${
                      isCompleted
                        ? 'rgba(16, 185, 129, 0.3)'
                        : 'rgba(245, 158, 11, 0.3)'
                    }`,
                    color: isCompleted ? '#34d399' : '#fbbf24',
                    padding: '1px 6px',
                    borderRadius: 4,
                  }}
                >
                  {transaction.status}
                </span>
              </div>
              <h3 style={{ margin: '4px 0 0', fontSize: 16, fontWeight: 600, color: '#fff' }}>
                {transaction.transactionNumber}
              </h3>
            </div>

            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#71717a',
                cursor: 'pointer',
                padding: 4,
              }}
              title="Close drawer"
            >
              <X size={18} />
            </button>
          </div>

          {/* Body */}
          <div
            style={{
              padding: '20px',
              overflowY: 'auto',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            {/* End-to-End Traceability Breadcrumbs */}
            <div
              style={{
                background: '#111116',
                border: '1px solid #1f1f28',
                borderRadius: 8,
                padding: '14px',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  color: '#71717a',
                  marginBottom: 10,
                }}
              >
                End-to-End Dealflow Traceability
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 4,
                  overflowX: 'auto',
                  paddingBottom: 4,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minWidth: 80,
                  }}
                >
                  <span style={{ fontSize: 10, color: '#71717a' }}>Request</span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: '#a78bfa',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    {transaction.requestReference}
                  </span>
                </div>

                <ArrowRight size={13} color="#4b5563" />

                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minWidth: 80,
                  }}
                >
                  <span style={{ fontSize: 10, color: '#71717a' }}>Approval</span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: '#34d399',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    Approved
                  </span>
                </div>

                <ArrowRight size={13} color="#4b5563" />

                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minWidth: 80,
                  }}
                >
                  <span style={{ fontSize: 10, color: '#71717a' }}>Execution</span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: '#c084fc',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    {transaction.executionId}
                  </span>
                </div>

                <ArrowRight size={13} color="#4b5563" />

                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minWidth: 90,
                  }}
                >
                  <span style={{ fontSize: 10, color: '#71717a' }}>Odoo SO (Demo)</span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: '#38bdf8',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    {transaction.odooSyncRef}
                  </span>
                </div>

                <ArrowRight size={13} color="#4b5563" />

                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minWidth: 85,
                  }}
                >
                  <span style={{ fontSize: 10, color: '#71717a' }}>Transaction</span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: '#10b981',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    {transaction.transactionNumber}
                  </span>
                </div>
              </div>
            </div>

            {/* Financial Details */}
            <div
              style={{
                background: '#121218',
                borderRadius: 8,
                border: '1px solid #20202c',
                padding: '16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 14,
              }}
            >
              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Customer</div>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: '#fff', marginTop: 2 }}>
                  {transaction.customer}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Settled Value</div>
                <div
                  style={{
                    fontSize: 15,
                    fontWeight: 700,
                    color: '#10b981',
                    marginTop: 2,
                    fontFamily: 'monospace',
                  }}
                >
                  {transaction.amount}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Payment Status</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                  <span
                    style={{
                      fontSize: 11,
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontWeight: 600,
                      background:
                        transaction.paymentStatus === 'Paid'
                          ? 'rgba(16, 185, 129, 0.15)'
                          : 'rgba(245, 158, 11, 0.15)',
                      color:
                        transaction.paymentStatus === 'Paid' ? '#34d399' : '#fbbf24',
                    }}
                  >
                    {transaction.paymentStatus}
                  </span>
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Fulfillment Date</div>
                <div
                  style={{
                    fontSize: 12,
                    color: '#d4d4d8',
                    marginTop: 4,
                    fontFamily: 'monospace',
                  }}
                >
                  {transaction.completedDate
                    ? new Date(transaction.completedDate).toLocaleDateString('en-IN')
                    : 'Pending'}
                </div>
              </div>
            </div>

            {/* ERP Synchronization Details */}
            <div
              style={{
                background: '#0d1017',
                border: '1px solid #1c2638',
                borderRadius: 8,
                padding: '14px 16px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 8,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Server size={14} color="#60a5fa" />
                  <span style={{ fontSize: 11.5, fontWeight: 700, color: '#93c5fd' }}>
                    SIMULATED ERP RECORD
                  </span>
                </div>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    background: 'rgba(234, 179, 8, 0.15)',
                    border: '1px solid rgba(234, 179, 8, 0.3)',
                    color: '#facc15',
                    padding: '2px 6px',
                    borderRadius: 4,
                  }}
                >
                  Demo Odoo Operation
                </span>
              </div>

              <div
                style={{
                  padding: '10px 12px',
                  background: '#090d14',
                  borderRadius: 6,
                  border: '1px solid #141f30',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontSize: 10.5, color: '#64748b' }}>Simulated Sales Order</div>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 700,
                      color: '#38bdf8',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    {transaction.odooSyncRef}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10.5, color: '#64748b' }}>Integration Status</div>
                  <div style={{ fontSize: 11.5, fontWeight: 600, color: '#34d399', marginTop: 2 }}>
                    Synchronized (Demo)
                  </div>
                </div>
              </div>
            </div>

            {/* Traceability Timeline */}
            <div
              style={{
                background: '#0e0e13',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '14px 16px',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  color: '#71717a',
                  marginBottom: 12,
                }}
              >
                Auditable Lifecycle Timeline
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {transaction.timeline.map((event, idx) => (
                  <div
                    key={event.id || idx}
                    style={{
                      display: 'flex',
                      gap: 12,
                      alignItems: 'flex-start',
                    }}
                  >
                    <div
                      style={{
                        width: 20,
                        height: 20,
                        borderRadius: '50%',
                        background: '#0d2d1a',
                        border: '1px solid rgba(16, 185, 129, 0.4)',
                        color: '#10b981',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 10,
                        fontWeight: 700,
                        marginTop: 1,
                        flexShrink: 0,
                      }}
                    >
                      ✓
                    </div>

                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'baseline',
                        }}
                      >
                        <span style={{ fontSize: 12.5, fontWeight: 600, color: '#fff' }}>
                          {event.stage}
                        </span>
                        <span style={{ fontSize: 10.5, color: '#71717a', fontFamily: 'monospace' }}>
                          {new Date(event.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 1 }}>
                        By: {event.actor}
                      </div>
                      {event.note && (
                        <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                          {event.note}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div
            style={{
              padding: '14px 20px',
              borderTop: '1px solid #1c1c24',
              background: '#0c0c10',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <button
              onClick={onClose}
              className="df-btn-secondary"
              style={{ padding: '8px 16px', fontSize: 12 }}
            >
              Close
            </button>

            <div style={{ display: 'flex', gap: 8 }}>
              {onViewExecution && (
                <button
                  onClick={() => onViewExecution(transaction.executionId)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 6,
                    background: '#1f1f28',
                    border: '1px solid #2e2e3a',
                    color: '#d4d4d8',
                    fontSize: 12,
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  View Execution Log
                </button>
              )}

              {onNavigateToRequest && (
                <button
                  onClick={() => onNavigateToRequest(transaction.requestId)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 6,
                    background: '#7c3aed',
                    border: '1px solid rgba(139, 92, 246, 0.4)',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 12,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  Open Request <ExternalLink size={13} />
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
