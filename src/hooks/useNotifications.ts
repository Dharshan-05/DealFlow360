import { useState, useEffect, useCallback } from 'react'
import { notificationService } from '../services/notificationService'
import type { Notification, NotificationFilters } from '../types/notification'

export function useNotifications(initialFilters?: NotificationFilters) {
  const [filters, setFilters] = useState<NotificationFilters>(initialFilters || {})
  const [notifications, setNotifications] = useState<Notification[]>(() =>
    notificationService.getNotifications(initialFilters)
  )
  const [unreadCount, setUnreadCount] = useState<number>(() =>
    notificationService.getUnreadCount()
  )

  const reload = useCallback(() => {
    setNotifications(notificationService.getNotifications(filters))
    setUnreadCount(notificationService.getUnreadCount())
  }, [filters])

  useEffect(() => {
    reload()
    const unsubscribe = notificationService.subscribe(reload)
    return () => unsubscribe()
  }, [reload])

  const markAsRead = useCallback((id: string) => {
    notificationService.markAsRead(id)
    reload()
  }, [reload])

  const markAsUnread = useCallback((id: string) => {
    notificationService.markAsUnread(id)
    reload()
  }, [reload])

  const markAllAsRead = useCallback(() => {
    notificationService.markAllAsRead()
    reload()
  }, [reload])

  const deleteNotification = useCallback((id: string) => {
    notificationService.deleteNotification(id)
    reload()
  }, [reload])

  const clearAll = useCallback(() => {
    notificationService.clearAll()
    reload()
  }, [reload])

  const resetNotifications = useCallback(() => {
    notificationService.resetToDefaults()
    reload()
  }, [reload])

  return {
    notifications,
    unreadCount,
    filters,
    setFilters,
    markAsRead,
    markAsUnread,
    markAllAsRead,
    deleteNotification,
    clearAll,
    resetNotifications,
    reload,
  }
}
