import {
  motion,
  AnimatePresence,
  useReducedMotion,
  useMotionValue,
  useSpring,
  useInView,
} from 'framer-motion'
import { useEffect, useRef, useState, type ReactNode } from 'react'

// ─── Timing & easing ───────────────────────────────────────────────────────

export const DUR = {
  xs: 0.13,
  sm: 0.18,
  md: 0.25,
  lg: 0.38,
  xl: 0.48,
}

export const EASE = {
  out: [0.0, 0.0, 0.2, 1.0] as const,
  inOut: [0.4, 0.0, 0.2, 1.0] as const,
}

// ─── Variant factories ──────────────────────────────────────────────────────

export const fadeUpVariants = (distance = 12) => ({
  hidden: { opacity: 0, y: distance },
  show: { opacity: 1, y: 0 },
})

export const fadeInVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1 },
}

export const slideRightVariants = (distance = 20) => ({
  hidden: { opacity: 0, x: -distance },
  show: { opacity: 1, x: 0 },
})

export const slideLeftVariants = (distance = 20) => ({
  hidden: { opacity: 0, x: distance },
  show: { opacity: 1, x: 0 },
})

export const scaleInVariants = {
  hidden: { opacity: 0, scale: 0.96 },
  show: { opacity: 1, scale: 1 },
}

// ─── Stagger container + items ──────────────────────────────────────────────

interface StaggerContainerProps {
  children: ReactNode
  stagger?: number
  delayChildren?: number
  className?: string
  style?: React.CSSProperties
}

export function StaggerContainer({ children, stagger = 0.06, delayChildren = 0, className, style }: StaggerContainerProps) {
  const reduced = useReducedMotion()
  if (reduced) return <div className={className} style={style}>{children}</div>
  return (
    <motion.div
      className={className}
      style={style}
      variants={{ hidden: {}, show: { transition: { staggerChildren: stagger, delayChildren } } }}
      initial="hidden"
      animate="show"
    >
      {children}
    </motion.div>
  )
}

interface StaggerItemProps {
  children: ReactNode
  className?: string
  style?: React.CSSProperties
  distance?: number
}

export function StaggerItem({ children, className, style, distance = 10 }: StaggerItemProps) {
  const reduced = useReducedMotion()
  if (reduced) return <div className={className} style={style}>{children}</div>
  return (
    <motion.div
      className={className}
      style={style}
      variants={{
        hidden: { opacity: 0, y: distance },
        show: { opacity: 1, y: 0, transition: { duration: DUR.md, ease: EASE.out } },
      }}
    >
      {children}
    </motion.div>
  )
}

// ─── FadeIn ─────────────────────────────────────────────────────────────────

interface FadeInProps {
  children: ReactNode
  delay?: number
  duration?: number
  className?: string
  style?: React.CSSProperties
  distance?: number
}

export function FadeIn({ children, delay = 0, duration = DUR.md, className, style, distance = 10 }: FadeInProps) {
  const reduced = useReducedMotion()
  if (reduced) return <div className={className} style={style}>{children}</div>
  return (
    <motion.div
      className={className}
      style={style}
      initial={{ opacity: 0, y: distance }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration, delay, ease: EASE.out }}
    >
      {children}
    </motion.div>
  )
}

// ─── RevealOnScroll ──────────────────────────────────────────────────────────

interface RevealProps {
  children: ReactNode
  delay?: number
  className?: string
  style?: React.CSSProperties
  distance?: number
}

export function RevealOnScroll({ children, delay = 0, className, style, distance = 16 }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  const reduced = useReducedMotion()

  return (
    <motion.div
      ref={ref}
      className={className}
      style={style}
      initial={reduced ? false : { opacity: 0, y: distance }}
      animate={inView || reduced ? { opacity: 1, y: 0 } : { opacity: 0, y: distance }}
      transition={{ duration: DUR.lg, delay, ease: EASE.out }}
    >
      {children}
    </motion.div>
  )
}

// ─── PageTransition ──────────────────────────────────────────────────────────

interface PageTransitionProps {
  children: ReactNode
  pageKey: string
}

export function PageTransition({ children, pageKey }: PageTransitionProps) {
  const reduced = useReducedMotion()
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pageKey}
        initial={reduced ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{ duration: DUR.md, ease: EASE.out }}
        style={{ height: '100%' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}

// ─── AnimatedNumber (count-up) ───────────────────────────────────────────────

interface AnimatedNumberProps {
  value: number
  format?: (n: number) => string
  duration?: number
  className?: string
  style?: React.CSSProperties
}

export function AnimatedNumber({ value, format, duration = 1.2, className, style }: AnimatedNumberProps) {
  const reduced = useReducedMotion()
  const motionVal = useMotionValue(reduced ? value : 0)
  const spring = useSpring(motionVal, { stiffness: 60, damping: 20, restDelta: 0.1 })
  const [display, setDisplay] = useState(reduced ? value : 0)

  useEffect(() => { motionVal.set(value) }, [value, motionVal])
  useEffect(() => spring.on('change', v => setDisplay(v)), [spring])

  const formatted = format ? format(display) : String(Math.round(display))
  return <span className={className} style={style}>{formatted}</span>
}

// ─── HoverScale ─────────────────────────────────────────────────────────────

interface HoverScaleProps {
  children: ReactNode
  scale?: number
  className?: string
  style?: React.CSSProperties
}

export function HoverScale({ children, scale = 1.02, className, style }: HoverScaleProps) {
  const reduced = useReducedMotion()
  if (reduced) return <div className={className} style={style}>{children}</div>
  return (
    <motion.div
      className={className}
      style={style}
      whileHover={{ scale }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: DUR.xs, ease: EASE.out }}
    >
      {children}
    </motion.div>
  )
}

// ─── AnimatedCard ────────────────────────────────────────────────────────────

interface AnimatedCardProps {
  children: ReactNode
  className?: string
  style?: React.CSSProperties
  onClick?: () => void
}

export function AnimatedCard({ children, className, style, onClick }: AnimatedCardProps) {
  const reduced = useReducedMotion()
  if (reduced) {
    return <div className={className} style={style} onClick={onClick}>{children}</div>
  }
  return (
    <motion.div
      className={className}
      style={style}
      onClick={onClick}
      whileHover={{ y: -2, transition: { duration: DUR.xs } }}
      whileTap={{ scale: 0.99 }}
    >
      {children}
    </motion.div>
  )
}

// ─── TypingIndicator ─────────────────────────────────────────────────────────

export function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '4px 0' }}>
      {[0, 1, 2].map(i => (
        <motion.div
          key={i}
          style={{ width: 6, height: 6, borderRadius: '50%', background: '#7C3AED' }}
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.18, ease: 'easeInOut' }}
        />
      ))}
    </div>
  )
}

// ─── AnimatedDrawer (slide from right) ──────────────────────────────────────

interface DrawerProps {
  open: boolean
  children: ReactNode
  width?: number
  style?: React.CSSProperties
  className?: string
}

export function AnimatedDrawer({ open, children, width = 380, style, className }: DrawerProps) {
  const reduced = useReducedMotion()
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className={className}
          style={{ width, ...style }}
          initial={reduced ? false : { opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ duration: DUR.md, ease: EASE.out }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// ─── AnimatedDropdown ────────────────────────────────────────────────────────

interface DropdownProps {
  open: boolean
  children: ReactNode
  style?: React.CSSProperties
  className?: string
}

export function AnimatedDropdown({ open, children, style, className }: DropdownProps) {
  const reduced = useReducedMotion()
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className={className}
          style={style}
          initial={reduced ? false : { opacity: 0, y: -6, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -6, scale: 0.97 }}
          transition={{ duration: DUR.sm, ease: EASE.out }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// ─── SkeletonLoader ──────────────────────────────────────────────────────────

interface SkeletonProps {
  width?: number | string
  height?: number | string
  borderRadius?: number | string
  className?: string
  style?: React.CSSProperties
}

export function SkeletonLoader({ width = '100%', height = 16, borderRadius = 6, className, style }: SkeletonProps) {
  return (
    <div
      className={`df-skeleton${className ? ` ${className}` : ''}`}
      style={{ width, height, borderRadius, flexShrink: 0, ...style }}
    />
  )
}

/** Convenience: a column of skeleton lines mimicking text paragraphs */
export function SkeletonText({ lines = 3, gap = 8 }: { lines?: number; gap?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap }}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLoader key={i} height={12} width={i === lines - 1 ? '65%' : '100%'} />
      ))}
    </div>
  )
}

/** Skeleton that matches a KPI card layout */
export function SkeletonCard({ style, className }: { style?: React.CSSProperties; className?: string }) {
  return (
    <div className={`df-card${className ? ` ${className}` : ''}`} style={{ padding: '18px 20px', ...style }}>
      <SkeletonLoader height={10} width="45%" borderRadius={4} style={{ marginBottom: 12 }} />
      <SkeletonLoader height={28} width="60%" borderRadius={6} style={{ marginBottom: 8 }} />
      <SkeletonLoader height={10} width="35%" borderRadius={4} />
    </div>
  )
}

// ─── Re-exports ──────────────────────────────────────────────────────────────

export { motion, AnimatePresence, useReducedMotion, useInView }
