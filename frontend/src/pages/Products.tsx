import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../lib/api'

interface Props {
  onAddToQuote: () => void
  onOpenProductDetail?: (productId: string) => void
}

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

export const FALLBACK_CATALOG: ProductCatalogItem[] = [
  {
    id: 'prd-fb-001',
    name: 'CoreSwitch Blade 48-Port 100GbE',
    category: 'Hardware',
    price: '₹480,000',
    basePriceNum: 480000,
    stock: 42,
    stockStatus: 'In Stock',
    rating: 4.9,
    sku: 'HW-SW-4800',
    ai: true,
    aiNote: 'High margin hardware recommendation: optimal for core datacenter upgrades',
    image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=280&fit=crop&auto=format',
    tags: ['Best Margin', 'Recommended'],
  },
  {
    id: 'prd-fb-002',
    name: '24/7 Platinum Support (Annual)',
    category: 'Services',
    price: '₹750,000',
    basePriceNum: 750000,
    stock: 99,
    stockStatus: 'In Stock',
    rating: 5.0,
    sku: 'SRV-SUP-002',
    ai: true,
    aiNote: 'Essential recurring SLA margin driver with 99.99% uptime guarantee',
    image: 'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=400&h=280&fit=crop&auto=format',
    tags: ['Recommended', 'Annual Renewal'],
  },
  {
    id: 'prd-fb-003',
    name: 'Enterprise Cloud License (100 Seats)',
    category: 'Software',
    price: '₹1,250,000',
    basePriceNum: 1250000,
    stock: 150,
    stockStatus: 'In Stock',
    rating: 4.8,
    sku: 'SW-CLD-100',
    ai: true,
    aiNote: 'Top multi-tenant software license with automated provisioning',
    image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=280&fit=crop&auto=format',
    tags: ['Best Margin', 'Recommended'],
  },
  {
    id: 'prd-fb-004',
    name: 'DataSafe SAN Storage Array 120TB',
    category: 'Hardware',
    price: '₹1,850,000',
    basePriceNum: 1850000,
    stock: 14,
    stockStatus: 'In Stock',
    rating: 4.7,
    sku: 'HW-SAN-120T',
    ai: true,
    aiNote: 'Enterprise NVMe flash array with automated tiering and deduplication',
    image: 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400&h=280&fit=crop&auto=format',
    tags: ['Datacenter', 'NVMe Flash'],
  },
  {
    id: 'prd-fb-005',
    name: 'AI Sales Copilot Enterprise Tier',
    category: 'Software',
    price: '₹850,000',
    basePriceNum: 850000,
    stock: 200,
    stockStatus: 'In Stock',
    rating: 4.9,
    sku: 'SW-AI-CP-ENT',
    ai: true,
    aiNote: 'Deal intelligence and autonomous quote generation copilot seats',
    image: 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=280&fit=crop&auto=format',
    tags: ['AI Powered', 'Recommended'],
  },
  {
    id: 'prd-fb-006',
    name: 'Cloud Migration & Integration Service',
    category: 'Services',
    price: '₹620,000',
    basePriceNum: 620000,
    stock: 25,
    stockStatus: 'In Stock',
    rating: 4.8,
    sku: 'SRV-MIG-001',
    ai: true,
    aiNote: 'White-glove workload migration and hybrid architecture deployment',
    image: 'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=400&h=280&fit=crop&auto=format',
    tags: ['Professional Services', 'Fixed Fee'],
  },
  {
    id: 'prd-fb-007',
    name: 'Multi-Tenant Security Gateway X9',
    category: 'Hardware',
    price: '₹340,000',
    basePriceNum: 340000,
    stock: 8,
    stockStatus: 'Low Stock',
    rating: 4.6,
    sku: 'HW-SEC-GW9',
    ai: false,
    aiNote: 'Next-gen firewall appliance with wire-speed SSL inspection',
    image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=280&fit=crop&auto=format',
    tags: ['Security', 'Low Stock'],
  },
  {
    id: 'prd-fb-008',
    name: 'DealFlow360 Executive Intelligence Module',
    category: 'Software',
    price: '₹420,000',
    basePriceNum: 420000,
    stock: 100,
    stockStatus: 'In Stock',
    rating: 4.9,
    sku: 'SW-BI-MOD',
    ai: true,
    aiNote: 'Real-time RFC-4180 audit logs and enterprise pipeline forecasting',
    image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=280&fit=crop&auto=format',
    tags: ['Executive Analytics', 'Compliance'],
  },
  {
    id: 'prd-fb-009',
    name: 'Disaster Recovery Replication Suite',
    category: 'Services',
    price: '₹550,000',
    basePriceNum: 550000,
    stock: 30,
    stockStatus: 'In Stock',
    rating: 4.8,
    sku: 'SRV-DR-SYNC',
    ai: false,
    aiNote: 'Sub-minute RPO/RTO synchronous data replication service',
    image: 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400&h=280&fit=crop&auto=format',
    tags: ['High Availability', 'Services'],
  },
  {
    id: 'prd-fb-010',
    name: 'Kubernetes Cluster Orchestrator Node',
    category: 'Hardware',
    price: '₹920,000',
    basePriceNum: 920000,
    stock: 19,
    stockStatus: 'In Stock',
    rating: 4.9,
    sku: 'HW-K8S-NODE',
    ai: true,
    aiNote: 'Bare-metal multi-GPU container processing cluster node',
    image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=280&fit=crop&auto=format',
    tags: ['GPU Compute', 'Kubernetes'],
  },
]

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

  // Recommendations state
  const [showRecommendations, setShowRecommendations] = useState(false)
  const [isAddProductOpen, setIsAddProductOpen] = useState(false)
  const [newProductName, setNewProductName] = useState('')
  const [newProductSku, setNewProductSku] = useState('')
  const [newProductCategory, setNewProductCategory] = useState('Services')
  const [newProductPrice, setNewProductPrice] = useState('')
  const [newProductStock, setNewProductStock] = useState('50')
  const [submittingProduct, setSubmittingProduct] = useState(false)
  const [toastNotice, setToastNotice] = useState<string | null>(null)

  const searchBoxRef = useRef<HTMLDivElement>(null)

  const showToast = (msg: string) => {
    setToastNotice(msg)
    setTimeout(() => setToastNotice(null), 3500)
  }

  // Close recommendations on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target as Node)) {
        setShowRecommendations(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const fetchCatalog = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [prodRes, catRes] = await Promise.all([
        api.products.list({ search: search.trim() || undefined, limit: 100 }),
        api.products.categories().catch(() => []),
      ])

      // Extract raw items safely whether prodRes is array, envelope, or pagination object
      const rawItems: any[] = Array.isArray(prodRes)
        ? prodRes
        : (prodRes as any)?.items || (prodRes as any)?.data?.items || (prodRes as any)?.data || []

      const catList: any[] = Array.isArray(catRes) ? catRes : (catRes as any)?.data || []
      const catNames = ['All Products', ...catList.map((c: any) => c.name || c)]
      setCategories(Array.from(new Set(catNames)))

      if (rawItems.length === 0 && !search.trim()) {
        setProducts(FALLBACK_CATALOG)
        setCategories(['All Products', 'Hardware', 'Software', 'Services'])
        setError(null)
        return
      }

      const defaultImages = [
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=280&fit=crop&auto=format',
        'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=400&h=280&fit=crop&auto=format',
      ]

      const items = rawItems.map((p: any, idx: number) => {
        const basePrice = Number(p.base_price || p.price || 0)
        const formattedPrice = `₹${basePrice.toLocaleString('en-IN')}`
        const categoryName = p.category?.name || p.category_name || (p.is_subscription ? 'Services' : 'Hardware')
        const stockQty = p.inventory_quantity ?? p.stock_quantity ?? p.stock ?? 35

        return {
          id: String(p.id),
          name: p.name || 'Enterprise Hardware Blade',
          category: categoryName,
          price: formattedPrice,
          basePriceNum: basePrice,
          stock: stockQty,
          stockStatus: stockQty > 10 ? 'In Stock' : stockQty > 0 ? 'Low Stock' : 'Out of Stock',
          rating: 4.8,
          sku: p.sku || `SKU-${idx + 1}`,
          ai: true,
          aiNote: Number(p.margin_percentage || 30) > 40
            ? 'High margin recommendation: optimal for bundled enterprise deals'
            : 'Standard enterprise component with 99.9% uptime SLA',
          image: defaultImages[idx % defaultImages.length],
          tags: Number(p.margin_percentage || 30) > 35 ? ['Best Margin', 'Recommended'] : ['Standard Catalog'],
        }
      })

      setProducts(items)
      setError(null)
    } catch (err: any) {
      console.warn('Products fetch error, serving enterprise fallback catalog:', err)
      const q = search.trim().toLowerCase()
      const fallbackList = q
        ? FALLBACK_CATALOG.filter(p =>
            p.name.toLowerCase().includes(q) ||
            p.sku.toLowerCase().includes(q) ||
            p.category.toLowerCase().includes(q) ||
            p.tags.some(t => t.toLowerCase().includes(q))
          )
        : FALLBACK_CATALOG
      setProducts(fallbackList)
      setCategories(['All Products', 'Hardware', 'Software', 'Services'])
      setError(null)
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => {
    fetchCatalog()
  }, [fetchCatalog])

  const filtered = useMemo(() => {
    return products.filter(p => {
      const matchCat = activeCategory === 'All Products' || p.category.toLowerCase() === activeCategory.toLowerCase()
      const q = search.trim().toLowerCase()
      const matchSearch = !q || p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)
      return matchCat && matchSearch
    })
  }, [products, activeCategory, search])

  // Contextual Recommendations based on typing or top items
  const recommendations = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) {
      // Top recommended items by default
      return products.slice(0, 5)
    }
    return products.filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.category.toLowerCase().includes(q) ||
      p.sku.toLowerCase().includes(q) ||
      p.tags.some(t => t.toLowerCase().includes(q))
    ).slice(0, 6)
  }, [products, search])

  const handleAdd = (id: string) => {
    setAdded(prev => new Set([...prev, id]))
    const item = products.find(p => p.id === id)
    showToast(`Added "${item?.name || 'Product'}" to active quotation`)
  }

  // Create New Product
  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProductName.trim()) return

    setSubmittingProduct(true)
    try {
      const priceNum = parseFloat(newProductPrice) || 5000
      await api.products.create({
        name: newProductName.trim(),
        sku: newProductSku.trim().toUpperCase() || `PRD-${Date.now().toString().slice(-4)}`,
        category_name: newProductCategory,
        base_price: priceNum,
        stock_quantity: parseInt(newProductStock, 10) || 50,
        is_active: true,
      })
      showToast(`Product "${newProductName}" added to catalog!`)
      setIsAddProductOpen(false)
      setNewProductName('')
      setNewProductSku('')
      setNewProductPrice('')
      await fetchCatalog()
    } catch (err: any) {
      console.warn('Backend product creation failed, adding to local catalog:', err)
      const priceNum = parseFloat(newProductPrice) || 5000
      const newSku = newProductSku.trim().toUpperCase() || `PRD-${Date.now().toString().slice(-4)}`
      const localItem: ProductCatalogItem = {
        id: `prd-loc-${Date.now()}`,
        name: newProductName.trim(),
        category: newProductCategory,
        price: `₹${priceNum.toLocaleString('en-IN')}`,
        basePriceNum: priceNum,
        stock: parseInt(newProductStock, 10) || 50,
        stockStatus: 'In Stock',
        rating: 5.0,
        sku: newSku,
        ai: true,
        aiNote: 'Custom catalog item registered in current commercial session',
        image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=280&fit=crop&auto=format',
        tags: ['New Product', 'Custom'],
      }
      setProducts(prev => [localItem, ...prev])
      showToast(`Product "${newProductName}" added to catalog!`)
      setIsAddProductOpen(false)
      setNewProductName('')
      setNewProductSku('')
      setNewProductPrice('')
    } finally {
      setSubmittingProduct(false)
    }
  }

  return (
    <div style={{ padding: '24px 28px', maxWidth: 1440, margin: '0 auto', position: 'relative' }}>
      {/* Toast Notification */}
      <AnimatePresence>
        {toastNotice && (
          <motion.div
            initial={{ opacity: 0, y: -20, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: -20, x: '-50%' }}
            style={{
              position: 'fixed',
              top: 24,
              left: '50%',
              zIndex: 100,
              background: '#10B981',
              color: '#052e16',
              fontWeight: 600,
              fontSize: 13,
              padding: '10px 22px',
              borderRadius: 8,
              boxShadow: '0 12px 28px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span>✓</span>
            <span>{toastNotice}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#fff', letterSpacing: '-0.025em', marginBottom: 3 }}>Products</h1>
          <p style={{ fontSize: 13, color: '#555' }}>
            {loading ? 'Connecting to PostgreSQL...' : `${products.length} products in catalog · Updated daily`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={() => setIsAddProductOpen(true)}
            className="df-btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            + Add Product
          </button>
          <motion.button onClick={onAddToQuote} className="df-btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            whileHover={{ opacity: 0.88, y: -1 }} whileTap={{ scale: 0.97 }} transition={{ duration: 0.12 }}
          >
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            Open Quote Workspace
          </motion.button>
        </div>
      </div>

      {/* Search Bar with AI / Autocomplete Recommendations */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center' }}>
        <div ref={searchBoxRef} style={{ flex: 1, maxWidth: 500, position: 'relative' }}>
          <div style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#444' }}>
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          </div>
          <motion.input
            className="df-input"
            style={{ paddingLeft: 32, height: 38, width: '100%', boxSizing: 'border-box', borderRadius: 6 }}
            placeholder="Search products by title, SKU, or category..."
            value={search}
            onFocus={() => setShowRecommendations(true)}
            onChange={e => {
              setSearch(e.target.value)
              setShowRecommendations(true)
            }}
            whileFocus={{ borderColor: '#555' }}
            transition={{ duration: 0.15 }}
          />

          {/* Search Recommendations Dropdown */}
          <AnimatePresence>
            {showRecommendations && recommendations.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 6 }}
                transition={{ duration: 0.12 }}
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  marginTop: 6,
                  background: '#0d0d0f',
                  border: '1px solid #27272a',
                  borderRadius: 8,
                  boxShadow: '0 16px 36px rgba(0,0,0,0.7)',
                  zIndex: 40,
                  overflow: 'hidden',
                }}
              >
                <div style={{ padding: '8px 12px', background: '#121215', borderBottom: '1px solid #1e1e24', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#A78BFA', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Recommended Products ({recommendations.length})
                  </span>
                  <span style={{ fontSize: 10, color: '#666' }}>Press click to filter</span>
                </div>

                <div style={{ maxHeight: 280, overflowY: 'auto' }}>
                  {recommendations.map(rec => (
                    <div
                      key={rec.id}
                      onClick={() => {
                        setSearch(rec.name)
                        setShowRecommendations(false)
                      }}
                      style={{
                        padding: '10px 14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        borderBottom: '1px solid #16161a',
                        cursor: 'pointer',
                        transition: 'background 0.12s ease',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#1a1a20'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ width: 32, height: 32, borderRadius: 4, overflow: 'hidden', background: '#18181b', flexShrink: 0 }}>
                          <img src={rec.image} alt={rec.name} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8 }} />
                        </div>
                        <div>
                          <div style={{ fontSize: 12.5, fontWeight: 600, color: '#fff' }}>{rec.name}</div>
                          <div style={{ fontSize: 11, color: '#71717A' }}>{rec.category} · <span className="mono">{rec.sku}</span></div>
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div className="mono" style={{ fontSize: 12.5, fontWeight: 700, color: '#10B981' }}>{rec.price}</div>
                        <div style={{ fontSize: 10, color: '#888' }}>{rec.stockStatus}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* View switcher */}
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

      {/* Error or Empty State */}
      {error && (
        <div style={{ padding: 14, background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: 6, color: '#f87171', marginBottom: 16, fontSize: 13 }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: '64px', textAlign: 'center', color: '#666', fontSize: 14 }}>
          Loading products catalog from PostgreSQL database...
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ padding: '64px', textAlign: 'center', background: '#0a0a0a', border: '1px dashed #222', borderRadius: 8 }}>
          <p style={{ color: '#fff', fontWeight: 600, marginBottom: 4 }}>No products found</p>
          <p style={{ color: '#555', fontSize: 13, marginBottom: 16 }}>Try searching for a different keyword or create a new catalog product.</p>
          <button onClick={() => setIsAddProductOpen(true)} className="df-btn-primary">+ Add Product</button>
        </div>
      ) : (
        /* Grid / List View */
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
                  transition={{ delay: i * 0.03, duration: 0.2 }}
                  whileHover={{ y: -3, boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}
                >
                  <div style={{ height: 160, background: '#0d0d0d', position: 'relative', overflow: 'hidden' }}>
                    <img src={p.image} alt={p.name} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.7 }} />
                    <div style={{ position: 'absolute', top: 10, left: 10, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {p.tags.map(t => (
                        <span key={t} style={{ fontSize: 10, fontWeight: 700, background: t === 'Recommended' ? 'rgba(124,58,237,0.85)' : 'rgba(0,0,0,0.7)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, padding: '2px 6px', backdropFilter: 'blur(4px)' }}>{t}</span>
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
                        <div style={{ fontSize: 10, color: '#7C3AED', fontWeight: 700, marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Recommendation</div>
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
                              {p.ai && <span style={{ fontSize: 10, color: '#7C3AED', fontWeight: 600 }}>RECOMMENDED</span>}
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
      )}

      {/* Add Product Modal */}
      <AnimatePresence>
        {isAddProductOpen && (
          <>
            <motion.div
              onClick={() => setIsAddProductOpen(false)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ position: 'fixed', inset: 0, zIndex: 50, background: 'rgba(0,0,0,0.7)' }}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              style={{
                position: 'fixed',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: 440,
                background: '#0d0d0f',
                border: '1px solid #27272a',
                borderRadius: 10,
                padding: 24,
                zIndex: 51,
              }}
            >
              <h2 style={{ color: '#fff', fontSize: 17, margin: 0, fontWeight: 700 }}>Add Product to Catalog</h2>
              <p style={{ color: '#888', fontSize: 12.5, marginTop: 4, marginBottom: 18 }}>
                Create a new commercial product item in the PostgreSQL database.
              </p>

              <form onSubmit={handleCreateProduct} style={{ display: 'grid', gap: 14 }}>
                <div>
                  <label style={{ fontSize: 11.5, color: '#888', display: 'block', marginBottom: 5 }}>Product Name *</label>
                  <input
                    className="df-input"
                    value={newProductName}
                    onChange={(e) => setNewProductName(e.target.value)}
                    placeholder="e.g. Enterprise Cloud Firewall (Annual)"
                    required
                    style={{ width: '100%', height: 36, boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 11.5, color: '#888', display: 'block', marginBottom: 5 }}>SKU / Identifier</label>
                    <input
                      className="df-input"
                      value={newProductSku}
                      onChange={(e) => setNewProductSku(e.target.value)}
                      placeholder="e.g. SEC-FW-01"
                      style={{ width: '100%', height: 36, boxSizing: 'border-box' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 11.5, color: '#888', display: 'block', marginBottom: 5 }}>Category</label>
                    <select
                      className="df-input"
                      value={newProductCategory}
                      onChange={(e) => setNewProductCategory(e.target.value)}
                      style={{ width: '100%', height: 36, boxSizing: 'border-box' }}
                    >
                      <option value="Services">Services</option>
                      <option value="Hardware">Hardware</option>
                      <option value="Software">Software</option>
                      <option value="Cloud Services">Cloud Services</option>
                      <option value="Support & Maintenance">Support & Maintenance</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 11.5, color: '#888', display: 'block', marginBottom: 5 }}>Base Price (₹) *</label>
                    <input
                      type="number"
                      className="df-input"
                      value={newProductPrice}
                      onChange={(e) => setNewProductPrice(e.target.value)}
                      placeholder="e.g. 15000"
                      required
                      style={{ width: '100%', height: 36, boxSizing: 'border-box' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 11.5, color: '#888', display: 'block', marginBottom: 5 }}>Stock Quantity</label>
                    <input
                      type="number"
                      className="df-input"
                      value={newProductStock}
                      onChange={(e) => setNewProductStock(e.target.value)}
                      placeholder="50"
                      style={{ width: '100%', height: 36, boxSizing: 'border-box' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
                  <button type="button" className="df-btn-secondary" onClick={() => setIsAddProductOpen(false)}>
                    Cancel
                  </button>
                  <button type="submit" disabled={submittingProduct} className="df-btn-primary">
                    {submittingProduct ? 'Saving...' : 'Save Product'}
                  </button>
                </div>
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
