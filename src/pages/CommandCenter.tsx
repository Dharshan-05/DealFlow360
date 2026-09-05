import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts"
import { motion } from "framer-motion"
import { useState, useMemo } from "react"
import {
  StaggerContainer,
  StaggerItem,
  AnimatedNumber,
} from "../lib/motion"
import type { AppView } from "../components/AppShell"
import { useRequests } from "../hooks/useRequests"
import { StatusBadge } from "../components/common"
import type { Request } from "../types/request"

interface Props {
  onNavigate: (v: AppView) => void
  onOpenOrders?: (status: string) => void
  onOpenRequest?: (id: string) => void
}

const volumeData = [
  { month: "Jan", requests: 28, value: 18.2 },
  { month: "Feb", requests: 35, value: 22.4 },
  { month: "Mar", requests: 32, value: 20.1 },
  { month: "Apr", requests: 44, value: 29.8 },
  { month: "May", requests: 41, value: 27.3 },
  { month: "Jun", requests: 49, value: 34.5 },
  { month: "Jul", requests: 56, value: 38.9 },
  { month: "Aug", requests: 62, value: 44.1 },
  { month: "Sep", requests: 68, value: 48.2 },
]

function StatCard({
  label,
  value,
  change,
  up,
  accent,
  sublabel,
  onClick,
}: {
  label: string
  value: number
  change: string
  up: boolean
  accent?: string
  sublabel?: string
  onClick?: () => void
}) {
  return (
    <StaggerItem>
      <motion.button
        type="button"
        className="df-card"
        style={{
          padding: "18px 20px",
          textAlign: "left",
          cursor: onClick ? "pointer" : "default",
          border: "1px solid #1e1e1e",
          width: "100%",
          background: "#080808",
        }}
        onClick={onClick}
        whileHover={{ y: -2, borderColor: "#333" }}
        whileTap={{ scale: onClick ? 0.99 : 1 }}
        transition={{ duration: 0.13 }}
      >
        <div
          style={{
            fontSize: 11,
            color: "#666",
            textTransform: "uppercase",
            letterSpacing: "0.07em",
            marginBottom: 8,
            fontWeight: 600,
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontSize: 26,
            fontWeight: 800,
            color: accent ?? "#fff",
            letterSpacing: "-0.03em",
            lineHeight: 1,
            marginBottom: 8,
          }}
          className="mono"
        >
          <AnimatedNumber value={value} />
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ fontSize: 11.5, color: up ? "#10B981" : "#A1A1AA" }}>
              {change}
            </span>
          </div>
          {sublabel && (
            <span style={{ fontSize: 11, color: "#555" }}>
              {sublabel}
            </span>
          )}
        </div>
      </motion.button>
    </StaggerItem>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div
      style={{
        background: "#0a0a0c",
        border: "1px solid #222",
        borderRadius: 6,
        padding: "8px 12px",
        boxShadow: "0 8px 16px rgba(0,0,0,0.5)",
      }}
    >
      <div style={{ fontSize: 11, color: "#666", marginBottom: 3 }}>
        {label} 2026
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, color: "#fff" }} className="mono">
        {payload[0].value} Requests
      </div>
    </div>
  )
}

export default function CommandCenter({ onNavigate, onOpenRequest }: Props) {
  const { requests, metrics, refresh } = useRequests()
  const [period, setPeriod] = useState("30D")
  const [search, setSearch] = useState("")
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState("Just now")

  const handleRefresh = () => {
    setRefreshing(true)
    refresh()
    setTimeout(() => {
      setRefreshing(false)
      setLastUpdated("Just now")
    }, 400)
  }

  const filteredRequests = useMemo(() => {
    if (!search.trim()) return requests.slice(0, 6)
    const term = search.toLowerCase()
    return requests.filter(
      (r) =>
        r.referenceNumber.toLowerCase().includes(term) ||
        r.title.toLowerCase().includes(term) ||
        r.customer.toLowerCase().includes(term) ||
        r.owner.toLowerCase().includes(term)
    )
  }, [requests, search])

  // Synthesize recent cross-request activities
  const recentActivities = useMemo(() => {
    const list: Array<{ id: string; action: string; actor: string; timestamp: string; reqRef: string; reqTitle: string }> = []
    for (const r of requests) {
      if (r.activity) {
        for (const act of r.activity) {
          list.push({
            id: act.id,
            action: act.action,
            actor: act.actor,
            timestamp: act.timestamp,
            reqRef: r.referenceNumber,
            reqTitle: r.title,
          })
        }
      }
    }
    // Sort by timestamp descending
    return list
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 5)
  }, [requests])

  // Pending actions
  const pendingActions = useMemo(() => {
    return requests.filter(
      (r) => r.status === "Draft" || r.status === "In Review" || r.status === "Pending Approval"
    ).slice(0, 4)
  }, [requests])

  const handleRowClick = (req: Request) => {
    if (onOpenRequest) {
      onOpenRequest(req.id)
    }
    onNavigate("quote-detail")
  }

  return (
    <div
      className="command-center"
      style={{ padding: "28px 28px", maxWidth: 1440, margin: "0 auto" }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          marginBottom: 24,
          flexWrap: "wrap",
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span
              style={{
                fontSize: 10.5,
                fontWeight: 700,
                color: "#7C3AED",
                background: "rgba(124, 58, 237, 0.12)",
                border: "1px solid rgba(124, 58, 237, 0.25)",
                borderRadius: 4,
                padding: "2px 7px",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              DealFlow360 Executive
            </span>
            <span style={{ fontSize: 11, color: "#444" }}>Updated {lastUpdated}</span>
          </div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: "#fff",
              letterSpacing: "-0.025em",
              margin: 0,
            }}
          >
            Dashboard
          </h1>
          <p style={{ fontSize: 13, color: "#666", margin: "4px 0 0" }}>
            Operational cockpit for enterprise transaction requests, review routing, and pipeline velocity.
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <motion.button
            aria-label="Refresh dashboard"
            onClick={refreshing ? undefined : handleRefresh}
            whileTap={{ scale: 0.94 }}
            style={{
              width: 32,
              height: 32,
              color: "#aaa",
              background: "#0d0d0d",
              border: "1px solid #222",
              borderRadius: 6,
              cursor: refreshing ? "wait" : "pointer",
              fontSize: 14,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transform: refreshing ? "rotate(180deg)" : undefined,
              transition: "transform .3s ease",
            }}
            title="Refresh Request Metrics"
          >
            ↻
          </motion.button>

          <div style={{ display: "flex", background: "#0d0d0d", border: "1px solid #1e1e1e", borderRadius: 6, padding: 2 }}>
            {["Today", "7D", "30D", "Q3"].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                style={{
                  padding: "5px 10px",
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  background: period === p ? "#fff" : "transparent",
                  color: period === p ? "#000" : "#666",
                  border: 0,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {p}
              </button>
            ))}
          </div>

          <motion.button
            className="df-btn-secondary"
            onClick={() => onNavigate("quotes")}
            whileTap={{ scale: 0.97 }}
            style={{ padding: "7px 12px", fontSize: 12 }}
          >
            All Requests
          </motion.button>

          <motion.button
            className="df-btn-primary"
            onClick={() => {
              if (onOpenRequest) onOpenRequest("new")
              onNavigate("quote-detail")
            }}
            whileTap={{ scale: 0.97 }}
            style={{ padding: "7px 14px", fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}
          >
            <span>+</span> Create Request
          </motion.button>
        </div>
      </div>

      {/* Primary KPI Grid (6 Request-Oriented Metrics) */}
      <StaggerContainer>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
            gap: 12,
            marginBottom: 24,
          }}
        >
          <StatCard
            label="Total Requests"
            value={metrics.total}
            change="+4 this month"
            up={true}
            sublabel="All lifecycle states"
            onClick={() => onNavigate("quotes")}
          />
          <StatCard
            label="Pending Review"
            value={metrics.pending}
            change="Awaiting review"
            up={false}
            accent="#F59E0B"
            sublabel="Requires decision"
            onClick={() => onNavigate("quotes")}
          />
          <StatCard
            label="Approved"
            value={metrics.approved}
            change="Ready for execution"
            up={true}
            accent="#10B981"
            sublabel="Commercials cleared"
            onClick={() => onNavigate("quotes")}
          />
          <StatCard
            label="Draft Requests"
            value={metrics.drafts}
            change="Saved locally"
            up={true}
            accent="#A1A1AA"
            sublabel="Incomplete"
            onClick={() => onNavigate("quotes")}
          />
          <StatCard
            label="Completed"
            value={metrics.completed}
            change="Executed"
            up={true}
            accent="#38BDF8"
            sublabel="Fulfillment done"
            onClick={() => onNavigate("quotes")}
          />
          <StatCard
            label="Action Required"
            value={metrics.requiringAction}
            change="Needs attention"
            up={false}
            accent="#EF4444"
            sublabel="High / Critical"
            onClick={() => onNavigate("quotes")}
          />
        </div>
      </StaggerContainer>

      {/* Main 2-Column Content Area */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 340px",
          gap: 20,
        }}
      >
        {/* Left Column: Velocity Chart + Recent Requests Table */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Velocity Trend Chart */}
          <div className="df-card" style={{ padding: "20px 22px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "#fff", margin: 0 }}>
                  Request Velocity & Throughput
                </h3>
                <p style={{ fontSize: 12, color: "#666", margin: "2px 0 0" }}>
                  Monthly volume of incoming and processed transaction requests.
                </p>
              </div>
              <div style={{ fontSize: 12, color: "#A1A1AA", fontFamily: "monospace" }}>
                Total Pipeline Value: <span style={{ color: "#fff", fontWeight: 700 }}>{metrics.formattedTotalValue}</span>
              </div>
            </div>

            <div style={{ height: 180, width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={volumeData} margin={{ top: 10, right: 10, left: -24, bottom: 0 }}>
                  <defs>
                    <linearGradient id="reqGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#7C3AED" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#141414" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" stroke="#333" tick={{ fill: "#555", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis stroke="#333" tick={{ fill: "#555", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="requests"
                    stroke="#7C3AED"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#reqGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Requests Section */}
          <div className="df-card" style={{ overflow: "hidden", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div
              style={{
                padding: "14px 18px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderBottom: "1px solid #161616",
                flexWrap: "wrap",
                gap: 10,
              }}
            >
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "#fff", margin: 0 }}>
                  Recent Requests
                </h3>
                <p style={{ fontSize: 11.5, color: "#555", margin: "2px 0 0" }}>
                  Active portfolio items and status updates
                </p>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="text"
                  placeholder="Filter recent..."
                  className="df-input"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{ width: 170, height: 30, fontSize: 12, padding: "0 10px" }}
                />
                <button
                  onClick={() => onNavigate("quotes")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#7C3AED",
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    padding: 4,
                  }}
                >
                  View All &rarr;
                </button>
              </div>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #141414" }}>
                    {["Request ID", "Title & Type", "Customer", "Amount", "Priority", "Status", ""].map((col) => (
                      <th
                        key={col}
                        style={{
                          fontSize: 10.5,
                          fontWeight: 600,
                          textTransform: "uppercase",
                          color: "#555",
                          padding: "10px 16px",
                          letterSpacing: "0.06em",
                        }}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredRequests.map((req, idx) => (
                    <motion.tr
                      key={req.id}
                      onClick={() => handleRowClick(req)}
                      whileHover={{ background: "rgba(255, 255, 255, 0.025)" }}
                      style={{
                        borderBottom: idx < filteredRequests.length - 1 ? "1px solid #111" : "none",
                        cursor: "pointer",
                        transition: "background 0.12s ease",
                      }}
                    >
                      <td style={{ padding: "12px 16px" }}>
                        <span
                          className="mono"
                          style={{
                            fontSize: 12,
                            fontWeight: 600,
                            color: "#fff",
                            background: "#141418",
                            padding: "2px 6px",
                            borderRadius: 4,
                            border: "1px solid #22222a",
                          }}
                        >
                          {req.referenceNumber}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", maxWidth: 220 }}>
                        <div
                          style={{
                            fontSize: 12.5,
                            fontWeight: 600,
                            color: "#fff",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {req.title}
                        </div>
                        <div style={{ fontSize: 11, color: "#666", marginTop: 2 }}>
                          {req.requestType}
                        </div>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <div style={{ fontSize: 12, color: "#D4D4D8", fontWeight: 500 }}>
                          {req.customer}
                        </div>
                        <div style={{ fontSize: 11, color: "#555" }}>
                          {req.owner}
                        </div>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span className="mono" style={{ fontSize: 12.5, fontWeight: 600, color: "#fff" }}>
                          {req.formattedAmount}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span
                          style={{
                            fontSize: 10.5,
                            fontWeight: 700,
                            padding: "2px 7px",
                            borderRadius: 4,
                            textTransform: "uppercase",
                            letterSpacing: "0.04em",
                            background:
                              req.priority === "Critical"
                                ? "rgba(239, 68, 68, 0.1)"
                                : req.priority === "High"
                                ? "rgba(249, 115, 22, 0.1)"
                                : req.priority === "Medium"
                                ? "rgba(245, 158, 11, 0.1)"
                                : "rgba(16, 185, 129, 0.1)",
                            color:
                              req.priority === "Critical"
                                ? "#EF4444"
                                : req.priority === "High"
                                ? "#F97316"
                                : req.priority === "Medium"
                                ? "#F59E0B"
                                : "#10B981",
                            border: `1px solid ${
                              req.priority === "Critical"
                                ? "rgba(239, 68, 68, 0.25)"
                                : req.priority === "High"
                                ? "rgba(249, 115, 22, 0.25)"
                                : req.priority === "Medium"
                                ? "rgba(245, 158, 11, 0.25)"
                                : "rgba(16, 185, 129, 0.25)"
                            }`,
                          }}
                        >
                          {req.priority}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <StatusBadge status={req.status} size="sm" showDot />
                      </td>
                      <td style={{ padding: "12px 16px", color: "#555", fontSize: 13, textAlign: "right" }}>
                        &rarr;
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Pending Actions + Recent Activity + Phase 5 Placeholder */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Pending Actions Card */}
          <div
            className="df-card"
            style={{ padding: "16px 18px", background: "#080808", border: "1px solid #1a1a1a" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#fff" }}>
                Pending Actions
              </div>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  color: "#F59E0B",
                  background: "rgba(245, 158, 11, 0.1)",
                  padding: "1px 6px",
                  borderRadius: 4,
                  border: "1px solid rgba(245, 158, 11, 0.25)",
                }}
              >
                {pendingActions.length} Waiting
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {pendingActions.map((req) => (
                <div
                  key={req.id}
                  onClick={() => handleRowClick(req)}
                  style={{
                    padding: "9px 10px",
                    borderRadius: 6,
                    background: "#0f0f12",
                    border: "1px solid #1e1e24",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div style={{ overflow: "hidden", paddingRight: 8 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {req.referenceNumber} · {req.customer}
                    </div>
                    <div style={{ fontSize: 11, color: "#71717A", marginTop: 2 }}>
                      {req.status === "Draft"
                        ? "Ready for completion & submission"
                        : req.status === "Ready for Approval"
                        ? "Awaiting commercial approval"
                        : "Under review"}
                    </div>
                  </div>
                  <span style={{ fontSize: 12, color: "#7C3AED", flexShrink: 0 }}>&rarr;</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity Feed */}
          <div
            className="df-card"
            style={{ padding: "16px 18px", background: "#080808", border: "1px solid #1a1a1a" }}
          >
            <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", marginBottom: 12 }}>
              Recent Activity
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {recentActivities.map((act, i) => (
                <div key={act.id || i} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                  <div
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: "#7C3AED",
                      marginTop: 6,
                      flexShrink: 0,
                    }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: "#E4E4E7" }}>
                      <span style={{ color: "#fff", fontWeight: 600 }}>{act.actor}</span> · {act.action}
                    </div>
                    <div style={{ fontSize: 11, color: "#71717A", marginTop: 1 }} className="mono">
                      {act.reqRef}
                    </div>
                    <div style={{ fontSize: 10, color: "#444", marginTop: 2 }}>
                      {new Date(act.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Intelligence Engine Status (Step 26) */}
          <div
            style={{
              padding: 14,
              borderRadius: 8,
              background: "linear-gradient(145deg, rgba(124, 58, 237, 0.08), #09090c)",
              border: "1px solid rgba(124, 58, 237, 0.25)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#7C3AED" }} />
                <span style={{ fontSize: 11, fontWeight: 700, color: "#A78BFA", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  AI Engine Status
                </span>
              </div>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 600,
                  padding: "1px 6px",
                  borderRadius: 3,
                  background: "rgba(16, 185, 129, 0.12)",
                  color: "#10B981",
                  border: "1px solid rgba(16, 185, 129, 0.25)",
                }}
              >
                ● Operational
              </span>
            </div>

            <p style={{ fontSize: 11.5, color: "#D4D4D8", margin: "0 0 10px 0", lineHeight: 1.5 }}>
              Continuous multi-factor policy scoring active. Multi-criteria analysis evaluates discounting variance, customer solvency, and margin thresholds.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 11.5,
                  color: "#A1A1AA",
                  padding: "5px 8px",
                  background: "#0c0c10",
                  borderRadius: 4,
                  border: "1px solid #1a1a22",
                }}
              >
                <span>Awaiting Analysis:</span>
                <span className="mono" style={{ color: "#F59E0B", fontWeight: 700 }}>
                  {requests.filter((r) => r.status === "Submitted").length} Requests
                </span>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 11.5,
                  color: "#A1A1AA",
                  padding: "5px 8px",
                  background: "#0c0c10",
                  borderRadius: 4,
                  border: "1px solid #1a1a22",
                }}
              >
                <span>Ready for Approval:</span>
                <span className="mono" style={{ color: "#A78BFA", fontWeight: 700 }}>
                  {requests.filter((r) => r.status === "Ready for Approval").length} Requests
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
