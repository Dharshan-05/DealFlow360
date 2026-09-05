import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNotifications } from '../hooks/useNotifications'
import type { NotificationFilters } from '../types/notification'
import { NotificationItem } from '../components/notifications/NotificationItem'
import {
  CheckCircle2Icon as CheckCircle,
  RotateCcwIcon as RotateCcw,
  FilterIcon as Filter,
  AlertCircleIcon as AlertCircle,
} from '../components/common/Icons'

interface Props {
  onNavigateView?: (view: string, id?: string) => void
}

export default function Notifications({ onNavigateView }: Props) {
  const [selectedType, setSelectedType] = useState<string>('All')
  const [selectedPriority, setSelectedPriority] = useState<string>('All')
  const [readStatus, setReadStatus] = useState<'all' | 'unread' | 'read'>('all')
  const [search, setSearch] = useState('')
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3000)
  }

  const filters: NotificationFilters = useMemo(
    () => ({
      type: selectedType === 'All' ? undefined : selectedType,
      priority: selectedPriority === 'All' ? undefined : selectedPriority,
      readStatus,
      search: search || undefined,
    }),
    [selectedType, selectedPriority, readStatus, search]
  )

  const {
    notifications,
    unreadCount,
    markAsRead,
    markAsUnread,
    markAllAsRead,
    deleteNotification,
    clearAll,
    resetNotifications,
  } = useNotifications(filters)

  const handleNavigate = (target?: string, id?: string) => {
    if (target && onNavigateView) {
      onNavigateView(target, id)
    }
  }

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1200, margin: '0 auto', color: '#f3f4f6' }}>
      {/* Toast Notification */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={{
              position: 'fixed',
              top: 24,
              right: 28,
              zIndex: 9999,
              background: '#09090b',
              border: '1px solid #27272a',
              padding: '10px 18px',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 13,
              color: '#e4e4e7',
              boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
            }}
          >
            <CheckCircle size={16} color="#10b981" />
            <span>{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 20,
          marginBottom: 24,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <h1 style={{ margin: 0, color: '#ffffff', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>
              Notifications & Alerts
            </h1>
            {unreadCount > 0 && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 12,
                  background: 'rgba(239, 68, 68, 0.15)',
                  color: '#ef4444',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                }}
              >
                {unreadCount} Unread
              </span>
            )}
          </div>
          <p style={{ margin: 0, color: '#71717a', fontSize: 13, maxWidth: 640, lineHeight: 1.5 }}>
            Real-time feed of commercial approval reviews, AI risk alerts, simulated ERP execution dispatches, and access notifications.
          </p>
        </div>

        {/* Header Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              markAllAsRead()
              showToast('All notifications marked as read')
            }}
            disabled={unreadCount === 0}
            style={{
              padding: '6px 14px',
              fontSize: 12,
              fontWeight: 600,
              background: '#27272a',
              border: '1px solid #3f3f46',
              borderRadius: 6,
              color: unreadCount > 0 ? '#ffffff' : '#71717a',
              cursor: unreadCount > 0 ? 'pointer' : 'not-allowed',
            }}
          >
            Mark all read
          </button>

          <button
            onClick={() => {
              resetNotifications()
              showToast('Restored default enterprise notifications')
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 12px',
              fontSize: 12,
              background: '#18181b',
              border: '1px solid #27272a',
              borderRadius: 6,
              color: '#d4d4d8',
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={14} />
            Reset Defaults
          </button>
        </div>
      </header>

      {/* Filter Toolbar */}
      <div
        style={{
          background: '#09090b',
          border: '1px solid #1c1c24',
          borderRadius: 8,
          padding: '14px 18px',
          marginBottom: 20,
          display: 'flex',
          gap: 12,
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        {/* Search */}
        <div style={{ flex: 1, minWidth: 200 }}>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search notification messages, references..."
            style={{
              width: '100%',
              background: '#121215',
              border: '1px solid #27272a',
              borderRadius: 6,
              padding: '7px 12px',
              fontSize: 12,
              color: '#ffffff',
            }}
          />
        </div>

        {/* Category Pills */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {['All', 'APPROVAL', 'AI', 'PROCESSING', 'SECURITY', 'SYSTEM'].map((cat) => {
            const isSelected = selectedType === cat
            return (
              <button
                key={cat}
                onClick={() => setSelectedType(cat)}
                style={{
                  padding: '5px 12px',
                  fontSize: 11,
                  fontWeight: isSelected ? 700 : 500,
                  borderRadius: 6,
                  background: isSelected ? '#6366f1' : '#18181b',
                  color: isSelected ? '#ffffff' : '#71717a',
                  border: isSelected ? '1px solid #6366f1' : '1px solid #27272a',
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  transition: 'all 0.15s ease',
                }}
              >
                {cat.toLowerCase()}
              </button>
            )
          })}
        </div>

        {/* Read Status Selector */}
        <select
          value={readStatus}
          onChange={(e) => setReadStatus(e.target.value as any)}
          style={{
            background: '#121215',
            border: '1px solid #27272a',
            borderRadius: 6,
            padding: '7px 12px',
            fontSize: 12,
            color: '#e4e4e7',
            cursor: 'pointer',
          }}
        >
          <option value="all">All Statuses</option>
          <option value="unread">Unread Only</option>
          <option value="read">Read Only</option>
        </select>

        {/* Priority Selector */}
        <select
          value={selectedPriority}
          onChange={(e) => setSelectedPriority(e.target.value)}
          style={{
            background: '#121215',
            border: '1px solid #27272a',
            borderRadius: 6,
            padding: '7px 12px',
            fontSize: 12,
            color: '#e4e4e7',
            cursor: 'pointer',
          }}
        >
          <option value="All">All Priorities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      {/* Notification Stream */}
      {notifications.length === 0 ? (
        <div
          style={{
            background: '#09090b',
            border: '1px solid #1c1c24',
            borderRadius: 8,
            padding: '48px 24px',
            textAlign: 'center',
          }}
        >
          <div style={{ color: '#52525b', fontSize: 14, fontWeight: 500 }}>
            No notifications match your current filter settings.
          </div>
          <p style={{ color: '#3f3f46', fontSize: 12, margin: '6px 0 0' }}>
            New system and workflow alerts will automatically appear here.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {notifications.map((notif) => (
            <NotificationItem
              key={notif.id}
              notification={notif}
              onMarkRead={markAsRead}
              onMarkUnread={markAsUnread}
              onDelete={deleteNotification}
              onNavigate={handleNavigate}
            />
          ))}
        </div>
      )}
    </div>
  )
}
