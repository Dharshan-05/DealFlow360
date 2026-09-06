import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { AuditEvent } from '../../types/audit'
import { AuditSeverityBadge } from './AuditSeverityBadge'
import {
  XIcon as X,
  ExternalLinkIcon as ExternalLink,
  ShieldCheckIcon as ShieldCheck,
  TerminalIcon as Terminal,
  ClockIcon as Clock,
  CheckCircle2Icon as CheckCircle,
  AlertCircleIcon as AlertCircle,
} from '../common/Icons'

interface Props {
  event: AuditEvent | null
  isOpen: boolean
  onClose: () => void
  onNavigateResource?: (resource: string, resourceId?: string) => void
}

export function AuditDetailDrawer({ event, isOpen, onClose, onNavigateResource }: Props) {
  if (!isOpen || !event) return null

  return (
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="audit-drawer-title"
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9999,
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
          }}
        />

        {/* Drawer panel */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 280 }}
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 580,
            height: '100%',
            background: '#09090b',
            borderLeft: '1px solid #27272a',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '-8px 0 32px rgba(0,0,0,0.8)',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '20px 24px',
              borderBottom: '1px solid #1c1c24',
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              gap: 16,
              background: '#0c0c0e',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span
                  className="mono"
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color: '#a1a1aa',
                    background: '#18181b',
                    padding: '2px 8px',
                    borderRadius: 4,
                    border: '1px solid #27272a',
                  }}
                >
                  {event.id}
                </span>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: 4,
                    color: '#818cf8',
                    background: 'rgba(129, 140, 248, 0.1)',
                    border: '1px solid rgba(129, 140, 248, 0.25)',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  {event.category}
                </span>
              </div>
              <h2
                id="audit-drawer-title"
                style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em' }}
              >
                {event.action}
              </h2>
            </div>

            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: '1px solid #27272a',
                borderRadius: 6,
                padding: 6,
                color: '#a1a1aa',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <X size={16} />
            </button>
          </div>

          {/* Content Body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
            {/* Status & Severity Bar */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '12px 14px',
                background: '#121215',
                border: '1px solid #27272a',
                borderRadius: 6,
                marginBottom: 20,
              }}
            >
              <div>
                <span style={{ fontSize: 11, color: '#71717a', display: 'block', marginBottom: 3 }}>
                  SEVERITY
                </span>
                <AuditSeverityBadge severity={event.severity} />
              </div>

              <div style={{ width: 1, height: 24, background: '#27272a', margin: '0 4px' }} />

              <div>
                <span style={{ fontSize: 11, color: '#71717a', display: 'block', marginBottom: 3 }}>
                  RESULT
                </span>
                <AuditSeverityBadge result={event.result} />
              </div>

              <div style={{ width: 1, height: 24, background: '#27272a', margin: '0 4px' }} />

              <div style={{ flex: 1 }}>
                <span style={{ fontSize: 11, color: '#71717a', display: 'block', marginBottom: 3 }}>
                  TIMESTAMP
                </span>
                <span className="mono" style={{ fontSize: 11, color: '#e4e4e7' }}>
                  {new Date(event.timestamp).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Description Section */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', marginBottom: 8 }}>
                Event Description
              </div>
              <div
                style={{
                  background: '#121215',
                  border: '1px solid #1e1e24',
                  borderRadius: 6,
                  padding: '14px',
                  fontSize: 13,
                  color: '#e4e4e7',
                  lineHeight: 1.5,
                }}
              >
                {event.description}
                {event.details && (
                  <div style={{ marginTop: 8, fontSize: 12, color: '#a1a1aa' }}>
                    {event.details}
                  </div>
                )}
              </div>
            </div>

            {/* Actor Information */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', marginBottom: 8 }}>
                Actor Profile
              </div>
              <div
                style={{
                  background: '#121215',
                  border: '1px solid #1e1e24',
                  borderRadius: 6,
                  padding: '14px',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 12,
                }}
              >
                <div>
                  <span style={{ fontSize: 10, color: '#71717a', textTransform: 'uppercase' }}>Actor Name</span>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff', marginTop: 2 }}>{event.actor}</div>
                </div>
                <div>
                  <span style={{ fontSize: 10, color: '#71717a', textTransform: 'uppercase' }}>Designated Role</span>
                  <div style={{ fontSize: 12, color: '#a1a1aa', marginTop: 2 }}>{event.actorRole}</div>
                </div>
                {event.actorEmail && (
                  <div>
                    <span style={{ fontSize: 10, color: '#71717a', textTransform: 'uppercase' }}>Email</span>
                    <div className="mono" style={{ fontSize: 11, color: '#e4e4e7', marginTop: 2 }}>{event.actorEmail}</div>
                  </div>
                )}
                <div>
                  <span style={{ fontSize: 10, color: '#71717a', textTransform: 'uppercase' }}>Network IP</span>
                  <div className="mono" style={{ fontSize: 11, color: '#71717a', marginTop: 2 }}>{event.ipAddress || '127.0.0.1'}</div>
                </div>
              </div>
            </div>

            {/* Target Resource */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', marginBottom: 8 }}>
                Target Resource
              </div>
              <div
                style={{
                  background: '#121215',
                  border: '1px solid #1e1e24',
                  borderRadius: 6,
                  padding: '12px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <span style={{ fontSize: 10, color: '#71717a', textTransform: 'uppercase' }}>Entity Type</span>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#ffffff', marginTop: 2 }}>
                    {event.resource}
                  </div>
                </div>
                {event.resourceId && (
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: 10, color: '#71717a', textTransform: 'uppercase' }}>Identifier</span>
                    <div className="mono" style={{ fontSize: 13, fontWeight: 700, color: '#818cf8', marginTop: 2 }}>
                      {event.resourceId}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Before vs After Diff Section */}
            {(event.before || event.after) && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', marginBottom: 8 }}>
                  Attribute Change Diff (Before vs After)
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 10,
                  }}
                >
                  <div
                    style={{
                      background: 'rgba(239, 68, 68, 0.05)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      borderRadius: 6,
                      padding: 12,
                    }}
                  >
                    <span style={{ fontSize: 10, color: '#f87171', fontWeight: 700, textTransform: 'uppercase' }}>
                      Previous State
                    </span>
                    <pre
                      className="mono"
                      style={{
                        margin: '6px 0 0',
                        fontSize: 11,
                        color: '#e4e4e7',
                        overflowX: 'auto',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {JSON.stringify(event.before, null, 2)}
                    </pre>
                  </div>

                  <div
                    style={{
                      background: 'rgba(16, 185, 129, 0.05)',
                      border: '1px solid rgba(16, 185, 129, 0.2)',
                      borderRadius: 6,
                      padding: 12,
                    }}
                  >
                    <span style={{ fontSize: 10, color: '#34d399', fontWeight: 700, textTransform: 'uppercase' }}>
                      Committed State
                    </span>
                    <pre
                      className="mono"
                      style={{
                        margin: '6px 0 0',
                        fontSize: 11,
                        color: '#e4e4e7',
                        overflowX: 'auto',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {JSON.stringify(event.after, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            {/* Technical Metadata Inspector */}
            {event.metadata && Object.keys(event.metadata).length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#71717a', textTransform: 'uppercase', marginBottom: 8 }}>
                  Payload Metadata
                </div>
                <div
                  style={{
                    background: '#121215',
                    border: '1px solid #1e1e24',
                    borderRadius: 6,
                    padding: 12,
                  }}
                >
                  <pre
                    className="mono"
                    style={{
                      margin: 0,
                      fontSize: 11,
                      color: '#a1a1aa',
                      overflowX: 'auto',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {JSON.stringify(event.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Technical Client Context */}
            {event.userAgent && (
              <div style={{ fontSize: 10, color: '#52525b', lineHeight: 1.4, marginTop: 16 }}>
                Client User Agent: {event.userAgent}
              </div>
            )}
          </div>

          {/* Footer Action */}
          <div
            style={{
              padding: '16px 24px',
              borderTop: '1px solid #1c1c24',
              background: '#0c0c0e',
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                fontSize: 12,
                fontWeight: 600,
                background: '#27272a',
                border: '1px solid #3f3f46',
                borderRadius: 6,
                color: '#ffffff',
                cursor: 'pointer',
              }}
            >
              Close Inspector
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
