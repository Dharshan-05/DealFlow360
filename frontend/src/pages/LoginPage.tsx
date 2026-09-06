import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useAuth } from "../hooks/useAuth"

interface Props {
  onLoginSuccess: (accountType: "internal" | "customer") => void
  onBack: () => void
}

type AuthMode = "login" | "signup" | "forgot" | "reset"

export default function LoginPage({ onLoginSuccess, onBack }: Props) {
  const { login, signup, requestPasswordReset, resetPassword, isLoading, error, clearError } = useAuth()

  const [mode, setMode] = useState<AuthMode>("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmNewPassword, setConfirmNewPassword] = useState("")
  const [accountType, setAccountType] = useState<"internal" | "customer">("internal")
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [localError, setLocalError] = useState("")
  const [notice, setNotice] = useState("")

  const switchMode = (newMode: AuthMode) => {
    setMode(newMode)
    setLocalError("")
    setNotice("")
    clearError()
  }

  // Pre-fill demo accounts for convenient testing
  const fillDemoAccount = (type: "director" | "customer") => {
    if (type === "director") {
      setEmail("arjun.sharma@dealflow360.io")
      setPassword("password123")
      setAccountType("internal")
    } else {
      setEmail("rajesh@acme.com")
      setPassword("password123")
      setAccountType("customer")
    }
    setLocalError("")
  }

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError("")
    setNotice("")

    if (!email.trim() || !email.includes("@")) {
      setLocalError("Please enter a valid work email.")
      return
    }
    if (!password) {
      setLocalError("Please enter your password.")
      return
    }

    try {
      const user = await login({ email, password, accountType, remember })
      onLoginSuccess(user.role === "Customer" ? "customer" : "internal")
    } catch (err: any) {
      setLocalError(err?.message || "Invalid credentials. Please try again.")
    }
  }

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError("")
    setNotice("")

    if (!name.trim()) {
      setLocalError("Please enter your full name.")
      return
    }
    if (!email.trim() || !email.includes("@")) {
      setLocalError("Please enter a valid work email.")
      return
    }
    if (!password || password.length < 6) {
      setLocalError("Password must be at least 6 characters.")
      return
    }
    if (password !== confirmPassword) {
      setLocalError("Passwords do not match.")
      return
    }

    try {
      const user = await signup({ name, email, password, accountType })
      onLoginSuccess(user.role === "Customer" ? "customer" : "internal")
    } catch (err: any) {
      setLocalError(err?.message || "Registration failed. Please try again.")
    }
  }

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError("")
    setNotice("")

    if (!email.trim() || !email.includes("@")) {
      setLocalError("Please enter your registered work email.")
      return
    }

    try {
      await requestPasswordReset(email)
      setNotice(`Recovery instructions sent to ${email}. You can now proceed to reset your password.`)
    } catch (err: any) {
      setLocalError(err?.message || "Could not send recovery instructions.")
    }
  }

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError("")
    setNotice("")

    if (!newPassword || newPassword.length < 6) {
      setLocalError("New password must be at least 6 characters.")
      return
    }
    if (newPassword !== confirmNewPassword) {
      setLocalError("Passwords do not match.")
      return
    }

    try {
      await resetPassword(newPassword)
      setNotice("Password successfully updated! You can now log in with your new password.")
      setNewPassword("")
      setConfirmNewPassword("")
      setTimeout(() => {
        switchMode("login")
      }, 1500)
    } catch (err: any) {
      setLocalError(err?.message || "Failed to update password.")
    }
  }

  const displayedError = localError || error

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#000",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse 60% 60% at 50% 50%, black 40%, transparent 100%)",
        }}
      />

      {/* Glow */}
      <motion.div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          translateX: "-50%",
          translateY: "-50%",
          width: 500,
          height: 500,
          background: "radial-gradient(ellipse, rgba(124,58,237,0.06) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
        initial={{ opacity: 0, scale: 0.7 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.0, 0.0, 0.2, 1.0] }}
      />

      {/* Back button */}
      <motion.button
        onClick={onBack}
        style={{
          position: "absolute",
          top: 24,
          left: 28,
          color: "#555",
          fontSize: 13,
          fontWeight: 500,
          background: "none",
          border: "none",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1, duration: 0.2 }}
        whileHover={{ color: "#fff", x: -2 }}
      >
        <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back
      </motion.button>

      {/* Logo */}
      <motion.div
        style={{
          position: "absolute",
          top: 24,
          left: "50%",
          translateX: "-50%",
          display: "flex",
          alignItems: "center",
          gap: 7,
        }}
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08, duration: 0.2 }}
      >
        <img
          src="/logo.png"
          alt="DealFlow360"
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            objectFit: "cover",
            boxShadow: "0 0 12px rgba(59, 130, 246, 0.4)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
          }}
        />
        <span style={{ fontWeight: 700, fontSize: 14, color: "#fff", letterSpacing: "-0.02em" }}>DealFlow360</span>
      </motion.div>

      {/* Auth card */}
      <motion.div
        style={{
          width: 410,
          background: "#080808",
          border: "1px solid #1e1e1e",
          borderRadius: 14,
          padding: "36px 32px",
          position: "relative",
          zIndex: 1,
        }}
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ delay: 0.15, duration: 0.3, ease: [0.0, 0.0, 0.2, 1.0] }}
      >
        {/* Mode Tabs for Login & Signup */}
        {(mode === "login" || mode === "signup") && (
          <div style={{ display: "flex", gap: 4, marginBottom: 20, background: "#000", border: "1px solid #1d1d1d", padding: 3, borderRadius: 8 }}>
            {(["login", "signup"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => switchMode(tab)}
                style={{
                  flex: 1,
                  border: 0,
                  borderRadius: 5,
                  padding: "7px",
                  background: mode === tab ? "#fff" : "transparent",
                  color: mode === tab ? "#000" : "#666",
                  font: "600 12px Inter",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {tab === "login" ? "Log In" : "Sign Up"}
              </button>
            ))}
          </div>
        )}

        {/* Heading based on mode */}
        <motion.h1
          key={`title-${mode}`}
          style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.03em", color: "#fff", marginBottom: 4 }}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15 }}
        >
          {mode === "login" && "Welcome back"}
          {mode === "signup" && "Create your account"}
          {mode === "forgot" && "Reset your password"}
          {mode === "reset" && "Set new password"}
        </motion.h1>

        <motion.p
          key={`desc-${mode}`}
          style={{ fontSize: 13, color: "#666", marginBottom: 20, lineHeight: 1.4 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
        >
          {mode === "login" && "Sign in to your DealFlow360 command workspace."}
          {mode === "signup" && "Set up your DealFlow360 workspace access."}
          {mode === "forgot" && "Enter your work email to receive password recovery instructions."}
          {mode === "reset" && "Create a strong, secure password for your account."}
        </motion.p>

        {/* Google SSO button (Login and Signup modes) */}
        {(mode === "login" || mode === "signup") && (
          <>
            <motion.button
              type="button"
              onClick={() => setNotice("Single Sign-On (Google Workspace) placeholder — use mock email authentication.")}
              style={{
                width: "100%",
                padding: "10px 14px",
                background: "#0d0d0d",
                border: "1px solid #222",
                borderRadius: 8,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 10,
                cursor: "pointer",
                marginBottom: 16,
              }}
              whileHover={{ borderColor: "#333" }}
              whileTap={{ scale: 0.98 }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span style={{ fontSize: 13, color: "#A1A1AA", fontWeight: 500 }}>Continue with Google</span>
            </motion.button>

            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <div style={{ flex: 1, height: 1, background: "#1a1a1a" }} />
              <span style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.04em" }}>or email</span>
              <div style={{ flex: 1, height: 1, background: "#1a1a1a" }} />
            </div>
          </>
        )}

        {/* Forms */}
        <AnimatePresence mode="wait">
          {mode === "login" && (
            <motion.form
              key="form-login"
              onSubmit={handleLoginSubmit}
              style={{ display: "flex", flexDirection: "column", gap: 13 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Work Email
                </label>
                <input
                  className="df-input"
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "#666", letterSpacing: "0.04em", textTransform: "uppercase" }}>
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => switchMode("forgot")}
                    style={{ fontSize: 11.5, color: "#7C3AED", background: "none", border: "none", cursor: "pointer", padding: 0 }}
                  >
                    Forgot password?
                  </button>
                </div>
                <div style={{ position: "relative" }}>
                  <input
                    className="df-input"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ position: "absolute", right: 10, top: 10, border: 0, background: "none", color: "#777", cursor: "pointer", fontSize: 11 }}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Account Mode
                </label>
                <select
                  value={accountType}
                  onChange={(e) => setAccountType(e.target.value as "internal" | "customer")}
                  className="df-input"
                  style={{ height: 38, padding: "0 10px", fontSize: 13 }}
                >
                  <option value="internal">Internal Workspace (Director / AE)</option>
                  <option value="customer">Customer Portal (Acme Corp)</option>
                </select>
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label style={{ display: "flex", alignItems: "center", gap: 7, color: "#777", fontSize: 12, cursor: "pointer" }}>
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /> Remember session
                </label>
                <div style={{ display: "flex", gap: 6 }}>
                  <button
                    type="button"
                    onClick={() => fillDemoAccount("director")}
                    style={{ border: 0, background: "none", color: "#555", fontSize: 11, cursor: "pointer", textDecoration: "underline" }}
                  >
                    Director Demo
                  </button>
                  <span style={{ color: "#333" }}>•</span>
                  <button
                    type="button"
                    onClick={() => fillDemoAccount("customer")}
                    style={{ border: 0, background: "none", color: "#555", fontSize: 11, cursor: "pointer", textDecoration: "underline" }}
                  >
                    Client Demo
                  </button>
                </div>
              </div>

              {displayedError && (
                <div role="alert" style={{ color: "#F87171", border: "1px solid rgba(239,68,68,0.24)", background: "rgba(239,68,68,0.07)", borderRadius: 6, padding: "8px 10px", fontSize: 12 }}>
                  {displayedError}
                </div>
              )}

              {notice && (
                <div role="status" style={{ color: "#A1A1AA", border: "1px solid #292929", background: "#111", borderRadius: 6, padding: "8px 10px", fontSize: 12 }}>
                  {notice}
                </div>
              )}

              <motion.button
                type="submit"
                disabled={isLoading}
                className="df-btn-primary"
                style={{ width: "100%", padding: "11px", marginTop: 4, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
                whileHover={isLoading ? {} : { opacity: 0.9 }}
                whileTap={isLoading ? {} : { scale: 0.98 }}
              >
                {isLoading ? (
                  <>
                    <motion.div
                      style={{ width: 13, height: 13, border: "2px solid #000", borderTopColor: "transparent", borderRadius: "50%" }}
                      animate={{ rotate: 360 }}
                      transition={{ duration: 0.6, repeat: Infinity, ease: "linear" }}
                    />
                    Signing in...
                  </>
                ) : (
                  "Sign In"
                )}
              </motion.button>
            </motion.form>
          )}

          {mode === "signup" && (
            <motion.form
              key="form-signup"
              onSubmit={handleSignupSubmit}
              style={{ display: "flex", flexDirection: "column", gap: 13 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Full Name
                </label>
                <input
                  className="df-input"
                  placeholder="Arjun Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Work Email
                </label>
                <input
                  className="df-input"
                  type="email"
                  placeholder="arjun@dealflow360.io"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Password (min. 6 characters)
                </label>
                <input
                  className="df-input"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Confirm Password
                </label>
                <input
                  className="df-input"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Account Type
                </label>
                <select
                  value={accountType}
                  onChange={(e) => setAccountType(e.target.value as "internal" | "customer")}
                  className="df-input"
                  style={{ height: 38, padding: "0 10px", fontSize: 13 }}
                >
                  <option value="internal">Internal Team Member</option>
                  <option value="customer">Client / Customer</option>
                </select>
              </div>

              {displayedError && (
                <div role="alert" style={{ color: "#F87171", border: "1px solid rgba(239,68,68,0.24)", background: "rgba(239,68,68,0.07)", borderRadius: 6, padding: "8px 10px", fontSize: 12 }}>
                  {displayedError}
                </div>
              )}

              <motion.button
                type="submit"
                disabled={isLoading}
                className="df-btn-primary"
                style={{ width: "100%", padding: "11px", marginTop: 4, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
                whileHover={isLoading ? {} : { opacity: 0.9 }}
                whileTap={isLoading ? {} : { scale: 0.98 }}
              >
                {isLoading ? "Creating Account..." : "Create Account"}
              </motion.button>
            </motion.form>
          )}

          {mode === "forgot" && (
            <motion.form
              key="form-forgot"
              onSubmit={handleForgotSubmit}
              style={{ display: "flex", flexDirection: "column", gap: 14 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Registered Email
                </label>
                <input
                  className="df-input"
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              {displayedError && (
                <div role="alert" style={{ color: "#F87171", border: "1px solid rgba(239,68,68,0.24)", background: "rgba(239,68,68,0.07)", borderRadius: 6, padding: "8px 10px", fontSize: 12 }}>
                  {displayedError}
                </div>
              )}

              {notice && (
                <div role="status" style={{ color: "#10B981", border: "1px solid rgba(16,185,129,0.24)", background: "rgba(16,185,129,0.08)", borderRadius: 6, padding: "10px 12px", fontSize: 12, lineHeight: 1.5 }}>
                  {notice}
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 6 }}>
                <motion.button
                  type="submit"
                  disabled={isLoading}
                  className="df-btn-primary"
                  style={{ width: "100%", padding: "11px", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
                >
                  {isLoading ? "Sending..." : "Send Recovery Instructions"}
                </motion.button>

                {notice && (
                  <button
                    type="button"
                    onClick={() => switchMode("reset")}
                    className="df-btn-secondary"
                    style={{ width: "100%", padding: "10px", fontSize: 12.5 }}
                  >
                    Proceed to Reset Password &rarr;
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => switchMode("login")}
                  style={{ background: "none", border: "none", color: "#777", fontSize: 12, cursor: "pointer", padding: 6 }}
                >
                  &larr; Back to Log in
                </button>
              </div>
            </motion.form>
          )}

          {mode === "reset" && (
            <motion.form
              key="form-reset"
              onSubmit={handleResetSubmit}
              style={{ display: "flex", flexDirection: "column", gap: 14 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  New Password (min. 6 chars)
                </label>
                <div style={{ position: "relative" }}>
                  <input
                    className="df-input"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ position: "absolute", right: 10, top: 10, border: 0, background: "none", color: "#777", cursor: "pointer", fontSize: 11 }}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#666", marginBottom: 5, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  Confirm New Password
                </label>
                <input
                  className="df-input"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  required
                />
              </div>

              {displayedError && (
                <div role="alert" style={{ color: "#F87171", border: "1px solid rgba(239,68,68,0.24)", background: "rgba(239,68,68,0.07)", borderRadius: 6, padding: "8px 10px", fontSize: 12 }}>
                  {displayedError}
                </div>
              )}

              {notice && (
                <div role="status" style={{ color: "#10B981", border: "1px solid rgba(16,185,129,0.24)", background: "rgba(16,185,129,0.08)", borderRadius: 6, padding: "10px 12px", fontSize: 12 }}>
                  {notice}
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 6 }}>
                <motion.button
                  type="submit"
                  disabled={isLoading}
                  className="df-btn-primary"
                  style={{ width: "100%", padding: "11px", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
                >
                  {isLoading ? "Updating..." : "Set New Password"}
                </motion.button>

                <button
                  type="button"
                  onClick={() => switchMode("login")}
                  style={{ background: "none", border: "none", color: "#777", fontSize: 12, cursor: "pointer", padding: 6 }}
                >
                  &larr; Back to Log in
                </button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>

        {/* Bottom Switcher */}
        {mode === "login" && (
          <p style={{ fontSize: 12.5, color: "#444", textAlign: "center", marginTop: 22, marginBottom: 0 }}>
            New to DealFlow360?{" "}
            <button
              type="button"
              onClick={() => switchMode("signup")}
              style={{ color: "#A1A1AA", cursor: "pointer", textDecoration: "underline", border: 0, background: "none", padding: 0 }}
            >
              Create account
            </button>
          </p>
        )}

        {mode === "signup" && (
          <p style={{ fontSize: 12.5, color: "#444", textAlign: "center", marginTop: 22, marginBottom: 0 }}>
            Already have an account?{" "}
            <button
              type="button"
              onClick={() => switchMode("login")}
              style={{ color: "#A1A1AA", cursor: "pointer", textDecoration: "underline", border: 0, background: "none", padding: 0 }}
            >
              Log in
            </button>
          </p>
        )}
      </motion.div>

      {/* Bottom fine print */}
      <div style={{ position: "absolute", bottom: 20, display: "flex", gap: 20 }}>
        {["Privacy Policy", "Terms of Service", "Security"].map((l) => (
          <span key={l} style={{ fontSize: 11.5, color: "#333", cursor: "pointer" }}>
            {l}
          </span>
        ))}
      </div>
    </div>
  )
}