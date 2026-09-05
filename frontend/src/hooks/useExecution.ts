import { useState, useEffect, useCallback } from 'react'
import type { Execution, ExecutionMetrics } from '../types/execution'
import type { Request } from '../types/request'
import type { Approval } from '../types/approval'
import { executionService, EXECUTION_UPDATED_EVENT } from '../services/executionService'

export function useExecution() {
  const [executions, setExecutions] = useState<Execution[]>(() => executionService.getExecutions())
  const [metrics, setMetrics] = useState<ExecutionMetrics>(() => executionService.getMetrics())
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => {
    setExecutions(executionService.getExecutions())
    setMetrics(executionService.getMetrics())
  }, [])

  useEffect(() => {
    refresh()
    const handleUpdate = () => refresh()
    window.addEventListener(EXECUTION_UPDATED_EVENT, handleUpdate)
    return () => window.removeEventListener(EXECUTION_UPDATED_EVENT, handleUpdate)
  }, [refresh])

  const createOrGetExecution = useCallback((request: Request, approval?: Approval) => {
    const exec = executionService.createOrGetExecution(request, approval)
    refresh()
    return exec
  }, [refresh])

  const startExecution = useCallback(
    async (executionId: string, simulateFailure = false): Promise<Execution> => {
      setIsRunning(true)
      setError(null)
      try {
        const result = await executionService.runExecution(executionId, {
          simulateFailure,
          onStepUpdate: (updated) => {
            setSelectedExecution(updated)
            refresh()
          },
        })
        setSelectedExecution(result)
        return result
      } catch (err: any) {
        const msg = err?.message || 'Execution error'
        setError(msg)
        throw err
      } finally {
        setIsRunning(false)
        refresh()
      }
    },
    [refresh]
  )

  const retryExecution = useCallback(
    async (executionId: string): Promise<Execution> => {
      setIsRunning(true)
      setError(null)
      try {
        const result = await executionService.retryExecution(executionId, {
          onStepUpdate: (updated) => {
            setSelectedExecution(updated)
            refresh()
          },
        })
        setSelectedExecution(result)
        return result
      } catch (err: any) {
        const msg = err?.message || 'Retry execution failed'
        setError(msg)
        throw err
      } finally {
        setIsRunning(false)
        refresh()
      }
    },
    [refresh]
  )

  const getExecutionForRequest = useCallback((requestId: string): Execution | undefined => {
    return executionService.getExecutionByRequestId(requestId)
  }, [])

  return {
    executions,
    metrics,
    selectedExecution,
    setSelectedExecution,
    isRunning,
    error,
    createOrGetExecution,
    startExecution,
    retryExecution,
    getExecutionForRequest,
    refresh,
  }
}
