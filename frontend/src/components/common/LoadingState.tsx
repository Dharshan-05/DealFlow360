import React from 'react'
import { SkeletonCard, SkeletonText } from '../../lib/motion'

export interface LoadingStateProps {
  type?: 'card' | 'text' | 'table' | 'spinner'
  lines?: number
  label?: string
  style?: React.CSSProperties
}

export default function LoadingState({
  type = 'card',
  lines = 4,
  label = 'Loading data...',
  style = {},
}: LoadingStateProps) {
  if (type === 'spinner') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 48,
          gap: 12,
          ...style,
        }}
      >
        <div
          style={{
            width: 22,
            height: 22,
            border: '2px solid #222',
            borderTopColor: '#7C3AED',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <span style={{ fontSize: 12, color: '#555' }}>{label}</span>
      </div>
    )
  }

  if (type === 'text') {
    return (
      <div className="df-card" style={{ padding: 20, ...style }}>
        <SkeletonText lines={lines} />
      </div>
    )
  }

  return <SkeletonCard style={style} />
}
