export function exportToCsv(
  filename: string,
  columns: { key: string; label: string }[],
  rows: Record<string, any>[]
): void {
  if (typeof window === 'undefined') return

  // Format header row
  const headerRow = columns.map((col) => escapeCsvValue(col.label)).join(',')

  // Format data rows
  const dataRows = rows.map((row) =>
    columns
      .map((col) => {
        const val = row[col.key]
        return escapeCsvValue(val !== undefined && val !== null ? String(val) : '')
      })
      .join(',')
  )

  const csvContent = [headerRow, ...dataRows].join('\r\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function exportReportAsCsv(report: { type: string; title: string; columns: { key: string; label: string }[]; rows: Record<string, any>[] }): void {
  const sanitizedTitle = report.title.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_')
  const filename = `${sanitizedTitle}_${new Date().toISOString().slice(0, 10)}.csv`
  exportToCsv(filename, report.columns, report.rows)
}


function escapeCsvValue(val: string): string {
  if (val.includes(',') || val.includes('"') || val.includes('\n') || val.includes('\r')) {
    return `"${val.replace(/"/g, '""')}"`
  }
  return val
}
