import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  XIcon as X,
  ServerIcon as Server,
  TerminalIcon as Terminal,
  CheckCircle2Icon as CheckCircle2,
  AlertCircleIcon as AlertCircle,
  ClockIcon as Clock,
  RotateCcwIcon as RotateCcw,
  ExternalLinkIcon as ExternalLink,
  ShieldCheckIcon as ShieldCheck,
} from '../common/Icons'
import type { Execution } from '../../types/execution'

interface Props {
  isOpen: boolean
  execution: Execution | null
  onClose: () => void
  onRetry?: (id: string) => Promise<any>
  onViewTransaction?: (txId: string) => void
}

export default function ExecutionDrawer({
  isOpen,
  execution,
  onClose,
  onRetry,
  onViewTransaction,
}: Props) {
  if (!isOpen || !execution) return null

  const isCompleted = execution.status === 'Completed'
  const isFailed = execution.status === 'Failed'

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
            maxWidth: 540,
            height: '100%',
            background: '#09090c',
            borderLeft: '1px solid #1f1f28',
            boxShadow: '-10px 0 40px rgba(0, 0, 0, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Drawer Header */}
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
                    color: '#8b5cf6',
                    letterSpacing: '0.04em',
                  }}
                >
                  Execution Detail
                </span>
                <span
                  style={{
                    fontSize: 10.5,
                    background: isCompleted
                      ? 'rgba(16, 185, 129, 0.15)'
                      : isFailed
                      ? 'rgba(239, 68, 68, 0.15)'
                      : 'rgba(139, 92, 246, 0.15)',
                    border: `1px solid ${
                      isCompleted
                        ? 'rgba(16, 185, 129, 0.3)'
                        : isFailed
                        ? 'rgba(239, 68, 68, 0.3)'
                        : 'rgba(139, 92, 246, 0.3)'
                    }`,
                    color: isCompleted ? '#34d399' : isFailed ? '#f87171' : '#c084fc',
                    padding: '1px 6px',
                    borderRadius: 4,
                  }}
                >
                  {execution.status}
                </span>
              </div>
              <h3 style={{ margin: '4px 0 0', fontSize: 16, fontWeight: 600, color: '#fff' }}>
                {execution.referenceNumber}
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

          {/* Drawer Content */}
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
            {/* Overview Key-Value */}
            <div
              style={{
                background: '#111116',
                borderRadius: 8,
                border: '1px solid #1f1f28',
                padding: '14px 16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 12,
              }}
            >
              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Customer</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginTop: 2 }}>
                  {execution.customer}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Total Amount</div>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: '#fff',
                    marginTop: 2,
                    fontFamily: 'monospace',
                  }}
                >
                  {execution.amount}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Approved By</div>
                <div style={{ fontSize: 12.5, color: '#d4d4d8', marginTop: 2 }}>
                  {execution.approverName || 'Commercial Director'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, color: '#71717a' }}>Duration</div>
                <div
                  style={{
                    fontSize: 12.5,
                    color: '#d4d4d8',
                    marginTop: 2,
                    fontFamily: 'monospace',
                  }}
                >
                  {execution.duration || '64s (simulated)'}
                </div>
              </div>
            </div>

            {/* Simulated ERP Card */}
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
                  marginBottom: 10,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Server size={14} color="#60a5fa" />
                  <span style={{ fontSize: 11.5, fontWeight: 700, color: '#93c5fd' }}>
                    ERP INTEGRATION
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
                  Simulated Odoo Operation
                </span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: 8,
                  padding: '10px',
                  background: '#090d14',
                  borderRadius: 6,
                  border: '1px solid #141f30',
                }}
              >
                <div>
                  <div style={{ fontSize: 10, color: '#64748b' }}>Target</div>
                  <div style={{ fontSize: 11.5, fontWeight: 600, color: '#e2e8f0', marginTop: 1 }}>
                    Odoo ERP
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10, color: '#64748b' }}>Model</div>
                  <div
                    style={{
                      fontSize: 11.5,
                      fontWeight: 600,
                      color: '#a5b4fc',
                      fontFamily: 'monospace',
                      marginTop: 1,
                    }}
                  >
                    {execution.odooOperation.model}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10, color: '#64748b' }}>Reference</div>
                  <div
                    style={{
                      fontSize: 11.5,
                      fontWeight: 700,
                      color: '#38bdf8',
                      fontFamily: 'monospace',
                      marginTop: 1,
                    }}
                  >
                    {execution.odooOperation.reference}
                  </div>
                </div>
              </div>

              <p style={{ margin: '8px 0 0', fontSize: 11, color: '#64748b', lineHeight: 1.4 }}>
                {execution.odooOperation.details}
              </p>
            </div>

            {/* Step Pipeline List */}
            <div
              style={{
                background: '#0f0f13',
                border: '1px solid #1f1f26',
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
                  marginBottom: 10,
                }}
              >
                Pipeline Stages ({execution.steps.length})
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {execution.steps.map((s, i) => (
                  <div
                    key={s.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 10px',
                      background: '#14141c',
                      borderRadius: 6,
                      border: '1px solid #20202a',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          color: s.status === 'completed' ? '#10b981' : s.status === 'failed' ? '#ef4444' : '#71717a',
                        }}
                      >
                        {s.status === 'completed' ? '✓' : s.status === 'failed' ? '✕' : i + 1}
                      </span>
                      <span style={{ fontSize: 12, color: '#d4d4d8' }}>{s.name}</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {s.duration && (
                        <span style={{ fontSize: 10.5, color: '#71717a', fontFamily: 'monospace' }}>
                          {s.duration}
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: 10.5,
                          padding: '1px 6px',
                          borderRadius: 4,
                          background:
                            s.status === 'completed'
                              ? 'rgba(16, 185, 129, 0.15)'
                              : s.status === 'failed'
                              ? 'rgba(239, 68, 68, 0.15)'
                              : 'rgba(255, 255, 255, 0.06)',
                          color:
                            s.status === 'completed'
                              ? '#34d399'
                              : s.status === 'failed'
                              ? '#f87171'
                              : '#71717a',
                        }}
                      >
                        {s.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Monospace Logs */}
            <div
              style={{
                background: '#070709',
                border: '1px solid #1a1a22',
                borderRadius: 8,
                padding: '12px 14px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 6,
                  color: '#71717a',
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                <Terminal size={12} />
                <span>EXECUTION LOG</span>
              </div>
              <div
                style={{
                  maxHeight: 140,
                  overflowY: 'auto',
                  fontFamily: 'monospace',
                  fontSize: 10.5,
                  lineHeight: 1.6,
                  color: '#a1a1aa',
                  background: '#040405',
                  padding: '8px 10px',
                  borderRadius: 4,
                }}
              >
                {execution.logs.map((log, idx) => (
                  <div key={idx}>{log}</div>
                ))}
              </div>
            </div>
          </div>

          {/* Drawer Footer */}
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
              style={{ padding: '8px 14px', fontSize: 12 }}
            >
              Close
            </button>

            <div style={{ display: 'flex', gap: 8 }}>
              {isFailed && onRetry && (
                <button
                  onClick={() => onRetry(execution.id)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 6,
                    background: '#f59e0b',
                    color: '#000',
                    fontWeight: 600,
                    fontSize: 12,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <RotateCcw size={13} /> Retry
                </button>
              )}

              {isCompleted && execution.transactionId && onViewTransaction && (
                <button
                  onClick={() => onViewTransaction(execution.transactionId!)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 6,
                    background: '#10b981',
                    color: '#000',
                    fontWeight: 600,
                    fontSize: 12,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  View Transaction <ExternalLink size={13} />
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
