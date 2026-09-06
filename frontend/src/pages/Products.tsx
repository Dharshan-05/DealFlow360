import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../lib/api'

interface Props { onAddToQuote: () => void }

export interface ProductCatalogItem {
  id: string
  name: string
  category: string
  price: string
  basePriceNum: number
  stock: number
  stockStatus: string
  rating: number
  sku: string
  ai: boolean
  aiNote: string
  image: string
  tags: string[]
}

function StarRating({ r }: { r: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
      {[1, 2, 3, 4, 5].map(i => (
        <svg key={i} width="10" height="10" viewBox="0 0 24 24" fill={i <= Math.floor(r) ? '#F59E0B' : '#1e1e1e'}>
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
        </svg>
      ))}
      <span style={{ fontSize: 11, color: '#555', marginLeft: 2 }}>{r}</span>
    </div>
  )
}

export default function Products({ onAddToQuote }: Props) {
  const [products, setProducts] = useState<ProductCatalogItem[]>([])
  const [categories, setCategories] = useState<string[]>(['All Products'])
  const [activeCategory, setActiveCategory] = useState('All Products')
  const [search, setSearch] = useState('')
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [added, setAdded] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCatalog = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [prodRes, catRes] = await Promise.all([
        api.products.list({ search: search.trim() || undefined, limit: 50 }),
        api.products.categories().catch(() => []),
      ])

      const catNames = ['All Products', ...(catRes || []).map((c: any) => c.name || c)]
      setCategories(Array.from(new Set(catNames)))

      const defaultImages = [
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=400&h=280&fit=crop&auto=format',
      ]

      const items = (prodRes.items || []).map((p: any, idx: number) => {
        const basePrice = Number(p.base_price || 0)
        const formattedPrice = `₹${basePrice.toLocaleString('en-IN')}`
        return {
          id: String(p.id),
          name: p.name || 'Enterprise Hardware',
          category: p.category_name || 'Hardware & Systems',
          price: formattedPrice,
          basePriceNum: basePrice,
          stock: p.stock_quantity ?? 24,
          stockStatus: (p.stock_quantity ?? 24) > 10 ? 'In Stock' : (p.stock_quantity ?? 24) > 0 ? 'Low Stock' : 'Out of Stock',
          rating: 4.8,
          sku: p.sku || `SKU-${idx + 1}`,
          ai: true,
          aiNote: 'High attach rate with Enterprise Support Bundle',
          image: defaultImages[idx % defaultImages.length],
          tags: (p.margin_percentage ?? 30) > 25 ? ['Best Margin', 'Best Seller'] : ['Standard Catalog'],
        }
      })
      setProducts(items)
    } catch (err: any) {
      setError(err?.message || 'Failed to load product catalog')
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => {
    fetchCatalog()
  }, [fetchCatalog])

  const filtered = products.filter(p => {
    const matchCat = activeCategory === 'All Products' || p.category === activeCategory
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || p.category.toLowerCase().includes(search.toLowerCase()) || p.sku.toLowerCase().includes(search.toLowerCase())
    return matchCat && matchSearch
  })

  const handleAdd = (id: string) => setAdded(prev => new Set([...prev, id]))

  return (
    <div style={{ padding: '24px 28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#fff', letterSpacing: '-0.025em', marginBottom: 3 }}>Products</h1>
          <p style={{ fontSize: 13, color: '#555' }}>{products.length} products in catalog &#183; Updated daily</p>
        </div>
        <motion.button onClick={onAddToQuote} className="df-btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          whileHover={{ opacity: 0.88, y: -1 }} whileTap={{ scale: 0.97 }} transition={{ duration: 0.12 }}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          Open Quote Workspace
        </motion.button>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center' }}>
        <div style={{ flex: 1, maxWidth: 440, position: 'relative' }}>
          <div style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#444' }}>
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          </div>
          <motion.input className="df-input"
            style={{ paddingLeft: 32, height: 36 }}
            placeholder="Search products..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            whileFocus={{ borderColor: '#444' }}
            transition={{ duration: 0.15 }}
          />
        </div>
        <div style={{ display: 'flex', background: '#0a0a0a', border: '1px solid #1e1e1e', borderRadius: 7, overflow: 'hidden' }}>
          {(['grid', 'list'] as const).map(v => (
            <motion.button key={v} onClick={() => setView(v)}
              style={{ padding: '7px 10px', background: view === v ? '#fff' : 'transparent', color: view === v ? '#000' : '#555', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
              whileTap={{ scale: 0.95 }}
              transition={{ duration: 0.1 }}
            >
              {v === 'grid'
                ? <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
                : <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
              }
            </motion.button>
          ))}
        </div>
      </div>

      {/* Categories */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 22, flexWrap: 'wrap' }}>
        {categories.map(cat => (
          <motion.button key={cat} onClick={() => setActiveCategory(cat)}
            style={{ padding: '6px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500, background: activeCategory === cat ? '#fff' : '#0a0a0a', color: activeCategory === cat ? '#000' : '#555', border: activeCategory === cat ? 'none' : '1px solid #1e1e1e', cursor: 'pointer', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap' }}
            whileHover={{ borderColor: '#333', color: activeCategory === cat ? '#000' : '#fff' }}
            whileTap={{ scale: 0.97 }}
            transition={{ duration: 0.12 }}
          >{cat}</motion.button>
        ))}
      </div>

      {/* Grid */}
      <AnimatePresence mode="wait">
        {view === 'grid' ? (
          <motion.div key="grid"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}
          >
            {filtered.map((p, i) => (
              <motion.div key={p.id}
                className="df-card"
                style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, duration: 0.2 }}
                whileHover={{ y: -3, boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}
              >
                <div style={{ height: 160, background: '#0d0d0d', position: 'relative', overflow: 'hidden' }}>
                  <img src={p.image} alt={p.name} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.7 }} />
                  <div style={{ position: 'absolute', top: 10, left: 10, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {p.tags.map(t => (
                      <span key={t} style={{ fontSize: 10, fontWeight: 700, background: t === 'AI-Powered' ? 'rgba(124,58,237,0.85)' : 'rgba(0,0,0,0.7)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, padding: '2px 6px', backdropFilter: 'blur(4px)' }}>{t}</span>
                    ))}
                  </div>
                  {p.ai && (
                    <div style={{ position: 'absolute', top: 10, right: 10, background: 'rgba(124,58,237,0.85)', borderRadius: 4, padding: '2px 6px', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <motion.div style={{ width: 5, height: 5, borderRadius: '50%', background: '#a78bfa' }}
                        animate={{ opacity: [1, 0.4, 1] }} transition={{ duration: 2, repeat: Infinity }}
                      />
                      <span style={{ fontSize: 10, fontWeight: 700, color: '#fff' }}>AI</span>
                    </div>
                  )}
                </div>

                <div style={{ padding: '14px 14px 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ fontSize: 11, color: '#555', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{p.category}</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#fff', lineHeight: 1.35 }}>{p.name}</div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 }}>
                    <StarRating r={p.rating} />
                    <span style={{ fontSize: 11, color: p.stockStatus === 'Low Stock' ? '#F59E0B' : '#10B981', fontWeight: 500 }}>{p.stockStatus}</span>
                  </div>

                  {p.ai && p.aiNote && (
                    <motion.div
                      style={{ background: 'rgba(124,58,237,0.06)', border: '1px solid rgba(124,58,237,0.15)', borderRadius: 5, padding: '6px 8px', marginTop: 2 }}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.1 }}
                    >
                      <div style={{ fontSize: 10, color: '#7C3AED', fontWeight: 700, marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Insight</div>
                      <div style={{ fontSize: 11, color: '#8B5CF6', lineHeight: 1.4 }}>{p.aiNote}</div>
                    </motion.div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto', paddingTop: 8 }}>
                    <div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#fff', letterSpacing: '-0.025em' }} className="mono">{p.price}</div>
                      <div style={{ fontSize: 11, color: '#444' }}>{p.stock < 100 ? `${p.stock} units` : 'Unlimited'}</div>
                    </div>
                    <motion.button
                      onClick={() => handleAdd(p.id)}
                      style={{
                        padding: '8px 14px', borderRadius: 7, fontSize: 12.5, fontWeight: 600,
                        background: added.has(p.id) ? '#0d2d1a' : '#fff',
                        color: added.has(p.id) ? '#10B981' : '#000',
                        border: added.has(p.id) ? '1px solid rgba(16,185,129,0.3)' : 'none',
                        cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                        display: 'flex', alignItems: 'center', gap: 5,
                      }}
                      whileHover={added.has(p.id) ? {} : { opacity: 0.88 }}
                      whileTap={{ scale: 0.95 }}
                      transition={{ duration: 0.1 }}
                    >
                      {added.has(p.id) ? (
                        <motion.span initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                          <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                          Added
                        </motion.span>
                      ) : '+ Add to Quote'}
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div key="list" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
            <div className="df-card" style={{ overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #141414' }}>
                    {['Product', 'Category', 'Price', 'Stock', 'Rating', ''].map(h => (
                      <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, color: '#444', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((p, i) => (
                    <motion.tr key={p.id}
                      style={{ borderBottom: i < filtered.length - 1 ? '1px solid #0d0d0d' : 'none' }}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.04 }}
                      whileHover={{ background: 'rgba(255,255,255,0.02)' }}
                    >
                      <td style={{ padding: '12px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div style={{ width: 40, height: 40, borderRadius: 6, overflow: 'hidden', flexShrink: 0, background: '#111' }}>
                            <img src={p.image} alt={p.name} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.7 }} />
                          </div>
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{p.name}</div>
                            {p.ai && <span style={{ fontSize: 10, color: '#7C3AED', fontWeight: 600 }}>AI RECOMMENDED</span>}
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: 12.5, color: '#555' }}>{p.category}</td>
                      <td style={{ padding: '12px 16px', fontSize: 13, fontWeight: 700, color: '#fff' }} className="mono">{p.price}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontSize: 12, color: p.stockStatus === 'Low Stock' ? '#F59E0B' : '#10B981', fontWeight: 500 }}>{p.stockStatus}</span>
                      </td>
                      <td style={{ padding: '12px 16px' }}><StarRating r={p.rating} /></td>
                      <td style={{ padding: '12px 16px' }}>
                        <motion.button onClick={() => handleAdd(p.id)}
                          style={{ padding: '7px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600, background: added.has(p.id) ? 'transparent' : '#fff', color: added.has(p.id) ? '#10B981' : '#000', border: added.has(p.id) ? '1px solid rgba(16,185,129,0.3)' : 'none', cursor: 'pointer', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap' }}
                          whileHover={added.has(p.id) ? {} : { opacity: 0.88 }}
                          whileTap={{ scale: 0.96 }}
                        >{added.has(p.id) ? '✓ Added' : '+ Quote'}</motion.button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
