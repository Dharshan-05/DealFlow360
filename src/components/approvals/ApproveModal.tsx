import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Approval } from '../../types/approval'

interface Props {
  isOpen: boolean
  approval: Approval | null
  onClose: () => void
  onConfirm: (comment: string) => Promise<void>
}

export default function ApproveModal({ isOpen, approval, onClose, onConfirm }: Props) {
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await onConfirm(comment.trim())
      onClose()
    } catch (err: any) {
      setError(err?.message || 'Failed to approve request. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="approve-modal-title"
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
            background: 'rgba(0, 0, 0, 0.78)',
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
            boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(16, 185, 129, 0.15)',
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
                  background: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#10B981',
                  fontSize: 16,
                  fontWeight: 700,
                }}
              >
                ✓
              </div>
              <div>
                <h3
                  id="approve-modal-title"
                  style={{
                    margin: 0,
                    fontSize: 16,
                    fontWeight: 600,
                    color: '#fff',
                    letterSpacing: '-0.01em',
                  }}
                >
                  Approve Transaction Request
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
              {/* Deal Summary Grid */}
              <div
                style={{
                  background: '#111116',
                  borderRadius: 8,
                  border: '1px solid #1c1c24',
                  padding: '14px 16px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ fontSize: 10.5, color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>
                    Deal Value
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#fff', marginTop: 2 }} className="mono">
                    {approval.amount}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10.5, color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>
                    Req. Discount
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#EF4444', marginTop: 2 }} className="mono">
                    {approval.requestedValue}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10.5, color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>
                    AI Guidance
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#7C3AED', marginTop: 2 }} className="mono">
                    {approval.aiRecommended}
                  </div>
                </div>
              </div>

              {/* AI Recommendation Context */}
              <div
                style={{
                  background: 'rgba(124, 58, 237, 0.06)',
                  border: '1px solid rgba(124, 58, 237, 0.2)',
                  borderRadius: 8,
                  padding: '12px 14px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#A78BFA', textTransform: 'uppercase' }}>
                      ✦ AI Recommendation Signal
                    </span>
                  </div>
                  <span className="mono" style={{ fontSize: 11, color: '#D4D4D8' }}>
                    {approval.aiConfidenceScore || 92}% Confidence
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#A1A1AA', lineHeight: 1.5 }}>
                  {approval.aiSummary || 'Terms evaluated within risk tolerances. Gross margins protected.'}
                </p>
              </div>

              {/* Consequence Notice */}
              <div
                style={{
                  background: 'rgba(16, 185, 129, 0.06)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                  borderRadius: 8,
                  padding: '12px 14px',
                }}
              >
                <div style={{ fontSize: 11.5, fontWeight: 600, color: '#34D399', marginBottom: 2 }}>
                  Approval Consequences:
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#A1A1AA', lineHeight: 1.5 }}>
                  Approving this transaction confirms commercial discount clearance. The request status will transition to{' '}
                  <strong style={{ color: '#fff' }}>Approved (Ready for Execution)</strong>, making it eligible for Phase 7 dispatch.
                </p>
              </div>

              {/* Optional Approval Comment */}
              <div>
                <label
                  htmlFor="approval-comment"
                  style={{
                    display: 'block',
                    fontSize: 12,
                    fontWeight: 500,
                    color: '#D4D4D8',
                    marginBottom: 6,
                  }}
                >
                  Decision Comment / Conditions <span style={{ color: '#71717A' }}>(Optional)</span>
                </label>
                <textarea
                  id="approval-comment"
                  className="df-input"
                  rows={2}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="e.g. Approved with standard 30-day payment commitment."
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
                  background: '#0d2d1a',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#10B981',
                  fontWeight: 600,
                  fontSize: 12.5,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  if (!submitting) e.currentTarget.style.background = '#113b22'
                }}
                onMouseLeave={(e) => {
                  if (!submitting) e.currentTarget.style.background = '#0d2d1a'
                }}
              >
                {submitting ? (
                  <>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        border: '2px solid #10B981',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 0.6s linear infinite',
                      }}
                    />
                    Approving...
                  </>
                ) : (
                  'Confirm Approval'
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
