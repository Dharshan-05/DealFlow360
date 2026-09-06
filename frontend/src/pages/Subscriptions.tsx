import { useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"

type Status = "Active" | "Trial" | "Paused" | "Cancelled" | "Past Due" | "At Risk"
type Subscription = { id: string; customer: string; plan: string; amount: string; cycle: "Monthly" | "Annual"; status: Status; next: string; owner: string }

const subscriptions: Subscription[] = [
  { id: "SUB-2041", customer: "Acme Corp", plan: "Enterprise", amount: "$2,400", cycle: "Monthly", status: "Active", next: "Sep 30", owner: "M. Shah" },
  { id: "SUB-2037", customer: "Nova Retail", plan: "Growth", amount: "$950", cycle: "Monthly", status: "Active", next: "Oct 02", owner: "R. Iyer" },
  { id: "SUB-2029", customer: "Beta Industries", plan: "Enterprise", amount: "$4,800", cycle: "Annual", status: "At Risk", next: "Oct 15", owner: "S. Kim" },
]

const statusTone: Record<Status, string> = { Active: "#10B981", Trial: "#A78BFA", Paused: "#A1A1AA", Cancelled: "#71717A", "Past Due": "#EF4444", "At Risk": "#F59E0B" }

export default function Subscriptions() {
  const [data, setData] = useState<Subscription[]>(() => {
    try {
      const saved = localStorage.getItem("dealflow_subscriptions")
      return saved ? JSON.parse(saved) : subscriptions
    } catch {
      return subscriptions
    }
  })
  const [query, setQuery] = useState("")
  const [status, setStatus] = useState<"All" | Status>("All")
  const [customer, setCustomer] = useState("All customers")
  const [cycle, setCycle] = useState("All cycles")
  const [selected, setSelected] = useState<Subscription | null>(null)
  const [modal, setModal] = useState<"edit" | "pause" | "cancel" | "plan" | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3500)
  }

  const updateSubscription = (id: string, updates: Partial<Subscription>) => {
    setData(prev => {
      const next = prev.map(item => item.id === id ? { ...item, ...updates } : item)
      try {
        localStorage.setItem("dealflow_subscriptions", JSON.stringify(next))
      } catch {}
      return next
    })
    setSelected(prev => (prev && prev.id === id ? { ...prev, ...updates } : prev))
  }

  const rows = useMemo(() => data.filter((item) => (status === "All" || item.status === status) && (customer === "All customers" || item.customer === customer) && (cycle === "All cycles" || item.cycle === cycle) && `${item.id} ${item.customer} ${item.plan}`.toLowerCase().includes(query.toLowerCase())), [data, query, status, customer, cycle])

  return <div style={{ padding: 28, maxWidth: 1440, margin: "0 auto", position: "relative" }}>
    <AnimatePresence>
      {toast && (
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
            padding: "10px 20px",
            borderRadius: 8,
            boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span>✓</span>
          <span>{toast}</span>
        </motion.div>
      )}
    </AnimatePresence>
    <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16, marginBottom: 22 }}><div><h1 style={h1}>Subscriptions</h1><p style={sub}>Recurring revenue, billing cycles, and customer lifecycle.</p></div><button className="df-btn-primary">+ New Subscription</button></header>
    <section className="df-card" style={{ overflow: "hidden" }}>
      <div style={{ padding: "14px 16px", borderBottom: "1px solid #1a1a1a", display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input className="df-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search subscriptions…" style={inputStyle}/>
        <Select value={status} setValue={setStatus} values={["All", "Active", "Trial", "Paused", "Cancelled", "Past Due", "At Risk"]}/>
        <Select value={customer} setValue={setCustomer} values={["All customers", "Acme Corp", "Nova Retail", "Beta Industries"]}/>
        <Select value={cycle} setValue={setCycle} values={["All cycles", "Monthly", "Annual"]}/>
        <input className="df-input" type="date" aria-label="Filter by next billing date" style={{ ...inputStyle, width: 145 }}/>
      </div>
      <div style={{ overflowX: "auto" }}><table style={{ width: "100%", minWidth: 990, borderCollapse: "collapse" }}><thead><tr>{["Subscription", "Customer", "Plan", "Amount", "Billing cycle", "Status", "Next billing", "Owner"].map((x) => <th key={x} style={th}>{x}</th>)}</tr></thead><tbody>{rows.map((item) => <motion.tr key={item.id} onClick={() => setSelected(item)} whileHover={{ background: "rgba(255,255,255,.025)" }} style={{ cursor: "pointer", borderTop: "1px solid #121212" }}><td className="mono" style={tdStrong}>{item.id}</td><td style={tdStrong}>{item.customer}</td><td style={td}>{item.plan}</td><td className="mono" style={tdStrong}>{item.amount}</td><td style={td}>{item.cycle}</td><td style={td}><Badge status={item.status}/></td><td style={td}>{item.next}</td><td style={td}>{item.owner}</td></motion.tr>)}</tbody></table></div>
    </section>
    <AnimatePresence>{selected && <><motion.button aria-label="Close subscription detail" onClick={() => setSelected(null)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={scrim}/><motion.aside initial={{ x: 480 }} animate={{ x: 0 }} exit={{ x: 480 }} transition={{ duration: .24 }} style={drawer}><div style={drawerHead}><div><div className="mono" style={{ color: "#fff", fontWeight: 700 }}>{selected.id}</div><div style={{ color: "#888", marginTop: 3, fontSize: 12 }}>{selected.customer}</div></div><button onClick={() => setSelected(null)} style={close}>×</button></div><div style={{ padding: 20, display: "grid", gap: 14 }}><div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 1, background: "#202020", border: "1px solid #202020" }}>{[["Plan", selected.plan], ["Status", selected.status], ["MRR", selected.amount], ["Billing cycle", selected.cycle], ["Next billing", selected.next]].map(([label, value]) => <div key={label} style={{ padding: 12, background: "#0b0b0b" }}><div style={labelStyle}>{label}</div><div style={{ color: "#fff", fontSize: 13, marginTop: 5, fontWeight: 600 }}>{value}</div></div>)}</div><Section title="Plan Details"><Field label="Contract term" value="12 months · renews Sep 30, 2027"/><Field label="Products / Services" value={`${selected.plan} platform · Priority support`}/></Section><Section title="Billing Information"><Field label="Payment method" value="Corporate Visa •••• 4182"/><Field label="Usage" value="184 / 250 included seats"/><Field label="Invoices" value="INV-3012 pending · 2 paid"/></Section><Section title="Subscription lifecycle"><div style={{ display: "flex", alignItems: "center", gap: 7, color: "#666", fontSize: 11, flexWrap: "wrap" }}><span>Trial</span><span>↓</span><strong style={{ color: selected.status === "Active" ? "#10B981" : selected.status === "Paused" ? "#A1A1AA" : selected.status === "Cancelled" ? "#EF4444" : "#F59E0B" }}>{selected.status} · current</strong><span>↓</span><span>Renewed</span><span>↓</span><span>Paused</span><span>↓</span><span>Cancelled</span></div><div style={{ color: "#777", fontSize: 11, marginTop: 8 }}>{selected.status === "Paused" ? "Subscription is currently paused. Resume anytime." : selected.status === "Cancelled" ? "Subscription has been cancelled." : "Previous: Trial · Next possible action: Renew, pause, or change plan."}</div></Section><Section title="Activity"><div style={{ color: "#aaa", fontSize: 12, lineHeight: 2 }}>Sep 01 · Invoice INV-3012 generated<br/>Aug 30 · Payment method verified<br/>Aug 15 · Subscription activated</div></Section><div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}><button className="df-btn-secondary" onClick={() => setModal("edit")}>Edit Subscription</button><button className="df-btn-secondary" onClick={() => setModal("plan")}>Change Plan</button><button className="df-btn-secondary" onClick={() => setModal("pause")}>{selected.status === "Paused" ? "Resume" : "Pause"}</button><button className="df-btn-secondary" onClick={() => setModal("cancel")}>Cancel</button></div></div></motion.aside></>}</AnimatePresence>
    <AnimatePresence>{modal && selected && <ActionModal type={modal} subscription={selected} onClose={() => setModal(null)} onUpdate={(updates, message) => { updateSubscription(selected.id, updates); setModal(null); showToast(message); }}/>}</AnimatePresence>
  </div>
}

function ActionModal({
  type,
  subscription,
  onClose,
  onUpdate,
}: {
  type: "edit" | "pause" | "cancel" | "plan"
  subscription: Subscription
  onClose: () => void
  onUpdate: (updates: Partial<Subscription>, message: string) => void
}) {
  const isPlan = type === "plan"
  const isEdit = type === "edit"
  const isPause = type === "pause"
  const isCancel = type === "cancel"

  const [selectedPlan, setSelectedPlan] = useState(subscription.plan)
  const [amount, setAmount] = useState(subscription.amount.replace(/[^0-9]/g, ""))
  const [cycle, setCycle] = useState(subscription.cycle)
  const [cancelReason, setCancelReason] = useState("")
  const isCurrentlyPaused = subscription.status === "Paused"

  const handleConfirm = () => {
    if (isPlan) {
      const isEnt = selectedPlan === "Enterprise"
      const newAmount = cycle === "Annual" ? (isEnt ? "$4,800" : "$1,900") : (isEnt ? "$2,400" : "$950")
      onUpdate({ plan: selectedPlan, amount: newAmount }, `Subscription updated to ${selectedPlan} plan`)
    } else if (isEdit) {
      const formattedAmount = `$${parseInt(amount || "0", 10).toLocaleString("en-US")}`
      onUpdate({ amount: formattedAmount, cycle }, `Subscription ${subscription.id} settings saved`)
    } else if (isPause) {
      if (isCurrentlyPaused) {
        onUpdate({ status: "Active" }, `Subscription ${subscription.id} resumed successfully`)
      } else {
        onUpdate({ status: "Paused" }, `Subscription ${subscription.id} paused`)
      }
    } else if (isCancel) {
      onUpdate({ status: "Cancelled" }, `Subscription ${subscription.id} cancelled`)
    }
  }

  return (
    <>
      <motion.button onClick={onClose} aria-label="Close dialog" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={scrim}/>
      <motion.div initial={{ opacity: 0, scale: .97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: .97 }} style={{ ...drawer, right: "50%", top: "50%", bottom: "auto", transform: "translate(50%,-50%)", width: 440, zIndex: 31, padding: 24, borderRadius: 10, border: "1px solid #27272a" }}>
        <h2 style={{ color: "#fff", fontSize: 17, margin: 0, fontWeight: 700 }}>
          {isEdit
            ? `Edit Subscription (${subscription.id})`
            : isPlan
            ? "Change Subscription Plan"
            : isPause
            ? isCurrentlyPaused
              ? "Resume subscription?"
              : "Pause subscription?"
            : "Cancel subscription?"}
        </h2>
        <p style={{ color: "#888", fontSize: 12.5, lineHeight: 1.5, marginTop: 6, marginBottom: 16 }}>
          {isEdit
            ? "Adjust billing cycle, recurring pricing, or subscription terms."
            : isPlan
            ? "Select the plan to take effect immediately or on the next billing date."
            : isPause
            ? isCurrentlyPaused
              ? "Billing and service will resume on the scheduled cycle."
              : "Billing will be temporarily held until this subscription is resumed."
            : "Cancellation ends recurring billing. This action is recorded in the audit trail."}
        </p>

        {isPlan && (
          <div style={{ display: "grid", gap: 10, marginBottom: 16 }}>
            <label style={{ fontSize: 12, color: "#aaa" }}>Tier Selection</label>
            <select
              className="df-input"
              value={selectedPlan}
              onChange={(e) => setSelectedPlan(e.target.value)}
              style={{ width: "100%", height: 38 }}
            >
              <option value="Enterprise">Enterprise — $2,400 / month (Unlimited features, SLA)</option>
              <option value="Growth">Growth — $950 / month (Up to 50 seats)</option>
            </select>
          </div>
        )}

        {isEdit && (
          <div style={{ display: "grid", gap: 14, marginBottom: 16 }}>
            <div>
              <label style={{ fontSize: 11.5, color: "#888", display: "block", marginBottom: 6 }}>MRR / Recurring Amount ($)</label>
              <input
                type="number"
                className="df-input"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                style={{ width: "100%", height: 36 }}
                placeholder="2400"
              />
            </div>
            <div>
              <label style={{ fontSize: 11.5, color: "#888", display: "block", marginBottom: 6 }}>Billing Cycle</label>
              <select
                className="df-input"
                value={cycle}
                onChange={(e) => setCycle(e.target.value as "Monthly" | "Annual")}
                style={{ width: "100%", height: 36 }}
              >
                <option value="Monthly">Monthly</option>
                <option value="Annual">Annual</option>
              </select>
            </div>
          </div>
        )}

        {isCancel && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 11.5, color: "#888", display: "block", marginBottom: 6 }}>Cancellation Reason</label>
            <textarea
              className="df-input"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="E.g., Customer downsized, switching vendor, or seasonal project finished..."
              style={{ width: "100%", minHeight: 80, padding: 10, boxSizing: "border-box" }}
            />
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 18 }}>
          <button className="df-btn-secondary" onClick={onClose}>Dismiss</button>
          <button
            className={isCancel ? "df-btn-secondary" : "df-btn-primary"}
            style={isCancel ? { background: "#EF4444", color: "#fff", border: "none" } : undefined}
            onClick={handleConfirm}
          >
            {isEdit
              ? "Save Changes"
              : isPlan
              ? "Confirm Plan Change"
              : isPause
              ? isCurrentlyPaused
                ? "Resume Subscription"
                : "Pause Subscription"
              : "Confirm Cancellation"}
          </button>
        </div>
      </motion.div>
    </>
  )
}
function Select({ value, setValue, values }: { value: string; setValue: (value: any) => void; values: string[] }) { return <select className="df-input" value={value} onChange={(e) => setValue(e.target.value)} style={{ ...inputStyle, width: "auto" }}>{values.map((x) => <option key={x}>{x}</option>)}</select> }
function Badge({ status }: { status: Status }) { const color = statusTone[status]; return <span style={{ display: "inline-flex", gap: 5, alignItems: "center", padding: "3px 7px", borderRadius: 4, border: `1px solid ${color}35`, background: `${color}14`, color, fontSize: 11, fontWeight: 600 }}><span style={{ width: 5, height: 5, borderRadius: 5, background: color }}/>{status}</span> }
function Section({ title, children }: { title: string; children: React.ReactNode }) { return <section style={{ paddingTop: 2 }}><div style={{ ...labelStyle, marginBottom: 10 }}>{title}</div><div className="df-card" style={{ padding: 13 }}>{children}</div></section> }
function Field({ label, value }: { label: string; value: string }) { return <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 12, padding: "5px 0" }}><span style={{ color: "#666" }}>{label}</span><span style={{ color: "#ddd", textAlign: "right" }}>{value}</span></div> }
const h1 = { margin: 0, color: "#fff", fontSize: 22, letterSpacing: "-.025em" }; const sub = { margin: "5px 0 0", color: "#555", fontSize: 13 }; const inputStyle = { height: 34, padding: "7px 10px", fontSize: 12, width: 210 }; const th = { color: "#555", fontSize: 10, textAlign: "left" as const, textTransform: "uppercase" as const, letterSpacing: ".07em", padding: "10px 16px", whiteSpace: "nowrap" as const }; const td = { color: "#999", fontSize: 12, padding: "13px 16px" }; const tdStrong = { ...td, color: "#f4f4f5", fontWeight: 600 }; const drawer = { position: "fixed" as const, top: 0, right: 0, bottom: 0, zIndex: 21, width: "min(480px,100vw)", overflowY: "auto" as const, background: "#0b0b0b", borderLeft: "1px solid #252525" }; const drawerHead = { padding: 20, display: "flex", justifyContent: "space-between", borderBottom: "1px solid #202020", position: "sticky" as const, top: 0, background: "#0b0b0b", zIndex: 1 }; const scrim = { position: "fixed" as const, inset: 0, zIndex: 20, border: 0, background: "rgba(0,0,0,.62)" }; const close = { border: 0, background: "none", color: "#aaa", fontSize: 20, cursor: "pointer" }; const labelStyle = { color: "#666", fontSize: 10, fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: ".07em" }
