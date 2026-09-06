import { useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"

type Invoice = {
  id: string
  customer: string
  companyName: string
  address: string
  amount: string
  subtotal: string
  tax: string
  issued: string
  due: string
  status: "Pending" | "Paid" | "Overdue"
  reference: string
  paymentTerms: string
  paymentMethod: string
  items: { name: string; qty: number; price: string; total: string }[]
  timeline: { date: string; text: string }[]
}

const initialInvoices: Invoice[] = [
  {
    id: "INV-3012",
    customer: "Acme",
    companyName: "Acme Corp",
    address: "100 Market Street, San Francisco, CA 94105",
    amount: "$2,400",
    subtotal: "$2,400",
    tax: "$0",
    issued: "Sep 1",
    due: "Sep 30",
    status: "Pending",
    reference: "SUB-2041",
    paymentTerms: "Net 30",
    paymentMethod: "Corporate Visa •••• 4182",
    items: [{ name: "Enterprise platform", qty: 1, price: "$2,400", total: "$2,400" }],
    timeline: [
      { date: "Sep 01", text: "Invoice issued" },
      { date: "Sep 01", text: "Sent to billing contact" },
      { date: "Sep 30", text: "Payment due" },
    ],
  },
  {
    id: "INV-3008",
    customer: "Nova",
    companyName: "Nova Retail Systems",
    address: "420 Indiranagar 100ft Rd, Bangalore, KA 560038",
    amount: "$950",
    subtotal: "$950",
    tax: "$0",
    issued: "Aug 28",
    due: "Sep 28",
    status: "Paid",
    reference: "SUB-2037",
    paymentTerms: "Net 30",
    paymentMethod: "Direct Bank Transfer (NEFT)",
    items: [{ name: "Growth tier platform subscription", qty: 1, price: "$950", total: "$950" }],
    timeline: [
      { date: "Aug 28", text: "Invoice issued" },
      { date: "Aug 29", text: "Sent to accounting contact" },
      { date: "Aug 30", text: "Payment received via NEFT ($950)" },
    ],
  },
  {
    id: "INV-3001",
    customer: "Beta",
    companyName: "Beta Industries Global",
    address: "702 Tech Hub, Bandra Kurla Complex, Mumbai, MH 400051",
    amount: "$4,800",
    subtotal: "$4,800",
    tax: "$0",
    issued: "Aug 15",
    due: "Sep 15",
    status: "Overdue",
    reference: "SUB-2029",
    paymentTerms: "Net 30",
    paymentMethod: "Wire Transfer / ACH",
    items: [
      { name: "Enterprise annual cloud license", qty: 1, price: "$4,800", total: "$4,800" },
    ],
    timeline: [
      { date: "Aug 15", text: "Invoice issued" },
      { date: "Aug 16", text: "Sent to billing contact" },
      { date: "Sep 15", text: "Payment overdue notice triggered" },
    ],
  },
]

const colors = { Pending: "#F59E0B", Paid: "#10B981", Overdue: "#EF4444" }

export default function Billing() {
  const [invoicesData, setInvoicesData] = useState<Invoice[]>(() => {
    try {
      const saved = localStorage.getItem("dealflow_invoices")
      return saved ? JSON.parse(saved) : initialInvoices
    } catch {
      return initialInvoices
    }
  })

  const [query, setQuery] = useState("")
  const [status, setStatus] = useState("All")
  const [customer, setCustomer] = useState("All customers")
  const [selected, setSelected] = useState<Invoice | null>(null)
  const [activeModal, setActiveModal] = useState<"send" | "record" | null>(null)
  const [toastNotice, setToastNotice] = useState<string | null>(null)

  // Modals state
  const [recipientEmail, setRecipientEmail] = useState("")
  const [sendSubject, setSendSubject] = useState("")
  const [sendMessage, setSendMessage] = useState("")
  const [sending, setSending] = useState(false)

  const [paymentMethod, setPaymentMethod] = useState("Credit Card")
  const [paymentAmount, setPaymentAmount] = useState("")
  const [paymentRef, setPaymentRef] = useState("")
  const [recording, setRecording] = useState(false)

  const showToast = (msg: string) => {
    setToastNotice(msg)
    setTimeout(() => setToastNotice(null), 3500)
  }

  const saveInvoices = (list: Invoice[]) => {
    setInvoicesData(list)
    try {
      localStorage.setItem("dealflow_invoices", JSON.stringify(list))
    } catch {}
  }

  const rows = useMemo(() => {
    return invoicesData.filter((x) => {
      const matchStatus = status === "All" || x.status === status
      const matchCustomer = customer === "All customers" || x.customer === customer
      const matchQuery = `${x.id} ${x.customer} ${x.companyName}`.toLowerCase().includes(query.toLowerCase())
      return matchStatus && matchCustomer && matchQuery
    })
  }, [invoicesData, query, status, customer])

  // Download Invoice Action (generates printable HTML / triggers print-save)
  const handleDownloadInvoice = (inv: Invoice) => {
    const printWindow = window.open("", "_blank")
    if (!printWindow) {
      showToast("Pop-up blocked! Please allow pop-ups to download invoice PDF.")
      return
    }

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Invoice - ${inv.id}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 40px; color: #111; max-width: 800px; margin: 0 auto; line-height: 1.5; }
          .header { display: flex; justify-content: space-between; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 24px; }
          .logo { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; color: #000; }
          .title { font-size: 20px; font-weight: 700; color: #555; }
          .badge { display: inline-block; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 12px; text-transform: uppercase; background: ${inv.status === 'Paid' ? '#dcfce7; color: #166534;' : inv.status === 'Overdue' ? '#fee2e2; color: #991b1b;' : '#fef3c7; color: #92400e;'} }
          .grid { display: flex; justify-content: space-between; margin-bottom: 28px; }
          .box { width: 48%; }
          .box-title { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #777; margin-bottom: 6px; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 24px; margin-top: 16px; }
          th { text-align: left; padding: 10px 8px; border-bottom: 1px solid #ccc; font-size: 12px; text-transform: uppercase; color: #555; }
          td { padding: 12px 8px; border-bottom: 1px solid #eee; font-size: 13px; }
          .summary { float: right; width: 280px; margin-bottom: 30px; }
          .summary-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; }
          .total { font-weight: 800; font-size: 16px; border-top: 1px solid #333; padding-top: 10px; margin-top: 6px; }
          .footer { clear: both; border-top: 1px solid #eee; padding-top: 20px; font-size: 11px; color: #888; text-align: center; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="logo">DealFlow360</div>
            <div style="color: #666; font-size: 12px; margin-top: 4px;">Enterprise Commercial Cloud Platform</div>
          </div>
          <div style="text-align: right;">
            <div class="title">${inv.id}</div>
            <div style="margin-top: 6px;"><span class="badge">${inv.status}</span></div>
          </div>
        </div>

        <div class="grid">
          <div class="box">
            <div class="box-title">Billed To</div>
            <strong style="font-size: 14px;">${inv.companyName}</strong><br/>
            ${inv.address}<br/>
            Reference: ${inv.reference}
          </div>
          <div class="box" style="text-align: right;">
            <div class="box-title">Invoice Details</div>
            <strong>Issue Date:</strong> ${inv.issued}<br/>
            <strong>Due Date:</strong> ${inv.due}<br/>
            <strong>Payment Terms:</strong> ${inv.paymentTerms}<br/>
            <strong>Payment Method:</strong> ${inv.paymentMethod}
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>Item & Description</th>
              <th style="text-align: center;">Qty</th>
              <th style="text-align: right;">Unit Price</th>
              <th style="text-align: right;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${inv.items.map(item => `
              <tr>
                <td><strong>${item.name}</strong></td>
                <td style="text-align: center;">${item.qty}</td>
                <td style="text-align: right;">${item.price}</td>
                <td style="text-align: right;"><strong>${item.total}</strong></td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <div class="summary">
          <div class="summary-row"><span>Subtotal:</span><span>${inv.subtotal}</span></div>
          <div class="summary-row"><span>Tax (0%):</span><span>${inv.tax}</span></div>
          <div class="summary-row total"><span>Total Due:</span><span>${inv.amount}</span></div>
        </div>

        <div class="footer">
          Thank you for choosing DealFlow360. For questions, contact billing@dealflow360.io.
        </div>

        <script>
          window.onload = function() {
            setTimeout(function() {
              window.print();
            }, 300);
          }
        </script>
      </body>
      </html>
    `

    printWindow.document.open()
    printWindow.document.write(html)
    printWindow.document.close()
    showToast(`Invoice ${inv.id} downloaded / sent to print queue`)
  }

  // Open Send Modal
  const openSendModal = (inv: Invoice) => {
    setRecipientEmail(`billing@${inv.customer.toLowerCase()}.com`)
    setSendSubject(`Invoice ${inv.id} from DealFlow360 - ${inv.amount}`)
    setSendMessage(`Hi ${inv.companyName} Accounts Team,\n\nPlease find attached invoice ${inv.id} for the amount of ${inv.amount}, due on ${inv.due}.\n\nYou can pay securely online or through bank transfer.\n\nBest regards,\nDealFlow360 Finance`)
    setActiveModal("send")
  }

  // Handle Send Execution
  const handleConfirmSend = () => {
    if (!selected) return
    setSending(true)
    setTimeout(() => {
      const updatedTimeline = [
        ...selected.timeline,
        { date: "Just now", text: `Invoice sent to ${recipientEmail}` },
      ]
      const updatedList = invoicesData.map((x) =>
        x.id === selected.id ? { ...x, timeline: updatedTimeline } : x
      )
      saveInvoices(updatedList)
      setSelected({ ...selected, timeline: updatedTimeline })
      setSending(false)
      setActiveModal(null)
      showToast(`Invoice ${selected.id} successfully sent to ${recipientEmail}`)
    }, 600)
  }

  // Open Record Payment Modal
  const openRecordPaymentModal = (inv: Invoice) => {
    setPaymentAmount(inv.amount.replace(/[^0-9.]/g, ""))
    setPaymentRef(`PAY-${Math.floor(100000 + Math.random() * 900000)}`)
    setPaymentMethod("Credit Card")
    setActiveModal("record")
  }

  // Handle Record Payment Execution
  const handleConfirmRecordPayment = () => {
    if (!selected) return
    setRecording(true)
    setTimeout(() => {
      const updatedTimeline = [
        ...selected.timeline,
        {
          date: "Just now",
          text: `Payment of $${Number(paymentAmount).toLocaleString("en-US")} recorded via ${paymentMethod} (Ref: ${paymentRef})`,
        },
      ]
      const updatedList = invoicesData.map((x) =>
        x.id === selected.id ? { ...x, status: "Paid" as const, timeline: updatedTimeline } : x
      )
      saveInvoices(updatedList)
      setSelected({ ...selected, status: "Paid", timeline: updatedTimeline })
      setRecording(false)
      setActiveModal(null)
      showToast(`Payment of $${Number(paymentAmount).toLocaleString("en-US")} recorded for ${selected.id}`)
    }, 600)
  }

  return (
    <div style={{ padding: 28, maxWidth: 1440, margin: "0 auto", position: "relative" }}>
      {/* Toast Notice */}
      <AnimatePresence>
        {toastNotice && (
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
            <span>{toastNotice}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: 16,
          marginBottom: 22,
        }}
      >
        <div>
          <h1 style={h1}>Invoices</h1>
          <p style={sub}>Invoice management and payment tracking.</p>
        </div>
        <button
          className="df-btn-secondary"
          onClick={() => {
            const blob = new Blob(
              [JSON.stringify(invoicesData, null, 2)],
              { type: "application/json" }
            )
            const url = URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url
            a.download = `dealflow_invoices_${new Date().toISOString().slice(0, 10)}.json`
            a.click()
            URL.revokeObjectURL(url)
            showToast("Invoices export downloaded")
          }}
        >
          Export
        </button>
      </header>

      <section className="df-card" style={{ overflow: "hidden" }}>
        <div
          style={{
            padding: "14px 16px",
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            borderBottom: "1px solid #1a1a1a",
          }}
        >
          <input
            className="df-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search invoices…"
            style={input}
          />
          <select
            className="df-input"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            style={select}
          >
            {["All", "Pending", "Paid", "Overdue"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
          <select
            className="df-input"
            value={customer}
            onChange={(e) => setCustomer(e.target.value)}
            style={select}
          >
            {["All customers", "Acme", "Nova", "Beta"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
          <input
            className="df-input"
            type="date"
            aria-label="Invoice date filter"
            style={{ ...input, width: 145 }}
          />
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", minWidth: 820, borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Invoice", "Customer", "Amount", "Issue date", "Due date", "Status"].map((x) => (
                  <th key={x} style={th}>
                    {x}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => (
                <motion.tr
                  key={item.id}
                  onClick={() => setSelected(item)}
                  whileHover={{ background: "rgba(255,255,255,.025)" }}
                  style={{
                    cursor: "pointer",
                    borderTop: "1px solid #121212",
                    background: selected?.id === item.id ? "rgba(255,255,255,0.04)" : "transparent",
                  }}
                >
                  <td className="mono" style={strong}>
                    {item.id}
                  </td>
                  <td style={strong}>{item.customer}</td>
                  <td className="mono" style={strong}>
                    {item.amount}
                  </td>
                  <td style={td}>{item.issued}</td>
                  <td style={{ ...td, color: item.status === "Overdue" ? "#EF4444" : "#999" }}>
                    {item.due}
                  </td>
                  <td style={td}>
                    <Badge status={item.status} />
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Invoice Detail Drawer */}
      <AnimatePresence>
        {selected && (
          <>
            <motion.button
              aria-label="Close invoice detail"
              onClick={() => setSelected(null)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={scrim}
            />
            <motion.aside
              initial={{ x: 480 }}
              animate={{ x: 0 }}
              exit={{ x: 480 }}
              transition={{ duration: 0.22 }}
              style={drawer}
            >
              <div style={head}>
                <div>
                  <div className="mono" style={{ color: "#fff", fontWeight: 700 }}>
                    {selected.id}
                  </div>
                  <div style={{ color: "#888", fontSize: 12, marginTop: 4 }}>
                    {selected.customer} · <Badge status={selected.status} />
                  </div>
                </div>
                <button onClick={() => setSelected(null)} style={close}>
                  ×
                </button>
              </div>

              <div style={{ padding: 20, display: "grid", gap: 16 }}>
                <section>
                  <div style={label}>Invoice details</div>
                  <div className="df-card" style={{ padding: 13, marginTop: 9 }}>
                    <Row label="Issue date" value={selected.issued} />
                    <Row label="Due date" value={selected.due} />
                    <Row label="Payment terms" value={selected.paymentTerms} />
                    <Row label="Reference" value={selected.reference} />
                  </div>
                </section>

                <section>
                  <div style={label}>Bill to</div>
                  <div
                    className="df-card"
                    style={{
                      padding: 13,
                      marginTop: 9,
                      color: "#ccc",
                      fontSize: 12,
                      lineHeight: 1.65,
                    }}
                  >
                    <strong>{selected.companyName}</strong>
                    <br />
                    {selected.address}
                  </div>
                </section>

                <section>
                  <div style={label}>Items</div>
                  <div className="df-card" style={{ marginTop: 9, overflow: "hidden" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                      <thead>
                        <tr>
                          {["Item", "Qty", "Price", "Disc.", "Tax", "Total"].map((x) => (
                            <th key={x} style={{ ...th, padding: 10 }}>
                              {x}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {selected.items.map((row) => (
                          <tr key={row.name}>
                            <td style={{ ...td, padding: 10, color: "#fff" }}>{row.name}</td>
                            <td style={{ ...td, padding: 10 }}>{row.qty}</td>
                            <td style={{ ...td, padding: 10 }}>{row.price}</td>
                            <td style={{ ...td, padding: 10 }}>—</td>
                            <td style={{ ...td, padding: 10 }}>$0</td>
                            <td style={{ ...td, padding: 10, color: "#fff", fontWeight: 700 }}>
                              {row.total}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="df-card" style={{ padding: 13 }}>
                  <Row label="Subtotal" value={selected.subtotal} />
                  <Row label="Discount" value="$0" />
                  <Row label="Tax" value={selected.tax} />
                  <Row label="Total due" value={selected.amount} strong />
                </section>

                <section>
                  <div style={label}>Payment & timeline</div>
                  <div style={{ color: "#aaa", fontSize: 12, lineHeight: 2, marginTop: 7 }}>
                    <div>
                      Payment method: <span style={{ color: "#fff" }}>{selected.paymentMethod}</span>
                    </div>
                    {selected.timeline.map((event, idx) => (
                      <div key={idx} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ color: "#666", fontSize: 11, minWidth: 50 }}>{event.date}</span>
                        <span style={{ color: "#bbb" }}>· {event.text}</span>
                      </div>
                    ))}
                  </div>
                </section>

                {/* ACTION BUTTONS: Download, Send, Record Payment */}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
                  <button
                    className="df-btn-secondary"
                    onClick={() => handleDownloadInvoice(selected)}
                    style={{ display: "flex", alignItems: "center", gap: 6 }}
                  >
                    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download
                  </button>
                  <button
                    className="df-btn-secondary"
                    onClick={() => openSendModal(selected)}
                    style={{ display: "flex", alignItems: "center", gap: 6 }}
                  >
                    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    Send
                  </button>
                  <button
                    className="df-btn-primary"
                    onClick={() => openRecordPaymentModal(selected)}
                    style={{
                      background: selected.status === "Paid" ? "#064e3b" : "#fff",
                      color: selected.status === "Paid" ? "#34d399" : "#000",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {selected.status === "Paid" ? "Payment Settled ✓" : "Record Payment"}
                  </button>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* SEND INVOICE MODAL */}
      <AnimatePresence>
        {activeModal === "send" && selected && (
          <>
            <motion.button
              onClick={() => setActiveModal(null)}
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
                width: 480,
                zIndex: 31,
                padding: 24,
                borderRadius: 10,
                border: "1px solid #27272a",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <h2 style={{ color: "#fff", fontSize: 17, margin: 0, fontWeight: 700 }}>
                  Send Invoice {selected.id}
                </h2>
                <button onClick={() => setActiveModal(null)} style={close}>
                  ×
                </button>
              </div>

              <div style={{ display: "grid", gap: 12 }}>
                <div>
                  <label style={label}>Recipient Email</label>
                  <input
                    className="df-input"
                    value={recipientEmail}
                    onChange={(e) => setRecipientEmail(e.target.value)}
                    style={{ ...input, width: "100%", marginTop: 6 }}
                  />
                </div>

                <div>
                  <label style={label}>Subject</label>
                  <input
                    className="df-input"
                    value={sendSubject}
                    onChange={(e) => setSendSubject(e.target.value)}
                    style={{ ...input, width: "100%", marginTop: 6 }}
                  />
                </div>

                <div>
                  <label style={label}>Email Message</label>
                  <textarea
                    className="df-input"
                    value={sendMessage}
                    onChange={(e) => setSendMessage(e.target.value)}
                    rows={4}
                    style={{
                      width: "100%",
                      marginTop: 6,
                      fontSize: 12,
                      padding: 10,
                      resize: "vertical",
                      fontFamily: "inherit",
                    }}
                  />
                </div>

                <div
                  style={{
                    padding: 10,
                    borderRadius: 6,
                    background: "#18181b",
                    border: "1px solid #27272a",
                    fontSize: 12,
                    color: "#A1A1AA",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <span>📎</span>
                  <span>Attachment: <strong>{selected.id}.pdf</strong> ({selected.amount})</span>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
                  <button className="df-btn-secondary" onClick={() => setActiveModal(null)}>
                    Cancel
                  </button>
                  <button
                    className="df-btn-primary"
                    disabled={sending}
                    onClick={handleConfirmSend}
                  >
                    {sending ? "Sending..." : "Send Invoice"}
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* RECORD PAYMENT MODAL */}
      <AnimatePresence>
        {activeModal === "record" && selected && (
          <>
            <motion.button
              onClick={() => setActiveModal(null)}
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
                width: 460,
                zIndex: 31,
                padding: 24,
                borderRadius: 10,
                border: "1px solid #27272a",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <h2 style={{ color: "#fff", fontSize: 17, margin: 0, fontWeight: 700 }}>
                  Record Payment for {selected.id}
                </h2>
                <button onClick={() => setActiveModal(null)} style={close}>
                  ×
                </button>
              </div>

              <div style={{ display: "grid", gap: 12 }}>
                <div>
                  <label style={label}>Payment Amount ($)</label>
                  <input
                    type="number"
                    className="df-input"
                    value={paymentAmount}
                    onChange={(e) => setPaymentAmount(e.target.value)}
                    style={{ ...input, width: "100%", marginTop: 6 }}
                  />
                </div>

                <div>
                  <label style={label}>Payment Method</label>
                  <select
                    className="df-input"
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    style={{ ...select, width: "100%", marginTop: 6 }}
                  >
                    <option value="Credit Card">Corporate Credit Card (Visa/Mastercard)</option>
                    <option value="Bank Transfer">Bank Transfer / NEFT / RTGS</option>
                    <option value="ACH / Wire">ACH / Wire Transfer</option>
                    <option value="Cheque">Corporate Cheque</option>
                  </select>
                </div>

                <div>
                  <label style={label}>Transaction Reference / Cheque No.</label>
                  <input
                    className="df-input"
                    value={paymentRef}
                    onChange={(e) => setPaymentRef(e.target.value)}
                    placeholder="e.g. TXN-984210"
                    style={{ ...input, width: "100%", marginTop: 6 }}
                  />
                </div>

                <div
                  style={{
                    padding: 12,
                    borderRadius: 6,
                    background: "rgba(16, 185, 129, 0.08)",
                    border: "1px solid rgba(16, 185, 129, 0.25)",
                    fontSize: 12,
                    color: "#34D399",
                  }}
                >
                  Recording this payment will immediately update the invoice status from <strong>{selected.status}</strong> to <strong>Paid</strong>.
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
                  <button className="df-btn-secondary" onClick={() => setActiveModal(null)}>
                    Cancel
                  </button>
                  <button
                    className="df-btn-primary"
                    disabled={recording}
                    onClick={handleConfirmRecordPayment}
                  >
                    {recording ? "Recording..." : "Confirm Payment"}
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

function Badge({ status }: { status: Invoice["status"] }) {
  const color = colors[status]
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        color,
        fontSize: 11,
        fontWeight: 600,
        border: `1px solid ${color}35`,
        background: `${color}14`,
        borderRadius: 4,
        padding: "3px 7px",
      }}
    >
      <span style={{ width: 5, height: 5, borderRadius: 5, background: color }} />
      {status}
    </span>
  )
}

function Row({
  label: key,
  value,
  strong: emph,
}: {
  label: string
  value: string
  strong?: boolean
}) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", fontSize: 12 }}>
      <span style={{ color: "#666" }}>{key}</span>
      <span className={emph ? "mono" : ""} style={{ color: "#eee", fontWeight: emph ? 800 : 500 }}>
        {value}
      </span>
    </div>
  )
}

const h1 = { margin: 0, color: "#fff", fontSize: 22, letterSpacing: "-.025em" }
const sub = { margin: "5px 0 0", color: "#555", fontSize: 13 }
const input = { height: 34, padding: "7px 10px", fontSize: 12, width: 210 }
const select = { ...input, width: "auto" }
const th = {
  color: "#555",
  fontSize: 10,
  textAlign: "left" as const,
  textTransform: "uppercase" as const,
  letterSpacing: ".07em",
  padding: "10px 16px",
  whiteSpace: "nowrap" as const,
}
const td = { color: "#999", fontSize: 12, padding: "13px 16px" }
const strong = { ...td, color: "#f4f4f5", fontWeight: 600 }
const scrim = {
  position: "fixed" as const,
  inset: 0,
  zIndex: 20,
  border: 0,
  background: "rgba(0,0,0,.62)",
}
const drawer = {
  position: "fixed" as const,
  top: 0,
  right: 0,
  bottom: 0,
  zIndex: 21,
  width: "min(480px,100vw)",
  overflowY: "auto" as const,
  background: "#0b0b0b",
  borderLeft: "1px solid #252525",
}
const head = {
  padding: 20,
  display: "flex",
  justifyContent: "space-between",
  borderBottom: "1px solid #202020",
  position: "sticky" as const,
  top: 0,
  background: "#0b0b0b",
  zIndex: 1,
}
const close = { border: 0, background: "none", color: "#aaa", fontSize: 20, cursor: "pointer" }
const label = {
  color: "#666",
  fontSize: 10,
  fontWeight: 700,
  textTransform: "uppercase" as const,
  letterSpacing: ".07em",
}
