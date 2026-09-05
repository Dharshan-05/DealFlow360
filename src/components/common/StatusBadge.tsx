import React from 'react'
import { STATUS_COLORS } from '../../config/constants'

export interface StatusBadgeProps {
  status: string
  size?: 'sm' | 'md'
  showDot?: boolean
  className?: string
  style?: React.CSSProperties
}

export default function StatusBadge({
  status,
  size = 'md',
  showDot = false,
  className = '',
  style = {},
}: StatusBadgeProps) {
  const palette = STATUS_COLORS[status as keyof typeof STATUS_COLORS] || {
    text: '#A1A1AA',
    bg: '#141414',
    border: '#242424',
  }

  const isSmall = size === 'sm'

  return (
    <span
      className={`df-badge ${className}`}
      style={{
        color: palette.text,
        background: palette.bg,
        border: `1px solid ${palette.border}`,
        fontSize: isSmall ? 10 : 11,
        padding: isSmall ? '1px 6px' : '2px 8px',
        ...style,
      }}
    >
      {showDot && (
        <span
          style={{
            width: 5,
            height: 5,
            borderRadius: '50%',
            background: palette.text,
            marginRight: 4,
          }}
        />
      )}
      {status}
    </span>
  )
}
