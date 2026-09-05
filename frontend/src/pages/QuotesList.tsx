import { useMemo, useState } from "react"
import { motion } from "framer-motion"
import { useRequests } from "../hooks/useRequests"
import { StatusBadge, EmptyState } from "../components/common"
import type { RequestPriority, RequestStatus, RequestType, Request } from "../types/request"

interface Props {
  onOpenQuote: (requestId?: string, mode?: "create" | "details" | "edit") => void
}

export default function QuotesList({ onOpenQuote }: Props) {
  const { requests } = useRequests()

  const [query, setQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("All")
  const [priorityFilter, setPriorityFilter] = useState<string>("All")
  const [typeFilter, setTypeFilter] = useState<string>("All")
  const [sortBy, setSortBy] = useState<"updated" | "amount" | "id">("updated")

  const statusOptions: string[] = [
    "All",
    "Draft",
    "Submitted",
    "In Review",
    "Ready for Approval",
    "Pending Approval",
    "Approved",
    "Changes Requested",
    "Rejected",
    "Completed",
  ]

  const priorityOptions: string[] = ["All", "Critical", "High", "Medium", "Low"]

  const typeOptions: string[] = [
    "All",
    "Commercial Exception",
    "Hardware Bundle",
    "Software License",
    "Custom SLA",
    "Standard Procurement",
    "Enterprise Expansion",
  ]

  const filteredRequests = useMemo(() => {
    return requests
      .filter((req) => {
        const matchesStatus =
          statusFilter === "All" ||
          req.status === statusFilter ||
          (statusFilter === "In Review" && req.status === "Under Review")

        const matchesPriority =
          priorityFilter === "All" || req.priority === priorityFilter

        const matchesType =
          typeFilter === "All" || req.requestType === typeFilter

        const q = query.trim().toLowerCase()
        const matchesQuery =
          !q ||
          req.referenceNumber.toLowerCase().includes(q) ||
          req.title.toLowerCase().includes(q) ||
          req.customer.toLowerCase().includes(q) ||
          req.owner.toLowerCase().includes(q) ||
          (req.requestType && req.requestType.toLowerCase().includes(q))

        return matchesStatus && matchesPriority && matchesType && matchesQuery
      })
      .sort((a, b) => {
        if (sortBy === "amount") {
          return (b.amount || 0) - (a.amount || 0)
        }
        if (sortBy === "id") {
          return b.referenceNumber.localeCompare(a.referenceNumber)
        }
        // default: updated
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      })
  }, [requests, statusFilter, priorityFilter, typeFilter, query, sortBy])

  const hasActiveFilters =
    query.trim() !== "" ||
    statusFilter !== "All" ||
    priorityFilter !== "All" ||
    typeFilter !== "All"

  const clearAllFilters = () => {
    setQuery("")
    setStatusFilter("All")
    setPriorityFilter("All")
    setTypeFilter("All")
  }

  const handleRowClick = (req: Request) => {
    onOpenQuote(req.id, "details")
  }

  return (
    <div style={{ padding: "28px", maxWidth: 1440, margin: "0 auto" }}>
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: 16,
          marginBottom: 22,
          flexWrap: "wrap",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "#7C3AED",
                background: "rgba(124, 58, 237, 0.12)",
                padding: "2px 8px",
                borderRadius: 4,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Requests Portfolio
            </span>
            <span style={{ fontSize: 11.5, color: "#666" }}>
              {requests.length} Total Requests
            </span>
          </div>
          <h1
            style={{
              color: "#fff",
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: "-.025em",
              margin: 0,
            }}
          >
            Requests
          </h1>
          <p style={{ color: "#666", fontSize: 13, margin: "4px 0 0" }}>
            Track, filter, and inspect incoming transaction requests across commercial exceptions, hardware, and SLA contracts.
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            onClick={() => onOpenQuote(undefined, "create")}
            className="df-btn-primary"
            style={{ padding: "8px 16px", fontSize: 12.5, display: "flex", alignItems: "center", gap: 6 }}
          >
            <span style={{ fontSize: 14 }}>+</span> Create Request
          </button>
        </div>
      </header>

      {/* Main Table Card */}
      <section className="df-card" style={{ overflow: "hidden", background: "#080808", border: "1px solid #1a1a1a" }}>
        {/* Filter Toolbar */}
        <div
          style={{
            padding: "14px 18px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
            borderBottom: "1px solid #161616",
          }}
        >
          {/* Top Filter Bar: Search + Priority + Type + Sort */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 12,
              flexWrap: "wrap",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 260 }}>
              <input
                aria-label="Search requests"
                className="df-input"
                placeholder="Search by ID, title, customer, owner..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                style={{
                  maxWidth: 340,
                  width: "100%",
                  height: 34,
                  fontSize: 12.5,
                  padding: "0 12px",
                }}
              />
              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={clearAllFilters}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#A1A1AA",
                    fontSize: 12,
                    textDecoration: "underline",
                    cursor: "pointer",
                    padding: "4px 8px",
                    whiteSpace: "nowrap",
                  }}
                >
                  Clear Filters
                </button>
              )}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              {/* Priority Select */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 11, color: "#666", textTransform: "uppercase" }}>Priority:</span>
                <select
                  className="df-input"
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  style={{ height: 32, padding: "0 8px", fontSize: 12, width: 110 }}
                >
                  {priorityOptions.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>

              {/* Type Select */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 11, color: "#666", textTransform: "uppercase" }}>Type:</span>
                <select
                  className="df-input"
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  style={{ height: 32, padding: "0 8px", fontSize: 12, width: 140 }}
                >
                  {typeOptions.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              {/* Sort By */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 11, color: "#666", textTransform: "uppercase" }}>Sort:</span>
                <select
                  className="df-input"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  style={{ height: 32, padding: "0 8px", fontSize: 12, width: 100 }}
                >
                  <option value="updated">Latest</option>
                  <option value="amount">Amount</option>
                  <option value="id">ID</option>
                </select>
              </div>
            </div>
          </div>

          {/* Status Tabs Bar */}
          <div
            style={{
              display: "flex",
              gap: 4,
              overflowX: "auto",
              paddingBottom: 2,
            }}
          >
            {statusOptions.map((status) => {
              const isActive = statusFilter === status
              return (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  style={{
                    background: isActive ? "#fff" : "#111",
                    color: isActive ? "#000" : "#888",
                    border: `1px solid ${isActive ? "#fff" : "#222"}`,
                    borderRadius: 5,
                    padding: "5px 10px",
                    fontSize: 11.5,
                    fontWeight: 600,
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    transition: "all 0.12s ease",
                  }}
                >
                  {status}
                </button>
              )
            })}
          </div>
        </div>

        {/* Requests Table */}
        <div style={{ overflowX: "auto" }}>
          {filteredRequests.length > 0 ? (
            <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 920 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #161616" }}>
                  {[
                    "Request ID",
                    "Title & Type",
                    "Customer",
                    "Amount",
                    "Priority",
                    "Status",
                    "Requester",
                    "Updated",
                    "",
                  ].map((label) => (
                    <th
                      key={label}
                      style={{
                        textAlign: "left",
                        color: "#555",
                        fontSize: 10.5,
                        padding: "11px 16px",
                        textTransform: "uppercase",
                        letterSpacing: ".06em",
                        fontWeight: 600,
                      }}
                    >
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRequests.map((req, i) => (
                  <motion.tr
                    key={req.id}
                    onClick={() => handleRowClick(req)}
                    whileHover={{ background: "rgba(255,255,255,.025)" }}
                    className="table-row"
                    style={{
                      cursor: "pointer",
                      borderBottom:
                        i < filteredRequests.length - 1 ? "1px solid #121216" : "none",
                      transition: "background 0.12s ease",
                    }}
                  >
                    <td style={{ padding: "12px 16px" }}>
                      <span
                        className="mono"
                        style={{
                          color: "#eee",
                          fontSize: 12,
                          fontWeight: 600,
                          background: "#141418",
                          border: "1px solid #22222a",
                          padding: "2px 6px",
                          borderRadius: 4,
                        }}
                      >
                        {req.referenceNumber}
                      </span>
                    </td>

                    <td style={{ padding: "12px 16px", maxWidth: 260 }}>
                      <div
                        style={{
                          color: "#fff",
                          fontSize: 12.5,
                          fontWeight: 600,
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

                    <td style={{ color: "#D4D4D8", fontSize: 12.5, fontWeight: 500, padding: "12px 16px" }}>
                      {req.customer}
                    </td>

                    <td className="mono" style={{ color: "#fff", fontSize: 12.5, fontWeight: 600, padding: "12px 16px" }}>
                      {req.formattedAmount}
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

                    <td style={{ color: "#71717A", padding: "12px 16px", fontSize: 12 }}>
                      {req.owner}
                    </td>

                    <td style={{ color: "#555", padding: "12px 16px", fontSize: 11.5 }}>
                      {new Date(req.updatedAt).toLocaleDateString()}
                    </td>

                    <td style={{ color: "#555", padding: "12px 16px", textAlign: "right" }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRowClick(req)
                        }}
                        style={{
                          background: "none",
                          border: "none",
                          color: "#7C3AED",
                          cursor: "pointer",
                          fontSize: 12,
                          fontWeight: 600,
                          padding: 4,
                        }}
                      >
                        View &rarr;
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: "32px 20px" }}>
              <EmptyState
                title="No requests match your current filters"
                description="Try changing your search terms, status, or priority filters to locate requests."
                actionLabel="Clear All Filters"
                onAction={clearAllFilters}
              />
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
