export type NotificationType =
  | 'approval'
  | 'ai_alert'
  | 'system'
  | 'execution'
  | 'APPROVAL'
  | 'AI'
  | 'PROCESSING'
  | 'SYSTEM'
  | 'SECURITY'

export type NotificationPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  description?: string // backwards compatibility alias for message
  timestamp: string
  createdAt?: string // alias for timestamp
  timeAgo?: string
  priority: NotificationPriority
  read: boolean
  isRead?: boolean // backwards compatibility
  relatedResource?: string
  relatedResourceId?: string
  resourceType?: string // alias for relatedResource
  resourceId?: string // alias for relatedResourceId
  linkTarget?: string
  dotColor?: string
  metadata?: Record<string, any>
}

export interface NotificationFilters {
  type?: string
  priority?: string
  readStatus?: 'all' | 'unread' | 'read'
  search?: string
}

