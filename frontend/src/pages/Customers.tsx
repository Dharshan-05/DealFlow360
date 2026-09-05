import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { StaggerContainer, StaggerItem, AnimatedDrawer } from '../lib/motion'

const customers = [
  { id: 1, name: 'Acme Corporation', contact: 'Rajesh Kumar', email: 'rajesh@acme.com', segment: 'Enterprise', deals: 3, revenue: '₹12.4M', health: 87, status: 'Active', location: 'Mumbai', since: '2022' },
  { id: 2, name: 'NovaTech Ltd', contact: 'Priya Mehta', email: 'priya@novatech.in', segment: 'Mid-Market', deals: 1, revenue: '₹1.8M', health: 41, status: 'At Risk', location: 'Bangalore', since: '2024' },
  { id: 3, name: 'GlobalFin Inc', contact: 'Vikram Singh', email: 'vikram@globalfin.com', segment: 'Enterprise', deals: 2, revenue: '₹18.6M', health: 91, status: 'Active', location: 'Delhi', since: '2021' },
  { id: 4, name: 'Vertex Systems', contact: 'Ananya Patel', email: 'ananya@vertex.io', segment: 'SMB', deals: 1, revenue: '₹3.3M', health: 88, status: 'Active', location: 'Pune', since: '2023' },
  { id: 5, name: 'Meridian Capital', contact: 'Deepak Nair', email: 'deepak@meridian.in', segment: 'Enterprise', deals: 1, revenue: '₹2.7M', health: 38, status: 'At Risk', location: 'Chennai', since: '2024' },
  { id: 6, name: 'Zenith Retail', contact: 'Kavya Reddy', email: 'kavya@zenith.com', segment: 'Mid-Market', deals: 1, revenue: '₹890K', health: 96, status: 'Active', location: 'Hyderabad', since: '2023' },
  { id: 7, name: 'Horizon Pharma', contact: 'Sanjay Kumar', email: 'sanjay@horizon.in', segment: 'Enterprise', deals: 2, revenue: '₹4.1M', health: 60, status: 'Active', location: 'Mumbai', since: '2022' },
]

export default function Customers() {
  const [selected, setSelected] = useState<typeof customers[0] | null>(null)

  return (
    <div style={{ padding: '24px 28px' }}>
      <motion.div
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}
        initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}
      >
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#fff', letterSpacing: '-0.025em', marginBottom: 3 }}>Customers</h1>
          <p style={{ fontSize: 13, color: '#555' }}>{customers.length} accounts &#183; Enterprise CRM</p>
        </div>
        <motion.button className="df-btn-primary" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>+ Add Customer</motion.button>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 360px' : '1fr', gap: 16 }}>
        <div className="df-card" style={{ overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #141414' }}>
                {['Company', 'Contact', 'Segment', 'Active Deals', 'Revenue', 'Health', 'Status'].map(h => (
                  <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, color: '#444', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {customers.map((c, i) => (
                <motion.tr key={c.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.18 }}
                  style={{ borderBottom: i < customers.length - 1 ? '1px solid #0d0d0d' : 'none', cursor: 'pointer', background: selected?.id === c.id ? 'rgba(255,255,255,0.025)' : 'transparent' }}
                  whileHover={{ background: 'rgba(255,255,255,0.015)' }}
                  onClick={() => setSelected(selected?.id === c.id ? null : c)}
                >
                  <td style={{ padding: '12px 14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 34, height: 34, borderRadius: 8, background: '#151515', border: '1px solid #222', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: '#A1A1AA', flexShrink: 0 }}>
                        {c.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{c.name}</div>
                        <div style={{ fontSize: 11, color: '#444' }}>{c.location} &#183; Since {c.since}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <div style={{ fontSize: 12.5, color: '#A1A1AA' }}>{c.contact}</div>
                    <div style={{ fontSize: 11, color: '#444' }}>{c.email}</div>
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span style={{ fontSize: 11.5, color: '#A1A1AA', background: '#111', border: '1px solid #1e1e1e', borderRadius: 4, padding: '3px 8px' }}>{c.segment}</span>
                  </td>
                  <td style={{ padding: '12px 14px', fontSize: 14, fontWeight: 700, color: '#fff', textAlign: 'center' }} className="mono">{c.deals}</td>
                  <td style={{ padding: '12px 14px', fontSize: 13, fontWeight: 700, color: '#A1A1AA' }} className="mono">{c.revenue}</td>
                  <td style={{ padding: '12px 14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 48, background: '#1a1a1a', borderRadius: 2, height: 3 }}>
                        <motion.div
                          style={{ background: c.health > 75 ? '#10B981' : c.health > 50 ? '#F59E0B' : '#EF4444', height: '100%', borderRadius: 2 }}
                          initial={{ width: 0 }}
                          animate={{ width: `${c.health}%` }}
                          transition={{ delay: i * 0.05 + 0.3, duration: 0.6, ease: [0.0, 0.0, 0.2, 1.0] }}
                        />
                      </div>
                      <span style={{ fontSize: 11, color: '#555' }} className="mono">{c.health}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span style={{ fontSize: 11.5, fontWeight: 600, color: c.status === 'Active' ? '#10B981' : '#EF4444', background: c.status === 'Active' ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)', borderRadius: 4, padding: '3px 8px' }}>{c.status}</span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        <AnimatedDrawer open={!!selected} width={360}>
          {selected && (
            <>
              <div style={{ padding: '14px 16px', borderBottom: '1px solid #1a1a1a', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13.5, fontWeight: 600, color: '#fff' }}>Customer Profile</span>
                <motion.button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#555' }}
                  whileHover={{ color: '#fff' }} transition={{ duration: 0.1 }}
                >
                  <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </motion.button>
              </div>
              <div style={{ padding: '16px', overflowY: 'auto', maxHeight: 'calc(100vh - 180px)' }}>
                <motion.div
                  style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                >
                  <div style={{ width: 52, height: 52, borderRadius: 12, background: '#151515', border: '1px solid #222', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: '#A1A1AA' }}>
                    {selected.name.slice(0, 2)}
                  </div>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#fff' }}>{selected.name}</div>
                    <div style={{ fontSize: 12.5, color: '#555' }}>{selected.segment} &#183; {selected.location}</div>
                  </div>
                </motion.div>

                <StaggerContainer style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }} stagger={0.06} delayChildren={0.15}>
                  {[
                    { label: 'Total Revenue', value: selected.revenue },
                    { label: 'Active Deals', value: String(selected.deals) },
                    { label: 'Deal Health', value: `${selected.health}%` },
                    { label: 'Customer Since', value: selected.since },
                  ].map(item => (
                    <StaggerItem key={item.label}>
                      <div style={{ background: '#111', borderRadius: 8, padding: '12px' }}>
                        <div style={{ fontSize: 10, color: '#555', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4, fontWeight: 600 }}>{item.label}</div>
                        <div style={{ fontSize: 18, fontWeight: 700, color: '#fff' }} className="mono">{item.value}</div>
                      </div>
                    </StaggerItem>
                  ))}
                </StaggerContainer>

                <motion.div style={{ marginBottom: 14 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#555', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Contact</div>
                  <div style={{ background: '#111', borderRadius: 8, padding: '12px' }}>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: '#fff', marginBottom: 4 }}>{selected.contact}</div>
                    <div style={{ fontSize: 12.5, color: '#555' }}>{selected.email}</div>
                  </div>
                </motion.div>

                <motion.div style={{ marginBottom: 14 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#555', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>AI Insights</div>
                  <div style={{ background: 'rgba(124,58,237,0.06)', border: '1px solid rgba(124,58,237,0.2)', borderRadius: 8, padding: '12px' }}>
                    <p style={{ fontSize: 12.5, color: '#A1A1AA', lineHeight: 1.6, margin: 0 }}>
                      {selected.health > 75 ? `${selected.name} is a healthy account with strong engagement. High probability for renewal and expansion.` : `${selected.name} shows signs of risk. Consider proactive outreach and executive sponsor engagement.`}
                    </p>
                  </div>
                </motion.div>

                <motion.div style={{ display: 'flex', gap: 8 }} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
                  <motion.button className="df-btn-primary" style={{ flex: 1, padding: '10px', fontSize: 13 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>New Quote</motion.button>
                  <motion.button className="df-btn-secondary" style={{ flex: 1, padding: '10px', fontSize: 13 }} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>View Deals</motion.button>
                </motion.div>
              </div>
            </>
          )}
        </AnimatedDrawer>
      </div>
    </div>
  )
}
