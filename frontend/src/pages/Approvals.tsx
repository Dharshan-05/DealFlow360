import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { StaggerContainer, StaggerItem, AnimatedDrawer } from '../lib/motion'
import { useApprovals } from '../hooks/useApprovals'
import { useAuth } from '../hooks/useAuth'
import { StatusBadge, EmptyState } from '../components/common'
import type { Approval, ApprovalStatus } from '../types/approval'
import ApproveModal from '../components/approvals/ApproveModal'
import RejectModal from '../components/approvals/RejectModal'
import RequestChangesModal from '../components/approvals/RequestChangesModal'

const riskColor = (r: string) => (r === 'Critical' ? '#EF4444' : r === 'High' ? '#F97316' : r === 'Medium' ? '#F59E0B' : '#10B981')
const riskBg = (r: string) =>
  r === 'Critical'
    ? 'rgba(239,68,68,0.08)'
    : r === 'High'
    ? 'rgba(249,115,22,0.08)'
    : r === 'Medium'
    ? 'rgba(245,158,11,0.08)'
    : 'rgba(16,185,129,0.08)'
const riskBorder = (r: string) =>
  r === 'Critical'
    ? 'rgba(239,68,68,0.2)'
    : r === 'High'
    ? 'rgba(249,115,22,0.2)'
    : r === 'Medium'
    ? 'rgba(245,158,11,0.2)'
    : 'rgba(16,185,129,0.2)'

export default function Approvals() {
  const {
    approvals,
    pendingApprovals,
    historyApprovals,
    metrics,
    approve,
    reject,
    requestChanges,
  } = useApprovals()

  const { user, hasPermission } = useAuth()
  const canApprove = hasPermission('approval:action') || hasPermission('approval:review')

  const [selected, setSelected] = useState<Approval | null>(null)
  const [activeTab, setActiveTab] = useState<'pending' | 'history' | 'all'>('pending')
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('All')
  const [priorityFilter, setPriorityFilter] = useState('All')
  const [typeFilter, setTypeFilter] = useState('All')
  const [aiTab, setAiTab] = useState<'commercial' | 'customer' | 'risk' | 'policy'>('commercial')

  // Modals state
  const [approveModalOpen, setApproveModalOpen] = useState(false)
  const [rejectModalOpen, setRejectModalOpen] = useState(false)
  const [changesModalOpen, setChangesModalOpen] = useState(false)
  const [actionApproval, setActionApproval] = useState<Approval | null>(null)

  // In-app toast notice
  const [toastNotice, setToastNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const showToast = (type: 'success' | 'error', message: string) => {
    setToastNotice({ type, message })
    setTimeout(() => {
      setToastNotice(null)
    }, 4500)
  }

  // Filtered dataset
  const baseList = activeTab === 'pending' ? pendingApprovals : activeTab === 'history' ? historyApprovals : approvals

  const filtered = useMemo(() => {
    return baseList.filter((a) => {
      const q = search.trim().toLowerCase()
      const matchesSearch =
        !q ||
        a.requestReference.toLowerCase().includes(q) ||
        a.customer.toLowerCase().includes(q) ||
        (a.title && a.title.toLowerCase().includes(q)) ||
        a.submittedBy.toLowerCase().includes(q)

      const matchesRisk = riskFilter === 'All' || a.riskLevel === riskFilter
      const matchesPriority = priorityFilter === 'All' || a.priority === priorityFilter
      const matchesType = typeFilter === 'All' || a.requestType === typeFilter

      return matchesSearch && matchesRisk && matchesPriority && matchesType
    })
  }, [baseList, search, riskFilter, priorityFilter, typeFilter])

  // Handlers for decision modals
  const handleOpenApprove = (approval: Approval) => {
    setActionApproval(approval)
    setApproveModalOpen(true)
  }

  const handleOpenReject = (approval: Approval) => {
    setActionApproval(approval)
    setRejectModalOpen(true)
  }

  const handleOpenChanges = (approval: Approval) => {
    setActionApproval(approval)
    setChangesModalOpen(true)
  }

  const handleConfirmApprove = async (comment: string) => {
    if (!actionApproval) return
    try {
      const updated = await approve(actionApproval.id, user?.name || 'Arjun Sharma', comment)
      if (selected?.id === actionApproval.id) {
        setSelected(updated || null)
      }
      showToast('success', `Request ${actionApproval.requestReference} approved successfully. It is now ready for execution.`)
    } catch (err: any) {
      showToast('error', err?.message || 'Unable to update approval. Please try again.')
    }
  }

  const handleConfirmReject = async (reason: string, comment?: string) => {
    if (!actionApproval) return
    try {
      const updated = await reject(actionApproval.id, user?.name || 'Arjun Sharma', reason, comment)
      if (selected?.id === actionApproval.id) {
        setSelected(updated || null)
      }
      showToast('success', `Request ${actionApproval.requestReference} rejected.`)
    } catch (err: any) {
      showToast('error', err?.message || 'Unable to reject request.')
    }
  }

  const handleConfirmChanges = async (reason: string, details?: string) => {
    if (!actionApproval) return
    try {
      const updated = await requestChanges(actionApproval.id, user?.name || 'Arjun Sharma', reason, details)
      if (selected?.id === actionApproval.id) {
        setSelected(updated || null)
      }
      showToast('success', `Changes requested from ${actionApproval.submittedBy}.`)
    } catch (err: any) {
      showToast('error', err?.message || 'Unable to request changes.')
    }
  }

  return (
    <div style={{ padding: '24px 28px', maxWidth: 1440, margin: '0 auto' }}>
      {/* Toast Notification */}
      <AnimatePresence>
        {toastNotice && (
          <motion.div
            initial={{ opacity: 0, y: -12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -12, scale: 0.98 }}
            style={{
              position: 'fixed',
              top: 20,
              right: 24,
              zIndex: 10000,
              padding: '12px 18px',
              borderRadius: 8,
              background: toastNotice.type === 'success' ? '#0d2d1a' : '#2d0d0d',
              border: `1px solid ${toastNotice.type === 'success' ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
              color: toastNotice.type === 'success' ? '#34D399' : '#F87171',
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.6)',
              fontSize: 13,
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span>{toastNotice.type === 'success' ? '✓' : '⚠'}</span>
            <span>{toastNotice.message}</span>
            <button
              onClick={() => setToastNotice(null)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 2, marginLeft: 8 }}
            >
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header & Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: '#fff', letterSpacing: '-0.025em', margin: 0 }}>
              Approval Management
            </h1>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                padding: '2px 8px',
                borderRadius: 4,
                background: 'rgba(124, 58, 237, 0.15)',
                color: '#A78BFA',
                border: '1px solid rgba(124, 58, 237, 0.3)',
              }}
            >
              Phase 6 Workflow
            </span>
          </div>
          <p style={{ fontSize: 13, color: '#71717A', margin: 0 }}>
            Human-in-the-loop authorization desk. Evaluate commercial exceptions, review AI risk insights, and grant execution clearance.
          </p>
        </div>

        {/* Tab Controls */}
        <div style={{ display: 'flex', gap: 8 }}>
          {[
            { key: 'pending', label: 'Pending Review', count: metrics.pending },
            { key: 'history', label: 'Approval History', count: metrics.approved + metrics.rejected + metrics.changesRequested },
            { key: 'all', label: 'All Records', count: metrics.total },
          ].map((tab) => (
            <motion.button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              style={{
                padding: '7px 16px',
                borderRadius: 7,
                fontSize: 13,
                fontWeight: 500,
                background: activeTab === tab.key ? '#fff' : '#0a0a0a',
                color: activeTab === tab.key ? '#000' : '#71717A',
                border: activeTab === tab.key ? 'none' : '1px solid #1e1e1e',
                cursor: 'pointer',
                fontFamily: 'Inter, sans-serif',
                display: 'flex',
                alignItems: 'center',
                gap: 7,
              }}
              whileHover={{ borderColor: '#333', color: activeTab === tab.key ? '#000' : '#fff' }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.12 }}
            >
              {tab.label}
              {tab.count > 0 && (
                <span
                  style={{
                    background: tab.key === 'pending' ? '#7C3AED' : '#222',
                    color: '#fff',
                    fontSize: 10,
                    fontWeight: 700,
                    borderRadius: 4,
                    padding: '1px 5px',
                  }}
                >
                  {tab.count}
                </span>
              )}
            </motion.button>
          ))}
        </div>
      </div>

      {/* RBAC Notice if user lacks action permission */}
      {!canApprove && (
        <div
          style={{
            padding: '10px 14px',
            borderRadius: 7,
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            color: '#FBBF24',
            fontSize: 12.5,
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span>ℹ</span>
          <span>
            You are signed in as <strong>{user?.role || 'Guest'}</strong> with read-only access to approvals. Approval authority (`approval:action`) is required to sign off on deals.
          </span>
        </div>
      )}

      {/* KPI Metrics Summary Bar (Step 2) */}
      <StaggerContainer>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(6, 1fr)',
            gap: 12,
            marginBottom: 20,
          }}
        >
          <StaggerItem>
            <div className="df-card" style={{ padding: '14px 16px', background: '#080808', border: '1px solid #18181c' }}>
              <div style={{ fontSize: 11, color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>Total Approvals</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#fff', marginTop: 4 }} className="mono">{metrics.total}</div>
              <div style={{ fontSize: 11, color: '#555', marginTop: 2 }}>All recorded requests</div>
            </div>
          </StaggerItem>

          <StaggerItem>
            <div className="df-card" style={{ padding: '14px 16px', background: '#080808', border: '1px solid #18181c' }}>
              <div style={{ fontSize: 11, color: '#A78BFA', textTransform: 'uppercase', fontWeight: 600 }}>Pending Action</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#A78BFA', marginTop: 4 }} className="mono">{metrics.pending}</div>
              <div style={{ fontSize: 11, color: '#71717A', marginTop: 2 }}>Awaiting sign-off</div>
            </div>
          </StaggerItem>

          <StaggerItem>
            <div className="df-card" style={{ padding: '14px 16px', background: '#080808', border: '1px solid #18181c' }}>
              <div style={{ fontSize: 11, color: '#34D399', textTransform: 'uppercase', fontWeight: 600 }}>Approved</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#10B981', marginTop: 4 }} className="mono">{metrics.approved}</div>
              <div style={{ fontSize: 11, color: '#555', marginTop: 2 }}>Ready for Execution</div>
            </div>
          </StaggerItem>

          <StaggerItem>
            <div className="df-card" style={{ padding: '14px 16px', background: '#080808', border: '1px solid #18181c' }}>
              <div style={{ fontSize: 11, color: '#F87171', textTransform: 'uppercase', fontWeight: 600 }}>Rejected</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#EF4444', marginTop: 4 }} className="mono">{metrics.rejected}</div>
              <div style={{ fontSize: 11, color: '#555', marginTop: 2 }}>Exceptions denied</div>
            </div>
          </StaggerItem>

          <StaggerItem>
            <div className="df-card" style={{ padding: '14px 16px', background: '#080808', border: '1px solid #18181c' }}>
              <div style={{ fontSize: 11, color: '#FBBF24', textTransform: 'uppercase', fontWeight: 600 }}>Changes Req.</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#F59E0B', marginTop: 4 }} className="mono">{metrics.changesRequested}</div>
              <div style={{ fontSize: 11, color: '#555', marginTop: 2 }}>Sent to requester</div>
            </div>
          </StaggerItem>

          <StaggerItem>
            <div className="df-card" style={{ padding: '14px 16px', background: '#080808', border: '1px solid #18181c' }}>
              <div style={{ fontSize: 11, color: '#FB923C', textTransform: 'uppercase', fontWeight: 600 }}>High / Critical</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#F97316', marginTop: 4 }} className="mono">{metrics.highRisk}</div>
              <div style={{ fontSize: 11, color: '#555', marginTop: 2 }}>Elevated deal risk</div>
            </div>
          </StaggerItem>
        </div>
      </StaggerContainer>

      {/* Filter Bar (Step 4) */}
      <div
        style={{
          background: '#0a0a0c',
          border: '1px solid #1c1c24',
          borderRadius: 8,
          padding: '12px 16px',
          marginBottom: 16,
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 12,
        }}
      >
        {/* Search */}
        <div style={{ flex: 1, minWidth: 220 }}>
          <input
            type="text"
            className="df-input"
            placeholder="Search request ID, customer, deal..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', height: 34, fontSize: 12.5 }}
          />
        </div>

        {/* Priority Filter */}
        <select
          className="df-input"
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          style={{ height: 34, fontSize: 12, background: '#111116', color: '#fff', padding: '0 8px' }}
        >
          <option value="All">All Priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        {/* Risk Filter */}
        <select
          className="df-input"
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          style={{ height: 34, fontSize: 12, background: '#111116', color: '#fff', padding: '0 8px' }}
        >
          <option value="All">All Risk Levels</option>
          <option value="Low">Low Risk</option>
          <option value="Medium">Medium Risk</option>
          <option value="High">High Risk</option>
          <option value="Critical">Critical Risk</option>
        </select>

        {/* Type Filter */}
        <select
          className="df-input"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={{ height: 34, fontSize: 12, background: '#111116', color: '#fff', padding: '0 8px' }}
        >
          <option value="All">All Request Types</option>
          <option value="Commercial Exception">Commercial Exception</option>
          <option value="Hardware Bundle">Hardware Bundle</option>
          <option value="Software License">Software License</option>
          <option value="Custom SLA">Custom SLA</option>
          <option value="Enterprise Expansion">Enterprise Expansion</option>
        </select>

        {(search || riskFilter !== 'All' || priorityFilter !== 'All' || typeFilter !== 'All') && (
          <button
            onClick={() => {
              setSearch('')
              setRiskFilter('All')
              setPriorityFilter('All')
              setTypeFilter('All')
            }}
            style={{
              background: 'none',
              border: 'none',
              color: '#A78BFA',
              cursor: 'pointer',
              fontSize: 12,
              padding: '4px 8px',
            }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Main Grid: Queue Table + Slide-over / Side Detail Drawer */}
      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 440px' : '1fr', gap: 16 }}>
        {/* Table Card */}
        <div className="df-card" style={{ overflow: 'hidden', background: '#080808', border: '1px solid #1a1a1a' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #141414' }}>
                  {['Request ID / Title', 'Customer', 'Value', 'Priority', 'Discount Req.', 'AI Risk', 'AI Confidence', 'Status', 'SLA / Approver', 'Action'].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: '12px 14px',
                        fontSize: 10.5,
                        color: '#666',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((a, i) => (
                  <motion.tr
                    key={a.id}
                    style={{
                      borderBottom: i < filtered.length - 1 ? '1px solid #0f0f0f' : 'none',
                      cursor: 'pointer',
                      background: selected?.id === a.id ? 'rgba(124, 58, 237, 0.05)' : undefined,
                    }}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03, duration: 0.16 }}
                    whileHover={{ background: 'rgba(255,255,255,0.02)' }}
                    onClick={() => setSelected(selected?.id === a.id ? null : a)}
                  >
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span className="mono" style={{ fontSize: 12.5, fontWeight: 700, color: '#fff' }}>
                          {a.requestReference}
                        </span>
                      </div>
                      <div
                        style={{
                          fontSize: 11.5,
                          color: '#71717A',
                          marginTop: 2,
                          maxWidth: 180,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {a.title || a.description || 'Commercial Request'}
                      </div>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontSize: 12.5, color: '#E4E4E7', fontWeight: 500 }}>{a.customer}</div>
                      <div style={{ fontSize: 11, color: '#555' }}>By {a.submittedBy}</div>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: '#fff' }}>
                        {a.amount}
                      </span>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <span
                        style={{
                          fontSize: 10.5,
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: 4,
                          textTransform: 'uppercase',
                          background:
                            a.priority === 'Critical'
                              ? 'rgba(239, 68, 68, 0.1)'
                              : a.priority === 'High'
                              ? 'rgba(249, 115, 22, 0.1)'
                              : a.priority === 'Medium'
                              ? 'rgba(245, 158, 11, 0.1)'
                              : 'rgba(16, 185, 129, 0.1)',
                          color:
                            a.priority === 'Critical'
                              ? '#EF4444'
                              : a.priority === 'High'
                              ? '#F97316'
                              : a.priority === 'Medium'
                              ? '#F59E0B'
                              : '#10B981',
                        }}
                      >
                        {a.priority}
                      </span>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span className="mono" style={{ fontSize: 13, fontWeight: 800, color: '#EF4444' }}>
                          {a.requestedValue}
                        </span>
                        <span style={{ fontSize: 11, color: '#555' }}>vs {a.policyLimit} limit</span>
                      </div>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 600,
                          color: riskColor(a.riskLevel),
                          background: riskBg(a.riskLevel),
                          border: `1px solid ${riskBorder(a.riskLevel)}`,
                          borderRadius: 4,
                          padding: '2px 8px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                        }}
                      >
                        {a.riskLevel} {a.riskScore ? `(${a.riskScore})` : ''}
                      </span>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <span className="mono" style={{ fontSize: 12, color: '#A78BFA', fontWeight: 600 }}>
                        {a.aiConfidenceScore || 92}%
                      </span>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <StatusBadge status={a.status as any} size="sm" showDot />
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontSize: 11.5, color: '#D4D4D8' }}>
                        {a.assignedApprover?.name || 'Commercial Desk'}
                      </div>
                      <div style={{ fontSize: 10.5, color: a.slaStatus === 'urgent' ? '#EF4444' : a.slaStatus === 'warning' ? '#F59E0B' : '#71717A' }}>
                        {a.slaDeadline || 'Standard SLA'}
                      </div>
                    </td>

                    <td style={{ padding: '12px 14px' }}>
                      {a.status === 'Pending' ? (
                        <div style={{ display: 'flex', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            disabled={!canApprove}
                            onClick={() => handleOpenApprove(a)}
                            style={{
                              padding: '5px 10px',
                              background: '#0d2d1a',
                              border: '1px solid rgba(16,185,129,0.3)',
                              color: '#10B981',
                              borderRadius: 5,
                              fontSize: 11.5,
                              cursor: canApprove ? 'pointer' : 'not-allowed',
                              fontWeight: 600,
                              opacity: canApprove ? 1 : 0.5,
                            }}
                          >
                            Approve
                          </button>

                          <button
                            type="button"
                            disabled={!canApprove}
                            onClick={() => handleOpenChanges(a)}
                            style={{
                              padding: '5px 8px',
                              background: 'transparent',
                              border: '1px solid #27272a',
                              color: '#F59E0B',
                              borderRadius: 5,
                              fontSize: 11.5,
                              cursor: canApprove ? 'pointer' : 'not-allowed',
                              opacity: canApprove ? 1 : 0.5,
                            }}
                            title="Request changes from requester"
                          >
                            Revise
                          </button>
                        </div>
                      ) : (
                        <span style={{ fontSize: 12, color: '#71717A', fontStyle: 'italic' }}>
                          Decided
                        </span>
                      )}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          {filtered.length === 0 && (
            <div style={{ padding: '48px 16px' }}>
              <EmptyState
                title={`No ${activeTab === 'pending' ? 'pending' : activeTab === 'history' ? 'historical' : ''} approvals found`}
                description="There are currently no transaction requests matching the selected filter criteria."
              />
            </div>
          )}
        </div>

        {/* Detail Drawer (Step 6 & 7) */}
        <AnimatedDrawer open={!!selected} width={440} style={{ position: 'relative' }}>
          {selected && (
            <div className="df-card" style={{ overflow: 'hidden', height: '100%', background: '#09090c', border: '1px solid #1a1a22' }}>
              {/* Drawer Top Header */}
              <div
                style={{
                  padding: '16px 20px',
                  borderBottom: '1px solid #1a1a22',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: '#fff' }}>
                      {selected.requestReference}
                    </span>
                    <StatusBadge status={selected.status as any} size="sm" showDot />
                  </div>
                  <div style={{ fontSize: 11.5, color: '#71717A', marginTop: 2 }}>
                    Assigned: {selected.assignedApprover?.level || 'Level 2 Authorization'}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  style={{ background: 'none', border: 'none', color: '#71717A', cursor: 'pointer', padding: 4 }}
                >
                  ✕
                </button>
              </div>

              {/* Scrollable Drawer Body */}
              <div style={{ padding: '18px 20px', overflowY: 'auto', maxHeight: 'calc(100vh - 180px)', display: 'flex', flexDirection: 'column', gap: 18 }}>
                {/* Deal Header */}
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', marginBottom: 2 }}>
                    {selected.title || selected.customer}
                  </div>
                  <div style={{ fontSize: 12.5, color: '#94A3B8' }}>
                    Customer: <span style={{ color: '#fff', fontWeight: 600 }}>{selected.customer}</span> · Value:{' '}
                    <span style={{ color: '#fff', fontWeight: 700 }} className="mono">{selected.amount}</span>
                  </div>
                </div>

                {/* Commercial Metrics Box */}
                <div
                  style={{
                    background: '#111116',
                    borderRadius: 8,
                    border: '1px solid #1e1e26',
                    padding: '12px 14px',
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr',
                    gap: 10,
                    textAlign: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontSize: 10, color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>
                      Requested
                    </div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: '#EF4444', marginTop: 2 }} className="mono">
                      {selected.requestedValue}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>
                      Policy Limit
                    </div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: '#A1A1AA', marginTop: 2 }} className="mono">
                      {selected.policyLimit}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: '#71717A', textTransform: 'uppercase', fontWeight: 600 }}>
                      AI Rec.
                    </div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: '#7C3AED', marginTop: 2 }} className="mono">
                      {selected.aiRecommended}
                    </div>
                  </div>
                </div>

                {/* Business Scope & Justification */}
                <div
                  style={{
                    padding: '12px 14px',
                    borderRadius: 8,
                    background: '#0d0d10',
                    border: '1px solid #1a1a22',
                  }}
                >
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#71717A', textTransform: 'uppercase', marginBottom: 4 }}>
                    Business Scope & Justification
                  </div>
                  <p style={{ margin: '0 0 6px 0', fontSize: 12.5, color: '#D4D4D8', lineHeight: 1.5 }}>
                    {selected.description || 'Standard transaction request.'}
                  </p>
                  {selected.businessJustification && (
                    <div style={{ fontSize: 12, color: '#94A3B8', borderTop: '1px solid #1a1a22', paddingTop: 6, marginTop: 6 }}>
                      <strong style={{ color: '#E4E4E7' }}>Justification: </strong>
                      {selected.businessJustification}
                    </div>
                  )}
                </div>

                {/* AI Intelligence Context (Step 7) */}
                <div
                  style={{
                    borderRadius: 8,
                    background: 'linear-gradient(145deg, rgba(124, 58, 237, 0.08), #0c0c10)',
                    border: '1px solid rgba(124, 58, 237, 0.25)',
                    padding: '14px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 12 }}>✦</span>
                      <span style={{ fontSize: 11.5, fontWeight: 700, color: '#A78BFA', textTransform: 'uppercase' }}>
                        AI Evaluation & Verdict
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 600,
                          color: riskColor(selected.riskLevel),
                          background: riskBg(selected.riskLevel),
                          padding: '1px 6px',
                          borderRadius: 4,
                        }}
                      >
                        {selected.riskLevel} Risk
                      </span>
                      <span className="mono" style={{ fontSize: 11, color: '#D4D4D8' }}>
                        {selected.aiConfidenceScore || 92}% Conf.
                      </span>
                    </div>
                  </div>

                  <div style={{ fontSize: 12.5, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
                    Recommendation: {selected.aiRecommended === selected.requestedValue ? 'Approve' : 'Approve with Conditions'}
                  </div>

                  <p style={{ margin: '0 0 10px 0', fontSize: 12, color: '#94A3B8', lineHeight: 1.5 }}>
                    {selected.aiSummary || 'AI model verified margins and customer solvency history.'}
                  </p>

                  {/* Explainable Reasoning Tabs */}
                  <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #1e1e28', paddingBottom: 6, marginBottom: 8 }}>
                    {(['commercial', 'customer', 'risk', 'policy'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setAiTab(t)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: aiTab === t ? '#A78BFA' : '#666',
                          fontSize: 11,
                          fontWeight: 600,
                          cursor: 'pointer',
                          textTransform: 'capitalize',
                          padding: '2px 6px',
                        }}
                      >
                        {t}
                      </button>
                    ))}
                  </div>

                  <div style={{ fontSize: 11.5, color: '#A1A1AA', lineHeight: 1.5 }}>
                    {aiTab === 'commercial' && (
                      <span>
                        Requested discount is within viable margin tolerance when accompanied by multi-year terms. Counter-offer of {selected.aiRecommended} preserves optimal IRR.
                      </span>
                    )}
                    {aiTab === 'customer' && (
                      <span>
                        Customer {selected.customer} maintains strong credit integrity with zero historical payment defaults across preceding contract terms.
                      </span>
                    )}
                    {aiTab === 'risk' && (
                      <span>
                        Calculated risk score is {selected.riskScore || 48}/100. Key sensitivity lies in volume commitment fulfillment.
                      </span>
                    )}
                    {aiTab === 'policy' && (
                      <span>
                        Requires Level 2 Commercial Sign-off per corporate delegation of authority matrix due to discount delta over 10%.
                      </span>
                    )}
                  </div>
                </div>

                {/* Timeline Section (Step 13) */}
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#71717A', textTransform: 'uppercase', marginBottom: 10 }}>
                    Approval Audit Trail
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {selected.history.map((h, idx) => (
                      <div key={h.id || idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                        <div
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: h.isCompleted ? '#10B981' : '#333',
                            border: h.isCompleted ? 'none' : '2px solid #555',
                            marginTop: 4,
                            flexShrink: 0,
                          }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 12, fontWeight: 500, color: h.isCompleted ? '#E4E4E7' : '#71717A' }}>
                            {h.event}
                          </div>
                          <div style={{ fontSize: 10.5, color: '#666' }}>
                            {h.actor} · {h.timestamp}
                          </div>
                          {h.comment && (
                            <div style={{ fontSize: 11, color: '#A1A1AA', marginTop: 2, fontStyle: 'italic' }}>
                              "{h.comment}"
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Decision Action Buttons (Step 8 - Human-in-the-loop) */}
                <div style={{ borderTop: '1px solid #1a1a22', paddingTop: 16, marginTop: 'auto' }}>
                  {selected.status === 'Pending' ? (
                    canApprove ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <button
                          type="button"
                          onClick={() => handleOpenApprove(selected)}
                          style={{
                            width: '100%',
                            padding: '10px 16px',
                            borderRadius: 6,
                            background: '#0d2d1a',
                            border: '1px solid rgba(16, 185, 129, 0.4)',
                            color: '#10B981',
                            fontWeight: 600,
                            fontSize: 13,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 6,
                          }}
                        >
                          <span>✓</span> Approve Request &rarr; Ready for Execution
                        </button>

                        <div style={{ display: 'flex', gap: 8 }}>
                          <button
                            type="button"
                            onClick={() => handleOpenChanges(selected)}
                            style={{
                              flex: 1,
                              padding: '8px 12px',
                              borderRadius: 6,
                              background: '#2e1f0c',
                              border: '1px solid rgba(245, 158, 11, 0.3)',
                              color: '#F59E0B',
                              fontWeight: 600,
                              fontSize: 12,
                              cursor: 'pointer',
                            }}
                          >
                            Request Changes
                          </button>

                          <button
                            type="button"
                            onClick={() => handleOpenReject(selected)}
                            style={{
                              flex: 1,
                              padding: '8px 12px',
                              borderRadius: 6,
                              background: '#2d0d0d',
                              border: '1px solid rgba(239, 68, 68, 0.3)',
                              color: '#EF4444',
                              fontWeight: 600,
                              fontSize: 12,
                              cursor: 'pointer',
                            }}
                          >
                            Reject Request
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div
                        style={{
                          padding: '10px 12px',
                          borderRadius: 6,
                          background: '#141418',
                          border: '1px solid #22222a',
                          color: '#71717A',
                          fontSize: 12,
                          textAlign: 'center',
                        }}
                      >
                        Read-only view. Approval authority required to decide.
                      </div>
                    )
                  ) : (
                    <div
                      style={{
                        padding: '12px',
                        borderRadius: 6,
                        background:
                          selected.status === 'Approved'
                            ? 'rgba(16, 185, 129, 0.08)'
                            : selected.status === 'Rejected'
                            ? 'rgba(239, 68, 68, 0.08)'
                            : 'rgba(245, 158, 11, 0.08)',
                        border: `1px solid ${
                          selected.status === 'Approved'
                            ? 'rgba(16, 185, 129, 0.25)'
                            : selected.status === 'Rejected'
                            ? 'rgba(239, 68, 68, 0.25)'
                            : 'rgba(245, 158, 11, 0.25)'
                        }`,
                        textAlign: 'center',
                      }}
                    >
                      <div
                        style={{
                          fontSize: 13,
                          fontWeight: 700,
                          color:
                            selected.status === 'Approved'
                              ? '#10B981'
                              : selected.status === 'Rejected'
                              ? '#EF4444'
                              : '#F59E0B',
                        }}
                      >
                        Status: {selected.status}
                      </div>
                      {selected.decisionComment && (
                        <div style={{ fontSize: 11.5, color: '#A1A1AA', marginTop: 4 }}>
                          "{selected.decisionComment}"
                        </div>
                      )}
                      {selected.status === 'Approved' && (
                        <div style={{ fontSize: 11, color: '#34D399', marginTop: 4, fontWeight: 500 }}>
                          Ready for Phase 7 execution handoff
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </AnimatedDrawer>
      </div>

      {/* Decision Modals */}
      <ApproveModal
        isOpen={approveModalOpen}
        approval={actionApproval}
        onClose={() => {
          setApproveModalOpen(false)
          setActionApproval(null)
        }}
        onConfirm={handleConfirmApprove}
      />

      <RejectModal
        isOpen={rejectModalOpen}
        approval={actionApproval}
        onClose={() => {
          setRejectModalOpen(false)
          setActionApproval(null)
        }}
        onConfirm={handleConfirmReject}
      />

      <RequestChangesModal
        isOpen={changesModalOpen}
        approval={actionApproval}
        onClose={() => {
          setChangesModalOpen(false)
          setActionApproval(null)
        }}
        onConfirm={handleConfirmChanges}
      />
    </div>
  )
}
