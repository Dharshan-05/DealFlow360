import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { realtimeClient } from '../lib/realtime'
import { ConnectionStatus, EventEnvelope, PersistentNotification } from '../types/realtime'
import { useAuth } from '../hooks/useAuth'
import { api } from '../lib/api'

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
    const token = api.getToken()
    realtimeClient.setToken(token)
  }, [user])

  const refreshNotifications = async () => {
    if (!api.getToken()) return

    try {
      const data = await api.notifications.list({ limit: 20 })
      if (data) {
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
    try {
      await api.notifications.markRead(id)
      refreshNotifications()
    } catch (e) {
      console.error('[RealtimeProvider] Failed to mark read', e)
    }
  }

  const markAllAsRead = async () => {
    try {
      await api.notifications.markAllRead()
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
