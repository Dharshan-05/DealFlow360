export type AnalyticsPeriod = '7d' | '30d' | '90d' | '12m' | 'all' | '7D' | '30D' | '90D' | '12M' | 'All'

export interface AnalyticsFilters {
  period?: AnalyticsPeriod
  requestType?: string
  priority?: string
  status?: string
  customer?: string
  riskLevel?: string
  department?: string
}


export interface OverviewMetrics {
  totalRequests: number
  totalRequestsChange: string
  approvalRate: number
  approvalRateFormatted: string
  avgProcessingHours: number
  aiRecommendationRate: number
  executionSuccessRate: number
  executionSuccessRateFormatted: string
  totalTransactionValue: string
  totalTransactionValueNumeric: number
  activePipelineValue: string
  activePipelineValueNumeric: number
}

export interface RequestAnalytics {
  total: number
  byStatus: { status: string; count: number; color: string }[]
  byPriority: { priority: string; count: number; color: string }[]
  byType: { type: string; count: number }[]
  trend: { period: string; count: number; value: number }[]
}

export interface ApprovalAnalytics {
  total: number
  pending: number
  approved: number
  rejected: number
  changesRequested: number
  approvalRate: number
  approvalRateFormatted: string
  avgTurnaroundHours: number
  highRiskCount: number
  outcomeDistribution: { outcome: string; count: number; color: string }[]
  byPriority: { priority: string; approved: number; rejected: number }[]
}

export interface AIAnalytics {
  analyzedCount: number
  avgConfidence: number
  riskDistribution: { level: string; count: number; color: string }[]
  recommendationDistribution: { recommendation: string; count: number; color: string }[]
  confidenceBands: { band: string; count: number }[]
}

export interface RiskFactorItem {
  factor: string
  category: string
  occurrences: number
  impact: 'High' | 'Medium' | 'Low'
}

export interface RiskAnalytics {
  levels: { level: string; count: number; percentage: number; color: string }[]
  avgScore: number
  highRiskCount: number
  topFactors: RiskFactorItem[]
}

export interface OperationalAnalytics {
  executionsStarted: number
  executionsCompleted: number
  executionsFailed: number
  successRate: number
  successRateFormatted: string
  avgDurationSec: number
  simulatedOdooOperations: number
  transactionsCreated: number
  statusBreakdown: { status: string; count: number; color: string }[]
}

export interface TransactionAnalytics {
  totalCount: number
  completedCount: number
  pendingCount: number
  failedCount: number
  totalValue: string
  totalValueNumeric: number
  avgValue: string
  byStatus: { status: string; count: number; color: string }[]
  byType: { type: string; count: number; value: number }[]
}

export interface FunnelStage {
  id: string
  name: string
  count: number
  conversionPercent: number
  dropCount: number
  note: string
}

export type ReportType =
  | 'request'
  | 'transaction'
  | 'ai'
  | 'approval'
  | 'performance'
  | 'audit'

export interface ReportColumn {
  key: string
  label: string
  mono?: boolean
}

export interface ReportDefinition {
  id: ReportType
  type: ReportType
  title: string
  description: string
  category: string
  columns: ReportColumn[]
  estimatedRows?: number
  recommendedFrequency?: string
  targetAudience?: string
}


export type ReportRecord = Record<string, any>

export interface GeneratedReport {
  id: string
  type: ReportType
  title: string
  generatedAt: string
  filterSummary: string
  summaryMetrics: { label: string; value: string | number; mono?: boolean }[]
  columns: ReportColumn[]
  rows: ReportRecord[]
  rowCount: number
}

export interface ReportHistoryItem {
  id: string
  type: ReportType
  title: string
  generatedAt: string
  filterSummary: string
  recordCount: number
  rowCount?: number
  fileSize?: string
  format?: string
}

