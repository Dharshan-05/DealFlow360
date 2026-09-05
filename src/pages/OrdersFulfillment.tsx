import { useEffect, useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import {
  AnimatedNumber,
  FadeIn,
  StaggerContainer,
  StaggerItem,
} from "../lib/motion"
import { useExecution } from "../hooks/useExecution"
import { useTransactions } from "../hooks/useTransactions"
import ExecutionModal from "../components/execution/ExecutionModal"
import ExecutionDrawer from "../components/execution/ExecutionDrawer"
import TransactionDrawer from "../components/transactions/TransactionDrawer"
import ERPExecutionView from "../components/execution/ERPExecutionView"
import type { Execution } from "../types/execution"
import type { Transaction } from "../types/transaction"

type OrderStatus = "Pending" | "Confirmed" | "Processing" | "Packed" | "Shipped" | "Out for Delivery" | "Delivered" | "Cancelled"

const orders = [
  {
    id: "ORD-2048",
    customer: "Acme Corporation",
    initials: "AC",
    products: "Enterprise Suite × 24",
    date: "Sep 05, 2026",
    amount: "₹4.20M",
    payment: "Paid",
    status: "Processing" as OrderStatus,
    delivery: "Sep 11",
    owner: "Nisha Rao",
  },
  {
    id: "ORD-2047",
    customer: "Vertex Systems",
    initials: "VS",
    products: "Cloud Analytics × 12",
    date: "Sep 04, 2026",
    amount: "₹1.85M",
    payment: "Paid",
    status: "Packed" as OrderStatus,
    delivery: "Sep 08",
    owner: "Ananya Patel",
  },
  {
    id: "ORD-2046",
    customer: "NovaTech Ltd",
    initials: "NT",
    products: "Platform Pro × 8",
    date: "Sep 03, 2026",
    amount: "₹980K",
    payment: "Pending",
    status: "Pending" as OrderStatus,
    delivery: "—",
    owner: "Priya Mehta",
  },
  {
    id: "ORD-2045",
    customer: "GlobalFin Inc",
    initials: "GF",
    products: "Risk Module × 16",
    date: "Sep 02, 2026",
    amount: "₹2.40M",
    payment: "Paid",
    status: "Shipped" as OrderStatus,
    delivery: "Sep 07",
    owner: "Vikram Singh",
  },
  {
    id: "ORD-2044",
    customer: "Zenith Retail",
    initials: "ZR",
    products: "Commerce Stack × 40",
    date: "Sep 01, 2026",
    amount: "₹740K",
    payment: "Paid",
    status: "Delivered" as OrderStatus,
    delivery: "Delivered Sep 04",
    owner: "Kavya Reddy",
  },
  {
    id: "ORD-2043",
    customer: "Meridian Capital",
    initials: "MC",
    products: "Data Platform × 10",
    date: "Aug 31, 2026",
    amount: "₹1.30M",
    payment: "Overdue",
    status: "Processing" as OrderStatus,
    delivery: "Sep 06",
    owner: "Deepak Nair",
  },
]

const kpis = [
  {
    label: "Total orders",
    value: 248,
    note: "+12.6% this month",
    tone: "#fff",
  },
  { label: "Pending", value: 18, note: "7 need payment", tone: "#F59E0B" },
  {
    label: "Processing",
    value: 42,
    note: "+8 since yesterday",
    tone: "#A1A1AA",
  },
  { label: "Shipped", value: 64, note: "96% on schedule", tone: "#60A5FA" },
  { label: "Delivered", value: 117, note: "+14.1% this week", tone: "#10B981" },
  { label: "Delayed", value: 7, note: "2 require attention", tone: "#EF4444" },
]

const throughput = [
  { day: "Aug 30", orders: 31 },
  { day: "31", orders: 38 },
  { day: "Sep 1", orders: 36 },
  { day: "2", orders: 48 },
  { day: "3", orders: 44 },
  { day: "4", orders: 57 },
  { day: "Today", orders: 52 },
]

const statuses: Array<"All" | OrderStatus> = [
  "All",
  "Pending",
  "Confirmed",
  "Processing",
  "Packed",
  "Shipped",
  "Out for Delivery",
  "Delivered",
  "Cancelled",
]

const statusStyle = (status: OrderStatus) =>
  ({
    Pending: {
      color: "#F59E0B",
      background: "rgba(245,158,11,.10)",
      border: "rgba(245,158,11,.18)",
    },
    Confirmed: { color: "#D4D4D8", background: "#151515", border: "#282828" },
    Processing: { color: "#D4D4D8", background: "#151515", border: "#282828" },
    Packed: {
      color: "#C4B5FD",
      background: "rgba(124,58,237,.11)",
      border: "rgba(124,58,237,.22)",
    },
    Shipped: {
      color: "#93C5FD",
      background: "rgba(59,130,246,.10)",
      border: "rgba(59,130,246,.2)",
    },
    "Out for Delivery": {
      color: "#93C5FD",
      background: "rgba(59,130,246,.10)",
      border: "rgba(59,130,246,.2)",
    },
    Delivered: {
      color: "#6EE7B7",
      background: "rgba(16,185,129,.10)",
      border: "rgba(16,185,129,.2)",
    },
    Cancelled: {
      color: "#FCA5A5",
      background: "rgba(239,68,68,.1)",
      border: "rgba(239,68,68,.2)",
    },
  })[status]

function SmallIcon({
  name,
}: {
  name: "search" | "filter" | "chevron" | "close" | "more" | "download"
}) {
  const path = {
    search: "M21 21l-4.7-4.7m2.2-5.3a7.5 7.5 0 11-15 0 7.5 7.5 0 0115 0z",
    filter: "M4 6h16M7 12h10m-7 6h4",
    chevron: "m9 18 6-6-6-6",
    close: "M6 6l12 12M18 6 6 18",
    more: "M12 5v.01M12 12v.01M12 19v.01",
    download: "M12 3v12m0 0 4-4m-4 4-4-4M5 21h14",
  }[name]
  return (
    <svg
      width="15"
      height="15"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      viewBox="0 0 24 24"
    >
      <path d={path} />
    </svg>
  )
}

function StatusBadge({ status }: { status: OrderStatus }) {
  const s = statusStyle(status)
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        border: `1px solid ${s.border}`,
        background: s.background,
        color: s.color,
        borderRadius: 4,
        padding: "3px 7px",
        fontSize: 11,
        fontWeight: 600,
      }}
    >
      <span
        style={{ width: 5, height: 5, borderRadius: 9, background: s.color }}
      />
      {status}
    </span>
  )
}

function Drawer({
  order,
  onClose,
  onStatusChange,
  onCancel,
  updating,
}: {
  order: typeof orders[number]
  onClose: () => void
  onStatusChange: (status: OrderStatus) => void
  onCancel: () => void
  updating: boolean
}) {
  const steps = [
    "Order confirmed",
    "Processing",
    "Packed",
    "Shipped",
    "Out for delivery",
    "Delivered",
  ]
  const complete =
    order.status === "Delivered"
      ? 6
      : order.status === "Out for Delivery"
        ? 5
        : order.status === "Shipped"
          ? 4
          : order.status === "Packed"
            ? 3
            : order.status === "Processing"
              ? 2
              : 1
  return (
    <AnimatePresence>
      {order && (
        <>
          <motion.button
            aria-label="Close order details"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: "fixed",
              inset: 0,
              border: 0,
              background: "rgba(0,0,0,.55)",
              zIndex: 20,
              cursor: "default",
            }}
          />
          <motion.aside
            initial={{ x: 420 }}
            animate={{ x: 0 }}
            exit={{ x: 420 }}
            transition={{ duration: 0.3, ease: [0, 0, 0.2, 1] }}
            style={{
              position: "fixed",
              top: 0,
              right: 0,
              bottom: 0,
              zIndex: 21,
              width: "min(420px, 100vw)",
              background: "#0b0b0b",
              borderLeft: "1px solid #242424",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                padding: "18px 20px",
                borderBottom: "1px solid #202020",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                position: "sticky",
                top: 0,
                background: "#0b0b0b",
                zIndex: 1,
              }}
            >
              <div>
                <div
                  className="mono"
                  style={{ color: "#fff", fontWeight: 700, fontSize: 15 }}
                >
                  {order.id}
                </div>
                <div style={{ color: "#555", fontSize: 12, marginTop: 3 }}>
                  Order details
                </div>
              </div>
              <motion.button
                onClick={onClose}
                whileTap={{ scale: 0.93 }}
                style={{
                  border: "1px solid #292929",
                  background: "#111",
                  color: "#999",
                  width: 30,
                  height: 30,
                  borderRadius: 6,
                  display: "grid",
                  placeItems: "center",
                  cursor: "pointer",
                }}
              >
                <SmallIcon name="close" />
              </motion.button>
            </div>
            <div style={{ padding: 20, display: "grid", gap: 20 }}>
              <section className="df-card" style={{ padding: 16 }}>
                <div
                  style={{
                    color: "#555",
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: ".08em",
                    fontWeight: 700,
                    marginBottom: 14,
                  }}
                >
                  Order summary
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 14,
                  }}
                >
                  <Detail label="Customer" value={order.customer} />
                  <Detail label="Order date" value={order.date} />
                  <Detail label="Total amount" value={order.amount} mono />
                  <Detail label="Owner" value={order.owner} />
                </div>
              </section>
              <section className="df-card" style={{ padding: 16 }}>
                <div
                  style={{
                    color: "#555",
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: ".08em",
                    fontWeight: 700,
                    marginBottom: 14,
                  }}
                >
                  Customer
                </div>
                <div style={{ color: "#fff", fontSize: 13, fontWeight: 600 }}>
                  {order.customer}
                </div>
                <div style={{ color: "#777", fontSize: 12, marginTop: 5 }}>
                  operations@
                  {order.customer
                    .toLowerCase()
                    .replace(/ /g, "")
                    .replace("ltd", "")
                    .replace("inc", "")}
                  .com · +91 80 4123 8900
                </div>
                <div style={{ color: "#555", fontSize: 11, marginTop: 7 }}>
                  Bangalore office · Karnataka, India
                </div>
              </section>
              <section className="df-card" style={{ padding: 16 }}>
                <div
                  style={{
                    color: "#555",
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: ".08em",
                    fontWeight: 700,
                    marginBottom: 14,
                  }}
                >
                  Items
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    color: "#fff",
                    fontSize: 13,
                  }}
                >
                  <span>{order.products}</span>
                  <span className="mono" style={{ color: "#A1A1AA" }}>
                    {order.amount}
                  </span>
                </div>
                <div style={{ color: "#555", fontSize: 11, marginTop: 6 }}>
                  Volume license · Standard implementation · No discount
                </div>
              </section>
              <section className="df-card" style={{ padding: 16 }}>
                <div
                  style={{
                    color: "#555",
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: ".08em",
                    fontWeight: 700,
                    marginBottom: 14,
                  }}
                >
                  Fulfillment progress
                </div>
                <div style={{ display: "grid", gap: 14 }}>
                  {steps.map((step, i) => (
                    <motion.div
                      key={step}
                      initial={{ opacity: 0, x: 8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.08 + i * 0.04 }}
                      style={{ display: "flex", gap: 10, alignItems: "center" }}
                    >
                      <div
                        style={{
                          width: 18,
                          height: 18,
                          borderRadius: 9,
                          display: "grid",
                          placeItems: "center",
                          color: i < complete ? "#000" : "#555",
                          background: i < complete ? "#fff" : "#151515",
                          border: i < complete ? "none" : "1px solid #2b2b2b",
                          fontSize: 10,
                        }}
                      >
                        {i < complete ? "✓" : i + 1}
                      </div>
                      <span
                        style={{
                          fontSize: 12.5,
                          color: i < complete ? "#fff" : "#555",
                          fontWeight: i === complete - 1 ? 600 : 400,
                        }}
                      >
                        {step}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </section>
              <section className="df-card" style={{ padding: 16 }}>
                <div
                  style={{
                    color: "#555",
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: ".08em",
                    fontWeight: 700,
                    marginBottom: 12,
                  }}
                >
                  Payment
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 13,
                  }}
                >
                  <span style={{ color: "#A1A1AA" }}>Wire transfer</span>
                  <span
                    style={{
                      color: order.payment === "Paid" ? "#10B981" : "#F59E0B",
                      fontWeight: 600,
                    }}
                  >
                    {order.payment}
                  </span>
                </div>
                <div style={{ color: "#555", fontSize: 11, marginTop: 7 }}>
                  Paid amount: {order.payment === "Paid" ? order.amount : "₹0"}{" "}
                  · Outstanding:{" "}
                  {order.payment === "Paid" ? "₹0" : order.amount}
                </div>
              </section>
              <section>
                <div
                  style={{
                    color: "#555",
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: ".08em",
                    fontWeight: 700,
                    marginBottom: 9,
                  }}
                >
                  Quick actions
                </div>
                <div style={{ display: "flex", gap: 7, flexWrap: "wrap" }}>
                  {order.status === "Pending" && (
                    <ActionButton
                      label="Confirm order"
                      loading={updating}
                      onClick={() => onStatusChange("Confirmed")}
                    />
                  )}
                  {order.status === "Confirmed" && (
                    <ActionButton
                      label="Process order"
                      loading={updating}
                      onClick={() => onStatusChange("Processing")}
                    />
                  )}
                  {order.status === "Processing" && (
                    <ActionButton
                      label="Mark packed"
                      loading={updating}
                      onClick={() => onStatusChange("Packed")}
                    />
                  )}
                  {order.status === "Packed" && (
                    <ActionButton
                      label="Create shipment"
                      loading={updating}
                      onClick={() => onStatusChange("Shipped")}
                    />
                  )}
                  {order.status === "Shipped" && (
                    <ActionButton
                      label="Out for delivery"
                      loading={updating}
                      onClick={() => onStatusChange("Out for Delivery")}
                    />
                  )}
                  {order.status === "Out for Delivery" && (
                    <ActionButton
                      label="Mark delivered"
                      loading={updating}
                      onClick={() => onStatusChange("Delivered")}
                    />
                  )}
                  {order.status !== "Delivered" &&
                    order.status !== "Cancelled" && (
                      <ActionButton
                        label="Cancel order"
                        danger
                        loading={updating}
                        onClick={onCancel}
                      />
                    )}
                </div>
                {updating && (
                  <div
                    role="status"
                    style={{ color: "#888", fontSize: 11, marginTop: 9 }}
                  >
                    Updating order…
                  </div>
                )}
              </section>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}

function Detail({
  label,
  value,
  mono,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div>
      <div
        style={{
          fontSize: 10,
          color: "#555",
          textTransform: "uppercase",
          letterSpacing: ".06em",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div
        className={mono ? "mono" : ""}
        style={{ fontSize: 12.5, color: "#E4E4E7", fontWeight: 600 }}
      >
        {value}
      </div>
    </div>
  )
}
function ActionButton({
  label,
  danger,
  onClick,
  loading,
}: {
  label: string
  danger?: boolean
  onClick: () => void
  loading?: boolean
}) {
  return (
    <motion.button
      disabled={loading}
      onClick={onClick}
      whileTap={loading ? undefined : { scale: 0.97 }}
      style={{
        border: `1px solid ${danger ? "rgba(239,68,68,.3)" : "#303030"}`,
        background: danger ? "rgba(239,68,68,.08)" : "#151515",
        color: danger ? "#F87171" : "#fff",
        borderRadius: 6,
        padding: "8px 10px",
        font: "600 12px Inter",
        cursor: loading ? "wait" : "pointer",
        opacity: loading ? 0.6 : 1,
      }}
    >
      {loading ? "Updating…" : label}
    </motion.button>
  )
}
function FilterChip({
  label,
  onRemove,
}: {
  label: string
  onRemove: () => void
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        border: "1px solid #2d2d2d",
        background: "#111",
        color: "#bbb",
        padding: "4px 6px 4px 8px",
        borderRadius: 5,
        fontSize: 11,
      }}
    >
      {label}
      <button
        aria-label={`Remove ${label} filter`}
        onClick={onRemove}
        style={{
          display: "grid",
          placeItems: "center",
          border: 0,
          borderRadius: 3,
          background: "#252525",
          color: "#bbb",
          width: 15,
          height: 15,
          cursor: "pointer",
        }}
      >
        ×
      </button>
    </span>
  )
}

interface OrdersFulfillmentProps {
  initialStatus?: string
}

export default function OrdersFulfillment({
  initialStatus,
}: OrdersFulfillmentProps) {
  const [tab, setTab] = useState<"All" | OrderStatus>("All")
  const [query, setQuery] = useState("")
  const [rows, setRows] = useState(orders)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [paymentFilter, setPaymentFilter] = useState("All payments")
  const [sort, setSort] = useState<"Newest" | "Amount">("Newest")
  const [toast, setToast] = useState<string | null>(null)
  const [confirmCancel, setConfirmCancel] = useState(false)
  const [updatingOrder, setUpdatingOrder] = useState(false)

  const [viewMode, setViewMode] = useState<"orders" | "erp">("orders")
  const {
    executions,
    metrics: execMetrics,
    startExecution,
    retryExecution,
  } = useExecution()
  const {
    transactions,
    metrics: txMetrics,
    getTransactionById,
  } = useTransactions()

  const [execModalOpen, setExecModalOpen] = useState(false)
  const [activeModalExecution, setActiveModalExecution] = useState<Execution | null>(null)
  const [selectedDrawerExec, setSelectedDrawerExec] = useState<Execution | null>(null)
  const [selectedDrawerTx, setSelectedDrawerTx] = useState<Transaction | null>(null)
  const [erpSubTab, setErpSubTab] = useState<"executions" | "transactions">("executions")
  useEffect(() => {
    if (
      initialStatus &&
      statuses.includes(initialStatus as "All" | OrderStatus)
    )
      setTab(initialStatus as "All" | OrderStatus)
  }, [initialStatus])
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return
      if (confirmCancel) setConfirmCancel(false)
      else if (selectedId) setSelectedId(null)
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [confirmCancel, selectedId])
  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(null), 2800)
    return () => window.clearTimeout(timeout)
  }, [toast])
  const filtered = useMemo(
    () =>
      rows
        .filter(
          (order) =>
            (tab === "All" || order.status === tab) &&
            (paymentFilter === "All payments" ||
              order.payment === paymentFilter) &&
            `${order.id} ${order.customer} ${order.products} ${order.status}`
              .toLowerCase()
              .includes(query.toLowerCase()),
        )
        .sort((a, b) =>
          sort === "Amount"
            ? Number.parseFloat(b.amount.replace(/[^\d.]/g, "")) -
              Number.parseFloat(a.amount.replace(/[^\d.]/g, ""))
            : b.id.localeCompare(a.id),
        ),
    [rows, tab, paymentFilter, query, sort],
  )
  const selected = rows.find((order) => order.id === selectedId) ?? null
  const updateStatus = (id: string, status: OrderStatus) => {
    if (updatingOrder) return
    setUpdatingOrder(true)
    window.setTimeout(() => {
      setRows((current) =>
        current.map((order) =>
          order.id === id ? { ...order, status } : order,
        ),
      )
      setToast(`${id} marked as ${status.toLowerCase()}.`)
      setUpdatingOrder(false)
    }, 420)
  }
  const toggleSelected = (id: string) =>
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : [...current, id],
    )
  return (
    <div
      className="orders-fulfillment"
      style={{ padding: "28px", maxWidth: 1480, margin: "0 auto" }}
    >
      <FadeIn distance={8}>
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            gap: 16,
            marginBottom: 24,
            flexWrap: "wrap",
          }}
        >
          <div>
            <h1
              style={{
                color: "#fff",
                fontSize: 22,
                fontWeight: 700,
                letterSpacing: "-.025em",
                margin: 0,
              }}
            >
              Orders &amp; Fulfillment
            </h1>
            <p style={{ color: "#555", fontSize: 13.5, margin: "5px 0 0" }}>
              Track orders, fulfillment progress, shipments, and delivery
              status.
            </p>
          </div>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <div
              style={{
                display: "flex",
                gap: 3,
                background: "#121217",
                padding: 3,
                borderRadius: 7,
                border: "1px solid #202028",
              }}
            >
              <button
                type="button"
                onClick={() => setViewMode("orders")}
                style={{
                  padding: "6px 14px",
                  fontSize: 12,
                  fontWeight: 600,
                  borderRadius: 5,
                  background: viewMode === "orders" ? "#22222c" : "transparent",
                  color: viewMode === "orders" ? "#fff" : "#71717a",
                  border: "none",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                Fulfillment Operations
              </button>
              <button
                type="button"
                onClick={() => setViewMode("erp")}
                style={{
                  padding: "6px 14px",
                  fontSize: 12,
                  fontWeight: 600,
                  borderRadius: 5,
                  background: viewMode === "erp" ? "rgba(124, 58, 237, 0.2)" : "transparent",
                  color: viewMode === "erp" ? "#c084fc" : "#71717a",
                  border: viewMode === "erp" ? "1px solid rgba(139, 92, 246, 0.35)" : "1px solid transparent",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  transition: "all 0.15s ease",
                }}
              >
                <span>⚡</span> ERP Execution &amp; Transactions
              </button>
            </div>

            {viewMode === "orders" && (
              <>
                <motion.button
                  className="df-btn-secondary"
                  style={{
                    padding: "8px 12px",
                    display: "flex",
                    gap: 6,
                    alignItems: "center",
                  }}
                  whileTap={{ scale: 0.97 }}
                >
                  <SmallIcon name="download" />
                  Export
                </motion.button>
                <motion.button
                  className="df-btn-primary"
                  style={{ padding: "8px 14px" }}
                  whileTap={{ scale: 0.97 }}
                >
                  + Create order
                </motion.button>
              </>
            )}
          </div>
        </header>
      </FadeIn>

      {viewMode === "erp" ? (
        <ERPExecutionView
          executions={executions}
          execMetrics={execMetrics}
          transactions={transactions}
          txMetrics={txMetrics}
          onOpenModal={(exec) => {
            setActiveModalExecution(exec)
            setExecModalOpen(true)
          }}
          onOpenExecDrawer={(exec) => setSelectedDrawerExec(exec)}
          onOpenTxDrawer={(tx) => setSelectedDrawerTx(tx)}
          onRetry={(id) => retryExecution(id)}
        />
      ) : (
        <>
          <StaggerContainer
            className="order-kpis"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(6,minmax(0,1fr))",
              gap: 10,
              marginBottom: 16,
            }}
            stagger={0.04}
          >
        {kpis.map((k) => (
          <StaggerItem key={k.label}>
            <motion.div
              className="df-card"
              whileHover={{ y: -2 }}
              transition={{ duration: 0.14 }}
              style={{ padding: "15px 16px" }}
            >
              <div
                style={{
                  color: "#555",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: ".065em",
                  fontSize: 10,
                }}
              >
                {k.label}
              </div>
              <div
                className="mono"
                style={{
                  color: k.tone,
                  fontSize: 25,
                  lineHeight: 1,
                  fontWeight: 800,
                  margin: "10px 0 7px",
                }}
              >
                <AnimatedNumber value={k.value} />
              </div>
              <div style={{ color: "#666", fontSize: 11 }}>{k.note}</div>
            </motion.div>
          </StaggerItem>
        ))}
      </StaggerContainer>
      <div
        className="orders-analytics"
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0,1fr) 320px",
          gap: 16,
          marginBottom: 16,
        }}
      >
        <FadeIn delay={0.12} style={{ minWidth: 0 }}>
          <section className="df-card" style={{ padding: "18px 20px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "start",
                justifyContent: "space-between",
                marginBottom: 12,
              }}
            >
              <div>
                <div style={{ color: "#fff", fontWeight: 600, fontSize: 14 }}>
                  Fulfillment throughput
                </div>
                <div style={{ color: "#555", fontSize: 12, marginTop: 3 }}>
                  Orders processed in the past 7 days
                </div>
              </div>
              <div
                className="mono"
                style={{ color: "#fff", fontWeight: 800, fontSize: 18 }}
              >
                52{" "}
                <span style={{ color: "#10B981", font: "500 11px Inter" }}>
                  +18%
                </span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={136}>
              <AreaChart
                data={throughput}
                margin={{ top: 8, right: 0, bottom: 0, left: -28 }}
              >
                <defs>
                  <linearGradient id="orderGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#fff" stopOpacity=".10" />
                    <stop offset="100%" stopColor="#fff" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1b1b1b" vertical={false} />
                <XAxis
                  dataKey="day"
                  tick={{ fill: "#444", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#444", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "#111",
                    border: "1px solid #282828",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "#777" }}
                  itemStyle={{ color: "#fff" }}
                />
                <Area
                  dataKey="orders"
                  type="monotone"
                  stroke="#fff"
                  strokeWidth={1.5}
                  fill="url(#orderGrad)"
                  dot={false}
                  animationDuration={850}
                />
              </AreaChart>
            </ResponsiveContainer>
          </section>
        </FadeIn>
        <FadeIn delay={0.16}>
          <section className="df-card" style={{ padding: 18 }}>
            <div style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>
              Today’s attention
            </div>
            <div style={{ display: "grid", gap: 11, marginTop: 14 }}>
              {[
                {
                  n: "07",
                  l: "Orders need payment confirmation",
                  c: "#F59E0B",
                },
                { n: "03", l: "Shipments are approaching SLA", c: "#EF4444" },
                {
                  n: "96%",
                  l: "On-time delivery rate this week",
                  c: "#10B981",
                },
              ].map((item) => (
                <div
                  key={item.l}
                  style={{ display: "flex", gap: 10, alignItems: "center" }}
                >
                  <div
                    className="mono"
                    style={{
                      color: item.c,
                      width: 31,
                      fontSize: 13,
                      fontWeight: 700,
                    }}
                  >
                    {item.n}
                  </div>
                  <div
                    style={{
                      borderLeft: "1px solid #262626",
                      paddingLeft: 10,
                      color: "#A1A1AA",
                      fontSize: 12,
                      lineHeight: 1.35,
                    }}
                  >
                    {item.l}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </FadeIn>
      </div>
      {(tab !== "All" || paymentFilter !== "All payments" || query) && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            margin: "0 0 12px",
            flexWrap: "wrap",
          }}
        >
          {tab !== "All" && (
            <FilterChip
              label={`Status: ${tab}`}
              onRemove={() => setTab("All")}
            />
          )}
          {paymentFilter !== "All payments" && (
            <FilterChip
              label={`Payment: ${paymentFilter}`}
              onRemove={() => setPaymentFilter("All payments")}
            />
          )}
          {query && (
            <FilterChip
              label={`Search: ${query}`}
              onRemove={() => setQuery("")}
            />
          )}
          <button
            onClick={() => {
              setTab("All")
              setPaymentFilter("All payments")
              setQuery("")
            }}
            style={{
              border: 0,
              background: "none",
              color: "#888",
              font: "600 11px Inter",
              cursor: "pointer",
              padding: 5,
            }}
          >
            Clear all
          </button>
        </motion.div>
      )}
      <FadeIn delay={0.2}>
        <section className="df-card" style={{ overflow: "hidden" }}>
          <div style={{ padding: "16px 18px 0" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 16,
                alignItems: "center",
                marginBottom: 16,
                flexWrap: "wrap",
              }}
            >
              <div>
                <div style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>
                  Order operations
                </div>
                <div style={{ color: "#555", fontSize: 12, marginTop: 3 }}>
                  {filtered.length} active records
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <label style={{ position: "relative", display: "block" }}>
                  <span
                    style={{
                      position: "absolute",
                      left: 10,
                      top: 9,
                      color: "#555",
                    }}
                  >
                    <SmallIcon name="search" />
                  </span>
                  <input
                    aria-label="Search orders"
                    className="df-input"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search orders…"
                    style={{
                      width: 190,
                      height: 34,
                      padding: "7px 10px 7px 31px",
                      fontSize: 12,
                    }}
                  />
                </label>
                <select
                  aria-label="Sort orders"
                  value={sort}
                  onChange={(e) =>
                    setSort(e.target.value as "Newest" | "Amount")
                  }
                  style={{
                    height: 34,
                    padding: "0 9px",
                    background: "#0a0a0a",
                    border: "1px solid #222",
                    borderRadius: 6,
                    color: "#999",
                    fontSize: 12,
                  }}
                >
                  <option value="Newest">Newest</option>
                  <option value="Amount">Amount</option>
                </select>
                <div style={{ position: "relative" }}>
                  <span
                    style={{
                      position: "absolute",
                      left: 9,
                      top: 9,
                      color: "#555",
                      pointerEvents: "none",
                    }}
                  >
                    <SmallIcon name="filter" />
                  </span>
                  <select
                    aria-label="Filter payment"
                    value={paymentFilter}
                    onChange={(e) => setPaymentFilter(e.target.value)}
                    style={{
                      height: 34,
                      padding: "0 26px 0 30px",
                      appearance: "none",
                      background: "#0a0a0a",
                      border: "1px solid #222",
                      borderRadius: 6,
                      color: "#999",
                      fontSize: 12,
                      outline: "none",
                    }}
                  >
                    <option>All payments</option>
                    <option>Paid</option>
                    <option>Pending</option>
                    <option>Overdue</option>
                  </select>
                  <span
                    style={{
                      position: "absolute",
                      right: 8,
                      top: 9,
                      pointerEvents: "none",
                      color: "#555",
                      transform: "rotate(90deg)",
                    }}
                  >
                    <SmallIcon name="chevron" />
                  </span>
                </div>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                gap: 3,
                overflowX: "auto",
                borderBottom: "1px solid #1b1b1b",
              }}
            >
              {statuses.map((s) => (
                <button
                  key={s}
                  onClick={() => setTab(s)}
                  style={{
                    position: "relative",
                    whiteSpace: "nowrap",
                    padding: "9px 11px",
                    color: tab === s ? "#fff" : "#555",
                    background: "none",
                    border: 0,
                    cursor: "pointer",
                    fontSize: 12,
                    fontWeight: tab === s ? 600 : 500,
                    fontFamily: "Inter, sans-serif",
                  }}
                >
                  {s}
                  {tab === s && (
                    <motion.span
                      layoutId="order-tab"
                      style={{
                        position: "absolute",
                        height: 2,
                        background: "#fff",
                        left: 10,
                        right: 10,
                        bottom: 0,
                      }}
                      transition={{ duration: 0.2 }}
                    />
                  )}
                </button>
              ))}
            </div>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                minWidth: 950,
                borderCollapse: "collapse",
              }}
            >
              <thead>
                <tr>
                  <th
                    style={{
                      padding: "10px 10px 10px 18px",
                      borderBottom: "1px solid #181818",
                    }}
                  >
                    <input
                      aria-label="Select all visible orders"
                      type="checkbox"
                      checked={
                        filtered.length > 0 &&
                        filtered.every((order) =>
                          selectedIds.includes(order.id),
                        )
                      }
                      onChange={() =>
                        setSelectedIds(
                          filtered.every((order) =>
                            selectedIds.includes(order.id),
                          )
                            ? []
                            : filtered.map((order) => order.id),
                        )
                      }
                    />
                  </th>
                  {[
                    "Order ID",
                    "Customer",
                    "Products",
                    "Order date",
                    "Amount",
                    "Payment",
                    "Fulfillment",
                    "Delivery",
                    "",
                  ].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "10px 18px",
                        color: "#444",
                        fontSize: 10,
                        textAlign: "left",
                        fontWeight: 700,
                        letterSpacing: ".07em",
                        textTransform: "uppercase",
                        borderBottom: "1px solid #181818",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((order, index) => (
                  <motion.tr
                    key={order.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.22 + index * 0.035 }}
                    onClick={() => setSelectedId(order.id)}
                    className="table-row"
                    style={{
                      cursor: "pointer",
                      borderBottom:
                        index === filtered.length - 1
                          ? "none"
                          : "1px solid #121212",
                    }}
                  >
                    <td style={{ padding: "12px 10px 12px 18px" }}>
                      <input
                        aria-label={`Select ${order.id}`}
                        type="checkbox"
                        checked={selectedIds.includes(order.id)}
                        onClick={(e) => e.stopPropagation()}
                        onChange={() => toggleSelected(order.id)}
                      />
                    </td>
                    <td
                      className="mono"
                      style={{
                        padding: "12px 18px",
                        color: "#D4D4D8",
                        fontSize: 12,
                        fontWeight: 600,
                      }}
                    >
                      {order.id}
                    </td>
                    <td style={{ padding: "12px 18px" }}>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                        }}
                      >
                        <span
                          style={{
                            width: 23,
                            height: 23,
                            display: "grid",
                            placeItems: "center",
                            borderRadius: 5,
                            background: "#1b1b1b",
                            color: "#aaa",
                            fontSize: 9,
                            fontWeight: 700,
                          }}
                        >
                          {order.initials}
                        </span>
                        <span
                          style={{
                            color: "#fff",
                            fontSize: 12.5,
                            fontWeight: 600,
                          }}
                        >
                          {order.customer}
                        </span>
                      </div>
                    </td>
                    <td
                      style={{
                        padding: "12px 18px",
                        color: "#777",
                        fontSize: 12,
                      }}
                    >
                      {order.products}
                    </td>
                    <td
                      style={{
                        padding: "12px 18px",
                        color: "#777",
                        fontSize: 12,
                      }}
                    >
                      {order.date}
                    </td>
                    <td
                      className="mono"
                      style={{
                        padding: "12px 18px",
                        color: "#D4D4D8",
                        fontSize: 12,
                        fontWeight: 600,
                      }}
                    >
                      {order.amount}
                    </td>
                    <td
                      style={{
                        padding: "12px 18px",
                        color:
                          order.payment === "Paid"
                            ? "#10B981"
                            : order.payment === "Overdue"
                              ? "#EF4444"
                              : "#F59E0B",
                        fontSize: 12,
                        fontWeight: 600,
                      }}
                    >
                      {order.payment}
                    </td>
                    <td style={{ padding: "12px 18px" }}>
                      <StatusBadge status={order.status} />
                    </td>
                    <td
                      style={{
                        padding: "12px 18px",
                        color: "#777",
                        fontSize: 12,
                      }}
                    >
                      {order.delivery}
                    </td>
                    <td style={{ padding: "12px 18px", color: "#555" }}>
                      <button
                        aria-label={`Actions for ${order.id}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleSelected(order.id)
                        }}
                        style={{
                          border: 0,
                          background: "none",
                          color: selectedIds.includes(order.id)
                            ? "#fff"
                            : "inherit",
                          cursor: "pointer",
                          padding: 4,
                        }}
                      >
                        <SmallIcon name="more" />
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div
                style={{
                  textAlign: "center",
                  padding: "48px 20px",
                  color: "#555",
                  fontSize: 13,
                }}
              >
                No orders match your current filters.
                <br />
                <button
                  onClick={() => {
                    setTab("All")
                    setPaymentFilter("All payments")
                    setQuery("")
                  }}
                  style={{
                    border: 0,
                    background: "none",
                    color: "#fff",
                    marginTop: 10,
                    font: "600 12px Inter",
                    cursor: "pointer",
                  }}
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>
          <footer
            style={{
              borderTop: "1px solid #181818",
              padding: "11px 18px",
              display: "flex",
              justifyContent: "space-between",
              color: "#555",
              fontSize: 12,
            }}
          >
            <span>Showing {filtered.length} of 248 orders</span>
            <span>Page 1 of 21</span>
          </footer>
        </section>
      </FadeIn>
      <AnimatePresence>
        {selectedIds.length > 0 && (
          <motion.div
            initial={{ y: 18, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 18, opacity: 0 }}
            style={{
              position: "fixed",
              bottom: 22,
              left: "50%",
              transform: "translateX(-50%)",
              display: "flex",
              alignItems: "center",
              gap: 12,
              background: "#171717",
              border: "1px solid #333",
              padding: "8px 9px 8px 14px",
              borderRadius: 8,
              boxShadow: "0 14px 40px rgba(0,0,0,.42)",
              zIndex: 12,
            }}
          >
            <span style={{ color: "#fff", fontSize: 12, fontWeight: 600 }}>
              {selectedIds.length} selected
            </span>
            <button
              onClick={() => {
                setToast(`${selectedIds.length} orders exported.`)
                setSelectedIds([])
              }}
              className="df-btn-primary"
              style={{ padding: "6px 10px", fontSize: 11 }}
            >
              Export
            </button>
            <button
              onClick={() => setSelectedIds([])}
              style={{
                border: 0,
                background: "none",
                color: "#888",
                font: "600 11px Inter",
                cursor: "pointer",
              }}
            >
              Clear
            </button>
          </motion.div>
        )}
      </AnimatePresence>
      {selected && (
        <Drawer
          order={selected}
          onClose={() => setSelectedId(null)}
          onStatusChange={(status) => updateStatus(selected.id, status)}
          onCancel={() => setConfirmCancel(true)}
          updating={updatingOrder}
        />
      )}
      <AnimatePresence>
        {confirmCancel && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 30,
              display: "grid",
              placeItems: "center",
              background: "rgba(0,0,0,.66)",
              padding: 20,
            }}
          >
            <motion.div
              initial={{ y: 12, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 12, opacity: 0 }}
              className="df-card"
              role="dialog"
              aria-modal="true"
              aria-label="Cancel order confirmation"
              style={{ padding: 20, width: 360, maxWidth: "100%" }}
            >
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 15 }}>
                Cancel this order?
              </div>
              <p
                style={{
                  color: "#777",
                  fontSize: 12.5,
                  lineHeight: 1.5,
                  margin: "8px 0 18px",
                }}
              >
                This will stop the fulfillment workflow for {selected?.id}. This
                action cannot be undone.
              </p>
              <div
                style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}
              >
                <button
                  className="df-btn-secondary"
                  onClick={() => setConfirmCancel(false)}
                  style={{ padding: "7px 11px", fontSize: 12 }}
                >
                  Keep order
                </button>
                <button
                  onClick={() => {
                    if (selected) {
                      updateStatus(selected.id, "Cancelled")
                      setConfirmCancel(false)
                      setSelectedId(null)
                    }
                  }}
                  style={{
                    background: "#EF4444",
                    color: "#fff",
                    border: 0,
                    borderRadius: 6,
                    padding: "7px 11px",
                    font: "600 12px Inter",
                    cursor: "pointer",
                  }}
                >
                  Cancel order
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
        </>
      )}

      <AnimatePresence>
        {toast && (
          <motion.div
            role="status"
            initial={{ y: 16, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 16, opacity: 0 }}
            style={{
              position: "fixed",
              right: 22,
              bottom: 22,
              zIndex: 40,
              border: "1px solid #303030",
              background: "#171717",
              color: "#fff",
              borderRadius: 7,
              padding: "11px 13px",
              fontSize: 12,
              boxShadow: "0 12px 32px rgba(0,0,0,.35)",
            }}
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Execution Pipeline Modal */}
      <ExecutionModal
        isOpen={execModalOpen}
        execution={activeModalExecution}
        onClose={() => setExecModalOpen(false)}
        onStart={(simulateFailure) =>
          activeModalExecution
            ? startExecution(activeModalExecution.id, simulateFailure)
            : Promise.reject(new Error("No active execution"))
        }
        onRetry={() =>
          activeModalExecution
            ? retryExecution(activeModalExecution.id)
            : Promise.reject(new Error("No active execution"))
        }
        onViewTransaction={(txId) => {
          setExecModalOpen(false)
          const tx = getTransactionById(txId)
          if (tx) setSelectedDrawerTx(tx)
        }}
      />

      {/* Execution Detail Drawer */}
      <ExecutionDrawer
        isOpen={Boolean(selectedDrawerExec)}
        execution={selectedDrawerExec}
        onClose={() => setSelectedDrawerExec(null)}
        onRetry={(id) => retryExecution(id)}
        onViewTransaction={(txId) => {
          setSelectedDrawerExec(null)
          const tx = getTransactionById(txId)
          if (tx) setSelectedDrawerTx(tx)
        }}
      />

      {/* Transaction Traceability Drawer */}
      <TransactionDrawer
        isOpen={Boolean(selectedDrawerTx)}
        transaction={selectedDrawerTx}
        onClose={() => setSelectedDrawerTx(null)}
        onViewExecution={(execId) => {
          setSelectedDrawerTx(null)
          const exec = executions.find((e) => e.id === execId)
          if (exec) setSelectedDrawerExec(exec)
        }}
      />
    </div>
  )
}
