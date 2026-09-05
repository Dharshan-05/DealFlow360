import { useState, useEffect } from 'react'
import {
  motion,
  AnimatePresence,
  FadeIn,
  RevealOnScroll,
  StaggerContainer,
  StaggerItem,
  HoverScale,
  AnimatedNumber,
} from '../lib/motion'

interface Props {
  onLogin: () => void
  onGetStarted: () => void
}

const features = [
  {
    tag: 'AI Sales Intelligence',
    title: 'Every deal, understood by AI.',
    desc: 'DealFlow360 continuously analyzes pipeline health, customer signals, and pricing patterns to surface the actions that close deals faster.',
    metric: 34, metricLabel: 'faster deal cycles', metricSuffix: '%',
    bullets: ['Behavioral deal scoring', 'Next-best-action recommendations', 'Win probability forecasting'],
  },
  {
    tag: 'Smart Pricing Engine',
    title: 'Discounts that protect margin.',
    desc: 'AI recommends optimal discounts within policy guardrails — balancing win probability with margin health for every quote.',
    metric: 18, metricLabel: 'average margin improvement', metricSuffix: '%',
    bullets: ['Policy-aware discount modeling', 'Customer segment benchmarking', 'Real-time risk scoring'],
  },
  {
    tag: 'Human Approval Layer',
    title: 'High-stakes decisions, under control.',
    desc: 'Escalation flows route high-impact approvals to the right people with full deal context, AI reasoning, and one-click decisions.',
    metric: 4.2, metricLabel: 'average approval time', metricSuffix: 'm',
    bullets: ['Smart escalation routing', 'AI-assisted decision briefs', 'Complete audit trail'],
  },
  {
    tag: 'Connected Finance',
    title: 'Quote to cash, without gaps.',
    desc: 'Billing, subscriptions, and payments stay connected to the originating deal — eliminating reconciliation overhead and revenue leakage.',
    metric: 99.7, metricLabel: 'billing accuracy', metricSuffix: '%',
    bullets: ['Automated invoice generation', 'Subscription lifecycle management', 'Payment health monitoring'],
  },
]

function HeroDashboard() {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 3000)
    return () => clearInterval(id)
  }, [])

  const aiActions = [
    'Acme Corp — discount at risk limit. Suggest 7%.',
    'NovaTech deal stalled. Recommend follow-up.',
    'GlobalFin ready to close. Upsell opportunity.',
  ]

  const deals = [
    { name: 'Acme Corp', value: '₹4.2M', stage: 'Quote', risk: 'medium', health: 74 },
    { name: 'NovaTech Ltd', value: '₹1.8M', stage: 'Approval', risk: 'high', health: 41 },
    { name: 'GlobalFin Inc', value: '₹6.1M', stage: 'Negotiation', risk: 'low', health: 91 },
    { name: 'Vertex Systems', value: '₹3.3M', stage: 'Fulfillment', risk: 'low', health: 88 },
  ]
  const riskColor = (r: string) =>
    r === 'high' ? '#EF4444' : r === 'medium' ? '#F59E0B' : '#10B981'

  return (
    <FadeIn delay={0.5} distance={24} style={{ position: 'relative', marginTop: 72, perspective: 1200 }}>
      <motion.div
        style={{
          background: 'linear-gradient(180deg, #111 0%, #0a0a0a 100%)',
          border: '1px solid #222',
          borderRadius: 16,
          overflow: 'hidden',
          maxWidth: 980,
          margin: '0 auto',
          transform: 'rotateX(4deg)',
          transformOrigin: 'top center',
          boxShadow: '0 40px 120px rgba(0,0,0,0.8), 0 0 0 1px #1a1a1a',
        }}
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, delay: 0.4, ease: [0.0, 0.0, 0.2, 1.0] }}
      >
        {/* Topbar */}
        <div style={{ borderBottom: '1px solid #1a1a1a', padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', gap: 6 }}>
            {[0, 1, 2].map(i => <div key={i} style={{ width: 10, height: 10, borderRadius: '50%', background: '#333' }} />)}
          </div>
          <div style={{ flex: 1, background: '#0d0d0d', borderRadius: 5, height: 24, border: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', padding: '0 10px' }}>
            <span style={{ fontSize: 11, color: '#444' }}>app.dealflow360.io/command-center</span>
          </div>
        </div>

        <div style={{ display: 'flex', height: 520 }}>
          {/* Sidebar */}
          <div style={{ width: 52, borderRight: '1px solid #1a1a1a', padding: '16px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 28, height: 28, background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', borderRadius: 6, marginBottom: 8 }} />
            {[0, 1, 2, 3, 4].map(i => (
              <motion.div key={i}
                style={{ width: 32, height: 32, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', background: i === 0 ? '#1a1a1a' : 'none' }}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + i * 0.06, duration: 0.2 }}
              >
                <div style={{ width: 16, height: 2, background: i === 0 ? '#fff' : '#2a2a2a', borderRadius: 1 }} />
              </motion.div>
            ))}
          </div>

          {/* Main */}
          <div style={{ flex: 1, padding: '20px', overflow: 'hidden' }}>
            {/* KPI row */}
            <StaggerContainer style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 18 }} stagger={0.07} delayChildren={0.7}>
              {[
                { label: 'Total Revenue', value: 48.2, suffix: 'M', up: true },
                { label: 'Pipeline Value', value: 124, suffix: 'M', up: true },
                { label: 'Pending Approvals', value: 7, suffix: '', up: false },
                { label: 'At Risk Deals', value: 12, suffix: '', up: false },
              ].map((kpi, i) => (
                <StaggerItem key={i}>
                  <div style={{ background: '#0d0d0d', border: '1px solid #1a1a1a', borderRadius: 8, padding: '12px 14px' }}>
                    <div style={{ fontSize: 10, color: '#555', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{kpi.label}</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: '#fff', lineHeight: 1 }}>
                      ₹<AnimatedNumber value={kpi.value} format={v => v.toFixed(1)} />{kpi.suffix}
                    </div>
                    <div style={{ fontSize: 10, color: kpi.up ? '#10B981' : '#71717A', marginTop: 3 }}>{kpi.up ? '+14%' : 'needs action'}</div>
                  </div>
                </StaggerItem>
              ))}
            </StaggerContainer>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: 12 }}>
              {/* Deal list */}
              <div style={{ background: '#0d0d0d', border: '1px solid #1a1a1a', borderRadius: 8, overflow: 'hidden' }}>
                <div style={{ padding: '10px 14px', borderBottom: '1px solid #1a1a1a', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: '#fff' }}>Active Deals</span>
                  <span style={{ fontSize: 10, color: '#555' }}>Live</span>
                </div>
                {deals.map((d, i) => (
                  <motion.div key={i}
                    style={{ padding: '9px 14px', borderBottom: i < deals.length - 1 ? '1px solid #141414' : 'none', display: 'flex', alignItems: 'center', gap: 10 }}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.9 + i * 0.08, duration: 0.2 }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, color: '#fff', fontWeight: 500 }}>{d.name}</div>
                      <div style={{ fontSize: 10, color: '#555' }}>{d.stage}</div>
                    </div>
                    <div style={{ fontSize: 12, color: '#A1A1AA', fontWeight: 600 }}>{d.value}</div>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: riskColor(d.risk) }} />
                    <div style={{ width: 60, background: '#1a1a1a', borderRadius: 2, height: 3 }}>
                      <motion.div
                        style={{ background: d.health > 75 ? '#10B981' : d.health > 55 ? '#F59E0B' : '#EF4444', height: '100%', borderRadius: 2 }}
                        initial={{ width: 0 }}
                        animate={{ width: `${d.health}%` }}
                        transition={{ delay: 1.1 + i * 0.08, duration: 0.5, ease: [0.0, 0.0, 0.2, 1.0] }}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* AI panel */}
              <div style={{ background: '#0d0d0d', border: '1px solid #1a1a1a', borderRadius: 8, overflow: 'hidden' }}>
                <div style={{ padding: '10px 14px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <motion.div
                    style={{ width: 6, height: 6, borderRadius: '50%', background: '#7C3AED' }}
                    animate={{ opacity: [1, 0.4, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                  <span style={{ fontSize: 12, fontWeight: 600, color: '#fff' }}>AI Actions</span>
                </div>
                {aiActions.map((a, i) => (
                  <motion.div key={i}
                    style={{ padding: '9px 12px', borderBottom: i < aiActions.length - 1 ? '1px solid #141414' : 'none' }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.0 + i * 0.15, duration: 0.25 }}
                  >
                    <div style={{ fontSize: 10.5, color: '#A1A1AA', lineHeight: 1.5 }}>{a}</div>
                    <div style={{ marginTop: 5, fontSize: 10, color: '#7C3AED', cursor: 'pointer', fontWeight: 600 }}>Take action →</div>
                  </motion.div>
                ))}
                <div style={{ padding: '10px 12px' }}>
                  <AnimatePresence mode="wait">
                    <motion.div key={tick}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{ duration: 0.2 }}
                      style={{ background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.2)', borderRadius: 6, padding: '8px 10px' }}
                    >
                      <div style={{ fontSize: 10, color: '#7C3AED', fontWeight: 600, marginBottom: 2 }}>AI COPILOT</div>
                      <div style={{ fontSize: 10.5, color: '#A1A1AA' }}>{aiActions[tick % aiActions.length].split('.')[0]}.</div>
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
      <div style={{ position: 'absolute', bottom: -40, left: '50%', transform: 'translateX(-50%)', width: 500, height: 80, background: 'radial-gradient(ellipse, rgba(124,58,237,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />
    </FadeIn>
  )
}

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  const isEven = index % 2 === 0
  return (
    <RevealOnScroll delay={0.05} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center', padding: '80px 0', borderBottom: '1px solid #111' }}>
      <div style={{ order: isEven ? 0 : 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, ease: [0.0, 0.0, 0.2, 1.0] }}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.15)', borderRadius: 5, padding: '4px 10px', marginBottom: 20 }}
        >
          <span style={{ fontSize: 11, color: '#7C3AED', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>{feature.tag}</span>
        </motion.div>
        <motion.h3
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.35, delay: 0.05, ease: [0.0, 0.0, 0.2, 1.0] }}
          style={{ fontSize: 34, fontWeight: 700, letterSpacing: '-0.03em', lineHeight: 1.15, color: '#fff', marginBottom: 16 }}
        >{feature.title}</motion.h3>
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.35, delay: 0.1, ease: [0.0, 0.0, 0.2, 1.0] }}
          style={{ fontSize: 16, color: '#71717A', lineHeight: 1.7, marginBottom: 28 }}
        >{feature.desc}</motion.p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {feature.bullets.map((b, i) => (
            <motion.div key={b}
              initial={{ opacity: 0, x: -8 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.25, delay: 0.15 + i * 0.06 }}
              style={{ display: 'flex', alignItems: 'center', gap: 10 }}
            >
              <div style={{ width: 5, height: 5, borderRadius: '50%', background: '#333', flexShrink: 0 }} />
              <span style={{ fontSize: 14, color: '#A1A1AA' }}>{b}</span>
            </motion.div>
          ))}
        </div>
      </div>
      <div style={{ order: isEven ? 1 : 0 }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, ease: [0.0, 0.0, 0.2, 1.0] }}
          style={{ background: '#0d0d0d', border: '1px solid #1e1e1e', borderRadius: 12, padding: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}
        >
          <div style={{ fontSize: 56, fontWeight: 800, letterSpacing: '-0.04em', color: '#fff' }}>
            <AnimatedNumber value={feature.metric} format={v => `${v.toFixed(feature.metricSuffix === 'm' ? 1 : 0)}${feature.metricSuffix}`} />
          </div>
          <div style={{ fontSize: 14, color: '#555', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{feature.metricLabel}</div>
          <div style={{ width: '100%', height: 1, background: '#1a1a1a' }} />
          <div style={{ fontSize: 13, color: '#A1A1AA', textAlign: 'center', lineHeight: 1.6 }}>{feature.desc.split('.')[0]}.</div>
        </motion.div>
      </div>
    </RevealOnScroll>
  )
}

export default function LandingPage({ onLogin, onGetStarted }: Props) {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 30)
    window.addEventListener('scroll', handler)
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <div style={{ background: '#000', color: '#fff', minHeight: '100vh' }}>
      {/* Navigation */}
      <motion.nav
        style={{
          position: 'sticky', top: 0, zIndex: 100,
          borderBottom: scrolled ? '1px solid #161616' : '1px solid transparent',
          background: scrolled ? 'rgba(0,0,0,0.92)' : 'transparent',
          backdropFilter: scrolled ? 'blur(16px)' : 'none',
          transition: 'background 0.3s ease, border-color 0.3s ease',
        }}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.0, 0.0, 0.2, 1.0] }}
      >
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 26, height: 26, background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', borderRadius: 6 }} />
            <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: '-0.025em' }}>DealFlow360</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
            {['Product', 'Solutions', 'AI Intelligence', 'Resources', 'Pricing'].map(link => (
              <motion.button key={link}
                style={{ color: '#71717A', fontSize: 14, fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                whileHover={{ color: '#fff' }}
                transition={{ duration: 0.12 }}
              >{link}</motion.button>
            ))}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <motion.button onClick={onLogin}
              style={{ color: '#A1A1AA', fontSize: 14, fontWeight: 500, background: 'none', border: 'none', cursor: 'pointer', padding: '8px 14px' }}
              whileHover={{ color: '#fff' }}
              transition={{ duration: 0.12 }}
            >Log in</motion.button>
            <motion.button onClick={onGetStarted} className="df-btn-primary"
              whileHover={{ opacity: 0.88, y: -1 }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.12 }}
            >Get Started</motion.button>
          </div>
        </div>
      </motion.nav>

      {/* Hero */}
      <section style={{ padding: '100px 32px 60px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
        <div className="hero-glow" />
        <div style={{ maxWidth: 760, margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <FadeIn delay={0.05} distance={8}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: '#0d0d0d', border: '1px solid #1e1e1e', borderRadius: 100, padding: '5px 14px', marginBottom: 36 }}>
              <motion.div
                style={{ width: 6, height: 6, borderRadius: '50%', background: '#7C3AED' }}
                animate={{ opacity: [1, 0.4, 1] }}
                transition={{ duration: 2.5, repeat: Infinity }}
              />
              <span style={{ fontSize: 12, color: '#A1A1AA', fontWeight: 500 }}>AI-Powered Sales Operations Platform</span>
            </div>
          </FadeIn>

          <FadeIn delay={0.12} distance={16}>
            <h1 style={{ fontSize: 68, fontWeight: 800, lineHeight: 1.04, letterSpacing: '-0.045em', marginBottom: 22 }}>
              Sales operations,<br />
              <span style={{ color: '#3a3a3a' }}>intelligently connected.</span>
            </h1>
          </FadeIn>

          <FadeIn delay={0.2} distance={10}>
            <p style={{ fontSize: 17, color: '#555', lineHeight: 1.7, marginBottom: 40, maxWidth: 520, margin: '0 auto 40px' }}>
              DealFlow360 connects customers, products, pricing, risk, approvals, fulfillment and finance into one intelligent sales operating system.
            </p>
          </FadeIn>

          <FadeIn delay={0.28}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <motion.button onClick={onGetStarted} className="df-btn-primary"
                style={{ fontSize: 15, padding: '12px 28px' }}
                whileHover={{ opacity: 0.88, y: -1 }}
                whileTap={{ scale: 0.97 }}
              >Get Started</motion.button>
              <motion.button className="df-btn-secondary"
                style={{ fontSize: 15, padding: '12px 28px' }}
                whileHover={{ borderColor: '#444', color: '#fff' }}
                whileTap={{ scale: 0.97 }}
              >Explore Platform</motion.button>
            </div>
          </FadeIn>
        </div>
        <HeroDashboard />
      </section>

      {/* Logos strip */}
      <RevealOnScroll style={{ borderTop: '1px solid #111', borderBottom: '1px solid #111', padding: '28px 32px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: '#3a3a3a', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 20 }}>Trusted by enterprise sales teams</p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 52, flexWrap: 'wrap' }}>
            {['Acme Corp', 'NovaTech', 'GlobalFin', 'Vertex Systems', 'Meridian Inc'].map(name => (
              <span key={name} style={{ fontSize: 14, fontWeight: 700, color: '#2a2a2a', letterSpacing: '-0.02em' }}>{name}</span>
            ))}
          </div>
        </div>
      </RevealOnScroll>

      {/* Features */}
      <section style={{ padding: '0 32px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <RevealOnScroll style={{ textAlign: 'center', padding: '80px 0 40px' }}>
            <h2 style={{ fontSize: 44, fontWeight: 800, letterSpacing: '-0.04em', marginBottom: 14 }}>Everything a deal needs to close.</h2>
            <p style={{ fontSize: 16, color: '#555', maxWidth: 440, margin: '0 auto' }}>From first contact to final payment, DealFlow360 orchestrates the entire revenue cycle.</p>
          </RevealOnScroll>
          {features.map((f, i) => <FeatureCard key={i} feature={f} index={i} />)}
        </div>
      </section>

      {/* AI Copilot */}
      <section style={{ padding: '100px 32px', borderTop: '1px solid #111' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center' }}>
          <RevealOnScroll>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.15)', borderRadius: 5, padding: '4px 10px', marginBottom: 20 }}>
              <span style={{ fontSize: 11, color: '#7C3AED', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>AI Copilot</span>
            </div>
            <h2 style={{ fontSize: 42, fontWeight: 800, letterSpacing: '-0.04em', lineHeight: 1.1, marginBottom: 18 }}>Your AI sales intelligence, always on.</h2>
            <p style={{ fontSize: 16, color: '#555', lineHeight: 1.7, marginBottom: 28 }}>
              Ask DealFlow360 anything about your pipeline, customers, or business performance.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {['"Which deals are most at risk this quarter?"', '"What is our average approval time?"', '"Summarize the GlobalFin negotiation."'].map((q, i) => (
                <motion.div key={q}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.1 + i * 0.08, duration: 0.25 }}
                  style={{ background: '#0d0d0d', border: '1px solid #1e1e1e', borderRadius: 8, padding: '10px 14px' }}
                >
                  <span style={{ fontSize: 13.5, color: '#A1A1AA', fontStyle: 'italic' }}>{q}</span>
                </motion.div>
              ))}
            </div>
          </RevealOnScroll>

          <RevealOnScroll delay={0.1} style={{ background: '#0a0a0a', border: '1px solid #1e1e1e', borderRadius: 14, overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', gap: 8 }}>
              <motion.div
                style={{ width: 8, height: 8, borderRadius: '50%', background: '#7C3AED' }}
                animate={{ opacity: [1, 0.4, 1] }}
                transition={{ duration: 2.5, repeat: Infinity }}
              />
              <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>AI Copilot</span>
            </div>
            <div style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <div style={{ background: '#fff', color: '#000', borderRadius: '10px 10px 2px 10px', padding: '10px 14px', fontSize: 13 }}>
                  Which deals need attention right now?
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <div style={{ width: 28, height: 28, borderRadius: 7, background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="14" height="14" fill="none" stroke="#fff" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                </div>
                <div style={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: '10px 10px 10px 2px', padding: '12px 14px', fontSize: 13, color: '#A1A1AA', lineHeight: 1.6, maxWidth: '85%' }}>
                  <strong style={{ color: '#fff', display: 'block', marginBottom: 4 }}>12 deals need your attention.</strong>
                  4 have high payment risk, 3 exceed discount policy limits, and 5 have stalled for more than 7 days.
                  <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {['Show high-risk deals', 'Review approvals', 'Find upsell opportunities'].map(a => (
                      <motion.div key={a}
                        style={{ background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.2)', borderRadius: 5, padding: '4px 10px', fontSize: 11, color: '#8B5CF6', cursor: 'pointer', fontWeight: 500 }}
                        whileHover={{ background: 'rgba(124,58,237,0.18)' }}
                      >{a}</motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div style={{ padding: '12px 14px', borderTop: '1px solid #141414' }}>
              <div style={{ background: '#0d0d0d', border: '1px solid #1e1e1e', borderRadius: 8, padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, color: '#333' }}>Ask DealFlow360...</span>
                <motion.div
                  style={{ marginLeft: 'auto', width: 2, height: 16, background: '#444' }}
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 1.1, repeat: Infinity }}
                />
              </div>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      {/* CTA */}
      <RevealOnScroll style={{ padding: '100px 32px', borderTop: '1px solid #111', textAlign: 'center' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 style={{ fontSize: 52, fontWeight: 800, letterSpacing: '-0.045em', lineHeight: 1.05, marginBottom: 20 }}>
            Your entire revenue cycle, finally connected.
          </h2>
          <p style={{ fontSize: 17, color: '#555', lineHeight: 1.7, marginBottom: 40 }}>
            Join enterprise sales teams using DealFlow360 to close faster, protect margins, and scale operations.
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <motion.button onClick={onGetStarted} className="df-btn-primary"
              style={{ fontSize: 15, padding: '13px 32px' }}
              whileHover={{ opacity: 0.88, y: -1 }}
              whileTap={{ scale: 0.97 }}
            >Get Started</motion.button>
            <motion.button className="df-btn-secondary"
              style={{ fontSize: 15, padding: '13px 28px' }}
              whileHover={{ borderColor: '#444', color: '#fff' }}
              whileTap={{ scale: 0.97 }}
            >Book a Demo</motion.button>
          </div>
        </div>
      </RevealOnScroll>

      <footer style={{ borderTop: '1px solid #111', padding: '40px 32px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 22, height: 22, background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', borderRadius: 5 }} />
            <span style={{ fontWeight: 700, fontSize: 14, letterSpacing: '-0.02em' }}>DealFlow360</span>
          </div>
          <div style={{ display: 'flex', gap: 24 }}>
            {['Privacy', 'Terms', 'Security', 'Status'].map(link => (
              <span key={link} style={{ fontSize: 13, color: '#444', cursor: 'pointer' }}>{link}</span>
            ))}
          </div>
          <span style={{ fontSize: 13, color: '#333' }}>&#169; 2026 DealFlow360</span>
        </div>
      </footer>
    </div>
  )
}
