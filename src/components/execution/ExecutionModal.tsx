import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PlayIcon as Play,
  RotateCcwIcon as RotateCcw,
  CheckCircle2Icon as CheckCircle2,
  AlertCircleIcon as AlertCircle,
  ClockIcon as Clock,
  TerminalIcon as Terminal,
  ServerIcon as Server,
  LayersIcon as Layers,
  FileCheck2Icon as FileCheck2,
  XIcon as X,
  ArrowRightIcon as ArrowRight,
  ExternalLinkIcon as ExternalLink,
} from '../common/Icons'
import type { Execution } from '../../types/execution'

interface Props {
  isOpen: boolean
  execution: Execution | null
  onClose: () => void
  onStart: (simulateFailure?: boolean) => Promise<Execution>
  onRetry: () => Promise<Execution>
  onViewTransaction?: (txId: string) => void
}

export default function ExecutionModal({
  isOpen,
  execution,
  onClose,
  onStart,
  onRetry,
  onViewTransaction,
}: Props) {
  const [simulateFailure, setSimulateFailure] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [execution?.logs])

  if (!isOpen || !execution) return null

  const isCompleted = execution.status === 'Completed'
  const isFailed = execution.status === 'Failed'
  const isRunning =
    execution.status === 'Validating' ||
    execution.status === 'Processing' ||
    execution.status === 'Odoo Sync'

  const handleStart = async () => {
    setLoading(true)
    setError(null)
    try {
      await onStart(simulateFailure)
    } catch (err: any) {
      setError(err?.message || 'Execution error')
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = async () => {
    setLoading(true)
    setError(null)
    try {
      await onRetry()
    } catch (err: any) {
      setError(err?.message || 'Retry error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="execution-modal-title"
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 16,
        }}
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={isRunning ? undefined : onClose}
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(5px)',
          }}
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 12 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 680,
            maxHeight: '92vh',
            background: '#09090b',
            border: '1px solid #27272a',
            borderRadius: 12,
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.9), 0 0 0 1px rgba(255, 255, 255, 0.05)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid #1f1f24',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: '#0f0f13',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: isCompleted
                    ? 'rgba(16, 185, 129, 0.15)'
                    : isFailed
                    ? 'rgba(239, 68, 68, 0.15)'
                    : isRunning
                    ? 'rgba(139, 92, 246, 0.15)'
                    : 'rgba(255, 255, 255, 0.08)',
                  border: `1px solid ${
                    isCompleted
                      ? 'rgba(16, 185, 129, 0.3)'
                      : isFailed
                      ? 'rgba(239, 68, 68, 0.3)'
                      : isRunning
                      ? 'rgba(139, 92, 246, 0.4)'
                      : 'rgba(255, 255, 255, 0.1)'
                  }`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: isCompleted
                    ? '#10b981'
                    : isFailed
                    ? '#ef4444'
                    : isRunning
                    ? '#a78bfa'
                    : '#e4e4e7',
                }}
              >
                {isCompleted ? (
                  <CheckCircle2 size={18} />
                ) : isFailed ? (
                  <AlertCircle size={18} />
                ) : isRunning ? (
                  <div
                    style={{
                      width: 14,
                      height: 14,
                      border: '2px solid #a78bfa',
                      borderTopColor: 'transparent',
                      borderRadius: '50%',
                      animation: 'spin 0.8s linear infinite',
                    }}
                  />
                ) : (
                  <Play size={16} />
                )}
              </div>
              <div>
                <h3
                  id="execution-modal-title"
                  style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#fff' }}
                >
                  Deal Execution & ERP Dispatch
                </h3>
                <p style={{ margin: 0, fontSize: 12, color: '#71717a' }}>
                  {execution.referenceNumber} · {execution.customer} · {execution.amount}
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              disabled={isRunning}
              style={{
                background: 'none',
                border: 'none',
                color: '#71717a',
                cursor: isRunning ? 'not-allowed' : 'pointer',
                padding: 4,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              title="Close modal"
            >
              <X size={18} />
            </button>
          </div>

          {/* Body */}
          <div
            style={{
              padding: '20px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              flex: 1,
            }}
          >
            {/* Progress Bar & Status Pill */}
            <div
              style={{
                background: '#121217',
                border: '1px solid #202028',
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
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: '#e4e4e7' }}>
                    Status: {execution.status}
                  </span>
                  {execution.retryCount > 0 && (
                    <span
                      style={{
                        fontSize: 10.5,
                        background: 'rgba(234, 179, 8, 0.15)',
                        border: '1px solid rgba(234, 179, 8, 0.3)',
                        color: '#facc15',
                        padding: '1px 6px',
                        borderRadius: 4,
                        fontFamily: 'monospace',
                      }}
                    >
                      Retry #{execution.retryCount}
                    </span>
                  )}
                </div>
                <span
                  style={{
                    fontSize: 12,
                    fontFamily: 'monospace',
                    fontWeight: 700,
                    color: isCompleted ? '#10b981' : isFailed ? '#ef4444' : '#a78bfa',
                  }}
                >
                  {execution.progressPercent}%
                </span>
              </div>

              {/* Progress Line */}
              <div
                style={{
                  height: 6,
                  background: '#27272a',
                  borderRadius: 3,
                  overflow: 'hidden',
                  position: 'relative',
                }}
              >
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${execution.progressPercent}%` }}
                  transition={{ duration: 0.3 }}
                  style={{
                    height: '100%',
                    background: isCompleted
                      ? '#10b981'
                      : isFailed
                      ? '#ef4444'
                      : 'linear-gradient(90deg, #7c3aed, #a855f7)',
                  }}
                />
              </div>
            </div>

            {/* Steps Visual Pipeline */}
            <div
              style={{
                background: '#0e0e12',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '14px 16px',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: '#71717a',
                  fontWeight: 600,
                  marginBottom: 12,
                }}
              >
                Execution Pipeline Stages
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {execution.steps.map((step, idx) => {
                  const isCurrent = idx === execution.currentStepIndex && isRunning
                  const isDone = step.status === 'completed'
                  const isStepFailed = step.status === 'failed'

                  return (
                    <div
                      key={step.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        borderRadius: 6,
                        background: isCurrent
                          ? 'rgba(124, 58, 237, 0.08)'
                          : isDone
                          ? 'rgba(16, 185, 129, 0.04)'
                          : isStepFailed
                          ? 'rgba(239, 68, 68, 0.08)'
                          : '#14141a',
                        border: `1px solid ${
                          isCurrent
                            ? 'rgba(124, 58, 237, 0.3)'
                            : isDone
                            ? 'rgba(16, 185, 129, 0.2)'
                            : isStepFailed
                            ? 'rgba(239, 68, 68, 0.3)'
                            : '#202028'
                        }`,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div
                          style={{
                            width: 22,
                            height: 22,
                            borderRadius: '50%',
                            fontSize: 11,
                            fontWeight: 700,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: isDone
                              ? '#0d2d1a'
                              : isStepFailed
                              ? '#3b1212'
                              : isCurrent
                              ? '#2a164d'
                              : '#1c1c24',
                            color: isDone
                              ? '#10b981'
                              : isStepFailed
                              ? '#ef4444'
                              : isCurrent
                              ? '#c084fc'
                              : '#71717a',
                            border: `1px solid ${
                              isDone
                                ? 'rgba(16, 185, 129, 0.4)'
                                : isStepFailed
                                ? 'rgba(239, 68, 68, 0.4)'
                                : isCurrent
                                ? 'rgba(168, 85, 247, 0.5)'
                                : '#2e2e38'
                            }`,
                          }}
                        >
                          {isDone ? '✓' : isStepFailed ? '✕' : idx + 1}
                        </div>

                        <div>
                          <div
                            style={{
                              fontSize: 12.5,
                              fontWeight: 500,
                              color: isDone || isCurrent ? '#fff' : '#a1a1aa',
                            }}
                          >
                            {step.name}
                          </div>
                          {step.details && (
                            <div style={{ fontSize: 11, color: '#71717a', marginTop: 1 }}>
                              {step.details}
                            </div>
                          )}
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {step.duration && (
                          <span
                            style={{
                              fontSize: 11,
                              color: '#71717a',
                              fontFamily: 'monospace',
                            }}
                          >
                            {step.duration}
                          </span>
                        )}
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: 4,
                            textTransform: 'capitalize',
                            background: isDone
                              ? 'rgba(16, 185, 129, 0.15)'
                              : isStepFailed
                              ? 'rgba(239, 68, 68, 0.15)'
                              : isCurrent
                              ? 'rgba(168, 85, 247, 0.15)'
                              : 'rgba(255, 255, 255, 0.05)',
                            color: isDone
                              ? '#34d399'
                              : isStepFailed
                              ? '#f87171'
                              : isCurrent
                              ? '#c084fc'
                              : '#71717a',
                          }}
                        >
                          {step.status === 'in_progress' ? 'Running' : step.status}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Simulated Odoo ERP Operation Card */}
            <div
              style={{
                background: '#0d1017',
                border: '1px solid #1e2638',
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
                    ERP INTEGRATION TARGET
                  </span>
                </div>
                {/* MANDATORY SIMULATION LABEL */}
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    background: 'rgba(234, 179, 8, 0.15)',
                    border: '1px solid rgba(234, 179, 8, 0.35)',
                    color: '#facc15',
                    padding: '2px 8px',
                    borderRadius: 4,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  ⚡ Simulated Odoo Operation · Demo ERP
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 12,
                  padding: '10px 12px',
                  background: '#090c12',
                  borderRadius: 6,
                  border: '1px solid #161e2e',
                }}
              >
                <div>
                  <div style={{ fontSize: 10.5, color: '#64748b' }}>Target ERP</div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0', marginTop: 2 }}>
                    Odoo ERP (Demo)
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10.5, color: '#64748b' }}>Data Model</div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: '#a5b4fc',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    {execution.odooOperation.model}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10.5, color: '#64748b' }}>Simulated Reference</div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color: '#38bdf8',
                      fontFamily: 'monospace',
                      marginTop: 2,
                    }}
                  >
                    {execution.odooOperation.reference}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10.5, color: '#64748b' }}>Status</div>
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color:
                        execution.odooOperation.status === 'Completed'
                          ? '#4ade80'
                          : execution.odooOperation.status === 'Failed'
                          ? '#f87171'
                          : '#fbbf24',
                      marginTop: 2,
                    }}
                  >
                    {execution.odooOperation.status}
                  </div>
                </div>
              </div>

              <p style={{ margin: '8px 0 0', fontSize: 11, color: '#64748b', lineHeight: 1.4 }}>
                {execution.odooOperation.details}
              </p>
            </div>

            {/* Monospace Execution Logs */}
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
                  marginBottom: 8,
                  color: '#71717a',
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                <Terminal size={13} />
                <span>EXECUTION LOG CONSOLE</span>
              </div>
              <div
                style={{
                  maxHeight: 120,
                  overflowY: 'auto',
                  fontFamily: 'monospace',
                  fontSize: 11,
                  lineHeight: 1.6,
                  color: '#a1a1aa',
                  background: '#040405',
                  padding: '8px 10px',
                  borderRadius: 4,
                  border: '1px solid #141418',
                }}
              >
                {execution.logs.map((log, idx) => (
                  <div
                    key={idx}
                    style={{
                      color: log.includes('[ERROR]')
                        ? '#f87171'
                        : log.includes('[COMPLETE]') || log.includes('[TRANSACTION]')
                        ? '#4ade80'
                        : log.includes('[ERP')
                        ? '#60a5fa'
                        : '#a1a1aa',
                    }}
                  >
                    {log}
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            </div>

            {/* Failure Alert Banner */}
            {isFailed && (
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 8,
                  padding: '12px 14px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 10,
                }}
              >
                <AlertCircle size={16} color="#ef4444" style={{ marginTop: 2, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12.5, fontWeight: 600, color: '#f87171' }}>
                    Simulated ERP Execution Failed
                  </div>
                  <p style={{ margin: '2px 0 0', fontSize: 11.5, color: '#fca5a5' }}>
                    {execution.failureReason || 'Simulated ERP connection timeout on demo instance.'}
                  </p>
                  <p style={{ margin: '6px 0 0', fontSize: 11, color: '#f87171' }}>
                    Click <strong>Retry Execution</strong> below to re-dispatch the payload and complete the transaction.
                  </p>
                </div>
              </div>
            )}

            {/* Success Alert Banner */}
            {isCompleted && (
              <div
                style={{
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: 8,
                  padding: '12px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <CheckCircle2 size={18} color="#10b981" style={{ flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: 12.5, fontWeight: 600, color: '#34d399' }}>
                      Fulfillment Loop Successfully Closed
                    </div>
                    <p style={{ margin: '2px 0 0', fontSize: 11.5, color: '#a7f3d0' }}>
                      Simulated ERP Reference: <strong>{execution.odooOperation.reference}</strong> · Duration:{' '}
                      <strong>{execution.duration || '6s'}</strong>
                    </p>
                  </div>
                </div>

                {execution.transactionId && onViewTransaction && (
                  <button
                    onClick={() => onViewTransaction(execution.transactionId!)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      fontSize: 11.5,
                      fontWeight: 600,
                      background: '#0d2d1a',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: '#34d399',
                      padding: '6px 12px',
                      borderRadius: 6,
                      cursor: 'pointer',
                    }}
                  >
                    View Transaction <ArrowRight size={13} />
                  </button>
                )}
              </div>
            )}

            {/* Simulation Options Toggle */}
            {!isCompleted && !isFailed && !isRunning && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  background: '#121217',
                  padding: '10px 14px',
                  borderRadius: 6,
                  border: '1px solid #1e1e26',
                }}
              >
                <input
                  type="checkbox"
                  id="simulate-failure-check"
                  checked={simulateFailure}
                  onChange={(e) => setSimulateFailure(e.target.checked)}
                  style={{ cursor: 'pointer' }}
                />
                <label
                  htmlFor="simulate-failure-check"
                  style={{ fontSize: 11.5, color: '#d4d4d8', cursor: 'pointer', userSelect: 'none' }}
                >
                  Simulate ERP Failure at Step 3 (demonstrates error handling & retry mechanism)
                </label>
              </div>
            )}

            {error && (
              <div
                style={{
                  padding: '8px 12px',
                  borderRadius: 6,
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#f87171',
                  fontSize: 12,
                }}
              >
                {error}
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div
            style={{
              padding: '14px 20px',
              borderTop: '1px solid #1f1f24',
              background: '#0b0b0e',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ fontSize: 11, color: '#71717a' }}>
              Phase 7 Frontend Simulation Mode
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <button
                type="button"
                disabled={isRunning}
                onClick={onClose}
                className="df-btn-secondary"
                style={{ padding: '8px 16px', fontSize: 12.5 }}
              >
                {isCompleted ? 'Close' : 'Cancel'}
              </button>

              {isFailed ? (
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleRetry}
                  style={{
                    padding: '8px 20px',
                    borderRadius: 6,
                    background: '#f59e0b',
                    border: '1px solid rgba(245, 158, 11, 0.5)',
                    color: '#000',
                    fontWeight: 700,
                    fontSize: 12.5,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <RotateCcw size={14} />
                  {loading ? 'Retrying...' : 'Retry Execution'}
                </button>
              ) : isCompleted ? (
                execution.transactionId && onViewTransaction ? (
                  <button
                    type="button"
                    onClick={() => onViewTransaction(execution.transactionId!)}
                    style={{
                      padding: '8px 20px',
                      borderRadius: 6,
                      background: '#10b981',
                      border: '1px solid rgba(16, 185, 129, 0.5)',
                      color: '#000',
                      fontWeight: 700,
                      fontSize: 12.5,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    View Transaction <ExternalLink size={13} />
                  </button>
                ) : null
              ) : (
                <button
                  type="button"
                  disabled={isRunning || loading}
                  onClick={handleStart}
                  style={{
                    padding: '8px 22px',
                    borderRadius: 6,
                    background: isRunning ? '#372061' : 'linear-gradient(135deg, #7c3aed, #6d28d9)',
                    border: '1px solid rgba(139, 92, 246, 0.4)',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 12.5,
                    cursor: isRunning || loading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    boxShadow: '0 4px 14px rgba(124, 58, 237, 0.3)',
                  }}
                >
                  {isRunning || loading ? (
                    <>
                      <div
                        style={{
                          width: 12,
                          height: 12,
                          border: '2px solid #fff',
                          borderTopColor: 'transparent',
                          borderRadius: '50%',
                          animation: 'spin 0.6s linear infinite',
                        }}
                      />
                      Executing Stages...
                    </>
                  ) : (
                    <>
                      <Play size={14} fill="#fff" />
                      Start Execution →
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
