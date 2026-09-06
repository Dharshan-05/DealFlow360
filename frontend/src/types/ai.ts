export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical'

export type AIAnalysisStatus = 'Ready' | 'Analyzing' | 'Complete' | 'Failed'

export type AIRecommendationType =
  | 'Approve'
  | 'Approve with Conditions'
  | 'Request Additional Information'
  | 'Request Changes'
  | 'Escalate for Review'
  | 'Reject'

export interface RiskFactor {
  id?: string
  category: 'Pricing' | 'Policy' | 'Customer' | 'Payment' | 'Operational' | 'Inventory'
  level: RiskLevel
  title: string
  description: string
  impact: string
  mitigation?: string
}

export interface RecommendationReasoning {
  summary: string
  commercialAssessment: string
  customerAssessment: string
  riskAssessment: string
  operationalAssessment: string
  policyAssessment: string
}

export interface AIRecommendation {
  id: string
  requestId: string
  type: AIRecommendationType
  title: string
  recommendedAction: string
  rationale: string
  confidence: number // 0 - 100
  impactDescription: string
  reasoning: RecommendationReasoning
  conditions?: string[]
  missingInformation?: string[]
  suggestedNextAction: string
  userDecision?: 'Accepted' | 'Manual Review' | 'Pending'
  decidedAt?: string
  accepted?: boolean
}

export interface AIAnalysis {
  id: string
  requestId: string
  status: AIAnalysisStatus
  overallRisk: RiskLevel
  riskScore: number // 0 - 100
  confidenceScore: number // 0 - 100
  summary: string
  factors: RiskFactor[]
  positiveSignals: string[]
  warnings: string[]
  insights: string[]
  recommendation: AIRecommendation
  analyzedAt: string
  runNumber: number
}

export interface AIAnalysisRun {
  id: string
  requestId: string
  runNumber: number
  overallRisk: RiskLevel
  riskScore: number
  confidenceScore: number
  recommendationType: AIRecommendationType
  analyzedAt: string
  status: AIAnalysisStatus
}

export interface AISignal {
  id: string
  level: RiskLevel
  title: string
  impact: string
  reason: string
  suggestedAction: string
}
