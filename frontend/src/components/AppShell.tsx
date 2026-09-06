import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { AnimatedDropdown, PageTransition } from "../lib/motion"
import CommandCenter from "../pages/CommandCenter"
import Products from "../pages/Products"
import QuoteWorkspace from "../pages/QuoteWorkspace"
import Approvals from "../pages/Approvals"
import RiskCenter from "../pages/RiskCenter"
import Customers from "../pages/Customers"
import Deals from "../pages/Deals"
import Billing from "../pages/Billing"
import Analytics from "../pages/Analytics"
import AICopilot from "../pages/AICopilot"
import OrdersFulfillment from "../pages/OrdersFulfillment"
import FulfillmentStock from "../pages/FulfillmentStock"
import Subscriptions from "../pages/Subscriptions"
import CustomerPortal from "../pages/CustomerPortal"
import QuotesList from "../pages/QuotesList"
import AuditCenter from "../pages/AuditCenter"
import Notifications from "../pages/Notifications"
import Settings from "../pages/Settings"
import { useNotifications } from "../hooks/useNotifications"
import type { User } from "../types/user"
import { mockCurrentUser } from "../mocks/users"
import { authService } from "../services/authService"
import { api } from "../lib/api"

export type AppView =
  | "command"
  | "copilot"
  | "deals"
  | "quotes"
  | "quote-detail"
  | "approvals"
  | "risk"
  | "customers"
  | "products"
  | "fulfillment"
  | "stock"
  | "subscriptions"
  | "billing"
  | "analytics"
  | "portal"
  | "notifications"
  | "audit"
  | "settings"

interface NavItem {
  id: AppView
  label: string
  icon: React.ReactNode
}

function Icon({ d, size = 16 }: { d: string | string[]; size?: number }) {
  const paths = Array.isArray(d) ? d : [d]
  return (
    <svg
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      viewBox="0 0 24 24"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths.map((p, i) => (
        <path key={i} d={p} />
      ))}
    </svg>
  )
}

const navItems: NavItem[] = [
  {
    id: "command",
    label: "Command Center",
    icon: (
      <Icon d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    ),
  },
  {
    id: "copilot",
    label: "AI Copilot",
    icon: (
      <Icon d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    ),
  },
  {
    id: "deals",
    label: "Deals",
    icon: (
      <Icon d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    ),
  },
  {
    id: "quotes",
    label: "Requests",
    icon: (
      <Icon d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    ),
  },
  {
    id: "approvals",
    label: "Approvals",
    icon: <Icon d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />,
  },
  {
    id: "risk",
    label: "Risk & Compliance",
    icon: (
      <Icon d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    ),
  },
  {
    id: "customers",
    label: "Customers",
    icon: (
      <Icon
        d={[
          "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z",
        ]}
      />
    ),
  },
  {
    id: "products",
    label: "Products",
    icon: (
      <Icon d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    ),
  },
  {
    id: "fulfillment",
    label: "Orders & Fulfillment",
    icon: (
      <Icon
        d={[
          "M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4",
        ]}
      />
    ),
  },
  {
    id: "subscriptions",
    label: "Subscriptions",
    icon: <Icon d="M12 8c-3.314 0-6-1.119-6-2.5S8.686 3 12 3s6 1.119 6 2.5S15.314 8 12 8zm-6-2.5V12c0 1.381 2.686 2.5 6 2.5s6-1.119 6-2.5V5.5M6 12v6.5C6 19.881 8.686 21 12 21s6-1.119 6-2.5V12" />,
  },
  {
    id: "billing",
    label: "Billing & Payments",
    icon: (
      <Icon
        d={[
          "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z",
        ]}
      />
    ),
  },
  {
    id: "analytics",
    label: "Analytics & Reports",
    icon: (
      <Icon d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    ),
  },
  {
    id: "notifications",
    label: "Notifications",
    icon: (
      <Icon d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    ),
  },
  {
    id: "audit",
    label: "Audit & Security",
    icon: (
      <Icon d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    ),
  },
  {
    id: "settings",
    label: "System Settings",
    icon: (
      <Icon d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    ),
  },
  {
    id: "portal",
    label: "Customer Portal",
    icon: <Icon d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2m18-9a4 4 0 11-8 0 4 4 0 018 0zM10 7a4 4 0 11-8 0 4 4 0 018 0z" />,
  },
]

interface Props {
  currentUser?: User
  onLogout: () => void
  initialView?: AppView
}

export default function AppShell({
  currentUser,
  onLogout,
  initialView = "command",
}: Props) {
  const user = currentUser || mockCurrentUser
  const [view, setView] = useState<AppView>(initialView)
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()
  const [search, setSearch] = useState("")
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchSuggestions, setSearchSuggestions] = useState<{
    deals: any[]
    customers: any[]
    products: any[]
  }>({ deals: [], customers: [], products: [] })
  const searchContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setSearchOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  useEffect(() => {
    const q = search.trim()
    if (!q) {
      setSearchSuggestions({ deals: [], customers: [], products: [] })
      return
    }

    const timer = setTimeout(async () => {
      try {
        const [dealsRes, custRes, prodRes] = await Promise.all([
          api.deals.list({ search: q, limit: 4 }).catch(() => []),
          api.customers.list({ search: q, limit: 4 }).catch(() => ({ items: [] })),
          api.products.list({ search: q, limit: 4 }).catch(() => ({ items: [] })),
        ])

        const deals = Array.isArray(dealsRes) ? dealsRes : (dealsRes as any)?.items || (dealsRes as any)?.data || []
        const customers = Array.isArray(custRes) ? custRes : (custRes as any)?.items || (custRes as any)?.data?.items || []
        const products = Array.isArray(prodRes) ? prodRes : (prodRes as any)?.items || (prodRes as any)?.data?.items || []

        setSearchSuggestions({ deals, customers, products })
      } catch {
        // Fallback
      }
    }, 200)

    return () => clearTimeout(timer)
  }, [search])
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [changePasswordOpen, setChangePasswordOpen] = useState(false)
  const [currentPw, setCurrentPw] = useState("")
  const [newPw, setNewPw] = useState("")
  const [confirmPw, setConfirmPw] = useState("")
  const [pwLoading, setPwLoading] = useState(false)
  const [pwNotice, setPwNotice] = useState("")
  const [pwError, setPwError] = useState("")
  const [fulfillmentContext, setFulfillmentContext] =
    useState<string | undefined>()
  const [selectedRequestId, setSelectedRequestId] = useState<string | undefined>()
  const [requestWorkspaceMode, setRequestWorkspaceMode] = useState<"create" | "details" | "edit">("details")

  useEffect(() => {
    const handleResize = () => {
      if (typeof window !== "undefined" && window.innerWidth < 1024) {
        setSidebarCollapsed(true)
      }
    }
    handleResize()
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  const handleOpenRequest = (id?: string, mode: "create" | "details" | "edit" = "details") => {
    setSelectedRequestId(id)
    setRequestWorkspaceMode(mode)
    setView("quote-detail")
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwError("")
    setPwNotice("")

    if (!currentPw) {
      setPwError("Please enter your current password.")
      return
    }
    if (!newPw || newPw.length < 6) {
      setPwError("New password must be at least 6 characters.")
      return
    }
    if (newPw !== confirmPw) {
      setPwError("New passwords do not match.")
      return
    }

    setPwLoading(true)
    try {
      await authService.changePassword(currentPw, newPw)
      setPwNotice("Password successfully updated! Your next sign-in will use this password.")
      setCurrentPw("")
      setNewPw("")
      setConfirmPw("")
    } catch (err: any) {
      setPwError(err?.message || "Failed to update password.")
    } finally {
      setPwLoading(false)
    }
  }

  const currentLabel =
    view === "quote-detail"
      ? "Request Workspace"
      : view === "quotes"
      ? "Requests"
      : navItems.find((n) => n.id === view)?.label ?? "Command Center"

  function renderView() {
    switch (view) {
      case "command":
        return (
          <CommandCenter
            onNavigate={setView}
            onOpenOrders={(status) => {
              setFulfillmentContext(status)
              setView("fulfillment")
            }}
            onOpenRequest={(id) => handleOpenRequest(id, "details")}
          />
        )
      case "copilot":
        return <AICopilot />
      case "deals":
        return (
          <Deals
            onNavigate={(targetView, resourceId) => {
              if (targetView === "quote-detail" && resourceId) {
                handleOpenRequest(resourceId, "details")
              } else {
                setView(targetView as AppView)
              }
            }}
          />
        )
      case "quotes":
        return (
          <QuotesList
            onOpenQuote={(id, reqMode) => handleOpenRequest(id, reqMode || "details")}
          />
        )
      case "quote-detail":
        return (
          <QuoteWorkspace
            requestId={selectedRequestId}
            initialMode={requestWorkspaceMode}
            onBack={() => setView("quotes")}
          />
        )
      case "approvals":
        return <Approvals />
      case "risk":
        return <RiskCenter />
      case "customers":
        return <Customers />
      case "products":
        return <Products onAddToQuote={() => setView("quotes")} />
      case "fulfillment":
        return <OrdersFulfillment initialStatus={fulfillmentContext} />
      case "stock":
        return <FulfillmentStock />
      case "subscriptions":
        return <Subscriptions />
      case "billing":
        return <Billing />
      case "analytics":
        return <Analytics />
      case "notifications":
        return (
          <Notifications
            onNavigateView={(targetView, resourceId) => {
              if (targetView === "quotes" && resourceId) {
                handleOpenRequest(resourceId, "details")
              } else if (targetView === "deals" && resourceId) {
                handleOpenRequest(resourceId, "details")
              } else {
                setView(targetView as AppView)
              }
            }}
          />
        )
      case "audit":
        return <AuditCenter />
      case "settings":
        return <Settings />
      case "portal":
        return <CustomerPortal />
      default:
        return (
          <CommandCenter
            onNavigate={setView}
            onOpenOrders={(status) => {
              setFulfillmentContext(status)
              setView("fulfillment")
            }}
          />
        )
    }
  }

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        background: "#000",
        overflow: "hidden",
      }}
    >
      {/* Sidebar */}
      <motion.aside
        animate={{ width: sidebarCollapsed ? 52 : 220 }}
        transition={{ duration: 0.22, ease: [0.4, 0.0, 0.2, 1.0] }}
        style={{
          background: "#050505",
          borderRight: "1px solid #141414",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
          overflow: "hidden",
        }}
      >
        {/* Logo */}
        <div
          style={{
            padding: "16px 14px",
            borderBottom: "1px solid #141414",
            display: "flex",
            alignItems: "center",
            gap: 8,
            height: 56,
          }}
        >
          <img
            src="/logo.png"
            alt="DealFlow360"
            style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              objectFit: "cover",
              flexShrink: 0,
              boxShadow: "0 0 12px rgba(59, 130, 246, 0.4)",
              border: "1px solid rgba(59, 130, 246, 0.3)",
            }}
          />
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.span
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ duration: 0.15 }}
                style={{
                  fontWeight: 700,
                  fontSize: 14,
                  color: "#fff",
                  letterSpacing: "-0.025em",
                  whiteSpace: "nowrap",
                }}
              >
                DealFlow360
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Nav */}
        <div style={{ flex: 1, overflowY: "auto", padding: "10px 8px" }}>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.12 }}
                style={{
                  fontSize: 10,
                  color: "#333",
                  fontWeight: 600,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  padding: "8px 6px 4px",
                }}
              >
                Main
              </motion.div>
            )}
          </AnimatePresence>

          {navItems.slice(0, 6).map((item) => (
            <motion.button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => setView(item.id)}
              title={sidebarCollapsed ? item.label : undefined}
              style={{
                justifyContent: sidebarCollapsed ? "center" : "flex-start",
                padding: sidebarCollapsed ? "8px" : "8px 10px",
                position: "relative",
              }}
              whileHover={{ backgroundColor: "rgba(255,255,255,0.04)" }}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.1 }}
            >
              {view === item.id && (
                <motion.div
                  layoutId="activeIndicator"
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 4,
                    bottom: 4,
                    width: 2,
                    background: "#fff",
                    borderRadius: 1,
                  }}
                  transition={{ duration: 0.2, ease: [0.4, 0.0, 0.2, 1.0] }}
                />
              )}
              {item.icon}
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -6 }}
                    transition={{ duration: 0.14 }}
                    style={{ whiteSpace: "nowrap", overflow: "hidden" }}
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              {!sidebarCollapsed && item.id === "approvals" && user.permissions.includes("approval:review") && (
                <span
                  style={{
                    marginLeft: "auto",
                    background: "#EF4444",
                    color: "#fff",
                    fontSize: 10,
                    fontWeight: 700,
                    borderRadius: 4,
                    padding: "1px 5px",
                    flexShrink: 0,
                  }}
                >
                  7
                </span>
              )}
              {!sidebarCollapsed && item.id === "copilot" && (
                <motion.span
                  style={{
                    marginLeft: "auto",
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "#7C3AED",
                    flexShrink: 0,
                    display: "block",
                  }}
                  animate={{ opacity: [1, 0.4, 1] }}
                  transition={{ duration: 2.5, repeat: Infinity }}
                />
              )}
            </motion.button>
          ))}

          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.12 }}
                style={{
                  fontSize: 10,
                  color: "#333",
                  fontWeight: 600,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  padding: "12px 6px 4px",
                }}
              >
                Operations
              </motion.div>
            )}
          </AnimatePresence>

          {navItems.slice(6).map((item) => (
            <motion.button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => setView(item.id)}
              title={sidebarCollapsed ? item.label : undefined}
              style={{
                justifyContent: sidebarCollapsed ? "center" : "flex-start",
                padding: sidebarCollapsed ? "8px" : "8px 10px",
                position: "relative",
              }}
              whileHover={{ backgroundColor: "rgba(255,255,255,0.04)" }}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.1 }}
            >
              {view === item.id && (
                <motion.div
                  layoutId="activeIndicator"
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 4,
                    bottom: 4,
                    width: 2,
                    background: "#fff",
                    borderRadius: 1,
                  }}
                  transition={{ duration: 0.2, ease: [0.4, 0.0, 0.2, 1.0] }}
                />
              )}
              {item.icon}
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -6 }}
                    transition={{ duration: 0.14 }}
                    style={{ whiteSpace: "nowrap" }}
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              {!sidebarCollapsed && item.id === "notifications" && unreadCount > 0 && (
                <span
                  style={{
                    marginLeft: "auto",
                    background: "#EF4444",
                    color: "#fff",
                    fontSize: 10,
                    fontWeight: 700,
                    borderRadius: 4,
                    padding: "1px 5px",
                    flexShrink: 0,
                  }}
                >
                  {unreadCount}
                </span>
              )}
            </motion.button>
          ))}

          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.12 }}
              >
                <div
                  style={{
                    fontSize: 10,
                    color: "#333",
                    fontWeight: 600,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    padding: "12px 6px 4px",
                  }}
                >
                  Config
                </div>
                {[
                  { label: "Settings", target: "settings" as AppView },
                  { label: "Users & Roles", target: "audit" as AppView },
                  { label: "Integrations", target: "settings" as AppView },
                ].map(({ label, target }) => (
                  <motion.button
                    key={label}
                    onClick={() => setView(target)}
                    className={`nav-item ${view === target ? "active" : ""}`}
                    style={{ color: view === target ? "#fff" : "#71717A" }}
                    whileHover={{ backgroundColor: "rgba(255,255,255,0.03)", color: "#fff" }}
                  >
                    <Icon d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    {label}
                  </motion.button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User */}
        <div style={{ borderTop: "1px solid #141414", padding: "12px 10px" }}>
          <div
            onClick={() => setProfileOpen(true)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              cursor: "pointer",
              borderRadius: 6,
              padding: "4px 4px",
            }}
            title="Open Profile & Settings"
          >
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: "50%",
                background: "#1a1a1a",
                border: "1px solid #333",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 11,
                fontWeight: 700,
                color: "#A1A1AA",
                flexShrink: 0,
              }}
            >
              {user.initials || "DF"}
            </div>
            <AnimatePresence>
              {!sidebarCollapsed && (
                <motion.div
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  transition={{ duration: 0.14 }}
                  style={{ flex: 1, overflow: "hidden" }}
                >
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
                    {user.name}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: "#71717A",
                      textTransform: "capitalize",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {user.role ? user.role.replace(/_/g, " ") : "Member"}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <AnimatePresence>
              {!sidebarCollapsed && (
                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={onLogout}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: "#333",
                    padding: 4,
                  }}
                  whileHover={{ color: "#fff" }}
                  transition={{ duration: 0.12 }}
                >
                  <Icon
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    size={14}
                  />
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.aside>

      {/* Main */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Topbar */}
        <header
          style={{
            height: 56,
            borderBottom: "1px solid #141414",
            background: "#050505",
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "0 20px",
            flexShrink: 0,
          }}
        >
          <motion.button
            onClick={() => setSidebarCollapsed((c) => !c)}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "#444",
              padding: 4,
              borderRadius: 5,
              display: "flex",
            }}
            whileHover={{ color: "#fff" }}
            whileTap={{ scale: 0.92 }}
            transition={{ duration: 0.12 }}
          >
            <Icon d={["M4 6h16M4 12h16M4 18h16"]} size={16} />
          </motion.button>

          <div style={{ width: 1, height: 20, background: "#1a1a1a" }} />

          <AnimatePresence mode="wait">
            <motion.span
              key={view}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.15 }}
              style={{ fontSize: 13.5, fontWeight: 600, color: "#fff" }}
            >
              {currentLabel}
            </motion.span>
          </AnimatePresence>

          <div
            ref={searchContainerRef}
            style={{
              flex: 1,
              maxWidth: 440,
              marginLeft: 24,
              position: "relative",
            }}
          >
            <div
              style={{
                position: "absolute",
                left: 10,
                top: "50%",
                transform: "translateY(-50%)",
                color: "#444",
                pointerEvents: "none",
              }}
            >
              <Icon d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" size={13} />
            </div>
            <motion.input
              className="df-input"
              type="text"
              placeholder="Search deals, customers, products..."
              value={search}
              onFocus={() => setSearchOpen(true)}
              onChange={(e) => {
                setSearch(e.target.value)
                setSearchOpen(true)
              }}
              style={{
                paddingLeft: 32,
                fontSize: 13,
                height: 34,
                width: "100%",
                boxSizing: "border-box",
                borderRadius: 6,
              }}
              whileFocus={{ borderColor: "#444" }}
              transition={{ duration: 0.15 }}
            />

            {/* Global Search Autocomplete Recommendations Dropdown */}
            <AnimatePresence>
              {searchOpen && (searchSuggestions.deals.length > 0 || searchSuggestions.customers.length > 0 || searchSuggestions.products.length > 0) && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 6 }}
                  transition={{ duration: 0.12 }}
                  style={{
                    position: "absolute",
                    top: "100%",
                    left: 0,
                    right: 0,
                    marginTop: 6,
                    background: "#0d0d0f",
                    border: "1px solid #27272a",
                    borderRadius: 8,
                    boxShadow: "0 16px 36px rgba(0,0,0,0.7)",
                    zIndex: 250,
                    overflow: "hidden",
                    maxHeight: 380,
                    overflowY: "auto",
                  }}
                >
                  {/* Deals Category */}
                  {searchSuggestions.deals.length > 0 && (
                    <div>
                      <div style={{ padding: "6px 12px", background: "#121215", borderBottom: "1px solid #1c1c22", fontSize: 10, fontWeight: 700, color: "#A78BFA", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                        Deals & Opportunities
                      </div>
                      {searchSuggestions.deals.map((d: any) => (
                        <div
                          key={d.id}
                          onClick={() => {
                            setView("deals")
                            setSearchOpen(false)
                            setSearch("")
                          }}
                          style={{ padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #16161a", cursor: "pointer" }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = "#1a1a20")}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                        >
                          <div>
                            <div style={{ fontSize: 12.5, fontWeight: 600, color: "#fff" }}>{d.deal_code} · {d.customer_name}</div>
                            <div style={{ fontSize: 11, color: "#71717A" }}>{d.title}</div>
                          </div>
                          <span style={{ fontSize: 11, color: "#10B981", fontWeight: 600 }}>{d.stage}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Customers Category */}
                  {searchSuggestions.customers.length > 0 && (
                    <div>
                      <div style={{ padding: "6px 12px", background: "#121215", borderBottom: "1px solid #1c1c22", fontSize: 10, fontWeight: 700, color: "#38BDF8", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                        Customers & Accounts
                      </div>
                      {searchSuggestions.customers.map((c: any) => (
                        <div
                          key={c.id}
                          onClick={() => {
                            setView("customers")
                            setSearchOpen(false)
                            setSearch("")
                          }}
                          style={{ padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #16161a", cursor: "pointer" }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = "#1a1a20")}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                        >
                          <div>
                            <div style={{ fontSize: 12.5, fontWeight: 600, color: "#fff" }}>{c.name}</div>
                            <div style={{ fontSize: 11, color: "#71717A" }}>{c.customer_code} · {c.city || "India"}</div>
                          </div>
                          <span style={{ fontSize: 11, color: "#A1A1AA" }}>View Account →</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Products Category */}
                  {searchSuggestions.products.length > 0 && (
                    <div>
                      <div style={{ padding: "6px 12px", background: "#121215", borderBottom: "1px solid #1c1c22", fontSize: 10, fontWeight: 700, color: "#F59E0B", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                        Products & Catalog
                      </div>
                      {searchSuggestions.products.map((p: any) => (
                        <div
                          key={p.id}
                          onClick={() => {
                            setView("products")
                            setSearchOpen(false)
                            setSearch("")
                          }}
                          style={{ padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #16161a", cursor: "pointer" }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = "#1a1a20")}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                        >
                          <div>
                            <div style={{ fontSize: 12.5, fontWeight: 600, color: "#fff" }}>{p.name}</div>
                            <div style={{ fontSize: 11, color: "#71717A" }}>{p.sku} · {p.category?.name || "Catalog Item"}</div>
                          </div>
                          <span className="mono" style={{ fontSize: 12, color: "#10B981", fontWeight: 600 }}>₹{Number(p.base_price || 0).toLocaleString("en-IN")}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div
            style={{
              marginLeft: "auto",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <motion.button
              className="df-btn-primary"
              onClick={() => handleOpenRequest(undefined, "create")}
              style={{
                padding: "7px 14px",
                fontSize: 13,
                borderRadius: 6,
                display: "flex",
                alignItems: "center",
                gap: 5,
              }}
              whileHover={{ opacity: 0.88, y: -1 }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.12 }}
            >
              <span style={{ fontSize: 16, lineHeight: 1, marginTop: -1 }}>
                +
              </span>{" "}
              New
            </motion.button>

            {/* Notifications */}
            <div style={{ position: "relative" }}>
              <motion.button
                onClick={() => setNotifOpen((o) => !o)}
                style={{
                  background: notifOpen ? "#111" : "none",
                  border: "1px solid",
                  borderColor: notifOpen ? "#222" : "transparent",
                  cursor: "pointer",
                  color: notifOpen ? "#fff" : "#555",
                  padding: 7,
                  borderRadius: 7,
                  display: "flex",
                  position: "relative",
                }}
                whileHover={{ color: "#fff" }}
                whileTap={{ scale: 0.94 }}
                transition={{ duration: 0.12 }}
                title={unreadCount > 0 ? `${unreadCount} unread notifications` : "Notifications"}
              >
                <Icon
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  size={15}
                />
                {unreadCount > 0 && (
                  <div
                    style={{
                      position: "absolute",
                      top: 3,
                      right: 3,
                      minWidth: 15,
                      height: 15,
                      padding: "0 3px",
                      borderRadius: 8,
                      background: "#EF4444",
                      color: "#fff",
                      fontSize: 9,
                      fontWeight: 700,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      border: "1.5px solid #050505",
                    }}
                  >
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </div>
                )}
              </motion.button>

              <AnimatedDropdown
                open={notifOpen}
                style={{
                  position: "absolute",
                  top: "100%",
                  right: 0,
                  marginTop: 8,
                  width: 340,
                  background: "#0d0d0d",
                  border: "1px solid #1e1e1e",
                  borderRadius: 10,
                  overflow: "hidden",
                  zIndex: 200,
                  boxShadow: "0 10px 30px rgba(0,0,0,0.7)",
                }}
              >
                <div
                  style={{
                    padding: "12px 14px",
                    borderBottom: "1px solid #1a1a1a",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span
                    style={{ fontSize: 13, fontWeight: 600, color: "#fff" }}
                  >
                    Notifications {unreadCount > 0 ? `(${unreadCount})` : ""}
                  </span>
                  {unreadCount > 0 && (
                    <span
                      onClick={() => markAllAsRead()}
                      style={{
                        fontSize: 11,
                        color: "#A78BFA",
                        cursor: "pointer",
                        fontWeight: 500,
                      }}
                    >
                      Mark all read
                    </span>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <div style={{ padding: "20px 14px", textAlign: "center", fontSize: 12, color: "#666" }}>
                    No notifications
                  </div>
                ) : (
                  notifications.slice(0, 5).map((n, i) => {
                    const dotColor =
                      n.priority === "CRITICAL"
                        ? "#EF4444"
                        : n.priority === "HIGH"
                        ? "#F97316"
                        : n.priority === "MEDIUM"
                        ? "#F59E0B"
                        : "#8B5CF6"
                    
                    const timeAgo = () => {
                      const timeStr = n.createdAt || n.timestamp
                      const diff = Math.floor((Date.now() - new Date(timeStr).getTime()) / 60000)
                      if (diff < 1) return "Just now"
                      if (diff < 60) return `${diff}m ago`
                      const hours = Math.floor(diff / 60)
                      if (hours < 24) return `${hours}h ago`
                      return `${Math.floor(hours / 24)}d ago`
                    }

                    return (
                      <motion.div
                        key={n.id || i}
                        onClick={() => {
                          markAsRead(n.id)
                          const resType = n.resourceType || n.relatedResource
                          const resId = n.resourceId || n.relatedResourceId
                          if ((resType === "quote" || resType === "request") && resId) {
                            handleOpenRequest(resId, "details")
                          } else if (resType === "approval") {
                            setView("approvals")
                          } else if (resType === "deal") {
                            setView("deals")
                          } else if (resType === "order") {
                            setView("fulfillment")
                          } else if (resType === "transaction") {
                            setView("billing")
                          }
                          setNotifOpen(false)
                        }}
                        style={{
                          padding: "11px 14px",
                          borderBottom: "1px solid #141414",
                          cursor: "pointer",
                          background: n.read ? "transparent" : "rgba(124, 58, 237, 0.04)",
                        }}
                        whileHover={{ background: "rgba(255,255,255,0.03)" }}
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.04, duration: 0.15 }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "flex-start",
                            gap: 8,
                          }}
                        >
                          <div
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: "50%",
                              background: dotColor,
                              flexShrink: 0,
                              marginTop: 5,
                            }}
                          />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div
                              style={{
                                fontSize: 12.5,
                                fontWeight: n.read ? 500 : 600,
                                color: n.read ? "#CCC" : "#fff",
                                marginBottom: 2,
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "baseline",
                              }}
                            >
                              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {n.title}
                              </span>
                              <span style={{ fontSize: 10, color: "#666", flexShrink: 0, marginLeft: 6 }}>
                                {timeAgo()}
                              </span>
                            </div>
                            <div
                              style={{
                                fontSize: 11.5,
                                color: "#71717A",
                                lineHeight: 1.4,
                                overflow: "hidden",
                                display: "-webkit-box",
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: "vertical",
                              }}
                            >
                              {n.message}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )
                  })
                )}
                <div
                  style={{
                    padding: "8px 12px",
                    borderTop: "1px solid #1a1a1a",
                    background: "#08080a",
                    textAlign: "center",
                  }}
                >
                  <button
                    onClick={() => {
                      setView("notifications")
                      setNotifOpen(false)
                    }}
                    style={{
                      background: "none",
                      border: "none",
                      color: "#A78BFA",
                      fontSize: 11.5,
                      fontWeight: 500,
                      cursor: "pointer",
                      padding: "4px 8px",
                      width: "100%",
                      borderRadius: 4,
                    }}
                  >
                    View all in Notification Center →
                  </button>
                </div>
              </AnimatedDropdown>
            </div>

            <motion.button
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "#444",
                padding: 7,
                borderRadius: 7,
                display: "flex",
              }}
              whileHover={{ color: "#fff" }}
              whileTap={{ scale: 0.94 }}
              transition={{ duration: 0.12 }}
            >
              <Icon
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                size={15}
              />
            </motion.button>

            <div
              onClick={() => setProfileOpen(true)}
              style={{
                width: 30,
                height: 30,
                borderRadius: "50%",
                background: "#1a1a1a",
                border: "1px solid #333",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 11,
                fontWeight: 700,
                color: "#A1A1AA",
                cursor: "pointer",
              }}
              title="Open Account Profile"
            >
              {user.initials || "DF"}
            </div>
          </div>
        </header>

        {/* Page content with transition */}
        <main style={{ flex: 1, overflowY: "auto", background: "#000" }}>
          <PageTransition pageKey={view}>{renderView()}</PageTransition>
        </main>
      </div>

      {/* User Profile & Security Slide-over Drawer */}
      <AnimatePresence>
        {profileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => setProfileOpen(false)}
              style={{
                position: "fixed",
                inset: 0,
                background: "rgba(0, 0, 0, 0.7)",
                backdropFilter: "blur(3px)",
                zIndex: 90,
              }}
            />

            {/* Slide-over Panel */}
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 300 }}
              style={{
                position: "fixed",
                top: 0,
                right: 0,
                bottom: 0,
                width: 440,
                maxWidth: "100%",
                background: "#0a0a0c",
                borderLeft: "1px solid #1e1e24",
                zIndex: 100,
                display: "flex",
                flexDirection: "column",
                boxShadow: "-12px 0 36px rgba(0, 0, 0, 0.6)",
              }}
            >
              {/* Header */}
              <div
                style={{
                  padding: "18px 24px",
                  borderBottom: "1px solid #1e1e24",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: 15,
                      fontWeight: 600,
                      color: "#fff",
                    }}
                  >
                    User Profile & Security
                  </h2>
                  <p
                    style={{
                      margin: 0,
                      fontSize: 12,
                      color: "#71717A",
                      marginTop: 2,
                    }}
                  >
                    Session credentials & RBAC authorization
                  </p>
                </div>
                <button
                  onClick={() => setProfileOpen(false)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#71717A",
                    cursor: "pointer",
                    padding: 6,
                    borderRadius: 6,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  title="Close panel"
                >
                  <Icon d="M6 18L18 6M6 6l12 12" size={16} />
                </button>
              </div>

              {/* Scrollable Content */}
              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: 24,
                  display: "flex",
                  flexDirection: "column",
                  gap: 24,
                }}
              >
                {/* Profile Card */}
                <div
                  style={{
                    padding: 16,
                    borderRadius: 8,
                    background: "#121216",
                    border: "1px solid #22222a",
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                  }}
                >
                  <div
                    style={{
                      width: 52,
                      height: 52,
                      borderRadius: "50%",
                      background: "rgba(124, 58, 237, 0.15)",
                      border: "1px solid rgba(124, 58, 237, 0.4)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 18,
                      fontWeight: 700,
                      color: "#A78BFA",
                      flexShrink: 0,
                    }}
                  >
                    {user.initials || "DF"}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontSize: 15,
                        fontWeight: 600,
                        color: "#fff",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {user.name}
                    </div>
                    <div
                      style={{
                        fontSize: 12.5,
                        color: "#94A3B8",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        marginTop: 2,
                      }}
                    >
                      {user.email}
                    </div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        marginTop: 8,
                      }}
                    >
                      <span
                        style={{
                          fontSize: 10.5,
                          fontWeight: 600,
                          textTransform: "uppercase",
                          padding: "2px 8px",
                          borderRadius: 4,
                          background: "rgba(124, 58, 237, 0.2)",
                          color: "#C4B5FD",
                          border: "1px solid rgba(124, 58, 237, 0.3)",
                          letterSpacing: "0.05em",
                        }}
                      >
                        {user.role}
                      </span>
                      <span
                        style={{
                          fontSize: 11,
                          color: "#71717A",
                        }}
                      >
                        {user.department || "Enterprise Sales"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Session & Storage Status */}
                <div
                  style={{
                    padding: 14,
                    borderRadius: 8,
                    background: "#0d0d10",
                    border: "1px solid #1e1e24",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 6,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        color: "#71717A",
                        letterSpacing: "0.05em",
                      }}
                    >
                      Session Persistence
                    </span>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 5,
                        fontSize: 11,
                        fontWeight: 600,
                        color: "#10B981",
                      }}
                    >
                      <span
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: "#10B981",
                        }}
                      />
                      Active (localStorage)
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: 11.5,
                      color: "#A1A1AA",
                      fontFamily: "monospace",
                      background: "#050507",
                      padding: "6px 10px",
                      borderRadius: 4,
                      border: "1px solid #181820",
                    }}
                  >
                    Storage Key: dealflow360_auth_session
                  </div>
                </div>

                {/* Permissions Badges */}
                <div>
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      textTransform: "uppercase",
                      color: "#71717A",
                      letterSpacing: "0.05em",
                      marginBottom: 10,
                    }}
                  >
                    Assigned Permissions ({user.permissions?.length || 0})
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: 6,
                    }}
                  >
                    {user.permissions && user.permissions.length > 0 ? (
                      user.permissions.map((perm) => (
                        <span
                          key={perm}
                          style={{
                            fontSize: 11,
                            fontFamily: "monospace",
                            padding: "3px 8px",
                            borderRadius: 4,
                            background: "#151518",
                            border: "1px solid #27272a",
                            color: "#D4D4D8",
                          }}
                        >
                          {perm}
                        </span>
                      ))
                    ) : (
                      <span style={{ fontSize: 12, color: "#555" }}>
                        No permissions assigned.
                      </span>
                    )}
                  </div>
                </div>

                {/* System & Audit Quick Navigation */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 10,
                  }}
                >
                  <button
                    onClick={() => {
                      setView("settings")
                      setProfileOpen(false)
                    }}
                    style={{
                      padding: "9px 12px",
                      borderRadius: 6,
                      background: "#121216",
                      border: "1px solid #22222a",
                      color: "#fff",
                      fontSize: 12,
                      fontWeight: 500,
                      cursor: "pointer",
                      textAlign: "center",
                    }}
                  >
                    System Settings →
                  </button>
                  <button
                    onClick={() => {
                      setView("audit")
                      setProfileOpen(false)
                    }}
                    style={{
                      padding: "9px 12px",
                      borderRadius: 6,
                      background: "#121216",
                      border: "1px solid #22222a",
                      color: "#fff",
                      fontSize: 12,
                      fontWeight: 500,
                      cursor: "pointer",
                      textAlign: "center",
                    }}
                  >
                    Audit & Security →
                  </button>
                </div>

                {/* Change Password Section */}
                <div
                  style={{
                    padding: 16,
                    borderRadius: 8,
                    background: "#0d0d10",
                    border: "1px solid #1e1e24",
                  }}
                >
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: "#fff",
                      marginBottom: 4,
                    }}
                  >
                    Change Password
                  </div>
                  <p
                    style={{
                      fontSize: 11.5,
                      color: "#71717A",
                      margin: "0 0 12px 0",
                    }}
                  >
                    Update credentials stored in local storage for this session.
                  </p>

                  {pwNotice && (
                    <div
                      style={{
                        padding: "8px 10px",
                        borderRadius: 6,
                        background: "rgba(16, 185, 129, 0.1)",
                        border: "1px solid rgba(16, 185, 129, 0.3)",
                        color: "#34D399",
                        fontSize: 12,
                        marginBottom: 12,
                      }}
                    >
                      {pwNotice}
                    </div>
                  )}

                  {pwError && (
                    <div
                      style={{
                        padding: "8px 10px",
                        borderRadius: 6,
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                        color: "#F87171",
                        fontSize: 12,
                        marginBottom: 12,
                      }}
                    >
                      {pwError}
                    </div>
                  )}

                  <form
                    onSubmit={handleChangePassword}
                    style={{ display: "flex", flexDirection: "column", gap: 10 }}
                  >
                    <div>
                      <label
                        style={{
                          display: "block",
                          fontSize: 11,
                          fontWeight: 500,
                          color: "#A1A1AA",
                          marginBottom: 4,
                        }}
                      >
                        Current Password
                      </label>
                      <input
                        type="password"
                        className="df-input"
                        placeholder="Enter current password"
                        value={currentPw}
                        onChange={(e) => setCurrentPw(e.target.value)}
                        style={{ width: "100%", height: 34, fontSize: 12 }}
                      />
                    </div>

                    <div>
                      <label
                        style={{
                          display: "block",
                          fontSize: 11,
                          fontWeight: 500,
                          color: "#A1A1AA",
                          marginBottom: 4,
                        }}
                      >
                        New Password
                      </label>
                      <input
                        type="password"
                        className="df-input"
                        placeholder="Minimum 6 characters"
                        value={newPw}
                        onChange={(e) => setNewPw(e.target.value)}
                        style={{ width: "100%", height: 34, fontSize: 12 }}
                      />
                    </div>

                    <div>
                      <label
                        style={{
                          display: "block",
                          fontSize: 11,
                          fontWeight: 500,
                          color: "#A1A1AA",
                          marginBottom: 4,
                        }}
                      >
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        className="df-input"
                        placeholder="Confirm new password"
                        value={confirmPw}
                        onChange={(e) => setConfirmPw(e.target.value)}
                        style={{ width: "100%", height: 34, fontSize: 12 }}
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={pwLoading}
                      className="df-btn-primary"
                      style={{
                        marginTop: 4,
                        padding: "8px 12px",
                        fontSize: 12,
                        borderRadius: 6,
                        opacity: pwLoading ? 0.6 : 1,
                        cursor: pwLoading ? "not-allowed" : "pointer",
                      }}
                    >
                      {pwLoading ? "Updating..." : "Update Password"}
                    </button>
                  </form>
                </div>
              </div>

              {/* Drawer Footer */}
              <div
                style={{
                  padding: 16,
                  borderTop: "1px solid #1e1e24",
                  background: "#08080a",
                }}
              >
                <button
                  onClick={() => {
                    setProfileOpen(false)
                    onLogout()
                  }}
                  style={{
                    width: "100%",
                    padding: "9px 16px",
                    borderRadius: 6,
                    background: "rgba(239, 68, 68, 0.08)",
                    border: "1px solid rgba(239, 68, 68, 0.25)",
                    color: "#EF4444",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(239, 68, 68, 0.15)"
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "rgba(239, 68, 68, 0.08)"
                  }}
                >
                  <Icon
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    size={14}
                  />
                  Sign Out of DealFlow360
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
