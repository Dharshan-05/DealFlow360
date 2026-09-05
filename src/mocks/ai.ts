import type { AIAnalysis, AIRecommendation, AISignal } from '../types/ai'

export const mockAIAnalysis: AIAnalysis = {
  id: 'ai_REQ-2026-1042_run1',
  requestId: 'req_1042',
  status: 'Complete',
  overallRisk: 'Medium',
  riskScore: 38,
  confidenceScore: 92,
  summary:
    'Commercial variance detected on line item 2. Overall account risk is low due to historical on-time payment track record.',
  factors: [
    {
      category: 'Pricing',
      level: 'High',
      title: 'Discount Variance Above Standard Ceiling',
      description: 'Setup Service requested discount of 18% exceeds standard 10% ceiling by 8pp.',
      impact: 'Reduces line gross margin by ₹36,000.',
      mitigation: 'Counter-offer with 10% discount and extended warranty.',
    },
    {
      category: 'Customer',
      level: 'Low',
      title: 'Established Account Track Record',
      description: 'Acme Corp has 4 active contracts with 98% on-time settlement history.',
      impact: 'Negligible default or commercial collection risk.',
    },
    {
      category: 'Payment',
      level: 'Medium',
      title: 'Commercial Credit Extension Request',
      description: 'Net 60 commercial credit requested instead of default Net 30.',
      impact: 'Working capital commitment extended by 30 days.',
      mitigation: 'Require 50% milestone billing on dispatch.',
    },
    {
      category: 'Inventory',
      level: 'Low',
      title: 'Hardware Stock Confirmed',
      description: 'All 24 units of Enterprise Laptop Pro 14 are in stock at Main Warehouse.',
      impact: 'Immediate fulfillment upon approval.',
    },
  ],
  positiveSignals: [
    'Acme Corp is a verified enterprise account with ₹8.4M trailing 12-month transaction volume.',
    'Zero historical invoice disputes or delayed payment defaults.',
    'Complete contractual pack including master service agreement attached.',
  ],
  warnings: [
    'Single-line discount of 18% exceeds default account rep authority threshold.',
  ],
  insights: [
    'Discount exception of 18% is standard for 20+ unit enterprise hardware deployments in this vertical.',
    'AI win-rate model calculates a 94% win probability with current configuration.',
  ],
  recommendation: {
    id: 'rec_001',
    requestId: 'req_1042',
    type: 'Approve with Conditions',
    title: 'Optimal Margin Protection Adjustment',
    recommendedAction: 'Adjust Setup Service discount to 10% and bundle Extended Support at 15%.',
    rationale:
      'Customer segment benchmarking shows a 94% deal-win probability with 10% discount when combined with multi-year warranty incentives.',
    confidence: 92,
    impactDescription: 'Protects ₹36,000 in gross margin while remaining within pre-approved AE delegation authority.',
    reasoning: {
      summary: 'Commercial variance is acceptable given enterprise account retention value.',
      commercialAssessment: 'Overall contract valuation of ₹4.20M preserves healthy 34% blended gross margin.',
      customerAssessment: 'Tier-1 customer with verified payment track record and zero default history.',
      riskAssessment: 'Evaluated as Medium Risk (38/100) due to commercial exception threshold trigger.',
      operationalAssessment: 'Hardware fleet is in stock; delivery SLA can be met within 5 business days.',
      policyAssessment: 'Requires Sales Director sign-off under Delegation Rule SEC-PRICING-04.',
    },
    conditions: [
      'Sales Director co-signature required for 18% setup discount.',
      'Net-60 credit terms approved contingent on automated milestone draw.',
    ],
    suggestedNextAction: 'Submit for managerial approval',
    userDecision: 'Pending',
    accepted: false,
  },
  analyzedAt: '2026-09-05T14:42:00Z',
  runNumber: 1,
}

export const mockAIRecommendations: AIRecommendation[] = [
  {
    id: 'rec_001',
    requestId: 'req_1042',
    type: 'Approve with Conditions',
    title: 'Optimal Margin Protection Adjustment',
    recommendedAction: 'Adjust Setup Service discount to 10% and bundle Extended Support at 15%.',
    rationale:
      'Customer segment benchmarking shows a 94% deal-win probability with 10% discount when combined with multi-year warranty incentives.',
    confidence: 92,
    impactDescription: 'Protects ₹36,000 in gross margin while remaining within pre-approved AE delegation authority.',
    reasoning: {
      summary: 'Commercial variance is acceptable given enterprise account retention value.',
      commercialAssessment: 'Overall contract valuation of ₹4.20M preserves healthy 34% blended gross margin.',
      customerAssessment: 'Tier-1 customer with verified payment track record.',
      riskAssessment: 'Medium risk profile.',
      operationalAssessment: 'Hardware in stock.',
      policyAssessment: 'Requires Sales Director sign-off.',
    },
    conditions: ['Sales Director co-signature required.'],
    suggestedNextAction: 'Submit for managerial approval',
    userDecision: 'Pending',
    accepted: false,
  },
  {
    id: 'rec_002',
    requestId: 'req_1038',
    type: 'Approve',
    title: 'Enterprise Upsell Attachment',
    recommendedAction: 'Add 24/7 Premium Mission-Critical SLA (+₹1.2M ACV).',
    rationale: '73% historical attachment rate for Financial Services customers in Q3.',
    confidence: 88,
    impactDescription: 'Expands Contract Annual Recurring Value by 19.6%.',
    reasoning: {
      summary: 'High close probability with expansion upside.',
      commercialAssessment: 'Accretive deal structure with ₹6.10M value.',
      customerAssessment: 'GlobalFin Inc is an investment-grade financial institution.',
      riskAssessment: 'Low risk profile (18/100).',
      operationalAssessment: 'Platform deployment pre-cleared.',
      policyAssessment: 'Full policy adherence.',
    },
    suggestedNextAction: 'Proceed with standard approval workflow',
    userDecision: 'Accepted',
    accepted: true,
  },
]

export const mockAISignals: AISignal[] = [
  {
    id: 'sig_001',
    level: 'High',
    title: 'Setup Service discount exceeds allowed policy threshold',
    impact: 'Requires managerial approval escalation and reduces deal margin by 4.2%.',
    reason: 'Requested discount of 18% vs max policy limit of 10%.',
    suggestedAction: 'Review discount or justify with volume commitment.',
  },
  {
    id: 'sig_002',
    level: 'Medium',
    title: 'Payment term extension to Net 60',
    impact: 'Increases working capital exposure by 30 days.',
    reason: 'Standard customer policy is Net 30.',
    suggestedAction: 'Request 50% upfront milestone payment.',
  },
]
