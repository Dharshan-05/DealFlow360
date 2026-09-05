import { motion, AnimatePresence } from 'framer-motion'
import AIAnalysisPanel from './AIAnalysisPanel'
import type { Request } from '../../types/request'

interface Props {
  isOpen: boolean
  request: Request | null
  onClose: () => void
  onNavigateToRequest?: () => void
}

export default function AIAnalysisModal({
  isOpen,
  request,
  onClose,
  onNavigateToRequest,
}: Props) {
  return (
    <AnimatePresence>
      {isOpen && request && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.72)',
              backdropFilter: 'blur(3px)',
              zIndex: 95,
            }}
          />

          {/* Slide-over Drawer */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              width: 820,
              maxWidth: '95vw',
              background: '#070709',
              borderLeft: '1px solid #1e1e24',
              zIndex: 100,
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '-16px 0 40px rgba(0, 0, 0, 0.7)',
              overflowY: 'auto',
              padding: '24px',
            }}
          >
            <AIAnalysisPanel
              request={request}
              onClose={onClose}
              onNavigateToRequest={() => {
                onClose()
                if (onNavigateToRequest) onNavigateToRequest()
              }}
            />
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
