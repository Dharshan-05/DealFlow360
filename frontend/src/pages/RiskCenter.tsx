import { useState } from 'react'
import { motion } from 'framer-motion'
import { StaggerContainer, StaggerItem, AnimatedNumber } from '../lib/motion'

const riskDeals = [
  { deal: 'Meridian Capital', customer: 'Deepak Nair', value: '₹2.7M', overall: 'Critical', pricing: 'Critical', payment: 'High', inventory: 'Low', policy: 'High', age: '2d', health: 22 },
  { deal: 'Pinnacle Group', customer: 'Ravi Sharma', value: '₹6.2M', overall: 'Critical', pricing: 'Critical', payment: 'Medium', inventory: 'Low', policy: 'Critical', age: '8h', health: 18 },
  { deal: 'NovaTech Ltd', customer: 'Priya Mehta', value: '₹1.8M', overall: 'High', pricing: 'High', payment: 'Medium', inventory: 'Low', policy: 'High', age: '1d', health: 41 },
  { deal: 'Apex Fintech', customer: 'Kiran Rao', value: '₹1.1M', overall: 'High', pricing: 'High', payment: 'High', inventory: 'Low', policy: 'Medium', age: '2d', health: 38 },
  { deal: 'Horizon Pharma', customer: 'Sanjay Kumar', value: '₹980K', overall: 'Medium', pricing: 'Medium', payment: 'Low', inventory: 'Medium', policy: 'Medium', age: '4h', health: 60 },
  { deal: 'GlobalFin Inc', customer: 'Vikram Singh', value: '₹6.1M', overall: 'Low', pricing: 'Low', payment: 'Low', inventory: 'Low', policy: 'Low', age: '7d', health: 91 },
  { deal: 'Zenith Retail', customer: 'Kavya Reddy', value: '₹890K', overall: 'Low', pricing: 'Low', payment: 'Low', inventory: 'Low', policy: 'Low', age: '18d', health: 96 },
]

const rc = (r: string) => r === 'Critical' ? '#EF4444' : r === 'High' ? '#F97316' : r === 'Medium' ? '#F59E0B' : '#10B981'
const rb = (r: string) => r === 'Critical' ? 'rgba(239,68,68,0.08)' : r === 'High' ? 'rgba(249,115,22,0.08)' : r === 'Medium' ? 'rgba(245,158,11,0.08)' : 'rgba(16,185,129,0.08)'

function RiskBadge({ level }: { level: string }) {
  return <span style={{ fontSize: 11, fontWeight: 600, color: rc(level), background: rb(level), borderRadius: 4, padding: '2px 8px', whiteSpace: 'nowrap' }}>{level}</span>
}

function HealthBar({ v }: { v: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width: 60, background: '#1a1a1a', borderRadius: 2, height: 3 }}>
        <motion.div
          style={{ background: v > 75 ? '#10B981' : v > 50 ? '#F59E0B' : '#EF4444', height: '100%', borderRadius: 2 }}
          initial={{ width: 0 }}
          animate={{ width: `${v}%` }}
          transition={{ duration: 0.7, delay: 0.2, ease: [0.0, 0.0, 0.2, 1.0] }}
        />
      </div>
      <span style={{ fontSize: 11, color: '#555' }} className="mono">{v}</span>
    </div>
  )
}

const categories = [
  { label: 'Pricing Risk', count: 4, critical: 2 },
  { label: 'Payment Risk', count: 5, critical: 1 },
  { label: 'Policy Risk', count: 6, critical: 2 },
  { label: 'Inventory Risk', count: 2, critical: 0 },
  { label: 'Customer Risk', count: 3, critical: 1 },
  { label: 'Operational Risk', count: 2, critical: 0 },
]

export default function RiskCenter() {
  const [filter, setFilter] = useState('All')
  const counts = { Critical: 0, High: 0, Medium: 0, Low: 0 }
  riskDeals.forEach(d => { counts[d.overall as keyof typeof counts]++ })
  const filtered = filter === 'All' ? riskDeals : riskDeals.filter(d => d.overall === filter)

  return (
    <div style={{ padding: '24px 28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#fff', letterSpacing: '-0.025em', marginBottom: 3 }}>Risk & Compliance</h1>
          <p style={{ fontSize: 13, color: '#555' }}>Real-time risk monitoring across all active deals</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {['All', 'Critical', 'High', 'Medium', 'Low'].map(f => (
            <motion.button key={f} onClick={() => setFilter(f)}
              style={{ padding: '6px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500, background: filter === f ? (f === 'All' ? '#fff' : rb(f)) : '#0a0a0a', color: filter === f ? (f === 'All' ? '#000' : rc(f)) : '#555', border: filter === f ? (f === 'All' ? 'none' : `1px solid ${rc(f)}33`) : '1px solid #1e1e1e', cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}
              whileHover={{ borderColor: '#333', color: filter === f ? undefined : '#fff' }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.12 }}
            >{f} {f !== 'All' && <span className="mono" style={{ fontSize: 11 }}>({counts[f as keyof typeof counts]})</span>}</motion.button>
          ))}
        </div>
      </div>

      <StaggerContainer style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }} stagger={0.06}>
        {[
          { label: 'Critical', count: counts.Critical, color: '#EF4444', bg: 'rgba(239,68,68,0.06)', border: 'rgba(239,68,68,0.2)' },
          { label: 'High Risk', count: counts.High, color: '#F97316', bg: 'rgba(249,115,22,0.06)', border: 'rgba(249,115,22,0.2)' },
          { label: 'Medium Risk', count: counts.Medium, color: '#F59E0B', bg: 'rgba(245,158,11,0.06)', border: 'rgba(245,158,11,0.2)' },
          { label: 'Low Risk', count: counts.Low, color: '#10B981', bg: 'rgba(16,185,129,0.06)', border: 'rgba(16,185,129,0.2)' },
        ].map(card => (
          <StaggerItem key={card.label}>
            <motion.div
              style={{ background: card.bg, border: `1px solid ${card.border}`, borderRadius: 10, padding: '18px 20px', cursor: 'pointer' }}
              onClick={() => setFilter(card.label === 'High Risk' ? 'High' : card.label === 'Medium Risk' ? 'Medium' : card.label === 'Low Risk' ? 'Low' : card.label)}
              whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} transition={{ duration: 0.13 }}
            >
              <div style={{ fontSize: 11, color: card.color, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10, fontWeight: 600 }}>{card.label}</div>
              <div style={{ fontSize: 40, fontWeight: 800, color: card.color, letterSpacing: '-0.03em', lineHeight: 1 }} className="mono">
                <AnimatedNumber value={card.count} />
              </div>
              <div style={{ fontSize: 12, color: '#555', marginTop: 4 }}>active deals</div>
            </motion.div>
          </StaggerItem>
        ))}
      </StaggerContainer>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 16 }}>
        <div className="df-card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
            <span style={{ fontSize: 13.5, fontWeight: 600, color: '#fff' }}>Deal Risk Matrix</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #141414' }}>
                {['Deal', 'Value', 'Overall', 'Pricing', 'Payment', 'Policy', 'Age', 'Health'].map(h => (
                  <th key={h} style={{ padding: '9px 14px', textAlign: 'left', fontSize: 11, color: '#444', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((d, i) => (
                <motion.tr key={i}
                  style={{ borderBottom: i < filtered.length - 1 ? '1px solid #0d0d0d' : 'none' }}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.18 }}
                  whileHover={{ background: 'rgba(255,255,255,0.02)' }}
                >
                  <td style={{ padding: '11px 14px' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{d.deal}</div>
                    <div style={{ fontSize: 11, color: '#444' }}>{d.customer}</div>
                  </td>
                  <td style={{ padding: '11px 14px', fontSize: 13, fontWeight: 700, color: '#A1A1AA' }} className="mono">{d.value}</td>
                  <td style={{ padding: '11px 14px' }}><RiskBadge level={d.overall} /></td>
                  <td style={{ padding: '11px 14px' }}><RiskBadge level={d.pricing} /></td>
                  <td style={{ padding: '11px 14px' }}><RiskBadge level={d.payment} /></td>
                  <td style={{ padding: '11px 14px' }}><RiskBadge level={d.policy} /></td>
                  <td style={{ padding: '11px 14px', fontSize: 12, color: '#444' }}>{d.age}</td>
                  <td style={{ padding: '11px 14px' }}><HealthBar v={d.health} /></td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="df-card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
            <span style={{ fontSize: 13.5, fontWeight: 600, color: '#fff' }}>Risk by Category</span>
          </div>
          {categories.map((cat, i) => (
            <motion.div key={i}
              style={{ padding: '13px 16px', borderBottom: i < categories.length - 1 ? '1px solid #0d0d0d' : 'none' }}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 + i * 0.06, duration: 0.2 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: 13, color: '#A1A1AA', fontWeight: 500 }}>{cat.label}</span>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  {cat.critical > 0 && (
                    <span style={{ fontSize: 10, fontWeight: 700, color: '#EF4444', background: 'rgba(239,68,68,0.1)', borderRadius: 3, padding: '1px 5px' }}>{cat.critical} critical</span>
                  )}
                  <span style={{ fontSize: 13, fontWeight: 700, color: '#fff' }} className="mono">{cat.count}</span>
                </div>
              </div>
              <div style={{ background: '#111', borderRadius: 3, height: 4 }}>
                <motion.div
                  style={{ background: cat.critical > 1 ? '#EF4444' : cat.critical > 0 ? '#F97316' : '#F59E0B', height: '100%', borderRadius: 3 }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(cat.count / riskDeals.length) * 100}%` }}
                  transition={{ delay: 0.2 + i * 0.07, duration: 0.5, ease: [0.0, 0.0, 0.2, 1.0] }}
                />
              </div>
            </motion.div>
          ))}
          <div style={{ margin: '0 12px 12px', background: 'rgba(124,58,237,0.06)', border: '1px solid rgba(124,58,237,0.2)', borderRadius: 8, padding: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
              <motion.div style={{ width: 6, height: 6, borderRadius: '50%', background: '#7C3AED' }}
                animate={{ opacity: [1, 0.4, 1] }} transition={{ duration: 2.5, repeat: Infinity }}
              />
              <span style={{ fontSize: 11, fontWeight: 700, color: '#7C3AED', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Risk Summary</span>
            </div>
            <p style={{ fontSize: 12, color: '#A1A1AA', lineHeight: 1.6, margin: 0 }}>
              2 critical deals require immediate attention. Meridian Capital and Pinnacle Group both exceed policy limits significantly.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
