import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Approval } from '../../types/approval'

interface Props {
  isOpen: boolean
  approval: Approval | null
  onClose: () => void
  onConfirm: (reason: string, details?: string) => Promise<void>
}

const CHANGE_CATEGORIES = [
  'Reduce discount rate',
  'Adjust payment & billing terms',
  'Provide updated documentation / justification',
  'Adjust product configuration & line items',
  'Clarify SLA & fulfillment scope',
  'Other custom modification',
]

export default function RequestChangesModal({ isOpen, approval, onClose, onConfirm }: Props) {
  const [selectedCategory, setSelectedCategory] = useState(CHANGE_CATEGORIES[0])
  const [instructions, setInstructions] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      setSelectedCategory(CHANGE_CATEGORIES[0])
      setInstructions('')
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
    if (!instructions.trim()) {
      setError('Please provide specific revision instructions for the submitter.')
      return
    }

    setSubmitting(true)
    setError('')
    try {
      await onConfirm(selectedCategory, instructions.trim())
      onClose()
    } catch (err: any) {
      setError(err?.message || 'Failed to request changes. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="change-modal-title"
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
            background: 'rgba(0, 0, 0, 0.8)',
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
            boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(245, 158, 11, 0.15)',
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
                  background: 'rgba(245, 158, 11, 0.12)',
                  border: '1px solid rgba(245, 158, 11, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#F59E0B',
                  fontSize: 16,
                  fontWeight: 700,
                }}
              >
                ✎
              </div>
              <div>
                <h3
                  id="change-modal-title"
                  style={{
                    margin: 0,
                    fontSize: 16,
                    fontWeight: 600,
                    color: '#fff',
                    letterSpacing: '-0.01em',
                  }}
                >
                  Request Changes from Submitter
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
              {/* Revision Notice */}
              <div
                style={{
                  background: 'rgba(245, 158, 11, 0.06)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                  borderRadius: 8,
                  padding: '12px 14px',
                }}
              >
                <div style={{ fontSize: 11.5, fontWeight: 600, color: '#FBBF24', marginBottom: 2 }}>
                  Workflow Impact:
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#A1A1AA', lineHeight: 1.5 }}>
                  This request will transition to <strong style={{ color: '#fff' }}>Changes Requested</strong> and be sent back to{' '}
                  <strong style={{ color: '#fff' }}>{approval.submittedBy}</strong>. The request will become unlocked for editing so they can adjust commercial terms and resubmit.
                </p>
              </div>

              {/* Revision Category Selection */}
              <div>
                <label
                  htmlFor="change-category-select"
                  style={{
                    display: 'block',
                    fontSize: 12,
                    fontWeight: 500,
                    color: '#D4D4D8',
                    marginBottom: 6,
                  }}
                >
                  Revision Category <span style={{ color: '#F59E0B' }}>*</span>
                </label>
                <select
                  id="change-category-select"
                  className="df-input"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  style={{
                    width: '100%',
                    height: 36,
                    fontSize: 12.5,
                    padding: '0 10px',
                    color: '#fff',
                    background: '#121216',
                  }}
                >
                  {CHANGE_CATEGORIES.map((c) => (
                    <option key={c} value={c} style={{ background: '#121216', color: '#fff' }}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Revision Instructions */}
              <div>
                <label
                  htmlFor="change-instructions"
                  style={{
                    display: 'block',
                    fontSize: 12,
                    fontWeight: 500,
                    color: '#D4D4D8',
                    marginBottom: 6,
                  }}
                >
                  Required Action / Modification Instructions <span style={{ color: '#F59E0B' }}>*</span>
                </label>
                <textarea
                  id="change-instructions"
                  className="df-input"
                  rows={3}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Please reduce the discount from 18% to 12% to align with margin thresholds, or attach executive sponsor clearance."
                  style={{
                    width: '100%',
                    resize: 'none',
                    padding: '8px 12px',
                    fontSize: 12.5,
                    lineHeight: 1.5,
                  }}
                  required
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
                  background: '#2e1f0c',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  color: '#F59E0B',
                  fontWeight: 600,
                  fontSize: 12.5,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  if (!submitting) e.currentTarget.style.background = '#3d280d'
                }}
                onMouseLeave={(e) => {
                  if (!submitting) e.currentTarget.style.background = '#2e1f0c'
                }}
              >
                {submitting ? (
                  <>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        border: '2px solid #F59E0B',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 0.6s linear infinite',
                      }}
                    />
                    Submitting...
                  </>
                ) : (
                  'Send Back for Revisions'
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
