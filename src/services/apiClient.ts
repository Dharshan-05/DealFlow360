import { env } from '../config/env'

export interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  params?: Record<string, string | number | boolean | undefined>
}

export interface ApiResponse<T = any> {
  data: T
  status: number
  statusText: string
  ok: boolean
}

export class ApiError extends Error {
  status: number
  data?: unknown

  constructor(message: string, status: number, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = env.apiBaseUrl) {
    this.baseUrl = baseUrl
  }

  setToken(token: string | null): void {
    this.token = token
  }

  getToken(): string | null {
    return this.token
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url
  }

  private buildUrl(path: string, params?: ApiRequestOptions['params']): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`
    const url = this.baseUrl ? `${this.baseUrl}${cleanPath}` : cleanPath

    if (!params) return url

    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })

    const queryString = searchParams.toString()
    return queryString ? `${url}?${queryString}` : url
  }

  private async request<T = any>(
    method: string,
    path: string,
    options: ApiRequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const { body, params, headers = {}, ...rest } = options

    const finalHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...(headers as Record<string, string>),
    }

    const url = this.buildUrl(path, params)

    try {
      const response = await fetch(url, {
        method,
        headers: finalHeaders,
        body: body ? JSON.stringify(body) : undefined,
        ...rest,
      })

      const contentType = response.headers.get('content-type')
      const isJson = contentType && contentType.includes('application/json')
      const data = isJson ? await response.json() : await response.text()

      if (!response.ok) {
        throw new ApiError(
          (data && data.message) || response.statusText || 'API Request Failed',
          response.status,
          data
        )
      }

      return {
        data: data as T,
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        throw err
      }
      throw new ApiError(
        err?.message || 'Network error or backend unreachable',
        0,
        err
      )
    }
  }

  get<T = any>(path: string, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('GET', path, options)
  }

  post<T = any>(path: string, body?: unknown, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('POST', path, { ...options, body })
  }

  put<T = any>(path: string, body?: unknown, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', path, { ...options, body })
  }

  patch<T = any>(path: string, body?: unknown, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('PATCH', path, { ...options, body })
  }

  delete<T = any>(path: string, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', path, options)
  }
}

export const apiClient = new ApiClient()
export default apiClient
