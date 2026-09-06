import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { realtimeClient } from '../lib/realtime'
import { ConnectionStatus, EventEnvelope, PersistentNotification } from '../types/realtime'
import { useAuth } from '../hooks/useAuth'

interface RealtimeContextValue {
  status: ConnectionStatus
  lastEvent: EventEnvelope | null
  unreadCount: number
  notifications: PersistentNotification[]
  markAsRead: (id: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  refreshNotifications: () => Promise<void>
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null)

export const RealtimeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth()
  const [status, setStatus] = useState<ConnectionStatus>(realtimeClient.getStatus())
  const [lastEvent, setLastEvent] = useState<EventEnvelope | null>(null)
  const [notifications, setNotifications] = useState<PersistentNotification[]>([])
  const [unreadCount, setUnreadCount] = useState<number>(0)

  // Listen to status changes
  useEffect(() => {
    return realtimeClient.onStatusChange(setStatus)
  }, [])

  // Sync auth token to realtime client
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dealflow_access_token') : null
    realtimeClient.setToken(token)
  }, [user])

  const refreshNotifications = async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dealflow_access_token') : null
    if (!token) return

    try {
      const res = await fetch('/api/v1/notifications?limit=20', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setNotifications(data.items || [])
        setUnreadCount(data.unread_count || 0)
      }
    } catch (e) {
      console.error('[RealtimeProvider] Error fetching notifications', e)
    }
  }

  // Subscribe to realtime notifications and general events
  useEffect(() => {
    refreshNotifications()

    const unsubAll = realtimeClient.subscribe('*', (event) => {
      setLastEvent(event)
      refreshNotifications()
    })

    return () => {
      unsubAll()
    }
  }, [user])

  const markAsRead = async (id: string) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dealflow_access_token') : null
    if (!token) return

    try {
      await fetch(`/api/v1/notifications/${id}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      refreshNotifications()
    } catch (e) {
      console.error('[RealtimeProvider] Failed to mark read', e)
    }
  }

  const markAllAsRead = async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dealflow_access_token') : null
    if (!token) return

    try {
      await fetch('/api/v1/notifications/read-all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      refreshNotifications()
    } catch (e) {
      console.error('[RealtimeProvider] Failed to mark all read', e)
    }
  }

  return (
    <RealtimeContext.Provider
      value={{
        status,
        lastEvent,
        unreadCount,
        notifications,
        markAsRead,
        markAllAsRead,
        refreshNotifications,
      }}
    >
      {children}
    </RealtimeContext.Provider>
  )
}

export function useRealtime() {
  const ctx = useContext(RealtimeContext)
  if (!ctx) {
    throw new Error('useRealtime must be used within a RealtimeProvider')
  }
  return ctx
}
