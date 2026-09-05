import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Approval } from '../../types/approval'

interface Props {
  isOpen: boolean
  approval: Approval | null
  onClose: () => void
  onConfirm: (reason: string, comment?: string) => Promise<void>
}

const REJECTION_REASONS = [
  'Commercial terms unacceptable',
  'Risk too high',
  'Policy violation',
  'Insufficient justification',
  'Budget unavailable',
  'Other',
]

export default function RejectModal({ isOpen, approval, onClose, onConfirm }: Props) {
  const [selectedReason, setSelectedReason] = useState(REJECTION_REASONS[0])
  const [customReason, setCustomReason] = useState('')
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      setSelectedReason(REJECTION_REASONS[0])
      setCustomReason('')
      setComment('')
      setError('')
      setSubmitting(false)
    }
  }, [isOpen])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !submitting) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, submitting, onClose])

  if (!isOpen || !approval) return null

  const effectiveReason = selectedReason === 'Other' ? customReason.trim() : selectedReason

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!effectiveReason) {
      setError('Please specify a rejection reason.')
      return
    }

    setSubmitting(true)
    setError('')
    try {
      await onConfirm(effectiveReason, comment.trim() || undefined)
      onClose()
    } catch (err: any) {
      setError(err?.message || 'Failed to reject request. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="reject-modal-title"
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
          onClick={submitting ? undefined : onClose}
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.82)',
            backdropFilter: 'blur(4px)',
          }}
        />

        {/* Modal Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 540,
            background: '#0a0a0c',
            border: '1px solid #22222a',
            borderRadius: 12,
            boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(239, 68, 68, 0.15)',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '18px 24px',
              borderBottom: '1px solid #1a1a20',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#EF4444',
                  fontSize: 16,
                  fontWeight: 700,
                }}
              >
                ✕
              </div>
              <div>
                <h3
                  id="reject-modal-title"
                  style={{
                    margin: 0,
                    fontSize: 16,
                    fontWeight: 600,
                    color: '#fff',
                    letterSpacing: '-0.01em',
                  }}
                >
                  Reject Transaction Request
                </h3>
                <p style={{ margin: '2px 0 0', fontSize: 12, color: '#71717A' }}>
                  {approval.requestReference} · {approval.customer}
                </p>
              </div>
            </div>

            <button
              type="button"
              disabled={submitting}
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#71717A',
                cursor: submitting ? 'not-allowed' : 'pointer',
                fontSize: 18,
                padding: 4,
                lineHeight: 1,
              }}
              title="Close modal"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Warning Callout */}
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.06)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: 8,
                  padding: '12px 14px',
                }}
              >
                <div style={{ fontSize: 11.5, fontWeight: 600, color: '#F87171', marginBottom: 2 }}>
                  Rejection Notice:
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#A1A1AA', lineHeight: 1.5 }}>
                  Rejecting this transaction will officially decline the requested commercial exceptions. The request will be marked as{' '}
                  <strong style={{ color: '#fff' }}>Rejected</strong> and cannot proceed to Phase 7 execution.
                </p>
              </div>

              {/* Reason Category Selection */}
              <div>
                <label
                  htmlFor="rejection-reason-select"
                  style={{
                    display: 'block',
                    fontSize: 12,
                    fontWeight: 500,
                    color: '#D4D4D8',
                    marginBottom: 6,
                  }}
                >
                  Primary Rejection Reason <span style={{ color: '#EF4444' }}>*</span>
                </label>
                <select
                  id="rejection-reason-select"
                  className="df-input"
                  value={selectedReason}
                  onChange={(e) => setSelectedReason(e.target.value)}
                  style={{
                    width: '100%',
                    height: 36,
                    fontSize: 12.5,
                    padding: '0 10px',
                    color: '#fff',
                    background: '#121216',
                  }}
                >
                  {REJECTION_REASONS.map((r) => (
                    <option key={r} value={r} style={{ background: '#121216', color: '#fff' }}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              {/* Custom Reason Field if "Other" is selected */}
              {selectedReason === 'Other' && (
                <div>
                  <label
                    htmlFor="custom-reason-input"
                    style={{
                      display: 'block',
                      fontSize: 12,
                      fontWeight: 500,
                      color: '#D4D4D8',
                      marginBottom: 6,
                    }}
                  >
                    Specify Reason <span style={{ color: '#EF4444' }}>*</span>
                  </label>
                  <input
                    id="custom-reason-input"
                    type="text"
                    className="df-input"
                    value={customReason}
                    onChange={(e) => setCustomReason(e.target.value)}
                    placeholder="Enter custom rejection reason..."
                    style={{ width: '100%', height: 36, fontSize: 12.5 }}
                    required
                  />
                </div>
              )}

              {/* Additional Context / Comments */}
              <div>
                <label
                  htmlFor="rejection-comment"
                  style={{
                    display: 'block',
                    fontSize: 12,
                    fontWeight: 500,
                    color: '#D4D4D8',
                    marginBottom: 6,
                  }}
                >
                  Additional Context & Guidance for Submitter <span style={{ color: '#71717A' }}>(Optional)</span>
                </label>
                <textarea
                  id="rejection-comment"
                  className="df-input"
                  rows={3}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Provide constructive feedback explaining why commercial terms could not be approved..."
                  style={{
                    width: '100%',
                    resize: 'none',
                    padding: '8px 12px',
                    fontSize: 12.5,
                    lineHeight: 1.5,
                  }}
                />
              </div>

              {/* Error Notice */}
              {error && (
                <div
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    color: '#F87171',
                    fontSize: 12,
                  }}
                >
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div
              style={{
                padding: '16px 24px',
                borderTop: '1px solid #1a1a20',
                background: '#08080a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: 10,
              }}
            >
              <button
                type="button"
                disabled={submitting}
                onClick={onClose}
                className="df-btn-secondary"
                style={{ padding: '8px 16px', fontSize: 12.5 }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                style={{
                  padding: '8px 20px',
                  borderRadius: 6,
                  background: '#2d0d0d',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#EF4444',
                  fontWeight: 600,
                  fontSize: 12.5,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  if (!submitting) e.currentTarget.style.background = '#3b1111'
                }}
                onMouseLeave={(e) => {
                  if (!submitting) e.currentTarget.style.background = '#2d0d0d'
                }}
              >
                {submitting ? (
                  <>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        border: '2px solid #EF4444',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 0.6s linear infinite',
                      }}
                    />
                    Rejecting...
                  </>
                ) : (
                  'Confirm Rejection'
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
