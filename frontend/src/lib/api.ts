/**
 * DealFlow360 Centralized Typed HTTP/WebSocket API Client
 * Enterprise-grade client with auth token injection, tenant safety,
 * timeout handling, error normalization, and complete domain namespaces.
 */

export interface ApiResponse<T = any> {
  success?: boolean
  data: T
  message?: string
}

export interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  params?: Record<string, string | number | boolean | undefined | null>
  timeoutMs?: number
}

export class ApiError extends Error {
  public status: number
  public detail?: string
  public errors?: Record<string, any>
  public rawData?: unknown

  constructor(message: string, status: number, rawData?: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.rawData = rawData
    this.detail = typeof rawData === 'string' ? rawData : (rawData?.detail || rawData?.message || message)
    this.errors = rawData?.errors || (Array.isArray(rawData?.detail) ? { validation: rawData.detail } : undefined)
  }
}

class ApiClient {
  private baseUrl: string
  private token: string | null = null
  private defaultTimeoutMs: number = 30000

  constructor() {
    const metaEnv = typeof import.meta !== 'undefined' ? (import.meta as any).env : {}
    const configuredUrl = metaEnv?.VITE_API_BASE_URL || metaEnv?.NEXT_PUBLIC_API_URL || ''
    this.baseUrl = configuredUrl.replace(/\/+$/, '')
  }

  public setToken(token: string | null): void {
    this.token = token
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('dealflow_access_token', token)
      } else {
        localStorage.removeItem('dealflow_access_token')
      }
    }
  }

  public getToken(): string | null {
    if (this.token) return this.token
    if (typeof window !== 'undefined') {
      return localStorage.getItem('dealflow_access_token')
    }
    return null
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, '')
  }

  public getBaseUrl(): string {
    return this.baseUrl
  }

  private buildUrl(endpoint: string, params?: ApiRequestOptions['params']): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
    // If endpoint already starts with /api/v1, preserve it; otherwise prepend /api/v1
    const path = cleanEndpoint.startsWith('/api/v1') ? cleanEndpoint : `/api/v1${cleanEndpoint}`
    const fullPath = this.baseUrl ? `${this.baseUrl}${path}` : path

    if (!params) return fullPath

    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val))
      }
    })
    const qs = searchParams.toString()
    return qs ? `${fullPath}?${qs}` : fullPath
  }

  public async request<T = any>(
    method: string,
    endpoint: string,
    options: ApiRequestOptions = {}
  ): Promise<T> {
    const { body, params, headers = {}, timeoutMs = this.defaultTimeoutMs, ...rest } = options
    const url = this.buildUrl(endpoint, params)
    const token = this.getToken()

    const requestHeaders: Record<string, string> = {
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers as Record<string, string>),
    }

    if (body && !(body instanceof FormData) && !(body instanceof Blob)) {
      requestHeaders['Content-Type'] = 'application/json'
    }

    const controller = new AbortController()
    const timerId = setTimeout(() => controller.abort(), timeoutMs)

    try {
      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body instanceof FormData || body instanceof Blob ? body : body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
        ...rest,
      })
      clearTimeout(timerId)

      const contentType = response.headers.get('content-type') || ''
      const isJson = contentType.includes('application/json')
      const data = isJson ? await response.json() : await response.text()

      if (!response.ok) {
        if (response.status === 401 && typeof window !== 'undefined') {
          this.setToken(null)
          window.dispatchEvent(new CustomEvent('dealflow_auth_unauthorized'))
        }

        const errorMessage =
          (isJson && (data.detail || data.message)) ||
          response.statusText ||
          `HTTP Error ${response.status}`

        throw new ApiError(errorMessage, response.status, data)
      }

      // If response is wrapped in standard ApiResponse envelope, unpack data
      if (isJson && data && typeof data === 'object' && 'data' in data && 'success' in data) {
        return data.data as T
      }

      return data as T
    } catch (err: any) {
      clearTimeout(timerId)
      if (err.name === 'AbortError') {
        throw new ApiError(`Request timeout after ${timeoutMs}ms`, 408)
      }
      if (err instanceof ApiError) {
        throw err
      }
      throw new ApiError(err?.message || 'Network error or backend unreachable', 0, err)
    }
  }

  public get<T = any>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
    return this.request<T>('GET', endpoint, options)
  }

  public post<T = any>(endpoint: string, body?: unknown, options?: ApiRequestOptions): Promise<T> {
    return this.request<T>('POST', endpoint, { ...options, body })
  }

  public put<T = any>(endpoint: string, body?: unknown, options?: ApiRequestOptions): Promise<T> {
    return this.request<T>('PUT', endpoint, { ...options, body })
  }

  public patch<T = any>(endpoint: string, body?: unknown, options?: ApiRequestOptions): Promise<T> {
    return this.request<T>('PATCH', endpoint, { ...options, body })
  }

  public delete<T = any>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
    return this.request<T>('DELETE', endpoint, options)
  }

  // ===========================================================================
  // Domain Namespaces
  // ===========================================================================

  public auth = {
    login: (credentials: { email: string; password?: string }) =>
      this.post<{ access_token: string; token_type: string }>('/auth/login', credentials),
    register: (userData: { email: string; password: string; first_name: string; last_name: string }) =>
      this.post<any>('/auth/register', userData),
    me: () => this.get<any>('/auth/me'),
    logout: () => this.post<any>('/auth/logout'),
    refresh: (refreshToken?: string) =>
      this.post<{ access_token: string; token_type: string }>('/auth/refresh', { refresh_token: refreshToken }),
  }

  public customers = {
    list: (params?: { skip?: number; limit?: number; search?: string; is_active?: boolean }) =>
      this.get<{ items: any[]; total: number; skip: number; limit: number }>('/customers', { params }),
    get: (id: string) => this.get<any>(`/customers/${id}`),
    create: (data: any) => this.post<any>('/customers', data),
    update: (id: string, data: any) => this.put<any>(`/customers/${id}`, data),
    delete: (id: string) => this.delete<any>(`/customers/${id}`),
    analytics: () => this.get<any>('/customers/analytics'),
  }

  public products = {
    list: (params?: { skip?: number; limit?: number; search?: string; category_id?: string; inventory_status?: string }) =>
      this.get<{ items: any[]; total: number; skip: number; limit: number }>('/products', { params }),
    get: (id: string) => this.get<any>(`/products/${id}`),
    create: (data: any) => this.post<any>('/products', data),
    update: (id: string, data: any) => this.put<any>(`/products/${id}`, data),
    delete: (id: string) => this.delete<any>(`/products/${id}`),
    categories: () => this.get<any[]>('/product-categories'),
  }

  public inventory = {
    dashboard: () => this.get<any>('/inventory/dashboard'),
    alerts: (params?: { is_active?: boolean; severity?: string; skip?: number; limit?: number }) =>
      this.get<any>('/inventory/alerts', { params }),
    warehouses: () => this.get<any[]>('/warehouses'),
  }

  public discounts = {
    evaluate: (payload: any) =>
      this.post<any>('/governance/discounts/automation/evaluate-decision', payload),
    configurations: () => this.get<any>('/governance/discounts/configurations'),
  }

  public approvals = {
    list: (params?: { status?: string; skip?: number; limit?: number }) =>
      this.get<any[]>('/approvals/requests', { params }),
    get: (id: string) => this.get<any>(`/approvals/requests/${id}`),
    submit: (payload: any) => this.post<any>('/approvals/requests', payload),
    approve: (id: string, notes?: string) =>
      this.post<any>(`/approvals/requests/${id}/approve`, { notes }),
    reject: (id: string, reason?: string) =>
      this.post<any>(`/approvals/decision?approval_request_id=${id}&decision=REJECTED${reason ? `&reason=${encodeURIComponent(reason)}` : ''}`),
    escalate: (id: string, reason: string) =>
      this.post<any>(`/approvals/requests/${id}/escalate`, { reason }),
    dashboard: () => this.get<any>('/approvals/dashboard'),
    auditTrail: (id: string) => this.get<any[]>(`/approvals/requests/${id}/audit`),
  }

  public quotes = {
    list: (params?: { skip?: number; limit?: number; status?: string; search?: string }) =>
      this.get<any[]>('/quotations', { params }),
    get: (id: string) => this.get<any>(`/quotations/${id}`),
    create: (data: any) => this.post<any>('/quotations', data),
    update: (id: string, data: any) => this.put<any>(`/quotations/${id}`, data),
    calculate: (data: any) => this.post<any>('/quotations/calculate', data),
    submitApproval: (id: string, notes?: string) =>
      this.post<any>(`/quotations/${id}/submit-approval`, { notes }),
    accept: (id: string, signature?: string) =>
      this.post<any>(`/quotations/${id}/accept`, { signature }),
    reject: (id: string, reason?: string) =>
      this.post<any>(`/quotations/${id}/reject`, { reason }),
    convertToDeal: (id: string) =>
      this.post<any>(`/quotations/${id}/convert-deal`),
  }

  public deals = {
    list: (params?: { skip?: number; limit?: number; stage?: string; search?: string }) =>
      this.get<any[]>('/deals', { params }),
    get: (id: string) => this.get<any>(`/deals/${id}`),
    dashboard: () => this.get<any>('/deals/dashboard'),
    createFromQuote: (data: any) => this.post<any>('/deals/from-quote', data),
    updateStage: (id: string, stage: string) =>
      this.patch<any>(`/deals/${id}/stage`, { stage }),
  }

  public dealHealth = {
    dashboard: () => this.get<any>('/deal-health/dashboard'),
    predict: (payload: any) => this.post<any>('/deal-health/predict', payload),
    alerts: () => this.get<any[]>('/deal-health/alerts'),
  }

  public ai = {
    query: (payload: { prompt: string; conversation_id?: string; context?: Record<string, any> }) =>
      this.post<any>('/ai/query', payload),
    action: (payload: { conversation_id: string; tool_name: string; arguments: Record<string, any>; confirmed: boolean }) =>
      this.post<any>('/ai/action', payload),
    status: () => this.get<any>('/ai/status'),
    usage: () => this.get<any>('/ai/usage'),
  }

  public knowledge = {
    sources: () => this.get<any[]>('/knowledge/sources'),
    createSource: (data: { name: string; description?: string }) =>
      this.post<any>('/knowledge/sources', data),
    deleteSource: (id: string) => this.delete<any>(`/knowledge/sources/${id}`),
    ingest: (sourceId: string, file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return this.post<any>(`/knowledge/sources/${sourceId}/ingest`, formData)
    },
    query: (payload: { query: string; source_ids?: string[]; top_k?: number }) =>
      this.post<any>('/knowledge/query', payload),
  }

  public analytics = {
    dashboard: (params?: any) => this.get<any>('/reports/analytics/dashboard', { params }),
    revenue: (params?: any) => this.get<any>('/reports/analytics/revenue', { params }),
    conversion: (params?: any) => this.get<any>('/reports/analytics/conversion', { params }),
    customer: (params?: any) => this.get<any>('/reports/analytics/customer', { params }),
    product: (params?: any) => this.get<any>('/reports/analytics/product', { params }),
    discount: (params?: any) => this.get<any>('/reports/analytics/discount', { params }),
    inventory: (params?: any) => this.get<any>('/reports/analytics/inventory', { params }),
    approval: (params?: any) => this.get<any>('/reports/analytics/approval', { params }),
    dealHealth: (params?: any) => this.get<any>('/reports/analytics/deal-health', { params }),
  }

  public reports = {
    sales: (params?: any) => this.get<any>('/reports/sales', { params }),
    customers: (params?: any) => this.get<any>('/reports/customers', { params }),
    products: (params?: any) => this.get<any>('/reports/products', { params }),
    inventory: (params?: any) => this.get<any>('/reports/inventory', { params }),
    discounts: (params?: any) => this.get<any>('/reports/discounts', { params }),
    approvals: (params?: any) => this.get<any>('/reports/approvals', { params }),
    dealHealth: (params?: any) => this.get<any>('/reports/deal-health', { params }),
    export: async (reportType: string, format: 'csv' | 'json' = 'csv', params?: any) => {
      const token = this.getToken()
      const searchParams = new URLSearchParams({ format, ...(params || {}) }).toString()
      const url = this.buildUrl(`/reports/${reportType}/export?${searchParams}`)
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new ApiError(`Export failed for ${reportType}`, res.status)
      return res.blob()
    },
  }

  public notifications = {
    list: (params?: { skip?: number; limit?: number; unread_only?: boolean }) =>
      this.get<{ items: any[]; total: number; unread_count: number }>('/notifications', { params }),
    markRead: (id: string) => this.post<any>(`/notifications/${id}/read`),
    markAllRead: () => this.post<any>('/notifications/read-all'),
  }
}

export const api = new ApiClient()
export default api
