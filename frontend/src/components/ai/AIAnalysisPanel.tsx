import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAI } from '../../hooks/useAI'
import { StatusBadge } from '../common'
import type { Request } from '../../types/request'

interface Props {
  request: Request | null
  onClose?: () => void
  onNavigateToRequest?: () => void
}

const riskColor = (level: string) => {
  switch (level) {
    case 'Critical':
      return '#EF4444'
    case 'High':
      return '#F97316'
    case 'Medium':
      return '#F59E0B'
    case 'Low':
    default:
      return '#10B981'
  }
}

const riskBg = (level: string) => {
  switch (level) {
    case 'Critical':
      return 'rgba(239, 68, 68, 0.08)'
    case 'High':
      return 'rgba(249, 115, 22, 0.08)'
    case 'Medium':
      return 'rgba(245, 158, 11, 0.08)'
    case 'Low':
    default:
      return 'rgba(16, 185, 129, 0.08)'
  }
}

export default function AIAnalysisPanel({ request, onClose, onNavigateToRequest }: Props) {
  const {
    analysis,
    history,
    isAnalyzing,
    stageIndex,
    totalStages,
    currentStageLabel,
    startAnalysis,
    acceptRecommendation,
    requestManualReview,
  } = useAI(request)

  const [activeReasoningTab, setActiveReasoningTab] = useState<
    'commercial' | 'customer' | 'risk' | 'operational' | 'policy'
  >('commercial')
  const [decisionNotice, setDecisionNotice] = useState<string | null>(null)

  if (!request) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: '#71717A' }}>
        No request selected for AI Analysis.
      </div>
    )
  }

  const isDraft = request.status === 'Draft'
  const hasAnalysis = !!analysis

  const handleAccept = () => {
    const ok = acceptRecommendation()
    if (ok) {
      setDecisionNotice('Recommendation accepted. Request status moved to "Ready for Approval".')
    }
  }

  const handleManualReview = () => {
    const ok = requestManualReview()
    if (ok) {
      setDecisionNotice('Manual review initiated. Request status moved to "Under Review".')
    }
  }

  return (
    <div
      className="ai-analysis-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 20,
        color: '#E4E4E7',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid #1a1a1e',
          paddingBottom: 16,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span
              className="mono"
              style={{
                fontSize: 12,
                fontWeight: 700,
                color: '#fff',
                background: '#141418',
                padding: '2px 8px',
                borderRadius: 4,
                border: '1px solid #22222a',
              }}
            >
              {request.referenceNumber}
            </span>
            <StatusBadge status={request.status} size="sm" showDot />
            <span
              style={{
                fontSize: 10.5,
                fontWeight: 600,
                color: '#A78BFA',
                background: 'rgba(124, 58, 237, 0.12)',
                padding: '1px 6px',
                borderRadius: 4,
                textTransform: 'uppercase',
              }}
            >
              {request.requestType}
            </span>
            <span
              style={{
                fontSize: 10,
                color: '#71717A',
                background: '#09090b',
                border: '1px solid #18181f',
                padding: '2px 6px',
                borderRadius: 4,
                fontFamily: 'monospace',
              }}
            >
              Simulated AI Engine
            </span>
          </div>

          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#fff', margin: '4px 0 2px 0' }}>
            AI Intelligence Assessment: {request.title}
          </h2>
          <p style={{ fontSize: 12.5, color: '#71717A', margin: 0 }}>
            Account: <span style={{ color: '#fff' }}>{request.customer}</span> · Valuation: <span className="mono" style={{ color: '#fff' }}>{request.formattedAmount}</span> · Owner: {request.owner}
          </p>
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {hasAnalysis && !isAnalyzing && (
            <button
              onClick={() => startAnalysis(true)}
              className="df-btn-secondary"
              style={{ padding: '6px 12px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 5 }}
            >
              ↻ Re-analyze Request
            </button>
          )}

          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#71717A',
                cursor: 'pointer',
                fontSize: 16,
                padding: 6,
              }}
              title="Close Panel"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Decision Notice */}
      {decisionNotice && (
        <div
          style={{
            padding: '10px 14px',
            borderRadius: 6,
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#34D399',
            fontSize: 12.5,
          }}
        >
          {decisionNotice}
        </div>
      )}

      {/* DRAFT STATE: Cannot analyze until submitted */}
      {isDraft && (
        <div
          style={{
            padding: 24,
            borderRadius: 8,
            background: '#0a0a0c',
            border: '1px solid #1a1a1a',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
            Request is Currently in Draft
          </div>
          <p style={{ fontSize: 12.5, color: '#71717A', maxWidth: 460, margin: '0 auto 16px auto', lineHeight: 1.5 }}>
            Automated AI analysis is triggered upon request submission. Complete required information and submit this draft to initiate intelligence evaluation.
          </p>
          {onNavigateToRequest && (
            <button
              onClick={onNavigateToRequest}
              className="df-btn-primary"
              style={{ padding: '8px 16px', fontSize: 12.5 }}
            >
              Open Request Workspace &rarr;
            </button>
          )}
        </div>
      )}

      {/* PROCESSING STATE: Simulated sequential analysis */}
      {isAnalyzing && (
        <div
          style={{
            padding: 28,
            borderRadius: 10,
            background: '#09090b',
            border: '1px solid rgba(124, 58, 237, 0.3)',
            boxShadow: '0 0 24px rgba(124, 58, 237, 0.08)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <motion.div
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                border: '2px solid #7C3AED',
                borderTopColor: 'transparent',
              }}
              animate={{ rotate: 360 }}
              transition={{ duration: 0.6, repeat: Infinity, ease: 'linear' }}
            />
            <span style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>
              Analyzing Request Signals...
            </span>
            <span style={{ marginLeft: 'auto', fontSize: 11, color: '#A78BFA' }} className="mono">
              Stage {stageIndex + 1} of {totalStages}
            </span>
          </div>

          {/* Progress Bar */}
          <div
            style={{
              height: 4,
              background: '#18181f',
              borderRadius: 2,
              overflow: 'hidden',
              marginBottom: 16,
            }}
          >
            <motion.div
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, #7C3AED, #4F46E5)',
              }}
              initial={{ width: '0%' }}
              animate={{ width: `${((stageIndex + 1) / totalStages) * 100}%` }}
              transition={{ duration: 0.2 }}
            />
          </div>

          {/* Stage Sequence Display */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              'Validating request schema and line items',
              'Reviewing commercial discounting & gross margins',
              'Evaluating 14 risk factors against enterprise policy',
              'Analyzing historical customer payment signals',
              'Computing weighted confidence score',
              'Synthesizing recommendation & conditions',
            ].map((stg, idx) => {
              const isDone = idx < stageIndex
              const isCurr = idx === stageIndex
              return (
                <div key={stg} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                  <span
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      background: isDone ? '#10B981' : isCurr ? '#7C3AED' : '#18181f',
                      color: '#fff',
                      fontSize: 9,
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {isDone ? '✓' : idx + 1}
                  </span>
                  <span
                    style={{
                      color: isCurr ? '#fff' : isDone ? '#D4D4D8' : '#555',
                      fontWeight: isCurr ? 600 : 400,
                    }}
                  >
                    {stg}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* READY STATE: Request submitted but analysis not run yet */}
      {!isDraft && !isAnalyzing && !hasAnalysis && (
        <div
          style={{
            padding: 32,
            borderRadius: 10,
            background: 'rgba(124, 58, 237, 0.03)',
            border: '1px solid rgba(124, 58, 237, 0.2)',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: '50%',
              background: 'rgba(124, 58, 237, 0.15)',
              border: '1px solid rgba(124, 58, 237, 0.35)',
              color: '#A78BFA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px auto',
              fontSize: 18,
            }}
          >
            ✦
          </div>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#fff', margin: '0 0 4px 0' }}>
            Ready for AI Intelligence Analysis
          </h3>
          <p style={{ fontSize: 12.5, color: '#71717A', maxWidth: 480, margin: '0 auto 18px auto', lineHeight: 1.5 }}>
            Automated policy models are ready to evaluate commercial exceptions, margin impact, counterparty risk, and generate actionable recommendations.
          </p>
          <button
            onClick={() => startAnalysis(false)}
            className="df-btn-primary"
            style={{ padding: '9px 22px', fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <span>✦</span> Run AI Analysis &rarr;
          </button>
        </div>
      )}

      {/* COMPLETE ANALYSIS RESULT */}
      {!isAnalyzing && analysis && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Top Row: Risk Score + Confidence Score + Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* Risk Score Card */}
            <div
              style={{
                padding: '18px 20px',
                borderRadius: 8,
                background: '#080808',
                border: '1px solid #1a1a1a',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: '#71717A', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Calculated Risk Score
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: 4,
                      color: riskColor(analysis.overallRisk),
                      background: riskBg(analysis.overallRisk),
                      border: `1px solid ${riskColor(analysis.overallRisk)}33`,
                      textTransform: 'uppercase',
                    }}
                  >
                    {analysis.overallRisk} Risk
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 8 }}>
                  <span className="mono" style={{ fontSize: 32, fontWeight: 800, color: riskColor(analysis.overallRisk) }}>
                    {analysis.riskScore}
                  </span>
                  <span style={{ fontSize: 13, color: '#71717A' }} className="mono">
                    / 100
                  </span>
                </div>

                {/* Score bar */}
                <div style={{ height: 6, background: '#16161a', borderRadius: 3, overflow: 'hidden', marginBottom: 10 }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${analysis.riskScore}%`,
                      background: riskColor(analysis.overallRisk),
                      borderRadius: 3,
                    }}
                  />
                </div>
              </div>

              <div style={{ fontSize: 11.5, color: '#71717A', lineHeight: 1.45 }}>
                Evaluated against 14 risk benchmarks across pricing concessions, inventory allocation, and contract duration.
              </div>
            </div>

            {/* AI Confidence Card */}
            <div
              style={{
                padding: '18px 20px',
                borderRadius: 8,
                background: '#080808',
                border: '1px solid #1a1a1a',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: '#71717A', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    AI Confidence Score
                  </span>
                  <span
                    style={{
                      fontSize: 10.5,
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: 4,
                      color: '#10B981',
                      background: 'rgba(16, 185, 129, 0.08)',
                      border: '1px solid rgba(16, 185, 129, 0.25)',
                    }}
                  >
                    High Signal Integrity
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 8 }}>
                  <span className="mono" style={{ fontSize: 32, fontWeight: 800, color: '#fff' }}>
                    {analysis.confidenceScore}%
                  </span>
                </div>

                {/* Confidence Meter Bar */}
                <div style={{ height: 6, background: '#16161a', borderRadius: 3, overflow: 'hidden', marginBottom: 10 }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${analysis.confidenceScore}%`,
                      background: '#7C3AED',
                      borderRadius: 3,
                    }}
                  />
                </div>
              </div>

              <div style={{ fontSize: 11.5, color: '#71717A', lineHeight: 1.45 }}>
                Confidence derived from verified customer financial track records, ERP pricing policies, and complete request schema.
              </div>
            </div>
          </div>

          {/* Prominent Recommendation Card (Step 11 & 14) */}
          <div
            style={{
              padding: '22px 24px',
              borderRadius: 10,
              background: 'linear-gradient(145deg, rgba(124, 58, 237, 0.08), #09090c)',
              border: '1px solid rgba(124, 58, 237, 0.28)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{
                    fontSize: 10.5,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    padding: '2px 8px',
                    borderRadius: 4,
                    background:
                      analysis.recommendation.type === 'Approve'
                        ? 'rgba(16, 185, 129, 0.15)'
                        : analysis.recommendation.type === 'Reject'
                        ? 'rgba(239, 68, 68, 0.15)'
                        : 'rgba(245, 158, 11, 0.15)',
                    color:
                      analysis.recommendation.type === 'Approve'
                        ? '#34D399'
                        : analysis.recommendation.type === 'Reject'
                        ? '#F87171'
                        : '#FBBF24',
                    border: `1px solid ${
                      analysis.recommendation.type === 'Approve'
                        ? 'rgba(16, 185, 129, 0.3)'
                        : analysis.recommendation.type === 'Reject'
                        ? 'rgba(239, 68, 68, 0.3)'
                        : 'rgba(245, 158, 11, 0.3)'
                    }`,
                  }}
                >
                  {analysis.recommendation.type}
                </span>
                <span style={{ fontSize: 11.5, color: '#A78BFA' }}>
                  Recommendation Confidence: {analysis.recommendation.confidence}%
                </span>
              </div>

              {analysis.recommendation.userDecision && analysis.recommendation.userDecision !== 'Pending' && (
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: '#fff',
                    background: '#18181f',
                    padding: '2px 8px',
                    borderRadius: 4,
                    border: '1px solid #27272a',
                  }}
                >
                  Decision: {analysis.recommendation.userDecision}
                </span>
              )}
            </div>

            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 6px 0' }}>
              {analysis.recommendation.title}
            </h3>

            <p style={{ fontSize: 13, color: '#D4D4D8', lineHeight: 1.55, margin: '0 0 14px 0' }}>
              {analysis.recommendation.rationale}
            </p>

            {/* Conditions List if applicable */}
            {analysis.recommendation.conditions && analysis.recommendation.conditions.length > 0 && (
              <div
                style={{
                  padding: '12px 14px',
                  borderRadius: 6,
                  background: 'rgba(245, 158, 11, 0.06)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                  marginBottom: 16,
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 700, color: '#F59E0B', textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.05em' }}>
                  Required Approval Conditions:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {analysis.recommendation.conditions.map((cond, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#FDE68A', display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                      <span style={{ color: '#F59E0B' }}>•</span>
                      <span>{cond}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Info List if applicable */}
            {analysis.recommendation.missingInformation && analysis.recommendation.missingInformation.length > 0 && (
              <div
                style={{
                  padding: '12px 14px',
                  borderRadius: 6,
                  background: 'rgba(239, 68, 68, 0.06)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  marginBottom: 16,
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 700, color: '#EF4444', textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.05em' }}>
                  Missing Information Required:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {analysis.recommendation.missingInformation.map((item, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#FECACA', display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                      <span style={{ color: '#EF4444' }}>•</span>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggested Next Action */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: 12,
                borderTop: '1px solid rgba(124, 58, 237, 0.18)',
                flexWrap: 'wrap',
                gap: 12,
              }}
            >
              <div style={{ fontSize: 12, color: '#A1A1AA' }}>
                <span style={{ color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>Suggested Next Action: </span>
                <span style={{ color: '#fff', fontWeight: 600 }}>{analysis.recommendation.suggestedNextAction}</span>
              </div>

              {/* User Decision Buttons (Step 14: Does NOT directly approve; transitions toward Ready for Approval) */}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  onClick={handleAccept}
                  className="df-btn-primary"
                  style={{ padding: '7px 14px', fontSize: 12 }}
                >
                  Accept Recommendation &rarr;
                </button>
                <button
                  type="button"
                  onClick={handleManualReview}
                  className="df-btn-secondary"
                  style={{ padding: '7px 14px', fontSize: 12 }}
                >
                  Review Manually
                </button>
              </div>
            </div>
          </div>

          {/* Row 3: Risk Factors & Positive Signals */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* Risk Factors */}
            <div style={{ padding: '18px 20px', borderRadius: 8, background: '#080808', border: '1px solid #1a1a1a' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 12 }}>
                Risk Factors ({analysis.factors.length})
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {analysis.factors.length > 0 ? (
                  analysis.factors.map((f, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 6,
                        background: '#0d0d10',
                        border: '1px solid #181820',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: '#fff' }}>{f.title}</span>
                        <span
                          style={{
                            fontSize: 9.5,
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: 3,
                            color: riskColor(f.level),
                            background: riskBg(f.level),
                            border: `1px solid ${riskColor(f.level)}25`,
                            textTransform: 'uppercase',
                          }}
                        >
                          {f.level}
                        </span>
                      </div>
                      <div style={{ fontSize: 11.5, color: '#A1A1AA', lineHeight: 1.45, marginBottom: 4 }}>
                        {f.description}
                      </div>
                      <div style={{ fontSize: 11, color: '#71717A' }}>
                        <span style={{ color: '#555' }}>Impact: </span>{f.impact}
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: 12, color: '#71717A', fontStyle: 'italic' }}>
                    Zero adverse risk factors identified.
                  </div>
                )}
              </div>
            </div>

            {/* Positive Signals & Insights */}
            <div style={{ padding: '18px 20px', borderRadius: 8, background: '#080808', border: '1px solid #1a1a1a' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 12 }}>
                Positive Signals & Highlights ({analysis.positiveSignals.length})
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
                {analysis.positiveSignals.map((sig, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '8px 10px',
                      borderRadius: 6,
                      background: 'rgba(16, 185, 129, 0.04)',
                      border: '1px solid rgba(16, 185, 129, 0.15)',
                      fontSize: 12,
                      color: '#6EE7B7',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 8,
                    }}
                  >
                    <span style={{ color: '#10B981', fontWeight: 700 }}>✓</span>
                    <span>{sig}</span>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: 12.5, fontWeight: 600, color: '#D4D4D8', marginBottom: 6 }}>
                Key Operational Insights
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {analysis.insights.map((ins, i) => (
                  <div key={i} style={{ fontSize: 11.5, color: '#A1A1AA', lineHeight: 1.45, paddingLeft: 8, borderLeft: '2px solid #7C3AED' }}>
                    {ins}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Row 4: Structured Reasoning ("Why this recommendation?") */}
          <div style={{ padding: '18px 20px', borderRadius: 8, background: '#080808', border: '1px solid #1a1a1a' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>
                Why This Recommendation? (Explainable Reasoning)
              </div>
              <span style={{ fontSize: 11, color: '#555' }}>
                Automated multi-criteria assessment
              </span>
            </div>

            {/* Reasoning category tabs */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 14, overflowX: 'auto' }}>
              {(
                [
                  { id: 'commercial', label: 'Commercial Terms' },
                  { id: 'customer', label: 'Customer Assessment' },
                  { id: 'risk', label: 'Risk Evaluation' },
                  { id: 'operational', label: 'Operational Feasibility' },
                  { id: 'policy', label: 'Policy Adherence' },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveReasoningTab(tab.id)}
                  style={{
                    padding: '5px 10px',
                    borderRadius: 4,
                    fontSize: 11.5,
                    fontWeight: 600,
                    background: activeReasoningTab === tab.id ? '#fff' : '#141418',
                    color: activeReasoningTab === tab.id ? '#000' : '#888',
                    border: `1px solid ${activeReasoningTab === tab.id ? '#fff' : '#222'}`,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Active Tab Content */}
            <div
              style={{
                padding: '12px 14px',
                borderRadius: 6,
                background: '#0d0d10',
                border: '1px solid #1e1e24',
                fontSize: 12.5,
                color: '#D4D4D8',
                lineHeight: 1.6,
              }}
            >
              {activeReasoningTab === 'commercial' && analysis.recommendation.reasoning.commercialAssessment}
              {activeReasoningTab === 'customer' && analysis.recommendation.reasoning.customerAssessment}
              {activeReasoningTab === 'risk' && analysis.recommendation.reasoning.riskAssessment}
              {activeReasoningTab === 'operational' && analysis.recommendation.reasoning.operationalAssessment}
              {activeReasoningTab === 'policy' && analysis.recommendation.reasoning.policyAssessment}
            </div>
          </div>

          {/* Row 5: AI Analysis Run History (Step 16) */}
          {history.length > 0 && (
            <div style={{ padding: '18px 20px', borderRadius: 8, background: '#080808', border: '1px solid #1a1a1a' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 12 }}>
                Analysis Run History ({history.length})
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #161616' }}>
                      {['Run #', 'Analyzed At', 'Risk Level', 'Risk Score', 'Confidence', 'Recommendation', 'Status'].map(
                        (h) => (
                          <th
                            key={h}
                            style={{
                              padding: '8px 10px',
                              fontSize: 10.5,
                              color: '#555',
                              textTransform: 'uppercase',
                              letterSpacing: '.05em',
                            }}
                          >
                            {h}
                          </th>
                        )
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((run) => (
                      <tr key={run.id} style={{ borderBottom: '1px solid #111116' }}>
                        <td style={{ padding: '9px 10px', fontSize: 11.5, color: '#fff' }} className="mono">
                          Run {run.runNumber}
                        </td>
                        <td style={{ padding: '9px 10px', fontSize: 11.5, color: '#71717A' }}>
                          {new Date(run.analyzedAt).toLocaleString()}
                        </td>
                        <td style={{ padding: '9px 10px' }}>
                          <span
                            style={{
                              fontSize: 10,
                              fontWeight: 700,
                              padding: '1px 5px',
                              borderRadius: 3,
                              color: riskColor(run.overallRisk),
                              background: riskBg(run.overallRisk),
                              border: `1px solid ${riskColor(run.overallRisk)}25`,
                            }}
                          >
                            {run.overallRisk}
                          </span>
                        </td>
                        <td style={{ padding: '9px 10px', fontSize: 11.5, color: '#D4D4D8' }} className="mono">
                          {run.riskScore}/100
                        </td>
                        <td style={{ padding: '9px 10px', fontSize: 11.5, color: '#A78BFA' }} className="mono">
                          {run.confidenceScore}%
                        </td>
                        <td style={{ padding: '9px 10px', fontSize: 11.5, color: '#fff', fontWeight: 500 }}>
                          {run.recommendationType}
                        </td>
                        <td style={{ padding: '9px 10px', fontSize: 11, color: '#10B981' }}>
                          ● {run.status}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
