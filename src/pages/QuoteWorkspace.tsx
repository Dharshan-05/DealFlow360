import { useState, useMemo, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { AnimatedNumber } from "../lib/motion"
import { useRequests } from "../hooks/useRequests"
import { useAI } from "../hooks/useAI"
import { useExecution } from "../hooks/useExecution"
import { useTransactions } from "../hooks/useTransactions"
import { StatusBadge } from "../components/common"
import AIAnalysisModal from "../components/ai/AIAnalysisModal"
import ExecutionModal from "../components/execution/ExecutionModal"
import ExecutionDrawer from "../components/execution/ExecutionDrawer"
import TransactionDrawer from "../components/transactions/TransactionDrawer"
import type { Request, RequestItem, RequestPriority, RequestType } from "../types/request"
import type { Execution } from "../types/execution"
import type { Transaction } from "../types/transaction"

interface Props {
  requestId?: string
  initialMode?: "create" | "details" | "edit"
  onBack?: () => void
}

function fmtINR(n: number) {
  return "₹" + Math.round(n).toLocaleString("en-IN")
}

const defaultProducts = [
  { name: "Enterprise Laptop Pro 14", sku: "LTP-14-2026", price: 120000, limit: 15 },
  { name: "Onsite Setup Service", sku: "ONS-SETUP", price: 450000, limit: 10 },
  { name: "Extended Warranty & SLA", sku: "WAR-2YR", price: 18000, limit: 15 },
  { name: "CloudEdge Switch 48P", sku: "CES-48P-GX", price: 219999, limit: 10 },
  { name: "Developer Toolchain Suite", sku: "DTS-ENT-2026", price: 89999, limit: 10 },
  { name: "DealFlow360 Platform License", sku: "DF360-ENT-LIC", price: 3999999, limit: 10 },
]

export default function QuoteWorkspace({
  requestId,
  initialMode = "details",
  onBack,
}: Props) {
  const { requests, getRequestById, createDraft, submitRequest, updateRequest, addDocument } =
    useRequests()

  // Determine current active request
  const activeRequest = useMemo(() => {
    if (!requestId || requestId === "new") return null
    return getRequestById(requestId) || requests.find((r) => r.id === requestId) || null
  }, [requestId, requests, getRequestById])

  const [mode, setMode] = useState<"create" | "details" | "edit">(() => {
    if (!requestId || requestId === "new" || !activeRequest) return "create"
    return initialMode
  })

  // Sync mode if requestId changes
  useEffect(() => {
    if (!requestId || requestId === "new") {
      setMode("create")
    } else if (activeRequest) {
      setMode(initialMode)
    }
  }, [requestId, activeRequest, initialMode])

  // Form State for Create / Edit
  const [title, setTitle] = useState("")
  const [requestType, setRequestType] = useState<RequestType>("Commercial Exception")
  const [customer, setCustomer] = useState("")
  const [customerContact, setCustomerContact] = useState("")
  const [owner, setOwner] = useState("Arjun Sharma")
  const [priority, setPriority] = useState<RequestPriority>("Medium")
  const [dueDate, setDueDate] = useState("")
  const [description, setDescription] = useState("")
  const [businessJustification, setBusinessJustification] = useState("")
  const [expectedOutcome, setExpectedOutcome] = useState("")
  const [items, setItems] = useState<RequestItem[]>([])

  // Form validation errors
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [statusNotice, setStatusNotice] = useState<{ type: "success" | "error"; message: string } | null>(null)

  // Document upload simulator state
  const [docNameInput, setDocNameInput] = useState("")
  const [showDocModal, setShowDocModal] = useState(false)
  const [aiModalOpen, setAiModalOpen] = useState(false)

  const { analysis: activeAiAnalysis } = useAI(activeRequest)

  const {
    startExecution,
    retryExecution,
    createOrGetExecution,
    getExecutionForRequest,
  } = useExecution()

  const {
    getTransactionByRequestId,
    getTransactionById,
  } = useTransactions()

  const [executionModalOpen, setExecutionModalOpen] = useState(false)
  const [activeExecutionForModal, setActiveExecutionForModal] = useState<Execution | null>(null)
  const [selectedDrawerExecution, setSelectedDrawerExecution] = useState<Execution | null>(null)
  const [selectedDrawerTransaction, setSelectedDrawerTransaction] = useState<Transaction | null>(null)

  const activeExecution = useMemo(() => {
    if (!activeRequest) return null
    return getExecutionForRequest(activeRequest.id) || null
  }, [activeRequest, getExecutionForRequest, executionModalOpen])

  const activeTransaction = useMemo(() => {
    if (!activeRequest) return null
    return getTransactionByRequestId(activeRequest.id) || null
  }, [activeRequest, getTransactionByRequestId, executionModalOpen])

  const handleOpenExecution = () => {
    if (!activeRequest) return
    const exec = createOrGetExecution(activeRequest)
    setActiveExecutionForModal(exec)
    setExecutionModalOpen(true)
  }
  useEffect(() => {
    if (activeRequest && (mode === "edit" || mode === "details")) {
      setTitle(activeRequest.title)
      setRequestType(activeRequest.requestType || "Commercial Exception")
      setCustomer(activeRequest.customer)
      setCustomerContact(activeRequest.customerContact || "")
      setOwner(activeRequest.owner || "Arjun Sharma")
      setPriority(activeRequest.priority || "Medium")
      setDueDate(activeRequest.dueDate || "")
      setDescription(activeRequest.description || "")
      setBusinessJustification(activeRequest.businessJustification || "")
      setExpectedOutcome(activeRequest.expectedOutcome || "")
      setItems(activeRequest.items ? [...activeRequest.items] : [])
    } else if (mode === "create") {
      setTitle("")
      setRequestType("Commercial Exception")
      setCustomer("")
      setCustomerContact("")
      setOwner("Arjun Sharma")
      setPriority("Medium")
      setDueDate("")
      setDescription("")
      setBusinessJustification("")
      setExpectedOutcome("")
      setItems([
        {
          id: 1,
          name: "Enterprise Laptop Pro 14",
          sku: "LTP-14-2026",
          quantity: 2,
          unitPrice: 120000,
          discountPercent: 10,
          policyLimitPercent: 15,
          subtotal: 216000,
        },
      ])
    }
  }, [activeRequest, mode])

  // Items manipulation
  const updateItemQty = (id: string | number, qty: number) => {
    setItems((prev) =>
      prev.map((i) => {
        if (i.id === id) {
          const newQty = Math.max(1, qty)
          const discount = i.discountPercent || 0
          const subtotal = i.unitPrice * newQty * (1 - discount / 100)
          return { ...i, quantity: newQty, subtotal }
        }
        return i
      })
    )
  }

  const updateItemDiscount = (id: string | number, discount: number) => {
    setItems((prev) =>
      prev.map((i) => {
        if (i.id === id) {
          const safeDiscount = Math.max(0, Math.min(60, discount))
          const subtotal = i.unitPrice * i.quantity * (1 - safeDiscount / 100)
          return { ...i, discountPercent: safeDiscount, subtotal }
        }
        return i
      })
    )
  }

  const removeItem = (id: string | number) => {
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  const addItemFromPreset = (preset: typeof defaultProducts[0]) => {
    const newItem: RequestItem = {
      id: Date.now(),
      name: preset.name,
      sku: preset.sku,
      quantity: 1,
      unitPrice: preset.price,
      discountPercent: 5,
      policyLimitPercent: preset.limit,
      subtotal: preset.price * 0.95,
    }
    setItems((prev) => [...prev, newItem])
  }

  const subtotal = useMemo(
    () => items.reduce((sum, i) => sum + (i.subtotal || i.unitPrice * i.quantity), 0),
    [items]
  )
  const gst = subtotal * 0.18
  const total = subtotal + gst

  // Actions
  const handleSaveDraft = () => {
    setErrors({})
    setStatusNotice(null)

    if (!title.trim()) {
      setErrors({ title: "Please provide a request title to save as draft." })
      return
    }

    const payload: Partial<Request> = {
      id: activeRequest?.id,
      title: title.trim(),
      requestType,
      customer: customer.trim() || "Unassigned Account",
      customerContact,
      owner,
      priority,
      dueDate,
      description,
      businessJustification,
      expectedOutcome,
      items,
      amount: subtotal,
      formattedAmount: fmtINR(subtotal),
    }

    const result = createDraft(payload, owner)
    if (result.errors) {
      setErrors(result.errors)
      return
    }

    setStatusNotice({ type: "success", message: `Draft saved successfully! (Request ID: ${result.request.referenceNumber})` })
    setMode("details")
  }

  const handleSubmit = () => {
    setErrors({})
    setStatusNotice(null)

    const payload: Partial<Request> = {
      id: activeRequest?.id,
      title: title.trim(),
      requestType,
      customer: customer.trim(),
      customerContact,
      owner,
      priority,
      dueDate,
      description: description.trim(),
      businessJustification: businessJustification.trim(),
      expectedOutcome: expectedOutcome.trim(),
      items,
      amount: subtotal,
      formattedAmount: fmtINR(subtotal),
    }

    const result = submitRequest(payload, owner)
    if (!result.success && result.errors) {
      setErrors(result.errors)
      setStatusNotice({ type: "error", message: "Please resolve the validation errors below before submitting." })
      return
    }

    if (result.request) {
      setStatusNotice({ type: "success", message: `Request ${result.request.referenceNumber} has been officially submitted for review!` })
      setMode("details")
    }
  }

  const handleAttachDocument = (e: React.FormEvent) => {
    e.preventDefault()
    if (!docNameInput.trim() || !activeRequest) return
    addDocument(activeRequest.id, docNameInput.trim())
    setDocNameInput("")
    setShowDocModal(false)
  }

  // Visual status step calculation for progress bar
  const getStepIndex = (status?: string) => {
    switch (status) {
      case "Draft":
        return 0
      case "Submitted":
        return 1
      case "In Review":
      case "Under Review":
      case "Pending Approval":
      case "Ready for Approval":
        return 2
      case "Approved":
        return 3
      case "Completed":
        return 4
      case "Rejected":
        return 2 // stops at review
      case "Changes Requested":
        return 0 // returns to draft revision state
      default:
        return 1
    }
  }

  const currentStep = getStepIndex(activeRequest?.status)

  // -------------------------------------------------------------
  // RENDER: CREATE or EDIT FORM
  // -------------------------------------------------------------
  if (mode === "create" || mode === "edit") {
    return (
      <div style={{ padding: "24px 28px", maxWidth: 1200, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div>
            <button
              onClick={() => {
                if (activeRequest) setMode("details")
                else if (onBack) onBack()
              }}
              style={{
                background: "none",
                border: "none",
                color: "#71717A",
                cursor: "pointer",
                fontSize: 12.5,
                display: "flex",
                alignItems: "center",
                gap: 5,
                padding: 0,
                marginBottom: 6,
              }}
            >
              &larr; Back
            </button>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: "#fff", margin: 0, letterSpacing: "-0.02em" }}>
              {mode === "create" ? "Create New Request" : `Edit Request: ${activeRequest?.referenceNumber}`}
            </h1>
            <p style={{ fontSize: 13, color: "#666", margin: "4px 0 0" }}>
              Provide request specifications, business justification, and required line items.
            </p>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button
              type="button"
              onClick={handleSaveDraft}
              className="df-btn-secondary"
              style={{ padding: "8px 16px", fontSize: 12.5 }}
            >
              Save as Draft
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="df-btn-primary"
              style={{ padding: "8px 18px", fontSize: 12.5 }}
            >
              Submit Request &rarr;
            </button>
          </div>
        </div>

        {/* Global Notices */}
        {statusNotice && (
          <div
            style={{
              padding: "10px 14px",
              borderRadius: 6,
              marginBottom: 16,
              fontSize: 12.5,
              background: statusNotice.type === "success" ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
              border: `1px solid ${statusNotice.type === "success" ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
              color: statusNotice.type === "success" ? "#34D399" : "#F87171",
            }}
          >
            {statusNotice.message}
          </div>
        )}

        {/* Form Container */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Section 1: Request Information */}
          <div className="df-card" style={{ padding: "20px 22px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: "#fff", marginBottom: 4 }}>
              1. Request Information
            </div>
            <p style={{ fontSize: 12, color: "#666", margin: "0 0 16px 0" }}>
              Core identifiers, type categorization, and customer context.
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Request Title <span style={{ color: "#EF4444" }}>*</span>
                </label>
                <input
                  type="text"
                  className="df-input"
                  placeholder="e.g. Enterprise Hardware & Core Switch Expansion"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  style={{ width: "100%", height: 36, fontSize: 13 }}
                />
                {errors.title && <div style={{ color: "#EF4444", fontSize: 11, marginTop: 4 }}>{errors.title}</div>}
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Request Type <span style={{ color: "#EF4444" }}>*</span>
                </label>
                <select
                  className="df-input"
                  value={requestType}
                  onChange={(e) => setRequestType(e.target.value as RequestType)}
                  style={{ width: "100%", height: 36, fontSize: 13 }}
                >
                  <option value="Commercial Exception">Commercial Exception</option>
                  <option value="Hardware Bundle">Hardware Bundle</option>
                  <option value="Software License">Software License</option>
                  <option value="Custom SLA">Custom SLA</option>
                  <option value="Standard Procurement">Standard Procurement</option>
                  <option value="Enterprise Expansion">Enterprise Expansion</option>
                </select>
                {errors.requestType && <div style={{ color: "#EF4444", fontSize: 11, marginTop: 4 }}>{errors.requestType}</div>}
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Customer / Account Name <span style={{ color: "#EF4444" }}>*</span>
                </label>
                <input
                  type="text"
                  className="df-input"
                  placeholder="e.g. Acme Corporation"
                  value={customer}
                  onChange={(e) => setCustomer(e.target.value)}
                  style={{ width: "100%", height: 36, fontSize: 13 }}
                />
                {errors.customer && <div style={{ color: "#EF4444", fontSize: 11, marginTop: 4 }}>{errors.customer}</div>}
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Customer Contact
                </label>
                <input
                  type="text"
                  className="df-input"
                  placeholder="e.g. Rajesh Kumar"
                  value={customerContact}
                  onChange={(e) => setCustomerContact(e.target.value)}
                  style={{ width: "100%", height: 36, fontSize: 13 }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Priority <span style={{ color: "#EF4444" }}>*</span>
                </label>
                <select
                  className="df-input"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as RequestPriority)}
                  style={{ width: "100%", height: 36, fontSize: 13 }}
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Target Due Date
                </label>
                <input
                  type="date"
                  className="df-input"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  style={{ width: "100%", height: 36, fontSize: 13, colorScheme: "dark" }}
                />
              </div>
            </div>
          </div>

          {/* Section 2: Business Justification */}
          <div className="df-card" style={{ padding: "20px 22px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: "#fff", marginBottom: 4 }}>
              2. Business Information
            </div>
            <p style={{ fontSize: 12, color: "#666", margin: "0 0 16px 0" }}>
              Provide clear narrative on why this request is required and the business value created.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Detailed Description <span style={{ color: "#EF4444" }}>*</span>
                </label>
                <textarea
                  className="df-input"
                  rows={3}
                  placeholder="Describe scope, required deliverables, and technical requirements..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  style={{ width: "100%", padding: "10px", fontSize: 13, resize: "vertical" }}
                />
                {errors.description && <div style={{ color: "#EF4444", fontSize: 11, marginTop: 4 }}>{errors.description}</div>}
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Business Justification <span style={{ color: "#EF4444" }}>*</span>
                </label>
                <textarea
                  className="df-input"
                  rows={2}
                  placeholder="Explain why non-standard pricing or special approvals are justified..."
                  value={businessJustification}
                  onChange={(e) => setBusinessJustification(e.target.value)}
                  style={{ width: "100%", padding: "10px", fontSize: 13, resize: "vertical" }}
                />
                {errors.businessJustification && (
                  <div style={{ color: "#EF4444", fontSize: 11, marginTop: 4 }}>{errors.businessJustification}</div>
                )}
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717A", textTransform: "uppercase", marginBottom: 5 }}>
                  Expected Strategic Outcome
                </label>
                <input
                  type="text"
                  className="df-input"
                  placeholder="e.g. 3-year contract lock-in with expansion potential"
                  value={expectedOutcome}
                  onChange={(e) => setExpectedOutcome(e.target.value)}
                  style={{ width: "100%", height: 36, fontSize: 13 }}
                />
              </div>
            </div>
          </div>

          {/* Section 3: Request Items / Financials */}
          <div className="df-card" style={{ padding: "20px 22px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#fff", margin: 0 }}>
                  3. Request Items & Valuation
                </div>
                <div style={{ fontSize: 12, color: "#666", marginTop: 2 }}>
                  Add products, services, or license line items to this request.
                </div>
              </div>

              {/* Quick Add Presets */}
              <div style={{ display: "flex", gap: 6 }}>
                <span style={{ fontSize: 11, color: "#555", alignSelf: "center" }}>Quick Add:</span>
                {defaultProducts.slice(0, 3).map((p) => (
                  <button
                    key={p.sku}
                    type="button"
                    onClick={() => addItemFromPreset(p)}
                    style={{
                      background: "#141418",
                      border: "1px solid #27272e",
                      borderRadius: 4,
                      padding: "4px 8px",
                      color: "#A1A1AA",
                      fontSize: 11,
                      cursor: "pointer",
                    }}
                  >
                    + {p.name.split(" ")[0]}
                  </button>
                ))}
              </div>
            </div>

            {items.length > 0 ? (
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", marginBottom: 16 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #1a1a1a" }}>
                    {["Product / Service", "Qty", "Unit Price", "Discount %", "Subtotal", ""].map((h) => (
                      <th key={h} style={{ padding: "8px 10px", fontSize: 11, color: "#555", textTransform: "uppercase" }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((it) => (
                    <tr key={it.id} style={{ borderBottom: "1px solid #121214" }}>
                      <td style={{ padding: "10px" }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "#fff" }}>{it.name}</div>
                        <div style={{ fontSize: 11, color: "#555" }} className="mono">
                          {it.sku}
                        </div>
                      </td>
                      <td style={{ padding: "10px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <button
                            type="button"
                            onClick={() => updateItemQty(it.id, it.quantity - 1)}
                            style={{ width: 22, height: 22, background: "#18181b", border: "1px solid #27272a", color: "#fff", cursor: "pointer", borderRadius: 3 }}
                          >
                            -
                          </button>
                          <span style={{ fontSize: 12, color: "#fff", width: 24, textAlign: "center" }} className="mono">
                            {it.quantity}
                          </span>
                          <button
                            type="button"
                            onClick={() => updateItemQty(it.id, it.quantity + 1)}
                            style={{ width: 22, height: 22, background: "#18181b", border: "1px solid #27272a", color: "#fff", cursor: "pointer", borderRadius: 3 }}
                          >
                            +
                          </button>
                        </div>
                      </td>
                      <td style={{ padding: "10px", fontSize: 12.5, color: "#D4D4D8" }} className="mono">
                        {fmtINR(it.unitPrice)}
                      </td>
                      <td style={{ padding: "10px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <input
                            type="number"
                            className="df-input"
                            value={it.discountPercent || 0}
                            onChange={(e) => updateItemDiscount(it.id, parseFloat(e.target.value) || 0)}
                            style={{ width: 54, height: 28, fontSize: 12, padding: "0 6px" }}
                          />
                          <span style={{ fontSize: 11, color: "#777" }}>%</span>
                        </div>
                      </td>
                      <td style={{ padding: "10px", fontSize: 13, fontWeight: 600, color: "#fff" }} className="mono">
                        {fmtINR(it.subtotal || it.unitPrice * it.quantity)}
                      </td>
                      <td style={{ padding: "10px", textAlign: "right" }}>
                        <button
                          type="button"
                          onClick={() => removeItem(it.id)}
                          style={{ background: "none", border: "none", color: "#EF4444", cursor: "pointer", fontSize: 13 }}
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ padding: "20px", textAlign: "center", color: "#555", fontSize: 12.5, border: "1px dashed #222", borderRadius: 6, marginBottom: 16 }}>
                No items added yet. Use the quick-add buttons above.
              </div>
            )}

            {/* Financial Summary */}
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <div style={{ width: 260, display: "flex", flexDirection: "column", gap: 8, padding: "12px 16px", background: "#0d0d10", borderRadius: 6, border: "1px solid #1e1e24" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#71717A" }}>
                  <span>Subtotal</span>
                  <span className="mono" style={{ color: "#E4E4E7" }}>{fmtINR(subtotal)}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#71717A" }}>
                  <span>GST (18%)</span>
                  <span className="mono" style={{ color: "#E4E4E7" }}>{fmtINR(gst)}</span>
                </div>
                <div style={{ height: 1, background: "#1e1e24" }} />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, fontWeight: 700, color: "#fff" }}>
                  <span>Total Value</span>
                  <span className="mono">{fmtINR(total)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // -------------------------------------------------------------
  // RENDER: REQUEST DETAILS VIEW
  // -------------------------------------------------------------
  if (!activeRequest) {
    return (
      <div style={{ padding: 40, textAlign: "center" }}>
        <div style={{ color: "#fff", fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
          Request Not Found
        </div>
        <p style={{ color: "#71717A", fontSize: 13, marginBottom: 16 }}>
          The requested transaction record does not exist or has been removed.
        </p>
        <button onClick={onBack} className="df-btn-primary" style={{ padding: "8px 16px", fontSize: 13 }}>
          Return to Request List
        </button>
      </div>
    )
  }

  const isEditable = activeRequest.status === "Draft" || activeRequest.status === "Changes Requested"

  return (
    <div style={{ padding: "24px 28px", maxWidth: 1440, margin: "0 auto" }}>
      {/* Top Breadcrumb & Status Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 20,
          flexWrap: "wrap",
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <button
              onClick={onBack}
              style={{
                background: "none",
                border: "none",
                color: "#71717A",
                cursor: "pointer",
                fontSize: 12,
                display: "flex",
                alignItems: "center",
                gap: 4,
                padding: 0,
              }}
            >
              &larr; Requests
            </button>
            <span style={{ color: "#333" }}>/</span>
            <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: "#fff" }}>
              {activeRequest.referenceNumber}
            </span>
            <StatusBadge status={activeRequest.status} size="sm" showDot />
            <span
              style={{
                fontSize: 10.5,
                fontWeight: 700,
                padding: "1px 6px",
                borderRadius: 4,
                textTransform: "uppercase",
                background: "rgba(124, 58, 237, 0.12)",
                color: "#A78BFA",
                border: "1px solid rgba(124, 58, 237, 0.25)",
              }}
            >
              {activeRequest.requestType}
            </span>
          </div>

          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#fff", margin: 0, letterSpacing: "-0.025em" }}>
            {activeRequest.title}
          </h1>

          <p style={{ fontSize: 13, color: "#71717A", margin: "4px 0 0" }}>
            Account: <span style={{ color: "#fff", fontWeight: 600 }}>{activeRequest.customer}</span> · Owner:{" "}
            <span style={{ color: "#D4D4D8" }}>{activeRequest.owner}</span> · Created{" "}
            {new Date(activeRequest.createdAt).toLocaleDateString()}
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {isEditable ? (
            <>
              <button
                onClick={() => setMode("edit")}
                className="df-btn-secondary"
                style={{ padding: "8px 14px", fontSize: 12.5 }}
              >
                {activeRequest.status === "Changes Requested" ? "Revise Proposal" : "Edit Draft"}
              </button>
              <button
                onClick={() => {
                  submitRequest(activeRequest, activeRequest.owner)
                  setStatusNotice({ type: "success", message: "Request successfully resubmitted!" })
                }}
                className="df-btn-primary"
                style={{ padding: "8px 16px", fontSize: 12.5 }}
              >
                Submit Request &rarr;
              </button>
            </>
          ) : activeRequest.status === "Ready for Approval" ? (
            <div
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                background: "rgba(124, 58, 237, 0.12)",
                border: "1px solid rgba(124, 58, 237, 0.3)",
                fontSize: 12,
                color: "#A78BFA",
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontWeight: 600,
              }}
            >
              <span>✦</span> Approval Required — Pending Review
            </div>
          ) : activeRequest.status === "Approved" ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  padding: "6px 14px",
                  borderRadius: 6,
                  background: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  fontSize: 12,
                  color: "#10B981",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  fontWeight: 600,
                }}
              >
                <span>✓</span> Approved
              </div>
              <button
                onClick={handleOpenExecution}
                style={{
                  padding: "8px 18px",
                  borderRadius: 6,
                  background: "linear-gradient(135deg, #7c3aed, #6d28d9)",
                  border: "1px solid rgba(139, 92, 246, 0.4)",
                  color: "#fff",
                  fontWeight: 600,
                  fontSize: 12.5,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  boxShadow: "0 4px 14px rgba(124, 58, 237, 0.25)",
                }}
              >
                <span>▶</span> Start Execution &rarr;
              </button>
            </div>
          ) : activeRequest.status === "Completed" ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  padding: "6px 14px",
                  borderRadius: 6,
                  background: "rgba(16, 185, 129, 0.15)",
                  border: "1px solid rgba(16, 185, 129, 0.4)",
                  fontSize: 12,
                  color: "#34D399",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  fontWeight: 600,
                }}
              >
                <span>✓</span> Execution Completed
              </div>
              {activeTransaction && (
                <button
                  onClick={() => setSelectedDrawerTransaction(activeTransaction)}
                  className="df-btn-secondary"
                  style={{ padding: "8px 14px", fontSize: 12.5 }}
                >
                  View Transaction ({activeTransaction.transactionNumber})
                </button>
              )}
            </div>
          ) : activeRequest.status === "Rejected" ? (
            <div
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                fontSize: 12,
                color: "#EF4444",
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontWeight: 600,
              }}
            >
              <span>✕</span> Rejected
            </div>
          ) : (
            <div
              style={{
                padding: "6px 12px",
                borderRadius: 6,
                background: "#111116",
                border: "1px solid #22222a",
                fontSize: 12,
                color: "#A1A1AA",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#F59E0B" }} />
              Request Locked ({activeRequest.status})
            </div>
          )}
        </div>
      </div>

      {/* Notices */}
      {statusNotice && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 6,
            marginBottom: 16,
            fontSize: 12.5,
            background: statusNotice.type === "success" ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
            border: `1px solid ${statusNotice.type === "success" ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
            color: statusNotice.type === "success" ? "#34D399" : "#F87171",
          }}
        >
          {statusNotice.message}
        </div>
      )}

      {activeRequest.status === "Changes Requested" && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: 8,
            marginBottom: 16,
            fontSize: 13,
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.3)",
            color: "#FBBF24",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 16 }}>⚠</span>
            <div>
              <div style={{ fontWeight: 600, color: "#fff" }}>
                Commercial Revisions Requested
              </div>
              <div style={{ fontSize: 12, color: "#D4D4D8", marginTop: 2 }}>
                The commercial approval committee returned this deal for revisions. Click "Revise Proposal" to adjust discount, pricing, or attached documentation and resubmit.
              </div>
            </div>
          </div>
          <button
            onClick={() => setMode("edit")}
            style={{
              padding: "6px 14px",
              borderRadius: 6,
              background: "#F59E0B",
              color: "#000",
              fontWeight: 600,
              fontSize: 12,
              border: "none",
              cursor: "pointer",
              flexShrink: 0,
            }}
          >
            Revise Proposal &rarr;
          </button>
        </div>
      )}

      {activeRequest.status === "Approved" && (
        <div
          style={{
            padding: "14px 18px",
            borderRadius: 8,
            marginBottom: 16,
            background: "linear-gradient(90deg, rgba(124, 58, 237, 0.08), rgba(16, 185, 129, 0.08))",
            border: "1px solid rgba(139, 92, 246, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: 8,
                background: "rgba(124, 58, 237, 0.2)",
                border: "1px solid rgba(139, 92, 246, 0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#c084fc",
                fontSize: 16,
              }}
            >
              ⚡
            </div>
            <div>
              <div style={{ fontWeight: 600, color: "#fff", fontSize: 13.5 }}>
                Commercial Approval Granted — Ready for ERP Execution
              </div>
              <div style={{ fontSize: 12, color: "#a1a1aa", marginTop: 2 }}>
                Commercial sign-off confirmed. Click to simulate the automated multi-stage pipeline and create the demo Odoo Sales Order.
              </div>
            </div>
          </div>
          <button
            onClick={handleOpenExecution}
            style={{
              padding: "8px 18px",
              borderRadius: 6,
              background: "linear-gradient(135deg, #7c3aed, #6d28d9)",
              border: "1px solid rgba(139, 92, 246, 0.4)",
              color: "#fff",
              fontWeight: 600,
              fontSize: 12.5,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              boxShadow: "0 4px 14px rgba(124, 58, 237, 0.3)",
            }}
          >
            <span>▶</span> Start Execution Pipeline &rarr;
          </button>
        </div>
      )}

      {activeRequest.status === "Completed" && (
        <div
          style={{
            padding: "14px 18px",
            borderRadius: 8,
            marginBottom: 16,
            background: "rgba(16, 185, 129, 0.06)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: 8,
                background: "rgba(16, 185, 129, 0.15)",
                border: "1px solid rgba(16, 185, 129, 0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#10b981",
                fontSize: 16,
              }}
            >
              ✓
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontWeight: 600, color: "#fff", fontSize: 13.5 }}>
                  ERP Execution Completed &amp; Synchronized
                </span>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    background: "rgba(234, 179, 8, 0.15)",
                    border: "1px solid rgba(234, 179, 8, 0.3)",
                    color: "#facc15",
                    padding: "1px 6px",
                    borderRadius: 4,
                  }}
                >
                  Simulated Odoo Operation
                </span>
              </div>
              <div style={{ fontSize: 12, color: "#a1a1aa", marginTop: 3 }}>
                Simulated Odoo Ref:{" "}
                <strong style={{ color: "#38bdf8", fontFamily: "monospace" }}>
                  {activeRequest.odooReference || (activeExecution?.odooOperation?.reference ?? "SO-2026-0841")}
                </strong>
                {activeTransaction && (
                  <>
                    {" "}· Transaction:{" "}
                    <strong style={{ color: "#10b981", fontFamily: "monospace" }}>
                      {activeTransaction.transactionNumber}
                    </strong>
                  </>
                )}
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {activeExecution && (
              <button
                onClick={() => setSelectedDrawerExecution(activeExecution)}
                className="df-btn-secondary"
                style={{ padding: "7px 13px", fontSize: 12 }}
              >
                Inspect Pipeline
              </button>
            )}
            {activeTransaction && (
              <button
                onClick={() => setSelectedDrawerTransaction(activeTransaction)}
                style={{
                  padding: "7px 15px",
                  borderRadius: 6,
                  background: "#0d2d1a",
                  border: "1px solid rgba(16, 185, 129, 0.4)",
                  color: "#34d399",
                  fontWeight: 600,
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                View Transaction Trace &rarr;
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main 2-Column Detail Layout */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 380px",
          gap: 20,
        }}
      >
        {/* Left Column: Business Info + Line Items + Documents */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Business Overview Card */}
          <div className="df-card" style={{ padding: "20px 22px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: "#fff", marginBottom: 12 }}>
              Business Scope & Justification
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#666", textTransform: "uppercase", marginBottom: 3 }}>
                  Description
                </div>
                <div style={{ fontSize: 13, color: "#E4E4E7", lineHeight: 1.55 }}>
                  {activeRequest.description || "No description provided."}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#666", textTransform: "uppercase", marginBottom: 3 }}>
                  Commercial Justification
                </div>
                <div style={{ fontSize: 13, color: "#D4D4D8", lineHeight: 1.55 }}>
                  {activeRequest.businessJustification || "Standard business exception requirements."}
                </div>
              </div>

              {activeRequest.expectedOutcome && (
                <div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#666", textTransform: "uppercase", marginBottom: 3 }}>
                    Expected Outcome
                  </div>
                  <div style={{ fontSize: 13, color: "#A1A1AA", lineHeight: 1.55 }}>
                    {activeRequest.expectedOutcome}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Line Items Table */}
          <div className="df-card" style={{ overflow: "hidden", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div
              style={{
                padding: "14px 18px",
                borderBottom: "1px solid #161616",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>
                  Line Items & Pricing
                </div>
                <div style={{ fontSize: 11.5, color: "#555", marginTop: 2 }}>
                  {activeRequest.items?.length || 0} product and service records
                </div>
              </div>
              <span className="mono" style={{ fontSize: 15, fontWeight: 700, color: "#fff" }}>
                {activeRequest.formattedAmount}
              </span>
            </div>

            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #141414" }}>
                  {["Item / SKU", "Qty", "Unit Price", "Discount", "Subtotal"].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "10px 16px",
                        fontSize: 10.5,
                        color: "#555",
                        textTransform: "uppercase",
                        letterSpacing: ".06em",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activeRequest.items && activeRequest.items.length > 0 ? (
                  activeRequest.items.map((it, idx) => (
                    <tr
                      key={it.id || idx}
                      style={{
                        borderBottom:
                          idx < (activeRequest.items?.length || 0) - 1 ? "1px solid #111" : "none",
                      }}
                    >
                      <td style={{ padding: "12px 16px" }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "#fff" }}>{it.name}</div>
                        <div style={{ fontSize: 11, color: "#666" }} className="mono">
                          {it.sku}
                        </div>
                        {it.notes && (
                          <div style={{ fontSize: 11, color: "#F59E0B", marginTop: 2 }}>
                            Note: {it.notes}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: "12px 16px", fontSize: 12.5, color: "#E4E4E7" }} className="mono">
                        {it.quantity}
                      </td>
                      <td style={{ padding: "12px 16px", fontSize: 12.5, color: "#A1A1AA" }} className="mono">
                        {fmtINR(it.unitPrice)}
                      </td>
                      <td style={{ padding: "12px 16px", fontSize: 12.5, color: "#F59E0B" }} className="mono">
                        {it.discountPercent || 0}%
                      </td>
                      <td style={{ padding: "12px 16px", fontSize: 13, fontWeight: 600, color: "#fff" }} className="mono">
                        {fmtINR(it.subtotal)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} style={{ padding: 24, textAlign: "center", color: "#555", fontSize: 12.5 }}>
                      No items specified on this request.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Documents Section (Step 17) */}
          <div className="df-card" style={{ padding: "20px 22px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>
                  Attached Documents
                </div>
                <div style={{ fontSize: 11.5, color: "#555", marginTop: 2 }}>
                  Commercial terms, contracts, and technical specifications
                </div>
              </div>

              <button
                onClick={() => setShowDocModal(true)}
                className="df-btn-secondary"
                style={{ padding: "6px 12px", fontSize: 11.5 }}
              >
                + Attach Document
              </button>
            </div>

            {/* Doc Modal Simulator */}
            {showDocModal && (
              <form
                onSubmit={handleAttachDocument}
                style={{
                  padding: 12,
                  borderRadius: 6,
                  background: "#111116",
                  border: "1px solid #22222a",
                  marginBottom: 14,
                  display: "flex",
                  gap: 8,
                }}
              >
                <input
                  type="text"
                  placeholder="Document filename (e.g. Master_Agreement.pdf)"
                  className="df-input"
                  value={docNameInput}
                  onChange={(e) => setDocNameInput(e.target.value)}
                  style={{ flex: 1, height: 32, fontSize: 12 }}
                  required
                />
                <button type="submit" className="df-btn-primary" style={{ padding: "0 12px", fontSize: 12 }}>
                  Add
                </button>
                <button
                  type="button"
                  onClick={() => setShowDocModal(false)}
                  style={{ background: "none", border: "none", color: "#777", cursor: "pointer", fontSize: 12 }}
                >
                  Cancel
                </button>
              </form>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {activeRequest.documents && activeRequest.documents.length > 0 ? (
                activeRequest.documents.map((doc) => (
                  <div
                    key={doc.id}
                    style={{
                      padding: "10px 12px",
                      borderRadius: 6,
                      background: "#0d0d10",
                      border: "1px solid #1e1e24",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <div
                        style={{
                          width: 28,
                          height: 28,
                          borderRadius: 4,
                          background: "rgba(124, 58, 237, 0.15)",
                          color: "#A78BFA",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 10,
                          fontWeight: 700,
                        }}
                      >
                        {doc.type}
                      </div>
                      <div>
                        <div style={{ fontSize: 12.5, fontWeight: 500, color: "#fff" }}>{doc.name}</div>
                        <div style={{ fontSize: 11, color: "#666" }}>
                          {doc.size} · Uploaded by {doc.uploadedBy}
                        </div>
                      </div>
                    </div>

                    <span
                      style={{
                        fontSize: 10,
                        fontWeight: 600,
                        padding: "2px 6px",
                        borderRadius: 4,
                        background: doc.status === "Verified" ? "rgba(16,185,129,0.1)" : "rgba(161,161,170,0.1)",
                        color: doc.status === "Verified" ? "#10B981" : "#A1A1AA",
                        border: `1px solid ${doc.status === "Verified" ? "rgba(16,185,129,0.2)" : "rgba(161,161,170,0.2)"}`,
                      }}
                    >
                      {doc.status}
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: 12, color: "#555", fontStyle: "italic" }}>
                  No documents currently attached to this request.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Status Progression + Timeline + Activity History */}
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {/* Status Progression Card */}
          <div className="df-card" style={{ padding: "18px 20px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", marginBottom: 14 }}>
              Request Workflow Stage
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { label: "Draft Initialized", desc: "Specifications & line items configured" },
                { label: "Submitted for Review", desc: "Pending initial commercial clearance" },
                { label: "Under Review", desc: "Routing through risk & pricing controls" },
                { label: "Commercial Approval", desc: "Managerial sign-off" },
                { label: "Execution & Fulfillment", desc: "Odoo dispatch & sync" },
              ].map((step, idx) => {
                const isPassed = idx < currentStep
                const isCurrent = idx === currentStep
                return (
                  <div key={step.label} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                    <div
                      style={{
                        width: 18,
                        height: 18,
                        borderRadius: "50%",
                        background: isPassed ? "#10B981" : isCurrent ? "#7C3AED" : "#1a1a1e",
                        border: `1px solid ${isPassed ? "#10B981" : isCurrent ? "#A78BFA" : "#333"}`,
                        color: "#fff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 9.5,
                        fontWeight: 700,
                        marginTop: 2,
                        flexShrink: 0,
                      }}
                    >
                      {isPassed ? "✓" : idx + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: isCurrent ? 700 : 500, color: isCurrent ? "#fff" : isPassed ? "#E4E4E7" : "#555" }}>
                        {step.label}
                      </div>
                      <div style={{ fontSize: 11, color: isCurrent ? "#94A3B8" : "#444" }}>
                        {step.desc}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Timeline Section (Step 15) */}
          <div className="df-card" style={{ padding: "18px 20px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", marginBottom: 12 }}>
              Request Timeline
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {activeRequest.timeline && activeRequest.timeline.length > 0 ? (
                activeRequest.timeline.map((tl, i) => (
                  <div key={tl.id || i} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: "#7C3AED",
                        marginTop: 5,
                        flexShrink: 0,
                      }}
                    />
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "#fff" }}>
                        {tl.title}
                      </div>
                      <div style={{ fontSize: 11, color: "#71717A" }}>
                        {tl.actor} · {new Date(tl.timestamp).toLocaleString()}
                      </div>
                      {tl.note && (
                        <div style={{ fontSize: 11.5, color: "#94A3B8", marginTop: 2, lineHeight: 1.4 }}>
                          {tl.note}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: 12, color: "#555" }}>No timeline events recorded.</div>
              )}
            </div>
          </div>

          {/* Activity / History Log (Step 16) */}
          <div className="df-card" style={{ padding: "18px 20px", background: "#080808", border: "1px solid #1a1a1a" }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", marginBottom: 12 }}>
              Activity History
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {activeRequest.activity && activeRequest.activity.length > 0 ? (
                activeRequest.activity.map((act, i) => (
                  <div
                    key={act.id || i}
                    style={{
                      padding: "8px 10px",
                      borderRadius: 4,
                      background: "#0c0c0f",
                      border: "1px solid #18181f",
                    }}
                  >
                    <div style={{ fontSize: 11.5, fontWeight: 600, color: "#D4D4D8" }}>
                      {act.action}
                    </div>
                    <div style={{ fontSize: 10.5, color: "#71717A", marginTop: 2 }}>
                      {act.actor} · {new Date(act.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                    {act.description && (
                      <div style={{ fontSize: 11, color: "#888", marginTop: 2 }}>
                        {act.description}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div style={{ fontSize: 12, color: "#555" }}>No activity recorded yet.</div>
              )}
            </div>
          </div>

          {/* AI Intelligence Card (Step 17) */}
          <div
            style={{
              padding: 16,
              borderRadius: 8,
              background: "linear-gradient(145deg, rgba(124, 58, 237, 0.07), #09090c)",
              border: "1px solid rgba(124, 58, 237, 0.25)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#7C3AED" }} />
                <span style={{ fontSize: 11, fontWeight: 700, color: "#A78BFA", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  AI Intelligence
                </span>
              </div>
              {activeAiAnalysis ? (
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: "1px 6px",
                    borderRadius: 3,
                    background: "rgba(16, 185, 129, 0.12)",
                    color: "#10B981",
                    border: "1px solid rgba(16, 185, 129, 0.25)",
                  }}
                >
                  Analysis Complete
                </span>
              ) : (
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: "1px 6px",
                    borderRadius: 3,
                    background: "rgba(245, 158, 11, 0.12)",
                    color: "#F59E0B",
                    border: "1px solid rgba(245, 158, 11, 0.25)",
                  }}
                >
                  {activeRequest.status === "Draft" ? "Queued" : "Ready for Analysis"}
                </span>
              )}
            </div>

            {activeAiAnalysis ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ fontSize: 11, color: "#71717A" }}>Overall Risk: </span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: activeAiAnalysis.overallRisk === "Critical" ? "#EF4444" : activeAiAnalysis.overallRisk === "High" ? "#F97316" : activeAiAnalysis.overallRisk === "Medium" ? "#F59E0B" : "#10B981" }}>
                      {activeAiAnalysis.overallRisk} ({activeAiAnalysis.riskScore}/100)
                    </span>
                  </div>
                  <span className="mono" style={{ fontSize: 11.5, color: "#A78BFA" }}>
                    {activeAiAnalysis.confidenceScore}% Confidence
                  </span>
                </div>

                <div style={{ fontSize: 12, fontWeight: 600, color: "#fff", lineHeight: 1.4 }}>
                  {activeAiAnalysis.recommendation.title}
                </div>

                <p style={{ fontSize: 11.5, color: "#94A3B8", margin: 0, lineHeight: 1.45 }}>
                  {activeAiAnalysis.recommendation.rationale}
                </p>

                <button
                  type="button"
                  onClick={() => setAiModalOpen(true)}
                  className="df-btn-primary"
                  style={{
                    marginTop: 6,
                    padding: "8px 12px",
                    fontSize: 12,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 6,
                  }}
                >
                  <span>✦</span> View Full AI Analysis &rarr;
                </button>
              </div>
            ) : activeRequest.status === "Draft" ? (
              <div>
                <p style={{ fontSize: 11.5, color: "#94A3B8", margin: "0 0 8px 0", lineHeight: 1.45 }}>
                  Automated policy checks and pricing models evaluate requests upon submission. Submit this draft to run AI intelligence.
                </p>
              </div>
            ) : (
              <div>
                <p style={{ fontSize: 11.5, color: "#94A3B8", margin: "0 0 10px 0", lineHeight: 1.45 }}>
                  Automated risk evaluation, discount validation, and policy checks ready to run for this submitted request.
                </p>
                <button
                  type="button"
                  onClick={() => setAiModalOpen(true)}
                  className="df-btn-primary"
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    fontSize: 12,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 6,
                  }}
                >
                  <span>✦</span> Run AI Analysis &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Slide-over AI Analysis Modal (Step 3 to 16) */}
      <AIAnalysisModal
        isOpen={aiModalOpen}
        request={activeRequest}
        onClose={() => setAiModalOpen(false)}
      />

      {/* Execution Pipeline Modal */}
      <ExecutionModal
        isOpen={executionModalOpen}
        execution={activeExecutionForModal}
        onClose={() => setExecutionModalOpen(false)}
        onStart={(simulateFailure) =>
          activeExecutionForModal
            ? startExecution(activeExecutionForModal.id, simulateFailure)
            : Promise.reject(new Error("No active execution"))
        }
        onRetry={() =>
          activeExecutionForModal
            ? retryExecution(activeExecutionForModal.id)
            : Promise.reject(new Error("No active execution"))
        }
        onViewTransaction={(txId) => {
          setExecutionModalOpen(false)
          const tx = getTransactionById(txId)
          if (tx) setSelectedDrawerTransaction(tx)
        }}
      />

      {/* Execution Detail Drawer */}
      <ExecutionDrawer
        isOpen={Boolean(selectedDrawerExecution)}
        execution={selectedDrawerExecution}
        onClose={() => setSelectedDrawerExecution(null)}
        onRetry={(id) => retryExecution(id)}
        onViewTransaction={(txId) => {
          setSelectedDrawerExecution(null)
          const tx = getTransactionById(txId)
          if (tx) setSelectedDrawerTransaction(tx)
        }}
      />

      {/* Transaction Traceability Drawer */}
      <TransactionDrawer
        isOpen={Boolean(selectedDrawerTransaction)}
        transaction={selectedDrawerTransaction}
        onClose={() => setSelectedDrawerTransaction(null)}
        onViewExecution={(execId) => {
          setSelectedDrawerTransaction(null)
          const exec = getExecutionForRequest(activeRequest?.id || "")
          if (exec) setSelectedDrawerExecution(exec)
        }}
      />
    </div>
  )
}
