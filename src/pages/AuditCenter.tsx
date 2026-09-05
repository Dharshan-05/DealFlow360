import React, { useState, useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { motion, AnimatePresence } from 'framer-motion'
import { useAudit } from '../hooks/useAudit'
import type { AuditEvent, AuditFilters } from '../types/audit'
import { AuditSeverityBadge } from '../components/audit/AuditSeverityBadge'
import { AuditDetailDrawer } from '../components/audit/AuditDetailDrawer'
import { exportToCsv } from '../utils/exportCsv'
import {
  ShieldCheckIcon as ShieldCheck,
  RotateCcwIcon as RotateCcw,
  DownloadIcon as Download,
  FilterIcon as Filter,
  CheckCircle2Icon as CheckCircle,
  AlertCircleIcon as AlertCircle,
  ClockIcon as Clock,
  TerminalIcon as Terminal,
  ServerIcon as Server,
  ArrowRightIcon as ArrowRight,
} from '../components/common/Icons'

type AuditSubTab =
  | 'dashboard'
  | 'logs'
  | 'activity'
  | 'system'
  | 'security'
  | 'login'
  | 'changes'

const TABS: { id: AuditSubTab; label: string; count?: number }[] = [
  { id: 'dashboard', label: 'Audit Dashboard' },
  { id: 'logs', label: 'Audit Logs' },
  { id: 'activity', label: 'User Activity' },
  { id: 'system', label: 'System Events' },
  { id: 'security', label: 'Security Events' },
  { id: 'login', label: 'Login History' },
  { id: 'changes', label: 'Data Change History' },
]

export default function AuditCenter() {
  const [activeTab, setActiveTab] = useState<AuditSubTab>('dashboard')
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  // Filters State for Audit Logs
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All')
  const [severity, setSeverity] = useState('All')
  const [result, setResult] = useState('All')

  const filterParams: AuditFilters = useMemo(
    () => ({
      search: search || undefined,
      category: category === 'All' ? undefined : category,
      severity: severity === 'All' ? undefined : severity,
      result: result === 'All' ? undefined : result,
    }),
    [search, category, severity, result]
  )

  const {
    events,
    metrics,
    userActivities,
    systemEvents,
    securityEvents,
    loginHistory,
    dataChanges,
    clearAllLogs,
    resetLogs,
  } = useAudit(filterParams)

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3200)
  }

  const handleRowClick = (evt: AuditEvent) => {
    setSelectedEvent(evt)
    setIsDrawerOpen(true)
  }

  const handleExportAuditCsv = () => {
    const columns = [
      { key: 'id', label: 'Event ID' },
      { key: 'timestamp', label: 'Timestamp' },
      { key: 'category', label: 'Category' },
      { key: 'eventType', label: 'Event Type' },
      { key: 'actor', label: 'Actor' },
      { key: 'actorRole', label: 'Role' },
      { key: 'action', label: 'Action' },
      { key: 'resource', label: 'Resource' },
      { key: 'resourceId', label: 'Resource ID' },
      { key: 'result', label: 'Result' },
      { key: 'severity', label: 'Severity' },
      { key: 'description', label: 'Description' },
    ]
    exportToCsv(`dealflow_audit_events_${new Date().toISOString().slice(0, 10)}`, columns, events)
    showToast('Exported audit events to CSV')
  }

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
              padding: '10px 18px',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 13,
              color: '#e4e4e7',
              boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
            }}
          >
            <CheckCircle size={16} color="#10b981" />
            <span>{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 20,
          marginBottom: 24,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <h1 style={{ margin: 0, color: '#ffffff', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>
              Audit & Security Governance
            </h1>
            <span
              style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 4,
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Simulated Audit Trail
            </span>
          </div>
          <p style={{ margin: 0, color: '#71717a', fontSize: 13, maxWidth: 740, lineHeight: 1.5 }}>
            Immutable local record of all dealflow lifecycle transitions, AI evaluations, director approvals, simulated ERP dispatches, and access security attempts.
          </p>
        </div>

        {/* Global Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              resetLogs()
              showToast('Audit records restored to enterprise default dataset')
            }}
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
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={14} />
            Reset Defaults
          </button>

          <button
            onClick={handleExportAuditCsv}
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
              cursor: 'pointer',
            }}
          >
            <Download size={14} />
            Export Audit CSV
          </button>
        </div>
      </header>

      {/* Sub-Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid #27272a',
          marginBottom: 24,
          overflowX: 'auto',
          gap: 16,
        }}
      >
        {TABS.map((t) => {
          const isActive = activeTab === t.id
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                padding: '10px 4px 14px',
                fontSize: 13,
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : '#71717a',
                border: 'none',
                borderBottom: isActive ? '2px solid #6366f1' : '2px solid transparent',
                background: 'transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
            >
              {t.label}
            </button>
          )
        })}
      </div>

      {/* SUB-VIEW 1: AUDIT DASHBOARD */}
      {activeTab === 'dashboard' && (
        <div>
          {/* KPI Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 14,
              marginBottom: 24,
            }}
          >
            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '16px 18px' }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>Total Events</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ffffff', margin: '8px 0 4px' }}>
                {metrics.totalEvents}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Indexed audit entries</div>
            </div>

            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '16px 18px' }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>User Actions</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#6366f1', margin: '8px 0 4px' }}>
                {metrics.userActions}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Direct human interventions</div>
            </div>

            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '16px 18px' }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>System Events</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#38bdf8', margin: '8px 0 4px' }}>
                {metrics.systemEvents}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>AI, Odoo & ledger pipelines</div>
            </div>

            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '16px 18px' }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>Security Events</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#f59e0b', margin: '8px 0 4px' }}>
                {metrics.securityEvents}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Auth & session records</div>
            </div>

            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '16px 18px' }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>Data Changes</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#10b981', margin: '8px 0 4px' }}>
                {metrics.dataChanges}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Before/after attribute diffs</div>
            </div>

            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '16px 18px' }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>High Risk Events</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: metrics.highRiskEvents > 0 ? '#ef4444' : '#ffffff', margin: '8px 0 4px' }}>
                {metrics.highRiskEvents}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Severity high or critical</div>
            </div>
          </div>

          {/* Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 20, marginBottom: 24 }}>
            {/* Event Volume Trend */}
            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '20px 22px' }}>
              <h3 style={{ margin: '0 0 4px', fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                Weekly Event Ingestion Trend
              </h3>
              <div style={{ fontSize: 11, color: '#71717a', marginBottom: 16 }}>
                Daily count of audit entries recorded in browser store
              </div>
              <div style={{ height: 210 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics.eventTrends}>
                    <CartesianGrid stroke="#1f1f23" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="day" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: '#121215', border: '1px solid #27272a', borderRadius: 6, color: '#fff', fontSize: 12 }}
                    />
                    <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Category Breakdown */}
            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '20px 22px' }}>
              <h3 style={{ margin: '0 0 4px', fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                Event Category Distribution
              </h3>
              <div style={{ fontSize: 11, color: '#71717a', marginBottom: 16 }}>
                Events segmented by functional platform domain
              </div>
              <div style={{ height: 210 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics.categoryDistribution}>
                    <CartesianGrid stroke="#1f1f23" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="category" tick={{ fill: '#71717a', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: '#121215', border: '1px solid #27272a', borderRadius: 6, color: '#fff', fontSize: 12 }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {metrics.categoryDistribution.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recent Critical Events Table */}
          <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '20px 22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#ffffff' }}>
                  Recent Critical & High Severity Events
                </h3>
                <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>
                  Actions and anomalies requiring supervisory attention
                </div>
              </div>
              <button
                onClick={() => setActiveTab('logs')}
                style={{ background: 'transparent', border: 'none', color: '#818cf8', fontSize: 12, cursor: 'pointer' }}
              >
                View full logs →
              </button>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #27272a', textAlign: 'left', color: '#71717a' }}>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Event ID</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Action</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Actor</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Resource</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Severity</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.recentCritical.map((evt) => (
                    <tr
                      key={evt.id}
                      onClick={() => handleRowClick(evt)}
                      style={{ borderBottom: '1px solid #18181b', cursor: 'pointer' }}
                    >
                      <td style={{ padding: '12px 12px' }}>
                        <span className="mono" style={{ color: '#818cf8' }}>{evt.id}</span>
                      </td>
                      <td style={{ padding: '12px 12px', color: '#ffffff', fontWeight: 500 }}>{evt.action}</td>
                      <td style={{ padding: '12px 12px', color: '#d4d4d8' }}>{evt.actor}</td>
                      <td style={{ padding: '12px 12px' }}>
                        <span className="mono" style={{ color: '#a1a1aa' }}>{evt.resourceId || evt.resource}</span>
                      </td>
                      <td style={{ padding: '12px 12px' }}>
                        <AuditSeverityBadge severity={evt.severity} />
                      </td>
                      <td style={{ padding: '12px 12px', color: '#71717a' }}>
                        {new Date(evt.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SUB-VIEW 2: AUDIT LOGS */}
      {activeTab === 'logs' && (
        <div>
          {/* Filters Bar */}
          <div
            style={{
              background: '#09090b',
              border: '1px solid #1c1c24',
              borderRadius: 8,
              padding: '14px 18px',
              marginBottom: 20,
              display: 'flex',
              gap: 12,
              flexWrap: 'wrap',
              alignItems: 'center',
            }}
          >
            {/* Search */}
            <div style={{ flex: 1, minWidth: 220 }}>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by ID, action, actor, resource..."
                style={{
                  width: '100%',
                  background: '#121215',
                  border: '1px solid #27272a',
                  borderRadius: 6,
                  padding: '7px 12px',
                  fontSize: 12,
                  color: '#ffffff',
                }}
              />
            </div>

            {/* Category Filter */}
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: 6,
                padding: '7px 12px',
                fontSize: 12,
                color: '#e4e4e7',
                cursor: 'pointer',
              }}
            >
              <option value="All">All Categories</option>
              <option value="REQUEST">Request</option>
              <option value="APPROVAL">Approval</option>
              <option value="AI">AI</option>
              <option value="EXECUTION">Execution</option>
              <option value="TRANSACTION">Transaction</option>
              <option value="SECURITY">Security</option>
              <option value="SETTINGS">Settings</option>
            </select>

            {/* Severity Filter */}
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: 6,
                padding: '7px 12px',
                fontSize: 12,
                color: '#e4e4e7',
                cursor: 'pointer',
              }}
            >
              <option value="All">All Severities</option>
              <option value="INFO">Info</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>

            {/* Result Filter */}
            <select
              value={result}
              onChange={(e) => setResult(e.target.value)}
              style={{
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: 6,
                padding: '7px 12px',
                fontSize: 12,
                color: '#e4e4e7',
                cursor: 'pointer',
              }}
            >
              <option value="All">All Results</option>
              <option value="SUCCESS">Success</option>
              <option value="FAILURE">Failure</option>
              <option value="WARNING">Warning</option>
            </select>

            {(search || category !== 'All' || severity !== 'All' || result !== 'All') && (
              <button
                onClick={() => {
                  setSearch('')
                  setCategory('All')
                  setSeverity('All')
                  setResult('All')
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#818cf8',
                  fontSize: 11,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Reset
              </button>
            )}
          </div>

          {/* Audit Logs Table */}
          <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #27272a', background: '#0d0d10', textAlign: 'left', color: '#71717a' }}>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Event ID</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Timestamp</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Category</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Action</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Actor</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Resource</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Severity</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {events.length === 0 ? (
                    <tr>
                      <td colSpan={8} style={{ padding: 40, textAlign: 'center', color: '#52525b' }}>
                        No audit events match current criteria.
                      </td>
                    </tr>
                  ) : (
                    events.map((evt) => (
                      <tr
                        key={evt.id}
                        onClick={() => handleRowClick(evt)}
                        style={{ borderBottom: '1px solid #18181b', cursor: 'pointer', transition: 'background 0.12s ease' }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#121215')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      >
                        <td style={{ padding: '12px 14px' }}>
                          <span className="mono" style={{ color: '#818cf8', fontWeight: 600 }}>{evt.id}</span>
                        </td>
                        <td style={{ padding: '12px 14px', color: '#a1a1aa' }}>
                          {new Date(evt.timestamp).toLocaleString()}
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <span
                            style={{
                              fontSize: 10,
                              fontWeight: 700,
                              padding: '2px 6px',
                              borderRadius: 4,
                              background: '#18181b',
                              color: '#d4d4d8',
                              border: '1px solid #27272a',
                            }}
                          >
                            {evt.category}
                          </span>
                        </td>
                        <td style={{ padding: '12px 14px', color: '#ffffff', fontWeight: 500 }}>
                          {evt.action}
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ color: '#e4e4e7' }}>{evt.actor}</div>
                          <div style={{ fontSize: 10, color: '#71717a' }}>{evt.actorRole}</div>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <span className="mono" style={{ color: '#a1a1aa' }}>
                            {evt.resourceId || evt.resource}
                          </span>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <AuditSeverityBadge severity={evt.severity} />
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <AuditSeverityBadge result={evt.result} />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SUB-VIEW 3: USER ACTIVITY */}
      {activeTab === 'activity' && (
        <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '18px 20px', borderBottom: '1px solid #1c1c24' }}>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#ffffff' }}>
              Human Actor Activity Records
            </h3>
            <div style={{ fontSize: 12, color: '#71717a', marginTop: 2 }}>
              Dedicated audit trail of human decisions, request submissions, and administrative updates
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #27272a', background: '#0d0d10', textAlign: 'left', color: '#71717a' }}>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>User</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Role</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Action Performed</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Resource Target</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Timestamp</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Result</th>
                </tr>
              </thead>
              <tbody>
                {userActivities.map((act) => (
                  <tr key={act.id} style={{ borderBottom: '1px solid #18181b' }}>
                    <td style={{ padding: '12px 14px', color: '#ffffff', fontWeight: 600 }}>
                      {act.user}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#a1a1aa' }}>{act.role}</td>
                    <td style={{ padding: '12px 14px', color: '#e4e4e7' }}>{act.action}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ color: '#818cf8' }}>{act.resourceId || act.resource}</span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#71717a' }}>
                      {new Date(act.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <AuditSeverityBadge result={act.result} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-VIEW 4: SYSTEM EVENTS */}
      {activeTab === 'system' && (
        <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '18px 20px', borderBottom: '1px solid #1c1c24' }}>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#ffffff' }}>
              Automated System & Pipeline Event Stream
            </h3>
            <div style={{ fontSize: 12, color: '#71717a', marginTop: 2 }}>
              Simulated background tasks, ERP dispatches, AI assessments, and ledger records
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #27272a', background: '#0d0d10', textAlign: 'left', color: '#71717a' }}>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Event ID</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Module</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>System Event</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Reference</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Duration</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {systemEvents.map((sys) => (
                  <tr key={sys.id} style={{ borderBottom: '1px solid #18181b' }}>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ color: '#818cf8' }}>{sys.id}</span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#ffffff', fontWeight: 500 }}>{sys.module}</td>
                    <td style={{ padding: '12px 14px', color: '#e4e4e7' }}>{sys.event}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ color: '#a1a1aa' }}>{sys.reference}</span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: 4,
                          color: sys.status === 'SUCCESS' ? '#10b981' : sys.status === 'FAILED' ? '#ef4444' : '#38bdf8',
                          background: sys.status === 'SUCCESS' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                          border: `1px solid ${sys.status === 'SUCCESS' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                        }}
                      >
                        {sys.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#71717a' }}>{sys.duration || '60ms'}</td>
                    <td style={{ padding: '12px 14px', color: '#a1a1aa' }}>{sys.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-VIEW 5: SECURITY EVENTS */}
      {activeTab === 'security' && (
        <div>
          {/* Security Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 20 }}>
            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: 16 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>Successful Logins</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#10b981', margin: '6px 0 2px' }}>
                {metrics.loginEvents}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Verified director sessions</div>
            </div>

            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: 16 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>Failed Attempts</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ef4444', margin: '6px 0 2px' }}>
                {metrics.failedLogins}
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Blocked by mock boundary</div>
            </div>

            <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: 16 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>Active Sessions</span>
              <div className="mono" style={{ fontSize: 24, fontWeight: 700, color: '#ffffff', margin: '6px 0 2px' }}>
                1 Active
              </div>
              <div style={{ fontSize: 11, color: '#52525b' }}>Arjun Sharma (Current)</div>
            </div>
          </div>

          <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #27272a', background: '#0d0d10', textAlign: 'left', color: '#71717a' }}>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Event ID</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Security Event</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>User / Principal</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Timestamp</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Result</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Severity</th>
                    <th style={{ padding: '12px 14px', fontWeight: 600 }}>Device / IP</th>
                  </tr>
                </thead>
                <tbody>
                  {securityEvents.map((sec) => (
                    <tr key={sec.id} style={{ borderBottom: '1px solid #18181b' }}>
                      <td style={{ padding: '12px 14px' }}>
                        <span className="mono" style={{ color: '#818cf8' }}>{sec.id}</span>
                      </td>
                      <td style={{ padding: '12px 14px', color: '#ffffff', fontWeight: 500 }}>{sec.event}</td>
                      <td style={{ padding: '12px 14px', color: '#e4e4e7' }}>{sec.user}</td>
                      <td style={{ padding: '12px 14px', color: '#71717a' }}>
                        {new Date(sec.timestamp).toLocaleString()}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <AuditSeverityBadge result={sec.result as any} />
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <AuditSeverityBadge severity={sec.severity} />
                      </td>
                      <td style={{ padding: '12px 14px', color: '#a1a1aa' }}>
                        {sec.device || sec.ipAddress}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SUB-VIEW 6: LOGIN HISTORY */}
      {activeTab === 'login' && (
        <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '18px 20px', borderBottom: '1px solid #1c1c24' }}>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#ffffff' }}>
              Historical User Login & Session Registry
            </h3>
            <div style={{ fontSize: 12, color: '#71717a', marginTop: 2 }}>
              Simulated browser signatures and session durations across workspace users
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #27272a', background: '#0d0d10', textAlign: 'left', color: '#71717a' }}>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>User</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Role</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Login Timestamp</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Session Duration</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Result</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Device / Browser</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Session ID</th>
                </tr>
              </thead>
              <tbody>
                {loginHistory.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid #18181b' }}>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ color: '#ffffff', fontWeight: 600 }}>{log.user}</div>
                      <div style={{ fontSize: 10, color: '#71717a' }}>{log.email}</div>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#a1a1aa' }}>{log.role}</td>
                    <td style={{ padding: '12px 14px', color: '#e4e4e7' }}>
                      {new Date(log.loginTime).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#10b981', fontWeight: 500 }}>
                      {log.sessionDuration}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <AuditSeverityBadge result={log.loginResult as any} />
                    </td>
                    <td style={{ padding: '12px 14px', color: '#a1a1aa' }}>
                      {log.browser}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ color: '#71717a', fontSize: 11 }}>{log.sessionId}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-VIEW 7: DATA CHANGE HISTORY */}
      {activeTab === 'changes' && (
        <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '18px 20px', borderBottom: '1px solid #1c1c24' }}>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#ffffff' }}>
              Data Attribute Mutation History
            </h3>
            <div style={{ fontSize: 12, color: '#71717a', marginTop: 2 }}>
              Before vs After field transitions across requests, approvals, and system settings
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #27272a', background: '#0d0d10', textAlign: 'left', color: '#71717a' }}>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Change ID</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Resource</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Field</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Previous Value</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>New Value</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Actor</th>
                  <th style={{ padding: '12px 14px', fontWeight: 600 }}>Reason / Note</th>
                </tr>
              </thead>
              <tbody>
                {dataChanges.map((chg) => (
                  <tr key={chg.id} style={{ borderBottom: '1px solid #18181b' }}>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ color: '#818cf8' }}>{chg.id}</span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ color: '#ffffff', fontWeight: 600 }}>{chg.resourceId}</span>
                      <div style={{ fontSize: 10, color: '#71717a' }}>{chg.resource}</div>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#e4e4e7', fontWeight: 500 }}>
                      {chg.field}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ color: '#ef4444', background: 'rgba(239,68,68,0.1)', padding: '2px 6px', borderRadius: 4 }}>
                        {chg.previousValue}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ color: '#10b981', background: 'rgba(16,185,129,0.1)', padding: '2px 6px', borderRadius: 4 }}>
                        {chg.newValue}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#a1a1aa' }}>
                      <div>{chg.actor}</div>
                      <div style={{ fontSize: 10, color: '#71717a' }}>{chg.actorRole}</div>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#71717a' }}>
                      {chg.changeReason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Slide-over Audit Detail Drawer */}
      <AuditDetailDrawer
        event={selectedEvent}
        isOpen={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false)
          setSelectedEvent(null)
        }}
      />
    </div>
  )
}
