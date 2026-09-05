import { useState, useEffect, useCallback } from 'react'
import type { AIAnalysis, AIAnalysisRun } from '../types/ai'
import type { Request } from '../types/request'
import { aiService, AI_UPDATED_EVENT } from '../services/aiService'
import { REQUESTS_UPDATED_EVENT } from '../services/requestService'

export const ANALYSIS_STAGES = [
  'Validating request schema and line items...',
  'Reviewing commercial discounting & gross margins...',
  'Evaluating 14 risk factors against enterprise policy...',
  'Analyzing historical customer payment signals...',
  'Computing weighted confidence score...',
  'Synthesizing recommendation & conditions...',
]

export function useAI(request?: Request | null) {
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(() =>
    request?.id ? aiService.getAnalysis(request.id) : null
  )
  const [history, setHistory] = useState<AIAnalysisRun[]>(() =>
    request?.id ? aiService.getHistory(request.id) : []
  )
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [stageIndex, setStageIndex] = useState(-1)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(() => {
    if (request?.id) {
      setAnalysis(aiService.getAnalysis(request.id))
      setHistory(aiService.getHistory(request.id))
    } else {
      setAnalysis(null)
      setHistory([])
    }
  }, [request?.id])

  useEffect(() => {
    reload()

    const handleUpdate = () => {
      reload()
    }

    window.addEventListener(AI_UPDATED_EVENT, handleUpdate)
    window.addEventListener(REQUESTS_UPDATED_EVENT, handleUpdate)

    return () => {
      window.removeEventListener(AI_UPDATED_EVENT, handleUpdate)
      window.removeEventListener(REQUESTS_UPDATED_EVENT, handleUpdate)
    }
  }, [reload])

  const startAnalysis = useCallback(
    async (isRerun = false) => {
      if (!request) {
        setError('No active request found to analyze.')
        return null
      }

      setError(null)
      setIsAnalyzing(true)
      setStageIndex(0)

      // Step sequentially through stages (simulated in-browser)
      for (let i = 0; i < ANALYSIS_STAGES.length; i++) {
        setStageIndex(i)
        // Wait ~260ms per stage for smooth enterprise feel
        await new Promise((resolve) => setTimeout(resolve, 260))
      }

      const result = aiService.runAnalysis(request, isRerun)
      setAnalysis(result)
      setHistory(aiService.getHistory(request.id))
      setIsAnalyzing(false)
      setStageIndex(-1)
      return result
    },
    [request]
  )

  const acceptRecommendation = useCallback(() => {
    if (!request?.id) return false
    const res = aiService.acceptRecommendation(request.id)
    reload()
    return res.success
  }, [request?.id, reload])

  const requestManualReview = useCallback(() => {
    if (!request?.id) return false
    const res = aiService.markManualReview(request.id)
    reload()
    return res.success
  }, [request?.id, reload])

  return {
    analysis,
    history,
    isAnalyzing,
    stageIndex,
    currentStageLabel: stageIndex >= 0 ? ANALYSIS_STAGES[stageIndex] : '',
    totalStages: ANALYSIS_STAGES.length,
    error,
    startAnalysis,
    acceptRecommendation,
    requestManualReview,
    refresh: reload,
  }
}
