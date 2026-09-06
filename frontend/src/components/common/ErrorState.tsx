import React from 'react'
import { motion } from 'framer-motion'

export interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  retryLabel?: string
  style?: React.CSSProperties
}

export default function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred while processing this request.',
  onRetry,
  retryLabel = 'Retry',
  style = {},
}: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="df-card"
      style={{
        padding: '36px 24px',
        textAlign: 'center',
        background: 'rgba(239, 68, 68, 0.04)',
        border: '1px solid rgba(239, 68, 68, 0.2)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        ...style,
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#EF4444',
          marginBottom: 14,
        }}
      >
        <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>

      <div style={{ fontSize: 14, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
        {title}
      </div>

      <div style={{ fontSize: 12.5, color: '#A1A1AA', maxWidth: 400, lineHeight: 1.5, marginBottom: onRetry ? 18 : 0 }}>
        {message}
      </div>

      {onRetry && (
        <motion.button
          onClick={onRetry}
          className="df-btn-secondary"
          style={{ padding: '7px 16px', fontSize: 12 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {retryLabel}
        </motion.button>
      )}
    </motion.div>
  )
}
