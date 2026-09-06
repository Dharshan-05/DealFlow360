import {
  ClientMessage,
  ConnectionStatus,
  EventEnvelope,
  RealtimeTopic,
  ServerMessage,
} from '../types/realtime'

type EventHandler = (event: EventEnvelope) => void
type StatusListener = (status: ConnectionStatus) => void

export class RealtimeClient {
  private socket: WebSocket | null = null
  private status: ConnectionStatus = 'DISCONNECTED'
  private token: string | null = null
  private baseUrl: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectTimer: any = null
  private pingInterval: any = null
  private subscribers: Map<string, Set<EventHandler>> = new Map()
  private statusListeners: Set<StatusListener> = new Set()
  private subscribedTopics: Set<string> = new Set()

  constructor() {
    // Dynamically calculate WS URL based on current host or standard API port
    const isBrowser = typeof window !== 'undefined'
    const protocol = isBrowser && window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = isBrowser ? (window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host) : 'localhost:8000'
    this.baseUrl = `${protocol}//${host}/api/v1/ws`
  }

  public setToken(token: string | null) {
    this.token = token
    if (token && this.status === 'DISCONNECTED') {
      this.connect()
    } else if (!token && this.socket) {
      this.disconnect()
    }
  }

  public getStatus(): ConnectionStatus {
    return this.status
  }

  public onStatusChange(listener: StatusListener): () => void {
    this.statusListeners.add(listener)
    listener(this.status)
    return () => this.statusListeners.delete(listener)
  }

  private setStatus(newStatus: ConnectionStatus) {
    if (this.status !== newStatus) {
      this.status = newStatus
      this.statusListeners.forEach((fn) => fn(newStatus))
    }
  }

  public connect(): void {
    if (typeof window === 'undefined' || !this.token) return
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    this.setStatus(this.reconnectAttempts > 0 ? 'RECONNECTING' : 'CONNECTING')

    try {
      const url = `${this.baseUrl}?token=${encodeURIComponent(this.token)}`
      this.socket = new WebSocket(url)

      this.socket.onopen = () => {
        this.setStatus('CONNECTED')
        this.reconnectAttempts = 0
        this.startHeartbeat()

        // Re-subscribe to all active topics
        this.subscribedTopics.forEach((topic) => {
          this.sendMessage({ action: 'subscribe', topic })
        })
      }

      this.socket.onmessage = (ev) => {
        try {
          const msg: ServerMessage = JSON.parse(ev.data)
          this.handleServerMessage(msg)
        } catch (err) {
          console.error('[RealtimeClient] Failed to parse message', err)
        }
      }

      this.socket.onclose = () => {
        this.stopHeartbeat()
        this.socket = null
        this.setStatus('DISCONNECTED')
        this.scheduleReconnect()
      }

      this.socket.onerror = (err) => {
        console.warn('[RealtimeClient] WebSocket error', err)
      }
    } catch (e) {
      console.error('[RealtimeClient] Connection failure', e)
      this.setStatus('DISCONNECTED')
      this.scheduleReconnect()
    }
  }

  public disconnect(): void {
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.setStatus('DISCONNECTED')
  }

  public subscribe(topic: RealtimeTopic | string, handler: EventHandler): () => void {
    if (!this.subscribers.has(topic)) {
      this.subscribers.set(topic, new Set())
    }
    this.subscribers.get(topic)!.add(handler)

    if (!this.subscribedTopics.has(topic)) {
      this.subscribedTopics.add(topic)
      if (this.status === 'CONNECTED') {
        this.sendMessage({ action: 'subscribe', topic })
      }
    }

    return () => {
      const set = this.subscribers.get(topic)
      if (set) {
        set.delete(handler)
        if (set.size === 0) {
          this.subscribers.delete(topic)
          this.subscribedTopics.delete(topic)
          if (this.status === 'CONNECTED') {
            this.sendMessage({ action: 'unsubscribe', topic })
          }
        }
      }
    }
  }

  public sendMessage(msg: ClientMessage): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(msg))
    }
  }

  private handleServerMessage(msg: ServerMessage) {
    if (msg.type === 'event' && msg.payload) {
      const event: EventEnvelope = msg.payload
      const topic = msg.topic || 'notifications'

      // Dispatch to topic subscribers
      const topicSubs = this.subscribers.get(topic)
      if (topicSubs) {
        topicSubs.forEach((fn) => fn(event))
      }

      // Dispatch to wildcard subscribers
      const allSubs = this.subscribers.get('*')
      if (allSubs) {
        allSubs.forEach((fn) => fn(event))
      }
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.pingInterval = setInterval(() => {
      this.sendMessage({ action: 'ping' })
    }, 25000)
  }

  private stopHeartbeat(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts || !this.token) {
      return
    }

    this.reconnectAttempts += 1
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 20000)
    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }
}

export const realtimeClient = new RealtimeClient()
