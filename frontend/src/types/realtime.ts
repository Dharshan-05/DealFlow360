export type RealtimeTopic =
  | '*'
  | 'transactions'
  | 'approvals'
  | 'inventory'
  | 'deal_health'
  | 'ai'
  | 'notifications'

export interface EventEnvelope<T = any> {
  event_id: string
  event_type: string
  version: number
  timestamp: string
  company_id: string
  actor_id?: string | null
  entity_type: string
  entity_id: string
  correlation_id?: string | null
  payload: T
}

export type ServerMessageType = 'event' | 'ack' | 'pong' | 'error'

export interface ServerMessage<T = any> {
  type: ServerMessageType
  topic?: string
  correlation_id?: string | null
  payload: T
  timestamp: string
}

export interface ClientMessage {
  action: 'subscribe' | 'unsubscribe' | 'ping'
  topic?: string
  correlation_id?: string
}

export type ConnectionStatus = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING'

export interface PersistentNotification {
  id: string
  company_id: string
  user_id?: string | null
  recipient_role?: string | null
  title: string
  message: string
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT'
  event_type: string
  entity_type: string
  entity_id: string
  payload?: any
  is_read: boolean
  read_at?: string | null
  created_at: string
}
