import { useState, useEffect, useCallback } from 'react'
import type { Request } from '../types/request'
import { requestService, REQUESTS_UPDATED_EVENT } from '../services/requestService'

export function useRequests() {
  const [requests, setRequests] = useState<Request[]>(() => requestService.getRequests())
  const [metrics, setMetrics] = useState(() => requestService.getMetrics())
  const [isLoading, setIsLoading] = useState(false)

  const reload = useCallback(() => {
    setRequests(requestService.getRequests())
    setMetrics(requestService.getMetrics())
  }, [])

  useEffect(() => {
    reload()

    const handleUpdate = () => {
      reload()
    }

    window.addEventListener(REQUESTS_UPDATED_EVENT, handleUpdate)
    window.addEventListener('storage', handleUpdate)

    return () => {
      window.removeEventListener(REQUESTS_UPDATED_EVENT, handleUpdate)
      window.removeEventListener('storage', handleUpdate)
    }
  }, [reload])

  const createDraft = useCallback((data: Partial<Request>, actorName?: string) => {
    setIsLoading(true)
    try {
      const res = requestService.saveDraft(data, actorName)
      reload()
      return res
    } finally {
      setIsLoading(false)
    }
  }, [reload])

  const submit = useCallback((data: Partial<Request>, actorName?: string) => {
    setIsLoading(true)
    try {
      const res = requestService.submitRequest(data, actorName)
      reload()
      return res
    } finally {
      setIsLoading(false)
    }
  }, [reload])

  const update = useCallback((id: string, updates: Partial<Request>, actorName?: string) => {
    setIsLoading(true)
    try {
      const res = requestService.updateRequest(id, updates, actorName)
      reload()
      return res
    } finally {
      setIsLoading(false)
    }
  }, [reload])

  const remove = useCallback((id: string) => {
    const ok = requestService.deleteRequest(id)
    reload()
    return ok
  }, [reload])

  const getRequest = useCallback((id: string) => {
    return requestService.getRequestById(id)
  }, [])

  const addDoc = useCallback((id: string, name: string) => {
    const updated = requestService.addDocument(id, name)
    reload()
    return updated
  }, [reload])

  return {
    requests,
    metrics,
    isLoading,
    createDraft,
    submitRequest: submit,
    updateRequest: update,
    deleteRequest: remove,
    getRequestById: getRequest,
    addDocument: addDoc,
    refresh: reload,
  }
}
