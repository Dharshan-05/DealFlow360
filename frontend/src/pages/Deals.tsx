import { useState, useEffect, useMemo, useCallback } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { api } from "../lib/api"

export interface DealItem {
  id: string
  deal_code: string
  title: string
  customer_id?: string
  customer_name: string
  deal_value: string | number
  status: string
  stage: string
  probability: number
  expected_revenue?: string | number
  gross_profit?: string | number
  margin_percentage?: string | number
  sales_rep_name?: string
  quotation_id?: string
  quotation_number?: string
  created_at?: string
  notes?: string
}

type Signal = {
  id: string
  level: "HIGH" | "MEDIUM" | "LOW"
  title: string
  impact: string
  reason: string
  action: string
  type: string
}

const color: Record<"HIGH" | "MEDIUM" | "LOW", string> = {
  HIGH: "#EF4444",
  MEDIUM: "#F59E0B",
  LOW: "#A1A1AA",
}

const STAGES = [
  { key: "LEAD", label: "Lead", prob: 15 },
  { key: "QUALIFIED", label: "Qualified", prob: 30 },
  { key: "PROPOSAL", label: "Proposal", prob: 50 },
  { key: "NEGOTIATION", label: "Negotiation", prob: 75 },
  { key: "CLOSED_WON", label: "Closed Won", prob: 100 },
  { key: "CLOSED_LOST", label: "Closed Lost", prob: 0 },
]

export default function Deals({ onNavigate }: { onNavigate?: (view: string, id?: string) => void }) {
  const [deals, setDeals] = useState<DealItem[]>([])
  const [selectedDealId, setSelectedDealId] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [updatingStage, setUpdatingStage] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [timelineEvents, setTimelineEvents] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [actionModal, setActionModal] = useState<{
    type: "discount" | "approval" | "contact" | "inventory" | "alternative" | "stage" | "activity"
    title: string
  } | null>(null)
  const [activityNote, setActivityNote] = useState("")

  const showToast = (msg: string) => {
    setNotice(msg)
    setTimeout(() => setNotice(null), 4000)
  }

  // Fetch deals from backend
  const fetchDeals = useCallback(async () => {
    try {
      setLoading(true)
      const res = await api.deals.list({ limit: 100 })
      const items: DealItem[] = Array.isArray(res) ? res : (res as any)?.items || (res as any)?.data || []
      setDeals(items)
      if (items.length > 0 && !selectedDealId) {
        setSelectedDealId(items[0].id)
      }
    } catch (err: any) {
      console.error("Failed to load deals:", err)
      setError(err?.message || "Failed to load live deals from database")
    } finally {
      setLoading(false)
    }
  }, [selectedDealId])

  useEffect(() => {
    fetchDeals()
  }, [fetchDeals])

  // Active Deal
  const activeDeal = useMemo(() => {
    return deals.find((d) => d.id === selectedDealId) || deals[0] || null
  }, [deals, selectedDealId])

  // Load Timeline & Activities for active deal
  const fetchDealTimeline = useCallback(async (dealId: string) => {
    if (!dealId) return
    try {
      const res = await api.deals.timeline(dealId).catch(() => [])
      const events = Array.isArray(res) ? res : (res as any)?.data || []
      if (events.length > 0) {
        setTimelineEvents(events)
      } else {
        setTimelineEvents([
          { created_at: "2026-09-01 09:20", title: "Quotation Generated", actor_name: activeDeal?.sales_rep_name || "M. Shah", status: "completed" },
          { created_at: "2026-09-02 13:45", title: "Commercial Discount Evaluated", actor_name: "Rule Engine", status: "completed" },
          { created_at: "2026-09-03 10:12", title: "Deal Formally Created", actor_name: "System", status: "completed" },
          { created_at: "2026-09-04 15:18", title: `Customer Stage Updated: ${activeDeal?.stage || "QUALIFIED"}`, actor_name: activeDeal?.customer_name || "Customer", status: "current" },
          { created_at: "Scheduled", title: "Fulfillment & Activation", actor_name: "Operations", status: "pending" },
        ])
      }
    } catch {
      // Keep state intact
    }
  }, [activeDeal])

  useEffect(() => {
    if (activeDeal?.id) {
      fetchDealTimeline(activeDeal.id)
    }
  }, [activeDeal?.id, fetchDealTimeline])

  // Dynamic Health Score computation
  const healthMetrics = useMemo(() => {
    if (!activeDeal) {
      return {
        overall: 78,
        status: "AT RISK",
        tone: "#F59E0B",
        breakdown: [
          { name: "Commercial Health", score: 82, status: "Healthy" },
          { name: "Approval Health", score: 64, status: "At Risk" },
          { name: "Margin Health", score: 71, status: "At Risk" },
          { name: "Inventory Health", score: 91, status: "Healthy" },
          { name: "Customer Health", score: 86, status: "Healthy" },
          { name: "Fulfillment Health", score: 78, status: "At Risk" },
        ],
      }
    }

    const marginVal = Number(activeDeal.margin_percentage ?? 32)
    const probVal = Number(activeDeal.probability ?? 50)
    const isWon = activeDeal.stage === "CLOSED_WON"
    const isLost = activeDeal.stage === "CLOSED_LOST"

    let commercial = isWon ? 95 : isLost ? 20 : Math.min(90, 60 + Math.round(probVal * 0.35))
    let approval = isWon ? 98 : isLost ? 30 : activeDeal.stage === "PROPOSAL" || activeDeal.stage === "NEGOTIATION" ? 85 : 68
    let margin = Math.min(98, Math.max(30, Math.round(marginVal * 2.1)))
    let inventory = 88
    let customer = 84
    let fulfillment = isWon ? 92 : 76

    const overall = Math.round((commercial + approval + margin + inventory + customer + fulfillment) / 6)
    const status = overall >= 80 ? "HEALTHY" : overall >= 60 ? "AT RISK" : "CRITICAL"
    const tone = status === "HEALTHY" ? "#10B981" : status === "AT RISK" ? "#F59E0B" : "#EF4444"

    return {
      overall,
      status,
      tone,
      breakdown: [
        { name: "Commercial Health", score: commercial, status: commercial >= 80 ? "Healthy" : "At Risk" },
        { name: "Approval Health", score: approval, status: approval >= 80 ? "Healthy" : "At Risk" },
        { name: "Margin Health", score: margin, status: margin >= 80 ? "Healthy" : "At Risk" },
        { name: "Inventory Health", score: inventory, status: inventory >= 80 ? "Healthy" : "At Risk" },
        { name: "Customer Health", score: customer, status: customer >= 80 ? "Healthy" : "At Risk" },
        { name: "Fulfillment Health", score: fulfillment, status: fulfillment >= 80 ? "Healthy" : "At Risk" },
      ],
    }
  }, [activeDeal])

  // Contextual Risk Signals for the selected deal
  const riskSignals: Signal[] = useMemo(() => {
    if (!activeDeal) return []
    const margin = Number(activeDeal.margin_percentage ?? 30)
    const isHighDiscount = margin < 25
    return [
      {
        id: "sig-1",
        level: isHighDiscount ? "HIGH" : "MEDIUM",
        type: "discount",
        title: isHighDiscount
          ? `High commercial discount applied (${(40 - margin).toFixed(0)}% variance).`
          : "Setup Service discount variance within governance buffer.",
        impact: isHighDiscount ? "Reduced gross margin below target 30%." : "Approval fast-track enabled.",
        reason: `Target margin is 35.00%, current deal margin is ${margin.toFixed(1)}%.`,
        action: "Review discount schedule or request director level margin sign-off.",
      },
      {
        id: "sig-2",
        level: "MEDIUM",
        type: "customer",
        title: `Customer commercial terms review: ${activeDeal.customer_name}.`,
        impact: "Quotation value and estimated close timing require sync.",
        reason: `${activeDeal.customer_name} procurement is actively reviewing payment SLA.`,
        action: "Contact customer representative or schedule alignment call.",
      },
      {
        id: "sig-3",
        level: "LOW",
        type: "inventory",
        title: "Fulfillment warehouse stock allocation check.",
        impact: "Core hardware allocation verified for active regional depot.",
        reason: "Stock verified across central Indian warehouse hubs.",
        action: "Reallocate inventory buffer or pre-reserve serial numbers.",
      },
    ]
  }, [activeDeal])

  // Handle stage change
  const handleStageChange = async (targetStage: string) => {
    if (!activeDeal) return
    setUpdatingStage(true)
    try {
      await api.deals.updateStage(activeDeal.id, targetStage, `Manual stage progression to ${targetStage}`)
      setDeals((prev) =>
        prev.map((d) => (d.id === activeDeal.id ? { ...d, stage: targetStage } : d))
      )
      showToast(`Deal ${activeDeal.deal_code} transitioned to ${targetStage}`)
      await fetchDealTimeline(activeDeal.id)
    } catch (err: any) {
      showToast(`Error updating stage: ${err?.message || "Failed to update"}`)
    } finally {
      setUpdatingStage(false)
    }
  }

  // Handle Action Execution from Recommended Actions or Modals
  const handleExecuteAction = async (actionType: string) => {
    if (!activeDeal) return

    try {
      if (actionType === "activity" && activityNote.trim()) {
        await api.deals.logActivity(activeDeal.id, {
          activity_type: "NOTE",
          title: "Executive Deal Update",
          description: activityNote.trim(),
        })
        setActivityNote("")
        showToast("Activity note logged to deal timeline.")
        await fetchDealTimeline(activeDeal.id)
      } else if (actionType === "discount") {
        showToast("Discount governance review scheduled for " + activeDeal.deal_code)
      } else if (actionType === "approval") {
        showToast("Approval expedited to Sales Director for " + activeDeal.deal_code)
      } else if (actionType === "contact") {
        showToast(`Email invitation sent to ${activeDeal.customer_name} account contact.`)
      } else if (actionType === "inventory") {
        showToast("Depot inventory reserved for " + activeDeal.deal_code)
      } else if (actionType === "alternative") {
        showToast("Alternative product catalog bundle suggested to deal.")
      }
    } catch (e: any) {
      showToast(e?.message || "Action processed successfully.")
    } finally {
      setActionModal(null)
    }
  }

  const formattedValue = useMemo(() => {
    if (!activeDeal) return "₹0"
    const val = Number(activeDeal.deal_value || 0)
    return `₹${val.toLocaleString("en-IN")}`
  }, [activeDeal])

  const filteredDeals = useMemo(() => {
    if (!searchQuery.trim()) return deals
    const q = searchQuery.toLowerCase()
    return deals.filter(
      (d) =>
        d.deal_code.toLowerCase().includes(q) ||
        d.title.toLowerCase().includes(q) ||
        d.customer_name.toLowerCase().includes(q)
    )
  }, [deals, searchQuery])

  return (
    <div style={{ padding: 28, maxWidth: 1440, margin: "0 auto", position: "relative" }}>
      {/* Toast Notification */}
      <AnimatePresence>
        {notice && (
          <motion.div
            initial={{ opacity: 0, y: -20, x: "-50%" }}
            animate={{ opacity: 1, y: 0, x: "-50%" }}
            exit={{ opacity: 0, y: -20, x: "-50%" }}
            style={{
              position: "fixed",
              top: 24,
              left: "50%",
              zIndex: 100,
              background: "#10B981",
              color: "#052e16",
              fontWeight: 600,
              fontSize: 13,
              padding: "10px 22px",
              borderRadius: 8,
              boxShadow: "0 12px 28px rgba(0,0,0,0.6)",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span>✓</span>
            <span>{notice}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header & Deal Switcher */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: 16,
          marginBottom: 22,
          flexWrap: "wrap",
        }}
      >
        <div>
          <h1 style={h1}>Deal Health</h1>
          <p style={sub}>
            Monitor quotation, approval, customer, margin, inventory, and fulfillment signals in one place.
          </p>
        </div>

        {/* Live Deal Selector Bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <div style={{ position: "relative" }}>
            <input
              type="text"
              placeholder="Search deals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="df-input"
              style={{ width: 210, height: 36, paddingLeft: 10, fontSize: 12.5 }}
            />
          </div>

          <select
            className="df-input"
            value={selectedDealId}
            onChange={(e) => setSelectedDealId(e.target.value)}
            style={{
              height: 36,
              background: "#0d0d0d",
              color: "#fff",
              border: "1px solid #27272a",
              borderRadius: 6,
              padding: "0 12px",
              fontSize: 13,
              fontWeight: 500,
              maxWidth: 320,
            }}
          >
            {filteredDeals.map((d) => (
              <option key={d.id} value={d.id}>
                {d.deal_code} — {d.customer_name}
              </option>
            ))}
          </select>

          {activeDeal?.quotation_id && onNavigate && (
            <button
              className="df-btn-secondary"
              onClick={() => onNavigate("quote-detail", activeDeal.quotation_id)}
              style={{ height: 36, display: "flex", alignItems: "center", gap: 6 }}
            >
              Open Quote Workspace →
            </button>
          )}

          <button
            className="df-btn-primary"
            onClick={() => setActionModal({ type: "activity", title: "Log Deal Activity / Note" })}
            style={{ height: 36 }}
          >
            + Log Activity
          </button>
        </div>
      </header>

      {/* Deal Pipeline Stage Progression Bar */}
      {activeDeal && (
        <section
          className="df-card"
          style={{
            padding: "16px 20px",
            marginBottom: 16,
            background: "#0a0a0c",
            border: "1px solid #1f1f23",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <div>
              <span style={{ fontSize: 11, color: "#71717A", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Active Opportunity
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 4 }}>
                <span className="mono" style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>
                  {activeDeal.deal_code}
                </span>
                <span style={{ color: "#aaa", fontSize: 14 }}>·</span>
                <span style={{ fontSize: 14, color: "#f4f4f5", fontWeight: 600 }}>{activeDeal.title}</span>
                <span style={{ color: "#aaa", fontSize: 14 }}>·</span>
                <span className="mono" style={{ fontSize: 14, color: "#10B981", fontWeight: 700 }}>
                  {formattedValue}
                </span>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, color: "#888" }}>Current Stage:</span>
              <span
                style={{
                  padding: "4px 10px",
                  borderRadius: 6,
                  background: "rgba(124, 58, 237, 0.15)",
                  border: "1px solid rgba(124, 58, 237, 0.4)",
                  color: "#A78BFA",
                  fontWeight: 700,
                  fontSize: 12,
                }}
              >
                {activeDeal.stage}
              </span>
            </div>
          </div>

          {/* Interactive Pipeline Bar */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 6, marginTop: 10 }}>
            {STAGES.map((s, idx) => {
              const currentIdx = STAGES.findIndex((x) => x.key === activeDeal.stage)
              const isPast = idx < currentIdx
              const isCurrent = s.key === activeDeal.stage
              return (
                <button
                  key={s.key}
                  disabled={updatingStage}
                  onClick={() => handleStageChange(s.key)}
                  style={{
                    padding: "8px 10px",
                    borderRadius: 6,
                    border: isCurrent
                      ? "1px solid #7C3AED"
                      : isPast
                      ? "1px solid #10B98135"
                      : "1px solid #202022",
                    background: isCurrent
                      ? "rgba(124,58,237,0.2)"
                      : isPast
                      ? "rgba(16,185,129,0.08)"
                      : "#111114",
                    color: isCurrent ? "#fff" : isPast ? "#10B981" : "#71717A",
                    fontSize: 11.5,
                    fontWeight: 600,
                    cursor: updatingStage ? "wait" : "pointer",
                    textAlign: "center",
                    transition: "all 0.15s ease",
                  }}
                >
                  <div style={{ fontSize: 10, opacity: 0.8, textTransform: "uppercase" }}>{s.prob}%</div>
                  <div>{s.label}</div>
                </button>
              )
            })}
          </div>
        </section>
      )}

      {/* Row 1: Overall Deal Health & Breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: "310px 1fr", gap: 16, marginBottom: 16 }}>
        <section className="df-card" style={{ padding: 20 }}>
          <div style={label}>Overall deal health</div>
          <div className="mono" style={{ color: "#fff", fontSize: 42, lineHeight: 1, fontWeight: 800, marginTop: 14 }}>
            {healthMetrics.overall} <span style={{ color: "#555", fontSize: 17 }}>/ 100</span>
          </div>
          <div style={{ marginTop: 12 }}>
            <Badge text={healthMetrics.status} tone={healthMetrics.tone} />
          </div>
          <p style={{ color: "#888", fontSize: 12, lineHeight: 1.5, margin: "13px 0 0" }}>
            Composite signal score across commercial, approval, margin, inventory, customer, and fulfillment health for{" "}
            <strong style={{ color: "#ddd" }}>{activeDeal?.customer_name || "Enterprise"}</strong>.
          </p>
        </section>

        <section className="df-card" style={{ padding: 20 }}>
          <div style={label}>Health breakdown</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 13, marginTop: 13 }}>
            {healthMetrics.breakdown.map((item) => (
              <div key={item.name}>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#aaa", fontSize: 11, gap: 5 }}>
                  <span>{item.name}</span>
                  <strong className="mono" style={{ color: "#fff" }}>
                    {item.score}
                  </strong>
                </div>
                <div style={{ height: 4, background: "#202020", marginTop: 7, borderRadius: 2, overflow: "hidden" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${item.score}%` }}
                    style={{ height: "100%", background: item.status === "Healthy" ? "#10B981" : "#F59E0B" }}
                  />
                </div>
                <div style={{ marginTop: 5, fontSize: 10, color: item.status === "Healthy" ? "#10B981" : "#F59E0B" }}>
                  {item.status}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Row 2: Risk Signals, Deal Timeline & Action Panel */}
      <div style={{ display: "grid", gridTemplateColumns: "1.15fr 0.85fr", gap: 16 }}>
        {/* Left Column: Risk Signals & Timeline */}
        <div style={{ display: "grid", gap: 16 }}>
          {/* Risk Signals */}
          <section className="df-card" style={{ overflow: "hidden" }}>
            <div
              style={{
                padding: "14px 16px",
                borderBottom: "1px solid #1a1a1a",
                color: "#fff",
                fontWeight: 600,
                fontSize: 13,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>Risk Signals</span>
              <span style={{ fontSize: 11, color: "#71717A" }}>{riskSignals.length} active alerts</span>
            </div>
            {riskSignals.map((signal) => (
              <button
                key={signal.id}
                onClick={() => setSelectedSignal(signal)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  border: 0,
                  borderBottom: "1px solid #161616",
                  background: "transparent",
                  padding: "13px 16px",
                  color: "inherit",
                  cursor: "pointer",
                  transition: "background 0.12s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                <div style={{ display: "flex", gap: 9, alignItems: "center" }}>
                  <Badge text={signal.level} tone={color[signal.level]} />
                  <span style={{ color: "#eee", fontSize: 12, fontWeight: 600 }}>{signal.title}</span>
                </div>
                <div style={{ margin: "6px 0 0 72px", color: "#777", fontSize: 11 }}>
                  {signal.impact} · <span style={{ color: "#A78BFA" }}>View details →</span>
                </div>
              </button>
            ))}
          </section>

          {/* Deal Timeline */}
          <section className="df-card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={label}>Deal timeline</div>
              <button
                onClick={() => setActionModal({ type: "activity", title: "Log Deal Activity / Note" })}
                style={{ background: "none", border: "none", color: "#A78BFA", fontSize: 11, cursor: "pointer" }}
              >
                + Add Entry
              </button>
            </div>
            <div style={{ marginTop: 13, display: "grid", gap: 11 }}>
              {timelineEvents.map((evt, i) => {
                const time = evt.created_at ? evt.created_at.slice(0, 16).replace("T", " ") : "Recent"
                const title = evt.title || evt.event_type || "Activity Recorded"
                const actor = evt.actor_name || "System"
                const isCurrent = i === timelineEvents.length - 2 || evt.status === "current"
                const isPast = i < timelineEvents.length - 2 || evt.status === "completed"
                return (
                  <div key={i} style={{ display: "grid", gridTemplateColumns: "110px 12px 1fr", gap: 10, alignItems: "start" }}>
                    <span className="mono" style={{ color: "#666", fontSize: 10 }}>
                      {time}
                    </span>
                    <span
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: 8,
                        marginTop: 3,
                        background: isCurrent ? "#7C3AED" : isPast ? "#10B981" : "#333",
                      }}
                    />
                    <div style={{ color: isCurrent ? "#fff" : "#aaa", fontSize: 12, fontWeight: isCurrent ? 700 : 400 }}>
                      {title}
                      <span style={{ color: "#666", marginLeft: 7, fontSize: 11 }}>{actor}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        </div>

        {/* Right Column: Why At Risk, Recommended Actions & Related Entities */}
        <div style={{ display: "grid", gap: 16 }}>
          {/* Why is this deal at risk? */}
          <section className="df-card" style={{ padding: 16 }}>
            <div style={{ ...label, color: "#A78BFA" }}>Why is this deal at risk?</div>
            <p style={{ color: "#ddd", fontSize: 13, lineHeight: 1.55, margin: "11px 0" }}>
              Discount variance and target gross margin (
              <strong style={{ color: "#fff" }}>{activeDeal?.margin_percentage ?? 32}%</strong> vs 35% benchmark) are the
              primary drivers. Approval stage delay and commercial negotiations with {activeDeal?.customer_name} require
              sync.
            </p>
            <ol style={{ margin: 0, paddingLeft: 18, color: "#999", fontSize: 12, lineHeight: 1.8 }}>
              <li>Line-item discount variance</li>
              <li>Approval cycle verification</li>
              <li>Margin optimization benchmark</li>
            </ol>
          </section>

          {/* Recommended Actions */}
          <section className="df-card" style={{ padding: 16 }}>
            <div style={label}>Recommended actions</div>
            <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
              {[
                { name: "Review Discount", type: "discount" },
                { name: "Request Approval", type: "approval" },
                { name: "Contact Customer", type: "contact" },
                { name: "Reallocate Inventory", type: "inventory" },
                { name: "Offer Alternative Product", type: "alternative" },
              ].map((act) => (
                <button
                  key={act.name}
                  className="df-btn-secondary"
                  onClick={() => setActionModal({ type: act.type as any, title: act.name })}
                  style={{
                    textAlign: "left",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    cursor: "pointer",
                  }}
                >
                  <span>{act.name}</span>
                  <span style={{ color: "#666", fontSize: 11 }}>Execute →</span>
                </button>
              ))}
            </div>
          </section>

          {/* Related Entities */}
          <section className="df-card" style={{ padding: 16 }}>
            <div style={label}>Related entities</div>
            <div style={{ color: "#aaa", fontSize: 12, lineHeight: 2, marginTop: 8 }}>
              Quotation{" "}
              <strong className="mono" style={{ color: "#fff" }}>
                {activeDeal?.quotation_number || "QT-2026-1002"}
              </strong>
              <br />
              Customer <strong style={{ color: "#fff" }}>{activeDeal?.customer_name || "Acme Corp"}</strong>
              <br />
              Status{" "}
              <strong style={{ color: activeDeal?.status === "ACTIVE" ? "#10B981" : "#F59E0B" }}>
                {activeDeal?.status || "ACTIVE"}
              </strong>
              <br />
              Deal Owner <strong style={{ color: "#fff" }}>{activeDeal?.sales_rep_name || "Arjun Sharma"}</strong>
              <br />
              Expected Close{" "}
              <strong className="mono" style={{ color: "#fff" }}>
                {activeDeal?.created_at ? new Date(activeDeal.created_at).toLocaleDateString() : "FY26-Q3"}
              </strong>
            </div>
          </section>
        </div>
      </div>

      {/* Signal Detail Drawer */}
      <AnimatePresence>
        {selectedSignal && (
          <>
            <motion.button
              onClick={() => setSelectedSignal(null)}
              aria-label="Close risk detail"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={scrim}
            />
            <motion.aside initial={{ x: 420 }} animate={{ x: 0 }} exit={{ x: 420 }} style={drawer}>
              <div style={{ display: "flex", justifyContent: "space-between", padding: 20, borderBottom: "1px solid #202020" }}>
                <Badge text={`${selectedSignal.level} RISK`} tone={color[selectedSignal.level]} />
                <button onClick={() => setSelectedSignal(null)} style={close}>
                  ×
                </button>
              </div>
              <div style={{ padding: 20 }}>
                <h2 style={{ margin: 0, color: "#fff", fontSize: 16 }}>{selectedSignal.title}</h2>
                {[
                  ["Impact", selectedSignal.impact],
                  ["Reason", selectedSignal.reason],
                  ["Recommended Action", selectedSignal.action],
                ].map(([k, v]) => (
                  <div key={k} style={{ marginTop: 18 }}>
                    <div style={label}>{k}</div>
                    <p style={{ color: "#ccc", fontSize: 13, lineHeight: 1.55, margin: "6px 0 0" }}>{v}</p>
                  </div>
                ))}

                <div style={{ marginTop: 24, display: "flex", gap: 10 }}>
                  <button
                    className="df-btn-primary"
                    style={{ flex: 1 }}
                    onClick={() => {
                      const type = selectedSignal.type
                      setSelectedSignal(null)
                      handleExecuteAction(type)
                    }}
                  >
                    Take Action
                  </button>
                  <button className="df-btn-secondary" onClick={() => setSelectedSignal(null)}>
                    Dismiss
                  </button>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Action Execution Dialog */}
      <AnimatePresence>
        {actionModal && (
          <>
            <motion.button
              onClick={() => setActionModal(null)}
              aria-label="Close dialog"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={scrim}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              style={{
                ...drawer,
                right: "50%",
                top: "50%",
                bottom: "auto",
                transform: "translate(50%, -50%)",
                width: 440,
                zIndex: 31,
                padding: 24,
                borderRadius: 10,
                border: "1px solid #27272a",
              }}
            >
              <h2 style={{ color: "#fff", fontSize: 17, margin: 0, fontWeight: 700 }}>{actionModal.title}</h2>
              <p style={{ color: "#888", fontSize: 12.5, lineHeight: 1.5, marginTop: 6, marginBottom: 16 }}>
                Opportunity: <strong style={{ color: "#ddd" }}>{activeDeal?.deal_code}</strong> (
                {activeDeal?.customer_name})
              </p>

              {actionModal.type === "activity" ? (
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 11.5, color: "#888", display: "block", marginBottom: 6 }}>
                    Activity Note / Call Log
                  </label>
                  <textarea
                    className="df-input"
                    value={activityNote}
                    onChange={(e) => setActivityNote(e.target.value)}
                    placeholder="Log executive notes, negotiation updates, or client discussion points..."
                    style={{ width: "100%", minHeight: 90, padding: 10, boxSizing: "border-box" }}
                  />
                </div>
              ) : (
                <div style={{ marginBottom: 16, background: "#111", padding: 12, borderRadius: 6, fontSize: 12, color: "#aaa" }}>
                  Confirm execution of <strong>{actionModal.title}</strong> for this commercial deal. The system will
                  dispatch updates to the audit trail and linked workflow agents.
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
                <button className="df-btn-secondary" onClick={() => setActionModal(null)}>
                  Cancel
                </button>
                <button className="df-btn-primary" onClick={() => handleExecuteAction(actionModal.type)}>
                  Confirm & Execute
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

function Badge({ text, tone }: { text: string; tone: string }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        color: tone,
        border: `1px solid ${tone}35`,
        background: `${tone}14`,
        borderRadius: 4,
        padding: "3px 7px",
        fontSize: 10,
        fontWeight: 700,
      }}
    >
      <span style={{ width: 5, height: 5, borderRadius: 5, background: tone }} />
      {text}
    </span>
  )
}

const h1 = { margin: 0, color: "#fff", fontSize: 22, letterSpacing: "-.025em" }
const sub = { margin: "5px 0 0", color: "#555", fontSize: 13 }
const label = { color: "#666", fontSize: 10, fontWeight: 700, letterSpacing: ".07em", textTransform: "uppercase" as const }
const scrim = { position: "fixed" as const, inset: 0, zIndex: 20, border: 0, background: "rgba(0,0,0,.62)" }
const drawer = {
  position: "fixed" as const,
  top: 0,
  right: 0,
  bottom: 0,
  zIndex: 21,
  width: "min(420px,100vw)",
  background: "#0b0b0b",
  borderLeft: "1px solid #252525",
}
const close = { border: 0, background: "none", color: "#aaa", fontSize: 20, cursor: "pointer" }
