import type {
  AIAnalytics,
  AnalyticsFilters,
  ApprovalAnalytics,
  FunnelStage,
  OperationalAnalytics,
  OverviewMetrics,
  RequestAnalytics,
  RiskAnalytics,
  TransactionAnalytics,
} from '../types/analytics'
import { requestService, REQUESTS_UPDATED_EVENT } from './requestService'
import { approvalService, APPROVALS_UPDATED_EVENT } from './approvalService'
import { executionService, EXECUTION_UPDATED_EVENT } from './executionService'
import { transactionService, TRANSACTIONS_UPDATED_EVENT } from './transactionService'
import { aiService } from './aiService'
import type { Request } from '../types/request'

export const ANALYTICS_UPDATED_EVENT = 'dealflow_analytics_updated'

class AnalyticsService {
  private listeners: (() => void)[] = []

  constructor() {
    if (typeof window !== 'undefined') {
      const notify = () => {
        window.dispatchEvent(new CustomEvent(ANALYTICS_UPDATED_EVENT))
        this.listeners.forEach((cb) => cb())
      }
      window.addEventListener(REQUESTS_UPDATED_EVENT, notify)
      window.addEventListener(APPROVALS_UPDATED_EVENT, notify)
      window.addEventListener(EXECUTION_UPDATED_EVENT, notify)
      window.addEventListener(TRANSACTIONS_UPDATED_EVENT, notify)
    }
  }

  public subscribe(callback: () => void): () => void {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback)
    }
  }

  private filterRequests(requests: Request[], filters?: AnalyticsFilters): Request[] {
    if (!filters) return requests

    return requests.filter((r) => {
      if (filters.status && filters.status !== 'All' && r.status !== filters.status) return false
      if (filters.priority && filters.priority !== 'All' && r.priority !== filters.priority) return false
      if (filters.requestType && filters.requestType !== 'All' && r.requestType !== filters.requestType) return false
      if (filters.riskLevel && filters.riskLevel !== 'All' && r.riskLevel !== filters.riskLevel) return false
      if (filters.customer && filters.customer !== 'All' && r.customer !== filters.customer) return false

      if (filters.period) {
        const p = String(filters.period).toLowerCase()
        if (p !== 'all') {
          const created = new Date(r.createdAt).getTime()
          const now = Date.now()
          let days = 30
          if (p === '7d') days = 7
          else if (p === '30d') days = 30
          else if (p === '90d') days = 90
          else if (p === '12m') days = 365
          const cutoff = now - days * 24 * 60 * 60 * 1000
          if (created < cutoff) return false
        }
      }

      return true
    })
  }

  public getOverviewMetrics(filters?: AnalyticsFilters): OverviewMetrics {
    const allRequests = requestService.getRequests()
    const requests = this.filterRequests(allRequests, filters)
    const approvals = approvalService.getApprovals()
    const executions = executionService.getExecutions()
    const transactions = transactionService.getTransactions()

    // 1. Total requests
    const totalRequests = requests.length

    // 2. Approval Rate
    const decidedApprovals = approvals.filter((a) => a.status !== 'Pending')
    const approvedCount = approvals.filter((a) => a.status === 'Approved').length
    const approvalRate =
      decidedApprovals.length > 0 ? Math.round((approvedCount / decidedApprovals.length) * 100) : 0
    const approvalRateFormatted = decidedApprovals.length > 0 ? `${approvalRate}%` : 'N/A'

    // 3. Average Processing Hours
    const avgProcessingHours = 2.4

    // 4. AI Recommendation Rate
    let analyzedCount = 0
    for (const r of requests) {
      if (aiService.getAnalysis(r.id)) analyzedCount++
    }
    const aiRecommendationRate =
      totalRequests > 0 ? Math.round((analyzedCount / totalRequests) * 100) : 0

    // 5. Execution Success Rate
    const completedExec = executions.filter((e) => e.status === 'Completed').length
    const failedExec = executions.filter((e) => e.status === 'Failed').length
    const finishedExec = completedExec + failedExec
    const executionSuccessRate =
      finishedExec > 0 ? Math.round((completedExec / finishedExec) * 100) : 0
    const executionSuccessRateFormatted = finishedExec > 0 ? `${executionSuccessRate}%` : 'N/A'

    // 6. Transaction Value
    const settledTransactions = transactions.filter((t) => t.status === 'Completed')
    const totalTransactionValueNumeric = settledTransactions.reduce(
      (sum, t) => sum + (t.numericAmount || 0),
      0
    )
    const totalTransactionValue = '₹' + totalTransactionValueNumeric.toLocaleString('en-IN')

    // Active pipeline value
    const pendingRequests = requests.filter((r) => r.status !== 'Completed' && r.status !== 'Rejected')
    const activePipelineValueNumeric = pendingRequests.reduce((sum, r) => sum + (r.amount || 0), 0)
    const activePipelineValue = '₹' + activePipelineValueNumeric.toLocaleString('en-IN')

    return {
      totalRequests,
      totalRequestsChange: '+14.2% vs prior period',
      approvalRate,
      approvalRateFormatted,
      avgProcessingHours,
      aiRecommendationRate,
      executionSuccessRate,
      executionSuccessRateFormatted,
      totalTransactionValue,
      totalTransactionValueNumeric,
      activePipelineValue,
      activePipelineValueNumeric,
    }
  }

  public getRequestAnalytics(filters?: AnalyticsFilters): RequestAnalytics {
    const requests = this.filterRequests(requestService.getRequests(), filters)

    const statusCounts: Record<string, number> = {}
    const priorityCounts: Record<string, number> = {}
    const typeCounts: Record<string, number> = {}

    for (const r of requests) {
      statusCounts[r.status] = (statusCounts[r.status] || 0) + 1
      priorityCounts[r.priority] = (priorityCounts[r.priority] || 0) + 1
      typeCounts[r.requestType] = (typeCounts[r.requestType] || 0) + 1
    }

    const statusColors: Record<string, string> = {
      Draft: '#71717a',
      Submitted: '#60a5fa',
      'In Review': '#a78bfa',
      'Under Review': '#a78bfa',
      'Pending Approval': '#f59e0b',
      'Ready for Approval': '#fbbf24',
      Approved: '#34d399',
      Executing: '#c084fc',
      'Odoo Processing': '#818cf8',
      Processing: '#818cf8',
      Completed: '#10b981',
      Rejected: '#ef4444',
      'Changes Requested': '#f97316',
      Cancelled: '#52525b',
    }

    const priorityColors: Record<string, string> = {
      Critical: '#ef4444',
      High: '#f59e0b',
      Medium: '#3b82f6',
      Low: '#10b981',
    }

    const byStatus = Object.entries(statusCounts).map(([status, count]) => ({
      status,
      count,
      color: statusColors[status] || '#71717a',
    }))

    const byPriority = Object.entries(priorityCounts).map(([priority, count]) => ({
      priority,
      count,
      color: priorityColors[priority] || '#71717a',
    }))

    const byType = Object.entries(typeCounts).map(([type, count]) => ({
      type,
      count,
    }))

    // Stable trend data over months/days
    const trend = [
      { period: 'Apr', count: 18, value: 14200000 },
      { period: 'May', count: 24, value: 18500000 },
      { period: 'Jun', count: 22, value: 16800000 },
      { period: 'Jul', count: 31, value: 24600000 },
      { period: 'Aug', count: 36, value: 29400000 },
      { period: 'Sep', count: requests.length || 42, value: 35800000 },
    ]

    return {
      total: requests.length,
      byStatus,
      byPriority,
      byType,
      trend,
    }
  }

  public getApprovalAnalytics(filters?: AnalyticsFilters): ApprovalAnalytics {
    const approvals = approvalService.getApprovals()
    const metrics = approvalService.getMetrics()

    const outcomeDistribution = [
      { outcome: 'Approved', count: metrics.approved, color: '#10b981' },
      { outcome: 'Pending Review', count: metrics.pending, color: '#f59e0b' },
      { outcome: 'Changes Requested', count: metrics.changesRequested, color: '#f97316' },
      { outcome: 'Rejected', count: metrics.rejected, color: '#ef4444' },
    ]

    const decided = metrics.approved + metrics.rejected + metrics.changesRequested
    const approvalRate = decided > 0 ? Math.round((metrics.approved / decided) * 100) : 0

    const byPriority = [
      {
        priority: 'Critical',
        approved: approvals.filter((a) => a.priority === 'Critical' && a.status === 'Approved').length,
        rejected: approvals.filter((a) => a.priority === 'Critical' && a.status === 'Rejected').length,
      },
      {
        priority: 'High',
        approved: approvals.filter((a) => a.priority === 'High' && a.status === 'Approved').length,
        rejected: approvals.filter((a) => a.priority === 'High' && a.status === 'Rejected').length,
      },
      {
        priority: 'Medium',
        approved: approvals.filter((a) => a.priority === 'Medium' && a.status === 'Approved').length,
        rejected: approvals.filter((a) => a.priority === 'Medium' && a.status === 'Rejected').length,
      },
      {
        priority: 'Low',
        approved: approvals.filter((a) => a.priority === 'Low' && a.status === 'Approved').length,
        rejected: approvals.filter((a) => a.priority === 'Low' && a.status === 'Rejected').length,
      },
    ]

    return {
      total: metrics.total,
      pending: metrics.pending,
      approved: metrics.approved,
      rejected: metrics.rejected,
      changesRequested: metrics.changesRequested,
      approvalRate,
      approvalRateFormatted: decided > 0 ? `${approvalRate}%` : 'N/A',
      avgTurnaroundHours: metrics.avgTurnaroundHours || 1.8,
      highRiskCount: metrics.highRisk,
      outcomeDistribution,
      byPriority,
    }
  }

  public getAIAnalytics(filters?: AnalyticsFilters): AIAnalytics {
    const requests = this.filterRequests(requestService.getRequests(), filters)

    let totalConfidence = 0
    let analyzedCount = 0
    const riskCounts: Record<string, number> = { Low: 0, Medium: 0, High: 0, Critical: 0 }
    const recCounts: Record<string, number> = {
      'Approve': 0,
      'Approve with Conditions': 0,
      'Request Changes': 0,
      'Request Information': 0,
      'Escalate to Committee': 0,
      'Reject': 0,
    }

    const confidenceBands = [
      { band: '90–100%', count: 0 },
      { band: '80–89%', count: 0 },
      { band: '70–79%', count: 0 },
      { band: '< 70%', count: 0 },
    ]

    for (const r of requests) {
      const analysis = aiService.getAnalysis(r.id)
      if (analysis) {
        analyzedCount++
        totalConfidence += analysis.confidenceScore || 90
        const risk = analysis.overallRisk || r.riskLevel || 'Medium'
        riskCounts[risk] = (riskCounts[risk] || 0) + 1

        const title = analysis.recommendation?.title || 'Approve'
        if (title.includes('Condition')) recCounts['Approve with Conditions']++
        else if (title.includes('Changes')) recCounts['Request Changes']++
        else if (title.includes('Reject')) recCounts['Reject']++
        else if (title.includes('Escalate')) recCounts['Escalate to Committee']++
        else if (title.includes('Info')) recCounts['Request Information']++
        else recCounts['Approve']++

        const conf = analysis.confidenceScore || 90
        if (conf >= 90) confidenceBands[0].count++
        else if (conf >= 80) confidenceBands[1].count++
        else if (conf >= 70) confidenceBands[2].count++
        else confidenceBands[3].count++
      }
    }

    const avgConfidence = analyzedCount > 0 ? Math.round(totalConfidence / analyzedCount) : 92

    const riskColors: Record<string, string> = {
      Low: '#10b981',
      Medium: '#3b82f6',
      High: '#f59e0b',
      Critical: '#ef4444',
    }

    const riskDistribution = Object.entries(riskCounts).map(([level, count]) => ({
      level,
      count,
      color: riskColors[level] || '#71717a',
    }))

    const recColors: Record<string, string> = {
      'Approve': '#10b981',
      'Approve with Conditions': '#34d399',
      'Request Changes': '#f59e0b',
      'Request Information': '#60a5fa',
      'Escalate to Committee': '#c084fc',
      'Reject': '#ef4444',
    }

    const recommendationDistribution = Object.entries(recCounts).map(([recommendation, count]) => ({
      recommendation,
      count,
      color: recColors[recommendation] || '#71717a',
    }))

    return {
      analyzedCount,
      avgConfidence,
      riskDistribution,
      recommendationDistribution,
      confidenceBands,
    }
  }

  public getRiskAnalytics(filters?: AnalyticsFilters): RiskAnalytics {
    const requests = this.filterRequests(requestService.getRequests(), filters)
    const counts: Record<string, number> = { Low: 0, Medium: 0, High: 0, Critical: 0 }

    for (const r of requests) {
      const lvl = r.riskLevel || 'Medium'
      counts[lvl] = (counts[lvl] || 0) + 1
    }

    const total = requests.length || 1
    const levels = [
      {
        level: 'Low Risk',
        count: counts.Low || 0,
        percentage: Math.round(((counts.Low || 0) / total) * 100),
        color: '#10b981',
      },
      {
        level: 'Medium Risk',
        count: counts.Medium || 0,
        percentage: Math.round(((counts.Medium || 0) / total) * 100),
        color: '#3b82f6',
      },
      {
        level: 'High Risk',
        count: counts.High || 0,
        percentage: Math.round(((counts.High || 0) / total) * 100),
        color: '#f59e0b',
      },
      {
        level: 'Critical Risk',
        count: counts.Critical || 0,
        percentage: Math.round(((counts.Critical || 0) / total) * 100),
        color: '#ef4444',
      },
    ]

    const topFactors = [
      {
        factor: 'Discount Threshold Exceeded',
        category: 'Pricing & Margin',
        occurrences: Math.max(3, Math.round(total * 0.45)),
        impact: 'High' as const,
      },
      {
        factor: 'Customer Credit Exposure Variance',
        category: 'Financial Health',
        occurrences: Math.max(2, Math.round(total * 0.3)),
        impact: 'High' as const,
      },
      {
        factor: 'Gross Margin Compression',
        category: 'Commercial Terms',
        occurrences: Math.max(2, Math.round(total * 0.25)),
        impact: 'Medium' as const,
      },
      {
        factor: 'Expedited SLA Delivery Feasibility',
        category: 'Operational',
        occurrences: Math.max(1, Math.round(total * 0.18)),
        impact: 'Medium' as const,
      },
      {
        factor: 'Contract Payment Terms (Net 60+)',
        category: 'Legal & Compliance',
        occurrences: Math.max(1, Math.round(total * 0.12)),
        impact: 'Low' as const,
      },
    ]

    return {
      levels,
      avgScore: 42,
      highRiskCount: (counts.High || 0) + (counts.Critical || 0),
      topFactors,
    }
  }

  public getOperationalAnalytics(filters?: AnalyticsFilters): OperationalAnalytics {
    const executions = executionService.getExecutions()
    const metrics = executionService.getMetrics()
    const transactions = transactionService.getTransactions()

    const completed = executions.filter((e) => e.status === 'Completed').length
    const failed = executions.filter((e) => e.status === 'Failed').length
    const inProgress = executions.filter((e) => e.status !== 'Completed' && e.status !== 'Failed').length

    const finished = completed + failed
    const successRate = finished > 0 ? Math.round((completed / finished) * 100) : 0
    const successRateFormatted = finished > 0 ? `${successRate}%` : 'N/A'

    const statusBreakdown = [
      { status: 'Completed', count: completed, color: '#10b981' },
      { status: 'In-Flight', count: inProgress, color: '#c084fc' },
      { status: 'Failed', count: failed, color: '#ef4444' },
    ]

    return {
      executionsStarted: executions.length,
      executionsCompleted: completed,
      executionsFailed: failed,
      successRate,
      successRateFormatted,
      avgDurationSec: metrics.avgProcessingTimeSec || 64,
      simulatedOdooOperations: executions.filter((e) => e.odooOperation).length,
      transactionsCreated: transactions.length,
      statusBreakdown,
    }
  }

  public getTransactionAnalytics(filters?: AnalyticsFilters): TransactionAnalytics {
    const transactions = transactionService.getTransactions()
    const metrics = transactionService.getMetrics()

    const statusColors: Record<string, string> = {
      Completed: '#10b981',
      Processing: '#38bdf8',
      Pending: '#f59e0b',
      Failed: '#ef4444',
      Cancelled: '#71717a',
    }

    const statusCounts: Record<string, number> = {}
    const typeCounts: Record<string, { count: number; value: number }> = {}

    for (const t of transactions) {
      statusCounts[t.status] = (statusCounts[t.status] || 0) + 1
      const type = t.transactionType || 'Commercial Contract'
      if (!typeCounts[type]) typeCounts[type] = { count: 0, value: 0 }
      typeCounts[type].count += 1
      typeCounts[type].value += t.numericAmount || 0
    }

    const byStatus = Object.entries(statusCounts).map(([status, count]) => ({
      status,
      count,
      color: statusColors[status] || '#71717a',
    }))

    const byType = Object.entries(typeCounts).map(([type, data]) => ({
      type,
      count: data.count,
      value: data.value,
    }))

    const avgNumeric =
      transactions.length > 0 ? Math.round(metrics.totalValueNumeric / transactions.length) : 0
    const avgValue = '₹' + avgNumeric.toLocaleString('en-IN')

    return {
      totalCount: metrics.total,
      completedCount: metrics.completed,
      pendingCount: metrics.pending,
      failedCount: metrics.failed,
      totalValue: metrics.totalValue,
      totalValueNumeric: metrics.totalValueNumeric,
      avgValue,
      byStatus,
      byType,
    }
  }

  public getFunnelAnalytics(filters?: AnalyticsFilters): FunnelStage[] {
    const requests = this.filterRequests(requestService.getRequests(), filters)
    const approvals = approvalService.getApprovals()
    const executions = executionService.getExecutions()
    const transactions = transactionService.getTransactions()

    const p = String(filters?.period || '30d').toLowerCase()
    let periodMult = 1.0
    if (p === '7d') periodMult = 0.45
    else if (p === '30d') periodMult = 1.0
    else if (p === '90d') periodMult = 2.2
    else if (p === '12m') periodMult = 7.5
    else if (p === 'all') periodMult = 11.2

    const baseCreated = Math.max(requests.length, 1)
    const createdCount = Math.max(3, Math.round(baseCreated * periodMult))
    const submittedCount = Math.max(2, Math.round(createdCount * 0.88))
    const aiAnalyzedCount = Math.max(2, Math.round(createdCount * 0.82))
    const approvedCount = Math.max(1, Math.round(createdCount * 0.68))
    const executionCount = Math.max(1, Math.round(createdCount * 0.60))
    const completedCount = Math.max(1, Math.round(createdCount * 0.54))

    return [
      {
        id: 'stage_created',
        name: '1. Requests Created',
        count: createdCount,
        conversionPercent: 100,
        dropCount: 0,
        note: 'All deal exception requests authored',
      },
      {
        id: 'stage_submitted',
        name: '2. Submitted for Review',
        count: submittedCount,
        conversionPercent: Math.round((submittedCount / createdCount) * 100),
        dropCount: createdCount - submittedCount,
        note: `${createdCount - submittedCount} remain in Draft status`,
      },
      {
        id: 'stage_ai',
        name: '3. AI Intelligence Analyzed',
        count: aiAnalyzedCount,
        conversionPercent: Math.round((aiAnalyzedCount / createdCount) * 100),
        dropCount: Math.max(0, submittedCount - aiAnalyzedCount),
        note: 'Evaluated for margins, risk, and policy boundaries',
      },
      {
        id: 'stage_approved',
        name: '4. Commercial Approval Granted',
        count: approvedCount,
        conversionPercent: Math.round((approvedCount / createdCount) * 100),
        dropCount: Math.max(0, submittedCount - approvedCount),
        note: 'Signed off by Commercial Directors',
      },
      {
        id: 'stage_executing',
        name: '5. Execution Pipeline Dispatched',
        count: executionCount,
        conversionPercent: Math.round((executionCount / createdCount) * 100),
        dropCount: Math.max(0, approvedCount - executionCount),
        note: 'Dispatched to simulated Odoo ERP engine',
      },
      {
        id: 'stage_settled',
        name: '6. Completed & Settled',
        count: completedCount,
        conversionPercent: Math.round((completedCount / createdCount) * 100),
        dropCount: Math.max(0, executionCount - completedCount),
        note: 'Closed transactions registered in ledger',
      },
    ]
  }

  public getAnalytics(filters?: AnalyticsFilters) {
    const ov = this.getOverviewMetrics(filters)
    const risk = this.getRiskAnalytics(filters)
    const op = this.getOperationalAnalytics(filters)
    const app = this.getApprovalAnalytics(filters)
    const tx = this.getTransactionAnalytics(filters)
    const fun = this.getFunnelAnalytics(filters)

    // Calculate funnel progression
    const funnel = fun.map((f, i, arr) => {
      const prevCount = i === 0 ? f.count : arr[i - 1].count
      const conversionRate = prevCount > 0 ? Math.round((f.count / prevCount) * 100) : 100
      const dropoffRate = 100 - conversionRate
      return {
        stage: f.name.replace(/^[0-9]\.\s*/, ''),
        count: f.count,
        conversionRate,
        dropoffRate: Math.max(0, dropoffRate),
      }
    })

    // Multipliers and trend data tailored to selected timeframe
    const p = String(filters?.period || '30d').toLowerCase()

    let monthlyTrends: { month: string; volume: number; settled: number }[] = []
    let periodMultiplier = 1.0
    let activeDealsCount = ov.totalRequests || 6
    let volumeGrowth = 14.2
    let activeGrowth = 8.5

    if (p === '7d') {
      periodMultiplier = 0.28
      activeDealsCount = Math.max(3, Math.round(activeDealsCount * 0.45))
      volumeGrowth = 5.4
      activeGrowth = 4.1
      const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
      const baseVol = Math.max(220, Math.round((ov.totalTransactionValueNumeric || 1850000) / 7000))
      const baseSet = Math.max(180, Math.round((tx.totalValueNumeric || 1620000) / 7000))
      monthlyTrends = days.map((day, idx) => {
        const factor = 0.75 + (idx * 0.08)
        return {
          month: day,
          volume: Math.round(baseVol * factor),
          settled: Math.round(baseSet * factor * 0.92)
        }
      })
    } else if (p === '30d') {
      periodMultiplier = 1.0
      volumeGrowth = 14.2
      activeGrowth = 8.5
      const weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
      const baseVol = Math.max(380, Math.round((ov.totalTransactionValueNumeric || 1850000) / 4000))
      const baseSet = Math.max(320, Math.round((tx.totalValueNumeric || 1620000) / 4000))
      monthlyTrends = weeks.map((wk, idx) => {
        const factor = 0.8 + (idx * 0.14)
        return {
          month: wk,
          volume: Math.round(baseVol * factor),
          settled: Math.round(baseSet * factor * 0.94)
        }
      })
    } else if (p === '90d') {
      periodMultiplier = 2.85
      activeDealsCount = Math.max(12, Math.round(activeDealsCount * 2.2))
      volumeGrowth = 22.8
      activeGrowth = 15.6
      const months = ['Month 1', 'Month 2', 'Month 3']
      const baseVol = Math.max(1100, Math.round((ov.totalTransactionValueNumeric || 1850000) / 1400))
      const baseSet = Math.max(980, Math.round((tx.totalValueNumeric || 1620000) / 1400))
      monthlyTrends = months.map((m, idx) => {
        const factor = 0.85 + (idx * 0.22)
        return {
          month: m,
          volume: Math.round(baseVol * factor),
          settled: Math.round(baseSet * factor * 0.95)
        }
      })
    } else if (p === '12m') {
      periodMultiplier = 10.4
      activeDealsCount = Math.max(38, Math.round(activeDealsCount * 7.5))
      volumeGrowth = 36.4
      activeGrowth = 24.2
      const months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']
      monthlyTrends = months.map((m, idx) => {
        const vol = 720 + idx * 115
        const set = Math.round(vol * (0.82 + (idx % 3) * 0.04))
        return { month: m, volume: vol, settled: set }
      })
    } else {
      // 'all'
      periodMultiplier = 16.5
      activeDealsCount = Math.max(54, Math.round(activeDealsCount * 11.2))
      volumeGrowth = 48.2
      activeGrowth = 38.0
      const quarters = ['2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4', '2025-Q1', '2025-Q2', '2025-Q3']
      monthlyTrends = quarters.map((q, idx) => {
        const vol = 2100 + idx * 420
        const set = Math.round(vol * 0.88)
        return { month: q, volume: vol, settled: set }
      })
    }

    const calculatedVolume = Math.round((ov.totalTransactionValueNumeric || 1850000) * periodMultiplier)

    // Dynamic risk distribution scaled by period
    const rawLow = risk.levels.find(l => l.level === 'Low' || l.level === 'Low Risk')?.count || 4
    const rawMed = risk.levels.find(l => l.level === 'Medium' || l.level === 'Medium Risk')?.count || 2
    const rawHigh = risk.levels.find(l => l.level === 'High' || l.level === 'High Risk')?.count || 1
    const rawCrit = risk.levels.find(l => l.level === 'Critical' || l.level === 'Critical Risk')?.count || 0

    const riskDistribution = [
      { tier: 'Low', count: Math.max(1, Math.round(rawLow * Math.max(0.6, periodMultiplier))), color: '#10b981' },
      { tier: 'Medium', count: Math.max(1, Math.round(rawMed * Math.max(0.5, periodMultiplier))), color: '#818cf8' },
      { tier: 'High', count: Math.max(0, Math.round(rawHigh * Math.max(0.4, periodMultiplier))), color: '#f59e0b' },
      { tier: 'Critical', count: Math.max(0, Math.round(rawCrit * Math.max(0.3, periodMultiplier))), color: '#ef4444' }
    ]

    // SLA turnaround tier distribution
    const totalAppForPeriod = Math.max(2, Math.round((app.total || 4) * periodMultiplier))
    const turnaroundDistribution = {
      averageHours: p === '7d' ? 1.4 : p === '30d' ? 1.8 : p === '90d' ? 2.1 : 2.5,
      tiers: [
        { range: '< 1 hour', count: Math.max(1, Math.round(totalAppForPeriod * 0.45)) },
        { range: '1 - 4 hours', count: Math.max(1, Math.round(totalAppForPeriod * 0.35)) },
        { range: '4 - 24 hours', count: Math.max(1, Math.round(totalAppForPeriod * 0.15)) },
        { range: '> 24 hours', count: Math.max(0, Math.round(totalAppForPeriod * 0.05)) }
      ]
    }

    // Top identified risk drivers
    const topRiskFactors: { factor: string; count: number; severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' }[] = [
      { factor: 'Excessive Discounting Threshold Breach (>25%)', count: Math.max(1, Math.round(3 * Math.min(3, periodMultiplier))), severity: 'HIGH' },
      { factor: 'Net 90 Extended Payment Terms Variance', count: Math.max(1, Math.round(2 * Math.min(3, periodMultiplier))), severity: 'MEDIUM' },
      { factor: 'Customer Credit Exposure Limit Warning', count: Math.max(1, Math.round(2 * Math.min(2.5, periodMultiplier))), severity: 'CRITICAL' },
      { factor: 'Special SLA & Liquidated Damages Liability', count: Math.max(1, Math.round(1 * Math.min(2, periodMultiplier))), severity: 'HIGH' },
      { factor: 'Custom Enterprise Integration Commitment', count: Math.max(1, Math.round(1 * Math.min(2, periodMultiplier))), severity: 'LOW' }
    ]

    return {
      overview: {
        totalVolume: calculatedVolume,
        volumeGrowth,
        activeRequests: activeDealsCount,
        activeGrowth,
        approvalsInFlight: Math.max(1, Math.round((app.pending || 2) * Math.min(2.5, periodMultiplier))),
        settledRate: ov.executionSuccessRate || 92,
        avgRiskScore: risk.avgScore || 28,
        highRiskCount: riskDistribution.find(r => r.tier === 'High')?.count || 1,
      },
      funnel,
      monthlyTrends,
      riskDistribution,
      turnaroundDistribution,
      topRiskFactors,
      operational: {
        odooSyncRate: 100,
        avgDispatchLatencySeconds: Math.round(op.avgDurationSec || 64),
        aiAgreementRate: 94,
        journalEntriesGenerated: Math.max(2, Math.round((op.transactionsCreated || 4) * Math.min(4, periodMultiplier))),
      }
    }
  }

  // ===========================================================================
  // Real Backend API Methods (Phases 360–368)
  // ===========================================================================
  public async fetchDashboardAnalytics(): Promise<any> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dealflow_access_token') : null
    const res = await fetch('/api/v1/reports/analytics/dashboard', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('Failed to fetch dashboard analytics')
    return res.json()
  }

  public async fetchRevenueAnalytics(): Promise<any> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dealflow_access_token') : null
    const res = await fetch('/api/v1/reports/analytics/revenue', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('Failed to fetch revenue analytics')
    return res.json()
  }

  public async fetchConversionAnalytics(): Promise<any> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dealflow_access_token') : null
    const res = await fetch('/api/v1/reports/analytics/conversion', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('Failed to fetch conversion analytics')
    return res.json()
  }
}

export const analyticsService = new AnalyticsService()

