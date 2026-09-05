import type { Notification, NotificationFilters } from '../types/notification'
import { mockNotifications } from '../mocks/notifications'
import { APPROVALS_UPDATED_EVENT } from './approvalService'
import { EXECUTION_UPDATED_EVENT } from './executionService'
import { TRANSACTIONS_UPDATED_EVENT } from './transactionService'

export const NOTIFICATIONS_STORAGE_KEY = 'dealflow360_notifications'
export const NOTIFICATIONS_UPDATED_EVENT = 'dealflow_notifications_updated'

class NotificationService {
  private listeners: (() => void)[] = []
  private deduplicationSignatures: Set<string> = new Set()

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener(APPROVALS_UPDATED_EVENT, () => {
        this.autoTriggerNotification(
          'APPROVAL',
          'Governance State Updated',
          'A pending commercial exception was reviewed and decision committed.',
          'MEDIUM',
          'approvals'
        )
      })

      window.addEventListener(EXECUTION_UPDATED_EVENT, () => {
        this.autoTriggerNotification(
          'PROCESSING',
          'ERP Execution Pipeline Updated',
          'Simulated Odoo ERP fulfillment stage progression committed.',
          'LOW',
          'fulfillment'
        )
      })

      window.addEventListener(TRANSACTIONS_UPDATED_EVENT, () => {
        this.autoTriggerNotification(
          'PROCESSING',
          'Financial Transaction Registered',
          'New settled transaction registered into company commercial ledger.',
          'LOW',
          'billing'
        )
      })
    }
  }

  public subscribe(callback: () => void): () => void {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback)
    }
  }

  private notify(): void {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(NOTIFICATIONS_UPDATED_EVENT))
      this.listeners.forEach((cb) => cb())
    }
  }

  private autoTriggerNotification(
    type: any,
    title: string,
    message: string,
    priority: any,
    linkTarget?: string
  ) {
    const sig = `${type}_${title}_${Date.now().toString().slice(0, -3)}`
    if (this.deduplicationSignatures.has(sig)) return
    this.deduplicationSignatures.add(sig)
    setTimeout(() => this.deduplicationSignatures.delete(sig), 4000)

    this.addNotification({
      type,
      title,
      message,
      priority,
      linkTarget,
      dotColor: priority === 'HIGH' || priority === 'CRITICAL' ? '#EF4444' : '#10B981',
    })
  }

  public getNotifications(filters?: NotificationFilters): Notification[] {
    try {
      const raw = localStorage.getItem(NOTIFICATIONS_STORAGE_KEY)
      let list: Notification[] = raw ? JSON.parse(raw) : mockNotifications
      if (!raw) {
        this.saveNotifications(mockNotifications)
      }

      if (!filters) return list

      return list.filter((n) => {
        if (filters.type && filters.type !== 'All' && filters.type !== 'all' && n.type !== filters.type) {
          return false
        }
        if (filters.priority && filters.priority !== 'All' && n.priority !== filters.priority) {
          return false
        }
        if (filters.readStatus === 'unread' && n.read) return false
        if (filters.readStatus === 'read' && !n.read) return false
        if (filters.search) {
          const q = filters.search.toLowerCase()
          if (!n.title.toLowerCase().includes(q) && !(n.message || n.description || '').toLowerCase().includes(q)) {
            return false
          }
        }
        return true
      })
    } catch {
      return mockNotifications
    }
  }

  private saveNotifications(list: Notification[]): void {
    try {
      localStorage.setItem(NOTIFICATIONS_STORAGE_KEY, JSON.stringify(list))
      this.notify()
    } catch (e) {
      console.error('Failed to save notifications to localStorage', e)
    }
  }

  public getUnreadCount(): number {
    return this.getNotifications().filter((n) => !n.read).length
  }

  public markAsRead(id: string): void {
    const list = this.getNotifications().map((n) =>
      n.id === id ? { ...n, read: true, isRead: true } : n
    )
    this.saveNotifications(list)
  }

  public markAsUnread(id: string): void {
    const list = this.getNotifications().map((n) =>
      n.id === id ? { ...n, read: false, isRead: false } : n
    )
    this.saveNotifications(list)
  }

  public markAllAsRead(): void {
    const list = this.getNotifications().map((n) => ({
      ...n,
      read: true,
      isRead: true,
    }))
    this.saveNotifications(list)
  }

  public deleteNotification(id: string): void {
    const list = this.getNotifications().filter((n) => n.id !== id)
    this.saveNotifications(list)
  }

  public addNotification(notif: Partial<Notification>): Notification {
    const existing = this.getNotifications()
    const newNotif: Notification = {
      id: notif.id || `NOTIF-2026-${(existing.length + 1).toString().padStart(3, '0')}`,
      type: notif.type || 'SYSTEM',
      title: notif.title || 'System Notification',
      message: notif.message || notif.description || 'System activity reported.',
      description: notif.message || notif.description || 'System activity reported.',
      timestamp: notif.timestamp || new Date().toISOString(),
      timeAgo: notif.timeAgo || 'Just now',
      priority: notif.priority || 'LOW',
      read: false,
      isRead: false,
      relatedResource: notif.relatedResource,
      relatedResourceId: notif.relatedResourceId,
      linkTarget: notif.linkTarget,
      dotColor: notif.dotColor || '#818CF8',
      metadata: notif.metadata,
    }

    const updated = [newNotif, ...existing]
    if (updated.length > 50) updated.pop()
    this.saveNotifications(updated)
    return newNotif
  }

  public clearAll(): void {
    this.saveNotifications([])
  }

  public resetToDefaults(): void {
    this.saveNotifications(mockNotifications)
  }
}

export const notificationService = new NotificationService()
