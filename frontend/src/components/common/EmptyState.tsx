import React from 'react'
import { motion } from 'framer-motion'

export interface EmptyStateProps {
  title?: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  icon?: React.ReactNode
  className?: string
  style?: React.CSSProperties
}

export default function EmptyState({
  title = 'No items found',
  description = 'There are no records matching your current filter criteria.',
  actionLabel,
  onAction,
  icon,
  className = '',
  style = {},
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`df-card ${className}`}
      style={{
        padding: '56px 24px',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        ...style,
      }}
    >
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 10,
          background: '#151515',
          border: '1px solid #222',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#555',
          marginBottom: 16,
        }}
      >
        {icon || (
          <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        )}
      </div>

      <h3 style={{ fontSize: 14, fontWeight: 600, color: '#fff', marginBottom: 6 }}>
        {title}
      </h3>

      <p style={{ fontSize: 13, color: '#666', maxWidth: 360, lineHeight: 1.5, margin: 0 }}>
        {description}
      </p>

      {actionLabel && onAction && (
        <motion.button
          onClick={onAction}
          className="df-btn-primary"
          style={{ marginTop: 20, padding: '8px 16px', fontSize: 12.5 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {actionLabel}
        </motion.button>
      )}
    </motion.div>
  )
}
