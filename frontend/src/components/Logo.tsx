import React from 'react'

interface LogoProps {
  size?: number
  className?: string
  style?: React.CSSProperties
  rounded?: number | string
  withText?: boolean
  textColor?: string
  textSize?: number
}

export default function Logo({
  size = 28,
  className = '',
  style = {},
  rounded = '50%',
  withText = false,
  textColor = '#ffffff',
  textSize = 14,
}: LogoProps) {
  return (
    <div
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        userSelect: 'none',
        ...style,
      }}
    >
      <img
        src="/logo.png"
        alt="DealFlow360 Logo"
        width={size}
        height={size}
        style={{
          width: size,
          height: size,
          borderRadius: rounded,
          objectFit: 'cover',
          display: 'block',
          flexShrink: 0,
          boxShadow: '0 2px 8px rgba(37, 99, 235, 0.25)',
        }}
      />
      {withText && (
        <span
          style={{
            fontWeight: 700,
            fontSize: textSize,
            color: textColor,
            letterSpacing: '-0.025em',
            whiteSpace: 'nowrap',
          }}
        >
          DealFlow360
        </span>
      )}
    </div>
  )
}
