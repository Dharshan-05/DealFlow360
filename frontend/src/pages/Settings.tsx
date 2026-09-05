import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSettings } from '../hooks/useSettings'
import { resetAllDemoData } from '../utils/demoReset'
import {
  CheckCircle2Icon as CheckCircle,
  RotateCcwIcon as RotateCcw,
  ShieldCheckIcon as ShieldCheck,
  ServerIcon as Server,
  TerminalIcon as Terminal,
  ExternalLinkIcon as ExternalLink,
} from '../components/common/Icons'

type SettingsTab =
  | 'general'
  | 'workflow'
  | 'ai'
  | 'notifications'
  | 'integrations'
  | 'security'
  | 'system'

const SECTIONS: { id: SettingsTab; label: string; description: string }[] = [
  { id: 'general', label: 'General Settings', description: 'Workspace identity, localized currency, and timezone' },
  { id: 'workflow', label: 'Workflow Governance', description: 'Approval gates, validation rules, and ERP execution simulation' },
  { id: 'ai', label: 'AI Intelligence', description: 'Risk score thresholds, confidence bounds, and analysis modes' },
  { id: 'notifications', label: 'Notification Preferences', description: 'Alert routing, category filters, and retention duration' },
  { id: 'integrations', label: 'Integrations & ERP', description: 'Simulated Odoo connection, copilot engine, and local storage' },
  { id: 'security', label: 'Security & Access', description: 'Session timeouts, authentication policies, and credential changes' },
  { id: 'system', label: 'System Specifications', description: 'Runtime environment, storage engines, and demo transparency' },
]

export default function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')
  const { settings, updateSection, resetSettings, isSaved } = useSettings()

  // Local draft states
  const [generalDraft, setGeneralDraft] = useState(settings.general)
  const [workflowDraft, setWorkflowDraft] = useState(settings.workflow)
  const [aiDraft, setAiDraft] = useState(settings.ai)
  const [notifDraft, setNotifDraft] = useState(settings.notifications)
  const [secDraft, setSecDraft] = useState(settings.security)

  // Password modal simulation
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordNotice, setPasswordNotice] = useState<string | null>(null)
  const [resetFeedback, setResetFeedback] = useState<string | null>(null)

  const handleResetAllDemoData = () => {
    const res = resetAllDemoData()
    if (res.success) {
      setResetFeedback('All demo data restored to initial factory state.')
      setGeneralDraft(settings.general)
      setWorkflowDraft(settings.workflow)
      setAiDraft(settings.ai)
      setNotifDraft(settings.notifications)
      setSecDraft(settings.security)
      setTimeout(() => setResetFeedback(null), 4000)
    }
  }

  const handleSaveGeneral = () => {
    updateSection('general', generalDraft)
  }

  const handleSaveWorkflow = () => {
    updateSection('workflow', workflowDraft)
  }

  const handleSaveAI = () => {
    updateSection('ai', aiDraft)
  }

  const handleSaveNotifications = () => {
    updateSection('notifications', notifDraft)
  }

  const handleSaveSecurity = () => {
    updateSection('security', secDraft)
  }

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPassword || newPassword.length < 6) {
      setPasswordNotice('Password must be at least 6 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordNotice('Passwords do not match.')
      return
    }
    setPasswordNotice('Password changed successfully (simulated).')
    setTimeout(() => {
      setShowPasswordModal(false)
      setPasswordNotice(null)
      setNewPassword('')
      setConfirmPassword('')
    }, 1500)
  }

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1380, margin: '0 auto', color: '#f3f4f6' }}>
      {/* Save Success Banner */}
      <AnimatePresence>
        {isSaved && (
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
            <span>Settings saved successfully to browser storage</span>
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
          marginBottom: 28,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <h1 style={{ margin: 0, color: '#ffffff', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>
              System & Workspace Settings
            </h1>
            <span
              style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 4,
                background: 'rgba(99, 102, 241, 0.1)',
                color: '#a5b4fc',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                fontWeight: 600,
                textTransform: 'uppercase',
              }}
            >
              Enterprise Config
            </span>
          </div>
          <p style={{ margin: 0, color: '#71717a', fontSize: 13, maxWidth: 680, lineHeight: 1.5 }}>
            Configure commercial governance rules, AI risk sensitivity thresholds, simulated Odoo environment parameters, and user notification policies.
          </p>
        </div>

        {/* Header Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              resetSettings()
              setGeneralDraft(settings.general)
              setWorkflowDraft(settings.workflow)
              setAiDraft(settings.ai)
              setNotifDraft(settings.notifications)
              setSecDraft(settings.security)
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 14px',
              fontSize: 12,
              background: '#18181b',
              border: '1px solid #27272a',
              borderRadius: 6,
              color: '#d4d4d8',
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={14} />
            Reset Settings Defaults
          </button>
          <button
            onClick={handleResetAllDemoData}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 14px',
              fontSize: 12,
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: 6,
              color: '#f87171',
              cursor: 'pointer',
              fontWeight: 600,
            }}
            title="Restores all requests, approvals, ERP syncs, and transactions to factory demo baseline"
          >
            <RotateCcw size={14} />
            Reset All Demo Data
          </button>
        </div>
      </header>

      {resetFeedback && (
        <div style={{ marginBottom: 16, padding: '10px 16px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 6, color: '#34d399', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <CheckCircle size={15} />
          {resetFeedback}
        </div>
      )}

      {/* Two-Column Responsive Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 260px) 1fr', gap: 28 }}>
        {/* Left Navigation */}
        <nav
          style={{
            background: '#09090b',
            border: '1px solid #1c1c24',
            borderRadius: 8,
            padding: '10px',
            height: 'fit-content',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
          }}
        >
          {SECTIONS.map((sec) => {
            const isSelected = activeTab === sec.id
            return (
              <button
                key={sec.id}
                onClick={() => setActiveTab(sec.id)}
                style={{
                  textAlign: 'left',
                  padding: '10px 14px',
                  borderRadius: 6,
                  background: isSelected ? '#1c1c24' : 'transparent',
                  color: isSelected ? '#ffffff' : '#a1a1aa',
                  border: 'none',
                  fontSize: 13,
                  fontWeight: isSelected ? 600 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span>{sec.label}</span>
                {isSelected && <span style={{ width: 4, height: 4, borderRadius: '50%', background: '#6366f1' }} />}
              </button>
            )
          })}
        </nav>

        {/* Right Content Panels */}
        <div style={{ background: '#09090b', border: '1px solid #1c1c24', borderRadius: 8, padding: '24px 28px' }}>
          {/* SECTION 1: GENERAL */}
          {activeTab === 'general' && (
            <div>
              <div style={{ marginBottom: 20, borderBottom: '1px solid #1c1c24', paddingBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff' }}>General Workspace Preferences</h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>Organization name and localization formats</p>
              </div>

              <div style={{ display: 'grid', gap: 18, maxWidth: 640 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                    Organization Name
                  </label>
                  <input
                    type="text"
                    value={generalDraft.organizationName}
                    onChange={(e) => setGeneralDraft({ ...generalDraft, organizationName: e.target.value })}
                    style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: 13 }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                    Workspace Identifier
                  </label>
                  <input
                    type="text"
                    value={generalDraft.workspaceName}
                    onChange={(e) => setGeneralDraft({ ...generalDraft, workspaceName: e.target.value })}
                    style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: 13 }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                      Default Currency
                    </label>
                    <select
                      value={generalDraft.defaultCurrency}
                      onChange={(e) => setGeneralDraft({ ...generalDraft, defaultCurrency: e.target.value as any })}
                      style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: 13 }}
                    >
                      <option value="USD">USD ($)</option>
                      <option value="EUR">EUR (€)</option>
                      <option value="GBP">GBP (£)</option>
                      <option value="INR">INR (₹)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                      Timezone
                    </label>
                    <input
                      type="text"
                      value={generalDraft.defaultTimeZone}
                      onChange={(e) => setGeneralDraft({ ...generalDraft, defaultTimeZone: e.target.value })}
                      style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: 13 }}
                    />
                  </div>
                </div>

                <div>
                  <button
                    onClick={handleSaveGeneral}
                    style={{ padding: '8px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
                  >
                    Save General Settings
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 2: WORKFLOW */}
          {activeTab === 'workflow' && (
            <div>
              <div style={{ marginBottom: 20, borderBottom: '1px solid #1c1c24', paddingBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff' }}>Commercial Workflow & SLA Policies</h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>Governs approval gates, AI evaluation steps, and ERP execution simulation rules</p>
              </div>

              <div style={{ display: 'grid', gap: 18, maxWidth: 680 }}>
                {/* Switch: Require Approval */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: '#121215', border: '1px solid #27272a', borderRadius: 6 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>Require Human Commercial Approval</div>
                    <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>Non-standard discounts and custom terms require director signoff</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={workflowDraft.requireApproval}
                    onChange={(e) => setWorkflowDraft({ ...workflowDraft, requireApproval: e.target.checked })}
                    style={{ cursor: 'pointer', transform: 'scale(1.2)' }}
                  />
                </div>

                {/* Switch: AI Pre-Analysis */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: '#121215', border: '1px solid #27272a', borderRadius: 6 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>Automatic AI Pre-Analysis</div>
                    <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>Trigger copilot margin assessment upon request submission</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={workflowDraft.aiPreAnalysis}
                    onChange={(e) => setWorkflowDraft({ ...workflowDraft, aiPreAnalysis: e.target.checked })}
                    style={{ cursor: 'pointer', transform: 'scale(1.2)' }}
                  />
                </div>

                {/* Switch: Auto Create Transaction */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: '#121215', border: '1px solid #27272a', borderRadius: 6 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>Auto-Register Financial Transaction</div>
                    <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>Automatically generate ledger transaction after simulated ERP sync</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={workflowDraft.autoCreateTransactionAfterExecution}
                    onChange={(e) => setWorkflowDraft({ ...workflowDraft, autoCreateTransactionAfterExecution: e.target.checked })}
                    style={{ cursor: 'pointer', transform: 'scale(1.2)' }}
                  />
                </div>

                {/* Switch: Simulate Failure for Testing */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#f87171' }}>Simulate ERP Failure at Step 3 (Demo Test)</div>
                    <div style={{ fontSize: 11, color: '#a1a1aa', marginTop: 2 }}>Forces simulated Odoo inventory conflict to verify failure notifications & retry button</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={workflowDraft.simulateErpFailureAtStep3}
                    onChange={(e) => setWorkflowDraft({ ...workflowDraft, simulateErpFailureAtStep3: e.target.checked })}
                    style={{ cursor: 'pointer', transform: 'scale(1.2)' }}
                  />
                </div>

                {/* SLA Hours Select */}
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                    Standard Approval SLA Window
                  </label>
                  <select
                    value={workflowDraft.approvalSlaHours}
                    onChange={(e) => setWorkflowDraft({ ...workflowDraft, approvalSlaHours: Number(e.target.value) })}
                    style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: 13 }}
                  >
                    <option value={12}>12 Hours (Fast-Track SLA)</option>
                    <option value={24}>24 Hours (Standard Governance)</option>
                    <option value={48}>48 Hours (Enterprise Extended)</option>
                  </select>
                </div>

                <div>
                  <button
                    onClick={handleSaveWorkflow}
                    style={{ padding: '8px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
                  >
                    Save Workflow Settings
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 3: AI INTELLIGENCE */}
          {activeTab === 'ai' && (
            <div>
              <div style={{ marginBottom: 20, borderBottom: '1px solid #1c1c24', paddingBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff' }}>AI Intelligence Copilot Configuration</h3>
                  <span style={{ fontSize: 10, padding: '2px 8px', background: 'rgba(129, 140, 248, 0.1)', color: '#818cf8', border: '1px solid rgba(129, 140, 248, 0.25)', borderRadius: 4, fontWeight: 700 }}>
                    Frontend AI Simulation
                  </span>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>
                  Threshold sensitivity for automated risk scoring and deal recommendations. No external AI APIs are connected.
                </p>
              </div>

              <div style={{ display: 'grid', gap: 18, maxWidth: 680 }}>
                {/* Confidence Threshold Slider */}
                <div style={{ background: '#121215', border: '1px solid #27272a', padding: '14px 16px', borderRadius: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>Minimum AI Confidence Threshold</span>
                    <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: '#818cf8' }}>{aiDraft.confidenceThreshold}%</span>
                  </div>
                  <input
                    type="range"
                    min={50}
                    max={95}
                    value={aiDraft.confidenceThreshold}
                    onChange={(e) => setAiDraft({ ...aiDraft, confidenceThreshold: Number(e.target.value) })}
                    style={{ width: '100%', cursor: 'pointer' }}
                  />
                  <div style={{ fontSize: 11, color: '#71717a', marginTop: 6 }}>
                    Evaluations scoring beneath this mark trigger a "Low Confidence" flag
                  </div>
                </div>

                {/* High Risk Threshold Slider */}
                <div style={{ background: '#121215', border: '1px solid #27272a', padding: '14px 16px', borderRadius: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>High Risk Escalation Threshold</span>
                    <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: '#f59e0b' }}>{aiDraft.highRiskThreshold}/100</span>
                  </div>
                  <input
                    type="range"
                    min={40}
                    max={90}
                    value={aiDraft.highRiskThreshold}
                    onChange={(e) => setAiDraft({ ...aiDraft, highRiskThreshold: Number(e.target.value) })}
                    style={{ width: '100%', cursor: 'pointer' }}
                  />
                  <div style={{ fontSize: 11, color: '#71717a', marginTop: 6 }}>
                    Deals scoring above this mark require mandatory Vice President approval
                  </div>
                </div>

                {/* Recommendation Mode */}
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                    Copilot Recommendation Policy
                  </label>
                  <select
                    value={aiDraft.recommendationMode}
                    onChange={(e) => setAiDraft({ ...aiDraft, recommendationMode: e.target.value as any })}
                    style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: 13 }}
                  >
                    <option value="Conservative">Conservative (Prioritizes Gross Margins & Strict Terms)</option>
                    <option value="Balanced">Balanced (Standard Commercial Growth & Risk Balance)</option>
                    <option value="Aggressive">Aggressive (Prioritizes Rapid Deal Velocity & Expansion)</option>
                  </select>
                </div>

                <div>
                  <button
                    onClick={handleSaveAI}
                    style={{ padding: '8px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
                  >
                    Save AI Settings
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 4: NOTIFICATIONS */}
          {activeTab === 'notifications' && (
            <div>
              <div style={{ marginBottom: 20, borderBottom: '1px solid #1c1c24', paddingBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff' }}>Notification Channel Preferences</h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>Select which workflow alerts generate in-app and topbar notifications</p>
              </div>

              <div style={{ display: 'grid', gap: 14, maxWidth: 680 }}>
                {[
                  { key: 'approvalNotifications', label: 'Commercial Approval Alerts', desc: 'Notify on pending reviews, sign-offs, and request returns' },
                  { key: 'aiAlerts', label: 'AI Risk & Anomaly Warnings', desc: 'Notify when high margin risk or policy violations are flagged' },
                  { key: 'processingNotifications', label: 'ERP Execution Updates', desc: 'Notify upon simulated Odoo order dispatch and fulfillment milestones' },
                  { key: 'securityAlerts', label: 'Security & Access Warnings', desc: 'Notify on failed credentials and unauthorized route attempts' },
                  { key: 'systemMessages', label: 'System Configuration Changes', desc: 'Notify when workspace rules or SLAs are adjusted' },
                ].map((item) => (
                  <div
                    key={item.key}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: '#121215', border: '1px solid #27272a', borderRadius: 6 }}
                  >
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>{item.label}</div>
                      <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>{item.desc}</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={(notifDraft as any)[item.key]}
                      onChange={(e) => setNotifDraft({ ...notifDraft, [item.key]: e.target.checked })}
                      style={{ cursor: 'pointer', transform: 'scale(1.2)' }}
                    />
                  </div>
                ))}

                <div>
                  <button
                    onClick={handleSaveNotifications}
                    style={{ padding: '8px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
                  >
                    Save Notification Preferences
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 5: INTEGRATIONS */}
          {activeTab === 'integrations' && (
            <div>
              <div style={{ marginBottom: 20, borderBottom: '1px solid #1c1c24', paddingBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff' }}>System Integrations & ERP Adapters</h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>Enterprise connectors running in local simulation mode</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
                {Object.values(settings.integrations).map((integ) => (
                  <div
                    key={integ.name}
                    style={{ background: '#121215', border: '1px solid #27272a', borderRadius: 8, padding: '18px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                        <span style={{ fontSize: 14, fontWeight: 700, color: '#ffffff' }}>{integ.name}</span>
                        <span
                          style={{
                            fontSize: 10,
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: 4,
                            background: 'rgba(16, 185, 129, 0.1)',
                            color: '#10b981',
                            border: '1px solid rgba(16, 185, 129, 0.25)',
                          }}
                        >
                          {integ.status}
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: '#a1a1aa', margin: '0 0 14px', lineHeight: 1.45 }}>{integ.description}</p>
                      <div style={{ fontSize: 11, color: '#71717a', background: '#09090b', padding: '6px 10px', borderRadius: 4, border: '1px solid #1c1c24' }}>
                        Environment: <span style={{ color: '#e4e4e7' }}>{integ.environment}</span>
                      </div>
                    </div>

                    <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid #1e1e24', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 11, color: '#52525b' }}>Sync: {integ.lastSync}</span>
                      <button
                        onClick={() => alert(`Connector '${integ.name}' is operational in local simulation mode.`)}
                        style={{ background: 'transparent', border: '1px solid #27272a', padding: '4px 10px', borderRadius: 4, color: '#818cf8', fontSize: 11, cursor: 'pointer' }}
                      >
                        Inspect
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION 6: SECURITY */}
          {activeTab === 'security' && (
            <div>
              <div style={{ marginBottom: 20, borderBottom: '1px solid #1c1c24', paddingBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff' }}>Access & Credential Security</h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>Session expiration controls and password management</p>
              </div>

              <div style={{ display: 'grid', gap: 18, maxWidth: 680 }}>
                <div style={{ background: '#121215', border: '1px solid #27272a', padding: '14px 18px', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>Active User Password</div>
                    <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>Last changed 3 days ago for Arjun Sharma</div>
                  </div>
                  <button
                    onClick={() => setShowPasswordModal(true)}
                    style={{ padding: '6px 14px', background: '#27272a', border: '1px solid #3f3f46', borderRadius: 6, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
                  >
                    Change Password
                  </button>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                    Session Timeout Duration
                  </label>
                  <select
                    value={secDraft.sessionDurationMinutes}
                    onChange={(e) => setSecDraft({ ...secDraft, sessionDurationMinutes: Number(e.target.value) })}
                    style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: 13 }}
                  >
                    <option value={60}>60 Minutes (1 Hour)</option>
                    <option value={120}>120 Minutes (2 Hours)</option>
                    <option value={480}>480 Minutes (8 Hours)</option>
                  </select>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: '#121215', border: '1px solid #27272a', borderRadius: 6 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>Alert on Consecutive Failed Sign-ins</div>
                    <div style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>Dispatches security alert to Director notification feed</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={secDraft.securityAlertsOnFailedLogin}
                    onChange={(e) => setSecDraft({ ...secDraft, securityAlertsOnFailedLogin: e.target.checked })}
                    style={{ cursor: 'pointer', transform: 'scale(1.2)' }}
                  />
                </div>

                <div>
                  <button
                    onClick={handleSaveSecurity}
                    style={{ padding: '8px 18px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
                  >
                    Save Security Settings
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 7: SYSTEM SPECIFICATIONS */}
          {activeTab === 'system' && (
            <div>
              <div style={{ marginBottom: 20, borderBottom: '1px solid #1c1c24', paddingBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff' }}>Platform Runtime & Technical Architecture</h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717a' }}>Transparent verification details of frontend-only execution</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
                {[
                  { label: 'Application Version', value: settings.system.version },
                  { label: 'Runtime Environment', value: settings.system.environment },
                  { label: 'Data Persistence Layer', value: settings.system.dataStorage },
                  { label: 'Backend Integration Status', value: settings.system.backendStatus },
                  { label: 'Odoo ERP Operational Mode', value: settings.system.odooStatus },
                  { label: 'AI Intelligence Engine', value: settings.system.aiStatus },
                  { label: 'External REST / GraphQL APIs', value: settings.system.apiStatus },
                  { label: 'Build Quality Target', value: settings.system.buildStatus },
                ].map((item) => (
                  <div key={item.label} style={{ background: '#121215', border: '1px solid #27272a', borderRadius: 6, padding: '12px 14px' }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: '#71717a', textTransform: 'uppercase' }}>{item.label}</span>
                    <div className="mono" style={{ fontSize: 12.5, fontWeight: 600, color: '#ffffff', marginTop: 4 }}>
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Demo Data Reset Card */}
              <div style={{ marginTop: 24, padding: 18, background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
                  <div style={{ maxWidth: 540 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: '#ef4444' }}>Demo Data Reset Utility</div>
                    <p style={{ margin: '4px 0 0', fontSize: 12, color: '#a1a1aa', lineHeight: 1.5 }}>
                      Restore all operational requests, approvals, ERP executions, financial transactions, audit logs, and notification feeds to clean demo defaults. Keeps active login session intact.
                    </p>
                  </div>
                  <button
                    onClick={handleResetAllDemoData}
                    style={{
                      padding: '9px 18px',
                      background: '#ef4444',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 6,
                      fontSize: 12.5,
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <RotateCcw size={14} />
                    Reset All Demo Data
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            background: 'rgba(0,0,0,0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 20,
          }}
        >
          <div style={{ background: '#09090b', border: '1px solid #27272a', borderRadius: 8, width: '100%', maxWidth: 420, padding: 24 }}>
            <h3 style={{ margin: '0 0 8px', fontSize: 16, fontWeight: 700, color: '#ffffff' }}>Change Account Password</h3>
            <p style={{ margin: '0 0 16px', fontSize: 12, color: '#71717a' }}>Update local session credentials for current user.</p>

            <form onSubmit={handlePasswordSubmit} style={{ display: 'grid', gap: 12 }}>
              <div>
                <label style={{ fontSize: 11, color: '#a1a1aa', display: 'block', marginBottom: 4 }}>New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Min 6 characters"
                  style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 10px', borderRadius: 6, color: '#fff', fontSize: 12 }}
                />
              </div>

              <div>
                <label style={{ fontSize: 11, color: '#a1a1aa', display: 'block', marginBottom: 4 }}>Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  style={{ width: '100%', background: '#121215', border: '1px solid #27272a', padding: '8px 10px', borderRadius: 6, color: '#fff', fontSize: 12 }}
                />
              </div>

              {passwordNotice && (
                <div style={{ fontSize: 11, color: passwordNotice.includes('success') ? '#10b981' : '#ef4444' }}>
                  {passwordNotice}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
                <button
                  type="button"
                  onClick={() => setShowPasswordModal(false)}
                  style={{ padding: '6px 12px', background: 'transparent', border: '1px solid #27272a', borderRadius: 6, color: '#a1a1aa', fontSize: 12, cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ padding: '6px 14px', background: '#6366f1', border: 'none', borderRadius: 6, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
                >
                  Update Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
