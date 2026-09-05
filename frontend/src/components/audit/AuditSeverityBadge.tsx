import React from 'react'
import type { AuditSeverity, AuditResult } from '../../types/audit'

interface Props {
  severity?: AuditSeverity
  result?: AuditResult
  className?: string
  style?: React.CSSProperties
}

export function AuditSeverityBadge({ severity, result, style }: Props) {
  if (result) {
    const isSuccess = result === 'SUCCESS'
    const isFailure = result === 'FAILURE' || result === 'DENIED'
    const isWarning = result === 'WARNING'

    const color = isSuccess ? '#10B981' : isFailure ? '#EF4444' : isWarning ? '#F59E0B' : '#71717A'
    const bg = isSuccess ? 'rgba(16, 185, 129, 0.12)' : isFailure ? 'rgba(239, 68, 68, 0.12)' : isWarning ? 'rgba(245, 158, 11, 0.12)' : 'rgba(113, 113, 122, 0.12)'
    const border = isSuccess ? 'rgba(16, 185, 129, 0.25)' : isFailure ? 'rgba(239, 68, 68, 0.25)' : isWarning ? 'rgba(245, 158, 11, 0.25)' : 'rgba(113, 113, 122, 0.25)'

    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: '2px 7px',
          borderRadius: 4,
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          color,
          backgroundColor: bg,
          border: `1px solid ${border}`,
          ...style,
        }}
      >
        {result}
      </span>
    )
  }

  const s = severity || 'INFO'
  const isCritical = s === 'CRITICAL'
  const isHigh = s === 'HIGH'
  const isMedium = s === 'MEDIUM'
  const isLow = s === 'LOW'

  const color = isCritical
    ? '#EF4444'
    : isHigh
    ? '#F59E0B'
    : isMedium
    ? '#818CF8'
    : isLow
    ? '#10B981'
    : '#A1A1AA'

  const bg = isCritical
    ? 'rgba(239, 68, 68, 0.12)'
    : isHigh
    ? 'rgba(245, 158, 11, 0.12)'
    : isMedium
    ? 'rgba(129, 140, 248, 0.12)'
    : isLow
    ? 'rgba(16, 185, 129, 0.12)'
    : 'rgba(161, 161, 170, 0.12)'

  const border = isCritical
    ? 'rgba(239, 68, 68, 0.25)'
    : isHigh
    ? 'rgba(245, 158, 11, 0.25)'
    : isMedium
    ? 'rgba(129, 140, 248, 0.25)'
    : isLow
    ? 'rgba(16, 185, 129, 0.25)'
    : 'rgba(161, 161, 170, 0.25)'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 7px',
        borderRadius: 4,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
        color,
        backgroundColor: bg,
        border: `1px solid ${border}`,
        ...style,
      }}
    >
      {s}
    </span>
  )
}
