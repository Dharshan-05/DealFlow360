import { useState, useRef, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { TypingIndicator } from '../lib/motion'

interface Message {
  role: 'user' | 'ai'
  text: string
  actions?: string[]
}

const suggestions = [
  'Which deals are at risk this week?',
  'Show high-priority approvals',
  'Summarize GlobalFin deal status',
  'What is our Q3 pipeline coverage?',
  'Find upsell opportunities',
  'Generate pipeline report',
]

const aiResponses: Record<string, { text: string; actions?: string[] }> = {
  default: {
    text: 'I analyzed your current pipeline data. Here is what I found:\n\n12 deals require immediate attention. 4 have high payment risk, 3 exceed discount policy limits, and 5 have been stalled for more than 7 days. Your Q3 pipeline coverage is at 2.4x with a forecast range of ₹18.2M to ₹24.8M.',
    actions: ['Show high-risk deals', 'Review approvals', 'View pipeline'],
  },
  risk: {
    text: 'I found 2 critical deals that need your immediate attention:\n\n1. Meridian Capital — discount of 22% exceeds policy by 7pp. Risk score: Critical.\n2. Pinnacle Group — discount of 25% exceeds policy by 10pp. Risk score: Critical.\n\nBoth deals are pending approval and have been stalled for more than 2 days.',
    actions: ['Review Meridian Capital', 'Review Pinnacle Group', 'Bulk approve safe deals'],
  },
  approval: {
    text: 'There are currently 7 pending approval requests. 2 are critical (Meridian Capital and Pinnacle Group), 3 are high risk, and 2 are within acceptable policy thresholds.\n\nAverage time in approval queue: 4.2 hours. Oldest request: Apex Fintech at 2 days.',
    actions: ['Open approval center', 'Approve low-risk requests', 'Escalate critical deals'],
  },
  globalfin: {
    text: 'GlobalFin Inc deal is in the Negotiation stage. Current status:\n\n• Deal value: ₹6.1M\n• Health score: 91 (Excellent)\n• Discount applied: 8% (within policy)\n• Risk level: Low\n• AI recommendation: High probability of close this week. Consider offering Extended Support bundle for +₹1.2M ACV.',
    actions: ['Add upsell to quote', 'View full timeline', 'Contact Vikram Singh'],
  },
  upsell: {
    text: 'I identified 4 high-probability upsell opportunities:\n\n1. GlobalFin Inc — Add Extended Support (+₹1.2M, 73% probability)\n2. Acme Corporation — Upgrade to Enterprise tier (+₹800K, 68% probability)\n3. Vertex Systems — Add Cloud Backup module (+₹240K, 61% probability)\n4. Horizon Pharma — Add Analytics add-on (+₹180K, 55% probability)\n\nTotal potential: +₹2.4M',
    actions: ['Add GlobalFin upsell', 'View all opportunities', 'Generate proposals'],
  },
}

function getAIResponse(text: string): typeof aiResponses['default'] {
  const lower = text.toLowerCase()
  if (lower.includes('risk') || lower.includes('attention')) return aiResponses.risk
  if (lower.includes('approval') || lower.includes('pending')) return aiResponses.approval
  if (lower.includes('globalfin') || lower.includes('global')) return aiResponses.globalfin
  if (lower.includes('upsell') || lower.includes('opportunit')) return aiResponses.upsell
  return aiResponses.default
}

// Streaming text effect
function StreamingText({ text }: { text: string }) {
  const [displayed, setDisplayed] = useState('')

  useEffect(() => {
    setDisplayed('')
    let i = 0
    const id = setInterval(() => {
      setDisplayed(text.slice(0, i + 1))
      i++
      if (i >= text.length) clearInterval(id)
    }, 12)
    return () => clearInterval(id)
  }, [text])

  return (
    <span style={{ whiteSpace: 'pre-wrap' }}>
      {displayed}
      {displayed.length < text.length && (
        <motion.span
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.7, repeat: Infinity }}
          style={{ display: 'inline-block', width: 2, height: '1em', background: '#7C3AED', marginLeft: 1, verticalAlign: 'middle' }}
        />
      )}
    </span>
  )
}

export default function AICopilot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      text: 'Hello, I am your DealFlow360 AI Copilot. I have access to your full pipeline, customer data, and deal analytics. How can I help you today?',
      actions: ['Which deals need attention?', 'Show pipeline summary', 'Find upsell opportunities'],
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamIdx, setStreamIdx] = useState(-1)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = (text: string) => {
    if (!text.trim() || loading) return
    setMessages(m => [...m, { role: 'user', text }])
    setInput('')
    setLoading(true)
    setTimeout(() => {
      const resp = getAIResponse(text)
      setMessages(m => {
        const next = [...m, { role: 'ai' as const, text: resp.text, actions: resp.actions }]
        setStreamIdx(next.length - 1)
        return next
      })
      setLoading(false)
    }, 1000)
  }

  return (
    <div style={{ display: 'flex', height: '100%', background: '#000' }}>
      {/* Sidebar */}
      <motion.div
        style={{ width: 240, borderRight: '1px solid #141414', padding: '20px 12px', background: '#050505', flexShrink: 0 }}
        initial={{ opacity: 0, x: -12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.25 }}
      >
        <div style={{ fontSize: 11, color: '#444', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 14, padding: '0 4px' }}>Quick Questions</div>
        {suggestions.map((s, i) => (
          <motion.button key={i} onClick={() => send(s)}
            style={{ width: '100%', textAlign: 'left', padding: '9px 10px', background: 'none', border: 'none', color: '#555', fontSize: 13, cursor: 'pointer', borderRadius: 6, marginBottom: 2, fontFamily: 'Inter, sans-serif', lineHeight: 1.4, display: 'block' }}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 + i * 0.04 }}
            whileHover={{ background: 'rgba(255,255,255,0.04)', color: '#A1A1AA', x: 2 }}
            whileTap={{ scale: 0.98 }}
          >{s}</motion.button>
        ))}
        <div style={{ borderTop: '1px solid #141414', marginTop: 20, paddingTop: 16 }}>
          <div style={{ fontSize: 11, color: '#444', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 12, padding: '0 4px' }}>Recent Sessions</div>
          {['Pipeline review — Sep 4', 'Risk analysis — Sep 3', 'Q3 forecast — Sep 2'].map((s, i) => (
            <motion.div key={i}
              style={{ padding: '8px 10px', fontSize: 12.5, color: '#333', cursor: 'pointer', borderRadius: 6 }}
              whileHover={{ color: '#A1A1AA', background: 'rgba(255,255,255,0.02)' }}
            >{s}</motion.div>
          ))}
        </div>
      </motion.div>

      {/* Chat */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <motion.div
          style={{ padding: '16px 24px', borderBottom: '1px solid #141414', display: 'flex', alignItems: 'center', gap: 10 }}
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="18" height="18" fill="none" stroke="#fff" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#fff' }}>AI Copilot</div>
            <div style={{ fontSize: 11.5, color: '#7C3AED', display: 'flex', alignItems: 'center', gap: 5 }}>
              <motion.div style={{ width: 5, height: 5, borderRadius: '50%', background: '#7C3AED' }}
                animate={{ opacity: [1, 0.4, 1] }}
                transition={{ duration: 2.5, repeat: Infinity }}
              />
              Online &#8226; Real-time data access
            </div>
          </div>
        </motion.div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div key={i}
                style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', gap: 12 }}
                initial={{ opacity: 0, y: 10, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.2, ease: [0.0, 0.0, 0.2, 1.0] }}
              >
                {msg.role === 'ai' && (
                  <div style={{ width: 32, height: 32, borderRadius: 9, background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                    <svg width="15" height="15" fill="none" stroke="#fff" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                  </div>
                )}
                <div style={{ maxWidth: '70%' }}>
                  <div style={{
                    padding: '13px 16px',
                    borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                    background: msg.role === 'user' ? '#fff' : '#0d0d0d',
                    border: msg.role === 'ai' ? '1px solid #1e1e1e' : 'none',
                    color: msg.role === 'user' ? '#000' : '#A1A1AA',
                    fontSize: 13.5,
                    lineHeight: 1.65,
                  }}>
                    {msg.role === 'ai' && i === streamIdx
                      ? <StreamingText text={msg.text} />
                      : <span style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</span>
                    }
                  </div>
                  {msg.actions && (
                    <motion.div
                      style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      {msg.actions.map(action => (
                        <motion.button key={action} onClick={() => send(action)}
                          style={{ padding: '6px 12px', background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.2)', borderRadius: 6, fontSize: 12, color: '#8B5CF6', cursor: 'pointer', fontWeight: 500, fontFamily: 'Inter, sans-serif' }}
                          whileHover={{ background: 'rgba(124,58,237,0.15)', scale: 1.02 }}
                          whileTap={{ scale: 0.97 }}
                          transition={{ duration: 0.1 }}
                        >{action}</motion.button>
                      ))}
                    </motion.div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          <AnimatePresence>
            {loading && (
              <motion.div
                style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.18 }}
              >
                <div style={{ width: 32, height: 32, borderRadius: 9, background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <svg width="15" height="15" fill="none" stroke="#fff" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                </div>
                <div style={{ padding: '12px 16px', background: '#0d0d0d', border: '1px solid #1e1e1e', borderRadius: '12px 12px 12px 2px' }}>
                  <TypingIndicator />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={endRef} />
        </div>

        {/* Input */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid #141414' }}>
          <form onSubmit={e => { e.preventDefault(); send(input) }}>
            <motion.div
              style={{ display: 'flex', gap: 10, background: '#0a0a0a', border: '1px solid #222', borderRadius: 10, padding: '10px 14px' }}
              whileFocus={{ borderColor: '#333' }}
              transition={{ duration: 0.15 }}
            >
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask about your pipeline, deals, customers, or performance..."
                style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: '#fff', fontSize: 14, fontFamily: 'Inter, sans-serif' }}
                disabled={loading}
              />
              <motion.button type="submit" disabled={!input.trim() || loading}
                style={{ width: 32, height: 32, borderRadius: 7, background: input.trim() && !loading ? '#7C3AED' : '#1a1a1a', border: 'none', cursor: input.trim() && !loading ? 'pointer' : 'default', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}
                whileHover={input.trim() && !loading ? { background: '#6D28D9', scale: 1.04 } : {}}
                whileTap={input.trim() && !loading ? { scale: 0.95 } : {}}
                transition={{ duration: 0.1 }}
              >
                <svg width="14" height="14" fill="none" stroke="#fff" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
              </motion.button>
            </motion.div>
          </form>
          <p style={{ fontSize: 11.5, color: '#2a2a2a', textAlign: 'center', marginTop: 8 }}>AI Copilot has access to live pipeline, deal, and customer data.</p>
        </div>
      </div>
    </div>
  )
}
