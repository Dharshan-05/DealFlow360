import React from 'react'
import type { Notification } from '../../types/notification'
import {
  CheckCircle2Icon as CheckCircle,
  AlertCircleIcon as AlertCircle,
  ClockIcon as Clock,
  XIcon as X,
  ArrowRightIcon as ArrowRight,
} from '../common/Icons'

interface Props {
  notification: Notification
  onMarkRead: (id: string) => void
  onMarkUnread: (id: string) => void
  onDelete: (id: string) => void
  onNavigate?: (linkTarget?: string, relatedId?: string) => void
}

export function NotificationItem({
  notification,
  onMarkRead,
  onMarkUnread,
  onDelete,
  onNavigate,
}: Props) {
  const isUnread = !notification.read

  const typeColor =
    notification.type === 'APPROVAL'
      ? '#10b981'
      : notification.type === 'AI'
      ? '#f59e0b'
      : notification.type === 'PROCESSING'
      ? '#3b82f6'
      : notification.type === 'SECURITY'
      ? '#ef4444'
      : '#818cf8'

  const priorityBadge =
    notification.priority === 'CRITICAL'
      ? '#ef4444'
      : notification.priority === 'HIGH'
      ? '#f59e0b'
      : notification.priority === 'MEDIUM'
      ? '#818cf8'
      : '#71717a'

  return (
    <div
      style={{
        background: isUnread ? '#121215' : '#09090b',
        border: '1px solid',
        borderColor: isUnread ? 'rgba(99, 102, 241, 0.25)' : '#1c1c24',
        borderRadius: 8,
        padding: '16px 18px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 14,
        transition: 'all 0.15s ease',
        position: 'relative',
      }}
    >
      {/* Priority Indicator Bar / Dot */}
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: notification.dotColor || priorityBadge,
          marginTop: 6,
          flexShrink: 0,
          boxShadow: isUnread ? `0 0 8px ${notification.dotColor || priorityBadge}` : 'none',
        }}
      />

      {/* Main Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
          {/* Type Badge */}
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              padding: '1px 6px',
              borderRadius: 3,
              color: typeColor,
              background: `${typeColor}18`,
              border: `1px solid ${typeColor}35`,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            {notification.type}
          </span>

          {/* Priority Pill */}
          <span
            style={{
              fontSize: 9,
              fontWeight: 700,
              padding: '1px 5px',
              borderRadius: 3,
              color: priorityBadge,
              background: '#18181b',
              border: '1px solid #27272a',
              textTransform: 'uppercase',
            }}
          >
            {notification.priority}
          </span>

          {/* Timestamp */}
          <span style={{ fontSize: 11, color: '#71717a', marginLeft: 'auto' }}>
            {notification.timeAgo || new Date(notification.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Title */}
        <h4
          style={{
            margin: '0 0 4px',
            fontSize: 13.5,
            fontWeight: isUnread ? 700 : 600,
            color: isUnread ? '#ffffff' : '#d4d4d8',
          }}
        >
          {notification.title}
        </h4>

        {/* Message */}
        <p
          style={{
            margin: '0 0 10px',
            fontSize: 12,
            color: '#a1a1aa',
            lineHeight: 1.45,
          }}
        >
          {notification.message || notification.description}
        </p>

        {/* Action Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 11 }}>
          {notification.relatedResourceId && (
            <span
              className="mono"
              style={{
                fontSize: 10.5,
                color: '#818cf8',
                background: '#18181b',
                padding: '2px 6px',
                borderRadius: 4,
                border: '1px solid #27272a',
              }}
            >
              {notification.relatedResourceId}
            </span>
          )}

          {notification.linkTarget && onNavigate && (
            <button
              onClick={() => onNavigate(notification.linkTarget, notification.relatedResourceId)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#a5b4fc',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                padding: 0,
              }}
            >
              <span>Inspect record</span>
              <ArrowRight size={12} />
            </button>
          )}

          <button
            onClick={() => (isUnread ? onMarkRead(notification.id) : onMarkUnread(notification.id))}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#71717a',
              cursor: 'pointer',
              marginLeft: 'auto',
              padding: 0,
            }}
          >
            {isUnread ? 'Mark read' : 'Mark unread'}
          </button>
        </div>
      </div>

      {/* Delete / Dismiss Button */}
      <button
        onClick={() => onDelete(notification.id)}
        title="Dismiss notification"
        style={{
          background: 'transparent',
          border: 'none',
          color: '#52525b',
          cursor: 'pointer',
          padding: 4,
          borderRadius: 4,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <X size={14} />
      </button>
    </div>
  )
}
