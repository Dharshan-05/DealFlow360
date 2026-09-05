import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  XIcon as X,
  ExternalLinkIcon as ExternalLink,
  CheckCircle2Icon as CheckCircle2,
  FileCheck2Icon as FileCheck2,
} from '../common/Icons'
import type { GeneratedReport } from '../../types/analytics'

interface Props {
  isOpen: boolean
  report: GeneratedReport | null
  onClose: () => void
  onExportCsv: () => void
}

export default function ReportPreviewModal({
  isOpen,
  report,
  onClose,
  onExportCsv,
}: Props) {
  if (!isOpen || !report) return null

  const handlePrint = () => {
    window.print()
  }

  return (
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="report-modal-title"
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 16,
        }}
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(5px)',
          }}
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 12 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="print-report-container"
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 1040,
            maxHeight: '92vh',
            background: '#09090c',
            border: '1px solid #27272a',
            borderRadius: 12,
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.9), 0 0 0 1px rgba(255, 255, 255, 0.05)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '18px 24px',
              borderBottom: '1px solid #1f1f26',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: '#0e0e14',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{
                    fontSize: 10.5,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: '#a78bfa',
                    letterSpacing: '0.05em',
                  }}
                >
                  Official Report Preview
                </span>
                <span
                  style={{
                    fontSize: 10,
                    background: 'rgba(124, 58, 237, 0.15)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    color: '#c084fc',
                    padding: '1px 6px',
                    borderRadius: 4,
                    fontFamily: 'monospace',
                  }}
                >
                  {report.rowCount} Records
                </span>
              </div>
              <h2
                id="report-modal-title"
                style={{ margin: '4px 0 0', fontSize: 18, fontWeight: 700, color: '#fff' }}
              >
                {report.title}
              </h2>
              <div style={{ fontSize: 11.5, color: '#71717a', marginTop: 3 }}>
                Generated {new Date(report.generatedAt).toLocaleString('en-IN')} · Filters: {report.filterSummary}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                type="button"
                onClick={handlePrint}
                className="df-btn-secondary"
                style={{ padding: '7px 13px', fontSize: 12 }}
                title="Print this report sheet"
              >
                Print Report
              </button>
              <button
                type="button"
                onClick={onExportCsv}
                style={{
                  padding: '7px 15px',
                  borderRadius: 6,
                  background: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#000',
                  fontWeight: 700,
                  fontSize: 12,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                Export CSV ↓
              </button>
              <button
                type="button"
                onClick={onClose}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#71717a',
                  cursor: 'pointer',
                  padding: 4,
                  display: 'flex',
                  alignItems: 'center',
                }}
                title="Close preview"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Body */}
          <div
            style={{
              padding: '20px 24px',
              overflowY: 'auto',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            {/* Executive Summary Chips */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: `repeat(${report.summaryMetrics.length || 4}, minmax(0, 1fr))`,
                gap: 12,
              }}
            >
              {report.summaryMetrics.map((sm, i) => (
                <div
                  key={i}
                  style={{
                    background: '#121218',
                    border: '1px solid #1f1f28',
                    borderRadius: 8,
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ fontSize: 10.5, color: '#71717a', textTransform: 'uppercase', fontWeight: 600 }}>
                    {sm.label}
                  </div>
                  <div
                    className={sm.mono ? 'mono' : ''}
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: '#fff',
                      marginTop: 4,
                    }}
                  >
                    {sm.value}
                  </div>
                </div>
              ))}
            </div>

            {/* Tabular Data Grid */}
            <div
              style={{
                background: '#0b0b0e',
                border: '1px solid #1c1c24',
                borderRadius: 8,
                overflow: 'hidden',
              }}
            >
              <div style={{ maxHeight: 420, overflowY: 'auto', overflowX: 'auto' }}>
                <table style={{ width: '100%', minWidth: 780, borderCollapse: 'collapse' }}>
                  <thead style={{ position: 'sticky', top: 0, zIndex: 2 }}>
                    <tr style={{ background: '#121218', borderBottom: '1px solid #1f1f28' }}>
                      {report.columns.map((col) => (
                        <th
                          key={col.key}
                          style={{
                            padding: '10px 14px',
                            textAlign: 'left',
                            fontSize: 11,
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                            color: '#71717a',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {col.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.rows.length === 0 ? (
                      <tr>
                        <td
                          colSpan={report.columns.length}
                          style={{ padding: '36px 20px', textAlign: 'center', color: '#71717a', fontSize: 13 }}
                        >
                          No records available for this report criteria.
                        </td>
                      </tr>
                    ) : (
                      report.rows.map((row, rIdx) => (
                        <tr
                          key={rIdx}
                          style={{ borderBottom: '1px solid #14141c' }}
                          className="hover:bg-white/[0.02]"
                        >
                          {report.columns.map((col) => {
                            const val = row[col.key]
                            return (
                              <td
                                key={col.key}
                                className={col.mono ? 'mono' : ''}
                                style={{
                                  padding: '10px 14px',
                                  fontSize: 12,
                                  color: col.mono ? '#e4e4e7' : '#a1a1aa',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {val !== undefined && val !== null ? String(val) : '—'}
                              </td>
                            )
                          })}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Compliance Footer Note */}
            <div
              style={{
                fontSize: 11,
                color: '#52525b',
                lineHeight: 1.5,
                borderTop: '1px solid #181820',
                paddingTop: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                DealFlow360 Executive Report · Generated entirely in frontend environment without external BI transmission.
              </div>
              <div style={{ fontFamily: 'monospace' }}>
                Ref ID: {report.id}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
