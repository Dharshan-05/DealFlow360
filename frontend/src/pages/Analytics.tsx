import React, { useState, useEffect, useMemo } from 'react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts'
import { motion, AnimatePresence } from 'framer-motion'
import {
  analyticsService,
  reportService
} from '../services'
import {
  AnalyticsPeriod,
  AnalyticsFilters,
  ReportType,
  GeneratedReport,
  ReportHistoryItem
} from '../types/analytics'
import { exportReportAsCsv, exportToCsv } from '../utils/exportCsv'
import ReportPreviewModal from '../components/reports/ReportPreviewModal'
import {
  TrendingUpIcon,
  BarChart3Icon,
  FileTextIcon,
  DownloadIcon,
  PrinterIcon,
  RotateCcwIcon,
  FilterIcon,
  CheckCircle2Icon,
  AlertCircleIcon,
  ClockIcon,
  ShieldCheckIcon,
  ServerIcon,
  PlayIcon,
  ArrowRightIcon,
  TerminalIcon
} from '../components/common/Icons'

const PERIOD_OPTIONS: { label: string; value: AnalyticsPeriod }[] = [
  { label: '7D', value: '7d' },
  { label: '30D', value: '30d' },
  { label: '90D', value: '90d' },
  { label: '12M', value: '12m' },
  { label: 'ALL', value: 'all' }
]

const DEPT_OPTIONS = ['All', 'Procurement', 'IT', 'Finance', 'Legal', 'Operations']
const RISK_OPTIONS = ['All', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export default function Analytics() {
  const [activeTab, setActiveTab] = useState<'analytics' | 'reports'>('analytics')
  const [period, setPeriod] = useState<AnalyticsPeriod>('30d')
  const [department, setDepartment] = useState('All')
  const [riskLevel, setRiskLevel] = useState('All')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefreshed, setLastRefreshed] = useState<string>(new Date().toLocaleTimeString())

  // Report Generation State
  const [history, setHistory] = useState<ReportHistoryItem[]>([])
  const [generatingReportId, setGeneratingReportId] = useState<string | null>(null)
  const [previewReport, setPreviewReport] = useState<GeneratedReport | null>(null)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  // Trigger Toast helper
  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3500)
  }

  // Load Report History
  const refreshHistory = () => {
    setHistory(reportService.getHistory())
  }

  useEffect(() => {
    refreshHistory()
  }, [])

  // Build Analytics Filters
  const filters: AnalyticsFilters = useMemo(() => {
    return {
      period,
      department: department === 'All' ? undefined : department,
      riskLevel: riskLevel === 'All' ? undefined : (riskLevel as any)
    }
  }, [period, department, riskLevel])

  // Reactive Analytics Data
  const [analyticsData, setAnalyticsData] = useState(() => analyticsService.getAnalytics(filters))

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setAnalyticsData(analyticsService.getAnalytics(filters))
      refreshHistory()
      setLastRefreshed(new Date().toLocaleTimeString())
      setIsRefreshing(false)
      showToast('Analytics cache updated from local state')
    }, 280)
  }

  useEffect(() => {
    setAnalyticsData(analyticsService.getAnalytics(filters))
  }, [filters])

  // Available Reports List
  const availableReports = useMemo(() => reportService.getAvailableReports(), [])

  // Action: Generate & Preview Report
  const handleGenerateAndPreview = async (reportType: ReportType) => {
    try {
      setGeneratingReportId(reportType)
      const report = await reportService.generateReport(reportType, filters)
      setPreviewReport(report)
      setIsPreviewOpen(true)
      refreshHistory()
    } catch (err: any) {
      showToast(`Error generating report: ${err.message}`)
    } finally {
      setGeneratingReportId(null)
    }
  }

  // Action: Quick CSV Export
  const handleQuickCsv = async (reportType: ReportType) => {
    try {
      setGeneratingReportId(reportType)
      const report = await reportService.generateReport(reportType, filters)
      exportReportAsCsv(report)
      refreshHistory()
      showToast(`Exported ${report.title} (.csv)`)
    } catch (err: any) {
      showToast(`Export failed: ${err.message}`)
    } finally {
      setGeneratingReportId(null)
    }
  }

  // Action: Export Analytics Overview CSV
  const handleExportOverviewCsv = () => {
    const columns = [
      { key: 'Metric', label: 'Metric' },
      { key: 'Value', label: 'Value' },
      { key: 'Trend', label: 'Trend' },
    ]
    const kpis = [
      { Metric: 'Total Deal Volume', Value: `$${(analyticsData.overview.totalVolume / 1000).toFixed(1)}k`, Trend: `+${analyticsData.overview.volumeGrowth}%` },
      { Metric: 'Active Request Count', Value: analyticsData.overview.activeRequests, Trend: `+${analyticsData.overview.activeGrowth}%` },
      { Metric: 'Approvals In-Flight', Value: analyticsData.overview.approvalsInFlight, Trend: 'Live' },
      { Metric: 'Execution Settlement Rate', Value: `${analyticsData.overview.settledRate}%`, Trend: 'Optimal' },
      { Metric: 'Average AI Risk Score', Value: `${analyticsData.overview.avgRiskScore}/100`, Trend: 'Low-Moderate' },
      { Metric: 'High Risk Deals Flagged', Value: analyticsData.overview.highRiskCount, Trend: 'Flagged' }
    ]
    exportToCsv(`dealflow_analytics_overview_${period}`, columns, kpis)
    showToast('Analytics Overview CSV exported')
  }

  const { overview, funnel, monthlyTrends, riskDistribution, turnaroundDistribution, topRiskFactors, operational } = analyticsData

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1480, margin: '0 auto', color: '#f3f4f6' }}>
      {/* Toast Notification */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={{
              position: 'fixed',
              top: 24,
              right: 28,
              zIndex: 9999,
              background: '#09090b',
              border: '1px solid #27272a',
              boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
              padding: '10px 18px',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 13,
              color: '#e4e4e7'
            }}
          >
            <CheckCircle2Icon size={16} color="#10b981" />
            <span>{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Top Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 20,
          marginBottom: 24,
          flexWrap: 'wrap'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <h1 style={{ margin: 0, color: '#ffffff', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>
              Intelligence & Reports
            </h1>
            <span
              style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 4,
                background: 'rgba(99, 102, 241, 0.12)',
                color: '#a5b4fc',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                fontWeight: 600,
                letterSpacing: '0.04em',
                textTransform: 'uppercase'
              }}
            >
              Enterprise BI
            </span>
          </div>
          <p style={{ margin: 0, color: '#71717a', fontSize: 13, maxWidth: 680, lineHeight: 1.5 }}>
            Real-time pipeline visibility, approval velocity, AI risk distributions, and one-click RFC-4180 compliant financial audit reports.
          </p>
        </div>

        {/* Global Controls & Period Picker */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Period Selector */}
          <div
            style={{
              display: 'flex',
              background: '#121215',
              border: '1px solid #27272a',
              borderRadius: 6,
              padding: 2
            }}
          >
            {PERIOD_OPTIONS.map((opt) => {
              const isSelected = period === opt.value
              return (
                <button
                  key={opt.value}
                  onClick={() => setPeriod(opt.value)}
                  style={{
                    padding: '5px 12px',
                    fontSize: 11,
                    fontWeight: isSelected ? 700 : 500,
                    borderRadius: 4,
                    background: isSelected ? '#27272a' : 'transparent',
                    color: isSelected ? '#ffffff' : '#71717a',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            title="Refresh local analytics"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 12px',
              fontSize: 12,
              background: '#18181b',
              border: '1px solid #27272a',
              borderRadius: 6,
              color: '#d4d4d8',
              cursor: 'pointer'
            }}
          >
            <RotateCcwIcon size={14} className={isRefreshing ? 'animate-spin' : ''} />
            <span style={{ fontSize: 11, color: '#71717a' }}>{lastRefreshed}</span>
          </button>

          {/* Export CSV Button */}
          <button
            onClick={handleExportOverviewCsv}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 14px',
              fontSize: 12,
              fontWeight: 600,
              background: '#27272a',
              border: '1px solid #3f3f46',
              borderRadius: 6,
              color: '#ffffff',
              cursor: 'pointer'
            }}
          >
            <DownloadIcon size={14} />
            Export Overview
          </button>
        </div>
      </header>

      {/* Primary Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid #27272a',
          marginBottom: 24,
          gap: 24
        }}
      >
        <button
          onClick={() => setActiveTab('analytics')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 4px 14px',
            fontSize: 14,
            fontWeight: activeTab === 'analytics' ? 600 : 500,
            color: activeTab === 'analytics' ? '#ffffff' : '#71717a',
            border: 'none',
            borderBottom: activeTab === 'analytics' ? '2px solid #6366f1' : '2px solid transparent',
            background: 'transparent',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <BarChart3Icon size={16} color={activeTab === 'analytics' ? '#818cf8' : '#71717a'} />
          Executive Analytics
        </button>

        <button
          onClick={() => setActiveTab('reports')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 4px 14px',
            fontSize: 14,
            fontWeight: activeTab === 'reports' ? 600 : 500,
            color: activeTab === 'reports' ? '#ffffff' : '#71717a',
            border: 'none',
            borderBottom: activeTab === 'reports' ? '2px solid #6366f1' : '2px solid transparent',
            background: 'transparent',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <FileTextIcon size={16} color={activeTab === 'reports' ? '#818cf8' : '#71717a'} />
          Enterprise Reports Center
          <span
            style={{
              padding: '1px 6px',
              fontSize: 10,
              fontWeight: 700,
              borderRadius: 10,
              background: '#27272a',
              color: '#d4d4d8'
            }}
          >
            6
          </span>
        </button>
      </div>

      {/* TAB 1: EXECUTIVE ANALYTICS */}
      {activeTab === 'analytics' && (
        <div>
          {/* Top 6 KPI Metric Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
              gap: 14,
              marginBottom: 24
            }}
          >
            {/* Card 1: Total Volume */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '18px 20px',
                position: 'relative'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Total Pipeline Volume
                </span>
                <span style={{ fontSize: 11, color: '#10b981', fontWeight: 600 }}>
                  +{overview.volumeGrowth}%
                </span>
              </div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ffffff', margin: '10px 0 6px' }}>
                ${(overview.totalVolume / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })}k
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>
                Normalized across {overview.activeRequests} deals
              </div>
            </div>

            {/* Card 2: Active Requests */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '18px 20px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Active Deals
                </span>
                <span style={{ fontSize: 11, color: '#10b981', fontWeight: 600 }}>
                  +{overview.activeGrowth}%
                </span>
              </div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ffffff', margin: '10px 0 6px' }}>
                {overview.activeRequests}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>
                Across all workflow stages
              </div>
            </div>

            {/* Card 3: Approvals In-Flight */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '18px 20px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  In Governance SLA
                </span>
                <ClockIcon size={14} color="#f59e0b" />
              </div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ffffff', margin: '10px 0 6px' }}>
                {overview.approvalsInFlight}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>
                Avg turnaround {turnaroundDistribution.averageHours}h
              </div>
            </div>

            {/* Card 4: Execution Settlement Rate */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '18px 20px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Settlement Rate
                </span>
                <CheckCircle2Icon size={14} color="#10b981" />
              </div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ffffff', margin: '10px 0 6px' }}>
                {overview.settledRate}%
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>
                Execution dispatched & settled
              </div>
            </div>

            {/* Card 5: AI Risk Score */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '18px 20px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Mean Risk Index
                </span>
                <ShieldCheckIcon size={14} color="#818cf8" />
              </div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ffffff', margin: '10px 0 6px' }}>
                {overview.avgRiskScore}<span style={{ fontSize: 14, color: '#71717a' }}>/100</span>
              </div>
              <div style={{ fontSize: 11, color: '#10b981' }}>
                Low-to-moderate risk rating
              </div>
            </div>

            {/* Card 6: AI High Risk Flagged */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '18px 20px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  High Risk Deals
                </span>
                <AlertCircleIcon size={14} color={overview.highRiskCount > 0 ? '#ef4444' : '#10b981'} />
              </div>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: overview.highRiskCount > 0 ? '#f87171' : '#ffffff', margin: '10px 0 6px' }}>
                {overview.highRiskCount}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>
                Requiring committee escalations
              </div>
            </div>
          </div>

          {/* End-to-End Funnel Progression (6 Stages) */}
          <div
            style={{
              background: '#09090b',
              border: '1px solid #1c1c24',
              borderRadius: 8,
              padding: '22px 24px',
              marginBottom: 24
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                  End-to-End Deal Conversion Funnel
                </h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>
                  Lifecycle progression from initial request creation through AI scoring, governance approval, and ERP settlement.
                </p>
              </div>
              <span style={{ fontSize: 12, color: '#a1a1aa' }}>
                Overall Conversion: <strong className="mono" style={{ color: '#10b981' }}>{funnel.length > 0 ? funnel[funnel.length - 1].conversionRate : 0}%</strong>
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: 12
              }}
            >
              {funnel.map((stage, idx) => (
                <div
                  key={stage.stage}
                  style={{
                    background: '#121215',
                    border: '1px solid #27272a',
                    borderRadius: 6,
                    padding: '14px 16px',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Step 0{idx + 1}
                    </span>
                    <span className="mono" style={{ fontSize: 11, color: '#71717a' }}>
                      {stage.conversionRate}%
                    </span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#e4e4e7', marginBottom: 8 }}>
                    {stage.stage}
                  </div>
                  <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: '#ffffff' }}>
                    {stage.count}
                  </div>
                  <div style={{ marginTop: 8, height: 4, background: '#27272a', borderRadius: 2, overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${stage.conversionRate}%`,
                        background: idx === funnel.length - 1 ? '#10b981' : '#6366f1',
                        borderRadius: 2
                      }}
                    />
                  </div>
                  {stage.dropoffRate > 0 && (
                    <div style={{ fontSize: 10, color: '#71717a', marginTop: 6 }}>
                      {stage.dropoffRate}% drop-off
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Charts Row 1: Volume Trend & AI Risk Distribution */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))',
              gap: 20,
              marginBottom: 24
            }}
          >
            {/* Chart 1: Financial Flow & Pipeline Trend */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '20px 22px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                    Pipeline & Settlement Trend
                  </h3>
                  <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>
                    Monthly recognized settlements vs active pipeline ($k)
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 14, fontSize: 11 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#a5b4fc' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#6366f1' }} />
                    Volume ($k)
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6ee7b7' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
                    Settled ($k)
                  </span>
                </div>
              </div>

              <div style={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={monthlyTrends}>
                    <defs>
                      <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorSettled" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#1f1f23" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: '#121215',
                        border: '1px solid #27272a',
                        borderRadius: 6,
                        color: '#f4f4f5',
                        fontSize: 12
                      }}
                    />
                    <Area type="monotone" dataKey="volume" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorVolume)" />
                    <Area type="monotone" dataKey="settled" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorSettled)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: AI Risk Profile Distribution */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '20px 22px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                    AI Risk Distribution
                  </h3>
                  <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>
                    Request volume segmented by AI computed risk thresholds
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 11,
                    color: '#71717a'
                  }}
                >
                  {riskDistribution.reduce((acc, r) => acc + r.count, 0)} Total Scored
                </span>
              </div>

              <div style={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={riskDistribution}>
                    <CartesianGrid stroke="#1f1f23" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="tier" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: '#121215',
                        border: '1px solid #27272a',
                        borderRadius: 6,
                        color: '#f4f4f5',
                        fontSize: 12
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {riskDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Charts Row 2: SLA Turnaround & Operational ERP Performance */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))',
              gap: 20,
              marginBottom: 24
            }}
          >
            {/* Chart 3: Approval Turnaround Latency */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '20px 22px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                    Governance Turnaround Velocity
                  </h3>
                  <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>
                    Time elapsed from request submission to final signoff
                  </div>
                </div>
                <div style={{ fontSize: 12, color: '#10b981', fontWeight: 600 }}>
                  98.4% SLA Adherence
                </div>
              </div>

              <div style={{ height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={turnaroundDistribution.tiers}>
                    <CartesianGrid stroke="#1f1f23" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="range" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: '#121215',
                        border: '1px solid #27272a',
                        borderRadius: 6,
                        color: '#f4f4f5',
                        fontSize: 12
                      }}
                    />
                    <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Card 4: Operational & ERP Simulated Performance */}
            <div
              style={{
                background: '#09090b',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                padding: '20px 22px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                    Operational & ERP Sync Metrics
                  </h3>
                  <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>
                    Simulated Odoo ERP dispatch latency & validation accuracy
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    padding: '2px 8px',
                    borderRadius: 4,
                    background: 'rgba(16, 185, 129, 0.1)',
                    color: '#34d399',
                    border: '1px solid rgba(16, 185, 129, 0.2)'
                  }}
                >
                  Simulated Odoo Environment
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 14, marginTop: 10 }}>
                <div style={{ background: '#121215', border: '1px solid #27272a', padding: 14, borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase' }}>Odoo Sync Success</div>
                  <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: '#10b981', marginTop: 6 }}>
                    {operational.odooSyncRate}%
                  </div>
                  <div style={{ fontSize: 10, color: '#52525b', marginTop: 4 }}>0 sync timeouts / 100% committed</div>
                </div>

                <div style={{ background: '#121215', border: '1px solid #27272a', padding: 14, borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase' }}>Avg Dispatch Latency</div>
                  <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: '#ffffff', marginTop: 6 }}>
                    {operational.avgDispatchLatencySeconds}s
                  </div>
                  <div style={{ fontSize: 10, color: '#52525b', marginTop: 4 }}>Instant sandbox socket simulation</div>
                </div>

                <div style={{ background: '#121215', border: '1px solid #27272a', padding: 14, borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase' }}>AI Agreement Rate</div>
                  <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: '#a5b4fc', marginTop: 6 }}>
                    {operational.aiAgreementRate}%
                  </div>
                  <div style={{ fontSize: 10, color: '#52525b', marginTop: 4 }}>Approvers concurred with AI advice</div>
                </div>

                <div style={{ background: '#121215', border: '1px solid #27272a', padding: 14, borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase' }}>Audited Ledger Entries</div>
                  <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: '#ffffff', marginTop: 6 }}>
                    {operational.journalEntriesGenerated}
                  </div>
                  <div style={{ fontSize: 10, color: '#52525b', marginTop: 4 }}>Generated journal entries</div>
                </div>
              </div>
            </div>
          </div>

          {/* Deep-Dive: Top Risk Drivers Table */}
          <div
            style={{
              background: '#09090b',
              border: '1px solid #1c1c24',
              borderRadius: 8,
              padding: '20px 22px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                  Top Risk Factors & Flagged Drivers
                </h3>
                <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>
                  Frequently recurring risk categories flagged by the AI engine during workflow evaluations
                </div>
              </div>
              <span style={{ fontSize: 11, color: '#71717a' }}>
                Evaluated from all active deal payloads
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #27272a', textAlign: 'left', color: '#71717a' }}>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Risk Factor & Description</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Frequency</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Severity</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Recommended Mitigation</th>
                  </tr>
                </thead>
                <tbody>
                  {topRiskFactors.map((factor, index) => {
                    const badgeColor =
                      factor.severity === 'CRITICAL'
                        ? '#ef4444'
                        : factor.severity === 'HIGH'
                        ? '#f59e0b'
                        : factor.severity === 'MEDIUM'
                        ? '#818cf8'
                        : '#10b981'
                    return (
                      <tr key={index} style={{ borderBottom: '1px solid #18181b' }}>
                        <td style={{ padding: '12px 12px', color: '#e4e4e7', fontWeight: 500 }}>
                          {factor.factor}
                        </td>
                        <td style={{ padding: '12px 12px' }}>
                          <span className="mono" style={{ color: '#ffffff', fontWeight: 600 }}>
                            {factor.count}
                          </span>
                          <span style={{ color: '#71717a', marginLeft: 4 }}>deals</span>
                        </td>
                        <td style={{ padding: '12px 12px' }}>
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: 4,
                              fontSize: 10,
                              fontWeight: 700,
                              color: badgeColor,
                              background: `${badgeColor}18`,
                              border: `1px solid ${badgeColor}40`
                            }}
                          >
                            {factor.severity}
                          </span>
                        </td>
                        <td style={{ padding: '12px 12px', color: '#a1a1aa' }}>
                          {factor.severity === 'CRITICAL'
                            ? 'Executive Committee review required prior to ERP dispatch.'
                            : factor.severity === 'HIGH'
                            ? 'VP Finance approval and secondary vendor verification needed.'
                            : 'Standard manager signoff sufficient.'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ENTERPRISE REPORTS CENTER */}
      {activeTab === 'reports' && (
        <div>
          {/* Filter Bar */}
          <div
            style={{
              background: '#09090b',
              border: '1px solid #1c1c24',
              borderRadius: 8,
              padding: '16px 20px',
              marginBottom: 24,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16,
              flexWrap: 'wrap'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#a1a1aa', fontSize: 12 }}>
                <FilterIcon size={14} />
                <span style={{ fontWeight: 600 }}>Report Scope:</span>
              </div>

              {/* Department Selector */}
              <div>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  style={{
                    background: '#121215',
                    border: '1px solid #27272a',
                    borderRadius: 6,
                    padding: '6px 12px',
                    fontSize: 12,
                    color: '#e4e4e7',
                    cursor: 'pointer'
                  }}
                >
                  {DEPT_OPTIONS.map((dept) => (
                    <option key={dept} value={dept}>
                      {dept === 'All' ? 'All Departments' : dept}
                    </option>
                  ))}
                </select>
              </div>

              {/* Risk Level Selector */}
              <div>
                <select
                  value={riskLevel}
                  onChange={(e) => setRiskLevel(e.target.value)}
                  style={{
                    background: '#121215',
                    border: '1px solid #27272a',
                    borderRadius: 6,
                    padding: '6px 12px',
                    fontSize: 12,
                    color: '#e4e4e7',
                    cursor: 'pointer'
                  }}
                >
                  {RISK_OPTIONS.map((lvl) => (
                    <option key={lvl} value={lvl}>
                      {lvl === 'All' ? 'All Risk Levels' : `${lvl} Risk`}
                    </option>
                  ))}
                </select>
              </div>

              {(department !== 'All' || riskLevel !== 'All') && (
                <button
                  onClick={() => {
                    setDepartment('All')
                    setRiskLevel('All')
                  }}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#818cf8',
                    fontSize: 11,
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  Reset filters
                </button>
              )}
            </div>

            <div style={{ fontSize: 11, color: '#71717a' }}>
              RFC-4180 CSV Compliant · Print-Ready Vector Tables
            </div>
          </div>

          {/* 6 Pre-configured Standard Reports Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
              gap: 18,
              marginBottom: 32
            }}
          >
            {availableReports.map((def) => {
              const isGenerating = generatingReportId === def.id
              const categoryColor =
                def.category === 'FINANCIAL'
                  ? '#10b981'
                  : def.category === 'GOVERNANCE'
                  ? '#f59e0b'
                  : def.category === 'AI & RISK'
                  ? '#818cf8'
                  : def.category === 'AUDIT'
                  ? '#ec4899'
                  : '#3b82f6'

              return (
                <div
                  key={def.id}
                  style={{
                    background: '#09090b',
                    border: '1px solid #1c1c24',
                    borderRadius: 8,
                    padding: '20px 22px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    transition: 'border-color 0.15s ease'
                  }}
                >
                  <div>
                    {/* Header: Category Badge & Row Estimate */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: 4,
                          color: categoryColor,
                          background: `${categoryColor}18`,
                          border: `1px solid ${categoryColor}40`,
                          letterSpacing: '0.04em'
                        }}
                      >
                        {def.category}
                      </span>
                      <span style={{ fontSize: 11, color: '#71717a' }}>
                        ~{def.estimatedRows} records
                      </span>
                    </div>

                    {/* Report Title & Description */}
                    <h3 style={{ margin: '0 0 6px', fontSize: 15, fontWeight: 600, color: '#ffffff' }}>
                      {def.title}
                    </h3>
                    <p style={{ margin: '0 0 16px', fontSize: 12, color: '#a1a1aa', lineHeight: 1.5 }}>
                      {def.description}
                    </p>

                    {/* Meta: Recommended Frequency & Audience */}
                    <div
                      style={{
                        background: '#121215',
                        border: '1px solid #27272a',
                        borderRadius: 6,
                        padding: '8px 12px',
                        fontSize: 11,
                        color: '#71717a',
                        marginBottom: 18,
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 8
                      }}
                    >
                      <div>
                        <span style={{ display: 'block', color: '#52525b', fontSize: 10, textTransform: 'uppercase' }}>Cadence</span>
                        <span style={{ color: '#e4e4e7', fontWeight: 500 }}>{def.recommendedFrequency}</span>
                      </div>
                      <div>
                        <span style={{ display: 'block', color: '#52525b', fontSize: 10, textTransform: 'uppercase' }}>Audience</span>
                        <span style={{ color: '#e4e4e7', fontWeight: 500 }}>{def.targetAudience}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions: Generate & Preview / Quick CSV */}
                  <div style={{ display: 'flex', gap: 10 }}>
                    <button
                      onClick={() => handleGenerateAndPreview(def.id)}
                      disabled={isGenerating}
                      style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        padding: '8px 14px',
                        fontSize: 12,
                        fontWeight: 600,
                        background: '#6366f1',
                        border: 'none',
                        borderRadius: 6,
                        color: '#ffffff',
                        cursor: isGenerating ? 'not-allowed' : 'pointer',
                        opacity: isGenerating ? 0.7 : 1,
                        transition: 'background 0.15s ease'
                      }}
                    >
                      {isGenerating ? (
                        <>
                          <RotateCcwIcon size={14} className="animate-spin" />
                          <span>Generating...</span>
                        </>
                      ) : (
                        <>
                          <PlayIcon size={12} fill="#ffffff" />
                          <span>Generate & Preview</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => handleQuickCsv(def.id)}
                      disabled={isGenerating}
                      title="Quick Download CSV"
                      style={{
                        padding: '8px 12px',
                        background: '#18181b',
                        border: '1px solid #27272a',
                        borderRadius: 6,
                        color: '#d4d4d8',
                        cursor: isGenerating ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <DownloadIcon size={14} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Report Generation History */}
          <div
            style={{
              background: '#09090b',
              border: '1px solid #1c1c24',
              borderRadius: 8,
              padding: '20px 22px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                  Generated Report History
                </h3>
                <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>
                  Persisted log of reports compiled and downloaded in this browser workspace
                </div>
              </div>
              <button
                onClick={() => {
                  reportService.clearHistory()
                  refreshHistory()
                  showToast('Report history cleared')
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#71717a',
                  fontSize: 11,
                  cursor: 'pointer'
                }}
              >
                Clear History
              </button>
            </div>

            {history.length === 0 ? (
              <div style={{ padding: '36px 0', textAlign: 'center', color: '#52525b', fontSize: 13 }}>
                No reports generated in this session yet. Select any report template above to generate.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #27272a', textAlign: 'left', color: '#71717a' }}>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Report Title</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Generated Time</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Records</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Estimated File Size</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600 }}>Format</th>
                      <th style={{ padding: '10px 12px', fontWeight: 600, textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((item) => (
                      <tr key={item.id} style={{ borderBottom: '1px solid #18181b' }}>
                        <td style={{ padding: '12px 12px', color: '#e4e4e7', fontWeight: 500 }}>
                          {item.title}
                        </td>
                        <td style={{ padding: '12px 12px', color: '#a1a1aa' }}>
                          {new Date(item.generatedAt).toLocaleString()}
                        </td>
                        <td style={{ padding: '12px 12px' }}>
                          <span className="mono" style={{ color: '#ffffff' }}>
                            {item.rowCount}
                          </span>
                        </td>
                        <td style={{ padding: '12px 12px', color: '#71717a' }}>
                          {item.fileSize}
                        </td>
                        <td style={{ padding: '12px 12px' }}>
                          <span
                            style={{
                              padding: '2px 6px',
                              borderRadius: 4,
                              fontSize: 10,
                              fontWeight: 700,
                              background: '#27272a',
                              color: '#a1a1aa'
                            }}
                          >
                            {item.format}
                          </span>
                        </td>
                        <td style={{ padding: '12px 12px', textAlign: 'right' }}>
                          <button
                            onClick={() => handleGenerateAndPreview(item.type)}
                            style={{
                              background: 'transparent',
                              border: '1px solid #27272a',
                              borderRadius: 4,
                              padding: '4px 8px',
                              color: '#818cf8',
                              fontSize: 11,
                              cursor: 'pointer',
                              marginRight: 6
                            }}
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleQuickCsv(item.type)}
                            style={{
                              background: 'transparent',
                              border: '1px solid #27272a',
                              borderRadius: 4,
                              padding: '4px 8px',
                              color: '#d4d4d8',
                              fontSize: 11,
                              cursor: 'pointer'
                            }}
                          >
                            CSV
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Interactive Report Preview Modal */}
      <ReportPreviewModal
        report={previewReport}
        isOpen={isPreviewOpen}
        onClose={() => {
          setIsPreviewOpen(false)
          setPreviewReport(null)
        }}
        onExportCsv={() => {
          if (previewReport) {
            exportReportAsCsv(previewReport)
            showToast(`Exported ${previewReport.title} (.csv)`)
          }
        }}
      />
    </div>
  )
}
