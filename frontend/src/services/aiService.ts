import type {
  AIAnalysis,
  AIAnalysisRun,
  AIRecommendation,
  RiskFactor,
  RiskLevel,
} from '../types/ai'
import type { Request } from '../types/request'
import { requestService } from './requestService'

const AI_STORAGE_KEY = 'dealflow360_ai_analysis'
const AI_HISTORY_STORAGE_KEY = 'dealflow360_ai_history'
export const AI_UPDATED_EVENT = 'dealflow_ai_updated'

class AIService {
  private getStorage(): Record<string, AIAnalysis> {
    try {
      const raw = localStorage.getItem(AI_STORAGE_KEY)
      if (!raw) return {}
      return JSON.parse(raw) || {}
    } catch {
      return {}
    }
  }

  private setStorage(data: Record<string, AIAnalysis>): void {
    try {
      localStorage.setItem(AI_STORAGE_KEY, JSON.stringify(data))
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(AI_UPDATED_EVENT, { detail: data }))
      }
    } catch (e) {
      console.error('Failed to save AI analysis to localStorage', e)
    }
  }

  private getHistoryStorage(): Record<string, AIAnalysisRun[]> {
    try {
      const raw = localStorage.getItem(AI_HISTORY_STORAGE_KEY)
      if (!raw) return {}
      return JSON.parse(raw) || {}
    } catch {
      return {}
    }
  }

  private setHistoryStorage(data: Record<string, AIAnalysisRun[]>): void {
    try {
      localStorage.setItem(AI_HISTORY_STORAGE_KEY, JSON.stringify(data))
    } catch (e) {
      console.error('Failed to save AI history to localStorage', e)
    }
  }

  public getAnalysis(requestId: string): AIAnalysis | null {
    const store = this.getStorage()
    if (store[requestId]) {
      return store[requestId]
    }

    // If pre-seeded request, check if we should auto-initialize
    const req = requestService.getRequestById(requestId)
    if (req && req.status !== 'Draft') {
      const initial = this.generateDeterministicAnalysis(req, 1)
      store[requestId] = initial
      this.setStorage(store)
      this.recordHistory(req.id, initial)
      return initial
    }

    return null
  }

  public getHistory(requestId: string): AIAnalysisRun[] {
    const historyStore = this.getHistoryStorage()
    return historyStore[requestId] || []
  }

  public generateDeterministicAnalysis(request: Request, runNumber = 1): AIAnalysis {
    // 1. Calculate max discount across items
    let maxDiscount = 0
    if (request.items && request.items.length > 0) {
      for (const item of request.items) {
        if (item.discountPercent && item.discountPercent > maxDiscount) {
          maxDiscount = item.discountPercent
        }
      }
    } else if (request.title.includes('40%')) {
      maxDiscount = 40
    }

    // 2. Determine Risk Level, Risk Score, and Recommendation
    let overallRisk: RiskLevel = 'Low'
    let riskScore = 22
    let confidenceScore = 92
    let recType: AIRecommendation['type'] = 'Approve'
    let recTitle = 'Approve Commercial Terms'
    let recAction = 'Proceed with standard approval workflow.'
    let recRationale = 'Commercial terms, pricing margins, and contract clauses are within standard sales delegation limits.'
    let conditions: string[] | undefined = undefined
    let missingInfo: string[] | undefined = undefined

    const factors: RiskFactor[] = []
    const positiveSignals: string[] = []
    const warnings: string[] = []
    const insights: string[] = []

    // Customer relationship signals
    if (request.customer.includes('Acme') || request.customer.includes('GlobalFin')) {
      positiveSignals.push('Tier-1 Established Customer: 98%+ historical payment compliance and multi-year platform usage.')
      positiveSignals.push('Low counterparty credit exposure based on standard corporate solvency checks.')
      confidenceScore = 94
    } else if (request.customer.includes('Meridian')) {
      warnings.push('Customer has requested repeated off-cycle pricing concessions in previous quarters.')
    }

    // Documentation signals
    if (request.documents && request.documents.length > 0) {
      positiveSignals.push(`Complete Contractual Pack: ${request.documents.length} verified technical/commercial documents attached.`)
    } else {
      warnings.push('Supporting contractual documents not attached. Supplemental review suggested.')
      missingInfo = ['Signed client RFP or preliminary Statement of Work (SOW)', 'Formal billing contact verification']
    }

    // Discount and Pricing signals
    if (maxDiscount >= 35) {
      overallRisk = 'Critical'
      riskScore = 84
      recType = 'Reject'
      recTitle = 'Reject Commercial Exception'
      recAction = 'Reject proposed discount and recommend counter-proposal with maximum 15% incentive.'
      recRationale = `The requested discount of ${maxDiscount}% severely violates gross margin floor guidelines (maximum threshold 15%).`
      factors.push({
        category: 'Pricing',
        level: 'Critical',
        title: 'Severe Margin Compression',
        description: `Single line item discount of ${maxDiscount}% reduces projected transaction gross margin below corporate baseline.`,
        impact: 'Estimated gross margin loss exceeding ₹340,000.',
        mitigation: 'Counter-offer with 12% discount coupled with volume hardware bundling.',
      })
      factors.push({
        category: 'Policy',
        level: 'Critical',
        title: 'Policy Ceiling Breach',
        description: 'Exceeds VP of Sales delegation authority (capped at 20%).',
        impact: 'Requires CFO/Board level exception override.',
      })
      insights.push(`Discount of ${maxDiscount}% is in the 99th percentile of concessions across all FY26 enterprise accounts.`)
      insights.push('Historical deal win probability does not increase significantly above 14% discount for this segment.')
    } else if (maxDiscount >= 15 || request.priority === 'Critical') {
      overallRisk = 'High'
      riskScore = 64
      recType = 'Approve with Conditions'
      recTitle = 'Approve with Executive Conditions'
      recAction = 'Authorize approval contingent on upfront quarterly billing and hardware delivery lock.'
      recRationale = `Discount of ${maxDiscount || 18}% requires formal Sales Director review, but total ACV is accretive to regional targets.`
      factors.push({
        category: 'Pricing',
        level: 'High',
        title: 'Commercial Discount Exception',
        description: `Discount of ${maxDiscount || 18}% exceeds the standard account rep allowance (10%).`,
        impact: 'Requires dual managerial concurrence before execution.',
        mitigation: 'Attach 2-year warranty extension to balance gross margin.',
      })
      factors.push({
        category: 'Operational',
        level: 'Medium',
        title: 'Logistics Deployment Window',
        description: 'Accelerated deployment timeline requires confirmation from operations warehouse.',
        impact: 'Potential delivery expedited freight premium.',
      })
      conditions = [
        'Sales Director and Finance Controller formal co-signature required.',
        'Payment terms locked to Net-30 without grace extension.',
        'Operations confirmation of stock availability prior to dispatch.',
      ]
      insights.push(`Transaction gross value (${request.formattedAmount}) provides strategic reference value in target vertical.`)
      insights.push('AI win model estimates 88% probability of close with current terms.')
    } else if (maxDiscount >= 8 || request.priority === 'High') {
      overallRisk = 'Medium'
      riskScore = 42
      recType = 'Approve with Conditions'
      recTitle = 'Approve with Standard Conditions'
      recAction = 'Submit for standard managerial sign-off; within acceptable delegation parameters.'
      recRationale = 'Commercial exception is moderate and balanced by strong customer payment history.'
      factors.push({
        category: 'Pricing',
        level: 'Medium',
        title: 'Moderate Discount Variance',
        description: `Discount of ${maxDiscount || 10}% is slightly above the baseline automated threshold.`,
        impact: 'Minor margin adjustment within acceptable quarterly tolerance.',
      })
      conditions = [
        'Manager sign-off on 2-year SLA terms.',
        'Standard Net-30 invoice milestone.',
      ]
      positiveSignals.push('Customer has zero payment dispute history over past 24 months.')
      insights.push('Win rate benchmark: 91% probability of customer signing within 10 days.')
    } else {
      overallRisk = 'Low'
      riskScore = 18
      recType = 'Approve'
      recTitle = 'Fast-Track Commercial Approval'
      recAction = 'Eligible for expedited approval; commercial terms adhere to all corporate guidelines.'
      recRationale = 'Zero policy violations detected. Margins are healthy and credit risk is minimal.'
      positiveSignals.push('Full compliance with sales delegation policy (all items <= 10% discount).')
      positiveSignals.push('Healthy gross margin structure (> 38% projected margin).')
      positiveSignals.push('Standard ERP product catalog SKUs without custom engineering requirements.')
      insights.push('Recommended for zero-delay approval routing.')
      insights.push('Estimated time to fulfillment upon approval: 48 business hours.')
    }

    const reasoning = {
      summary: recRationale,
      commercialAssessment: `Pricing structure for ${request.title} yields a projected contract value of ${request.formattedAmount}. Maximum discount is ${maxDiscount}%, resulting in sustainable contribution margins.`,
      customerAssessment: `Account ${request.customer} represents a verified counterparty with positive historical transaction frequency.`,
      riskAssessment: `Overall risk posture evaluated at ${overallRisk} (${riskScore}/100) based on automated checks against 14 enterprise policy rules.`,
      operationalAssessment: 'Hardware line items and SLA components are cross-referenced with catalog availability.',
      policyAssessment: maxDiscount > 15 ? 'Triggered managerial exception rule SEC-PRICING-04.' : 'No policy exceptions triggered; within sales delegation authority.',
    }

    const recommendation: AIRecommendation = {
      id: 'rec_' + Date.now().toString(36),
      requestId: request.id,
      type: recType,
      title: recTitle,
      recommendedAction: recAction,
      rationale: recRationale,
      confidence: confidenceScore,
      impactDescription: `Supports ${request.formattedAmount} transaction pipeline with ${overallRisk.toLowerCase()} risk exposure.`,
      reasoning,
      conditions,
      missingInformation: missingInfo,
      suggestedNextAction: recType === 'Reject' ? 'Formulate revised counter-proposal' : 'Submit for managerial approval',
      userDecision: 'Pending',
    }

    return {
      id: `ai_${request.referenceNumber}_run${runNumber}`,
      requestId: request.id,
      status: 'Complete',
      overallRisk,
      riskScore,
      confidenceScore,
      summary: `Automated AI evaluation completed with ${confidenceScore}% confidence. Overall risk is ${overallRisk}. Recommendation: ${recType}.`,
      factors,
      positiveSignals,
      warnings,
      insights,
      recommendation,
      analyzedAt: new Date().toISOString(),
      runNumber,
    }
  }

  public recordHistory(requestId: string, analysis: AIAnalysis): void {
    const historyStore = this.getHistoryStorage()
    const currentList = historyStore[requestId] || []

    const runItem: AIAnalysisRun = {
      id: analysis.id,
      requestId,
      runNumber: analysis.runNumber,
      overallRisk: analysis.overallRisk,
      riskScore: analysis.riskScore,
      confidenceScore: analysis.confidenceScore,
      recommendationType: analysis.recommendation.type,
      analyzedAt: analysis.analyzedAt,
      status: analysis.status,
    }

    // Prepend latest run, limit to 5
    const updated = [runItem, ...currentList.filter((r) => r.id !== analysis.id)].slice(0, 5)
    historyStore[requestId] = updated
    this.setHistoryStorage(historyStore)
  }

  public runAnalysis(request: Request, isRerun = false): AIAnalysis {
    const store = this.getStorage()
    const existing = store[request.id]
    const nextRun = isRerun && existing ? existing.runNumber + 1 : 1

    const newAnalysis = this.generateDeterministicAnalysis(request, nextRun)
    store[request.id] = newAnalysis
    this.setStorage(store)
    this.recordHistory(request.id, newAnalysis)

    // Update request health score & risk level
    requestService.updateRequest(
      request.id,
      {
        riskLevel: newAnalysis.overallRisk,
        healthScore: 100 - newAnalysis.riskScore,
      },
      'AI Analysis Engine'
    )

    return newAnalysis
  }

  public acceptRecommendation(
    requestId: string,
    actorName = 'Arjun Sharma'
  ): { analysis: AIAnalysis | null; success: boolean } {
    const store = this.getStorage()
    const analysis = store[requestId]
    if (!analysis) return { analysis: null, success: false }

    analysis.recommendation.userDecision = 'Accepted'
    analysis.recommendation.accepted = true
    analysis.recommendation.decidedAt = new Date().toISOString()
    store[requestId] = analysis
    this.setStorage(store)

    // Transition Request state toward "Ready for Approval" (Step 14 & 30: Do NOT directly approve!)
    const req = requestService.getRequestById(requestId)
    if (req) {
      const targetStatus = analysis.recommendation.type === 'Reject' ? 'Rejected' : 'Ready for Approval'

      requestService.updateRequest(
        requestId,
        {
          status: targetStatus,
          activity: [
            {
              id: 'act_' + Date.now(),
              action: 'AI Recommendation Accepted',
              actor: actorName,
              timestamp: new Date().toISOString(),
              description: `User accepted AI recommendation (${analysis.recommendation.type}). Status transitioned to '${targetStatus}'.`,
            },
            ...(req.activity || []),
          ],
          timeline: [
            ...(req.timeline || []),
            {
              id: 'tl_ai_acc_' + Date.now(),
              event: 'AI Recommendation Accepted',
              title: `AI Recommendation Accepted: ${targetStatus}`,
              actor: actorName,
              timestamp: new Date().toISOString(),
              note: `Accepted: "${analysis.recommendation.title}". Ready for final stakeholder approval decision.`,
              status: targetStatus,
            },
          ],
        },
        actorName
      )
    }

    return { analysis, success: true }
  }

  public markManualReview(
    requestId: string,
    actorName = 'Arjun Sharma'
  ): { analysis: AIAnalysis | null; success: boolean } {
    const store = this.getStorage()
    const analysis = store[requestId]
    if (!analysis) return { analysis: null, success: false }

    analysis.recommendation.userDecision = 'Manual Review'
    analysis.recommendation.decidedAt = new Date().toISOString()
    store[requestId] = analysis
    this.setStorage(store)

    const req = requestService.getRequestById(requestId)
    if (req) {
      requestService.updateRequest(
        requestId,
        {
          status: 'Under Review',
          activity: [
            {
              id: 'act_' + Date.now(),
              action: 'Manual Review Requested',
              actor: actorName,
              timestamp: new Date().toISOString(),
              description: 'User bypassed automated recommendation in favor of custom manual review.',
            },
            ...(req.activity || []),
          ],
          timeline: [
            ...(req.timeline || []),
            {
              id: 'tl_man_rev_' + Date.now(),
              event: 'Manual Review Requested',
              title: 'Manual Review Initiated',
              actor: actorName,
              timestamp: new Date().toISOString(),
              note: 'User initiated deep manual underwriting review.',
              status: 'Under Review',
            },
          ],
        },
        actorName
      )
    }

    return { analysis, success: true }
  }
}

export const aiService = new AIService()
