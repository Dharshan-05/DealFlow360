/**
 * Common formatting utilities for currency, numbers, and dates.
 */

export function formatINR(val: number): string {
  if (val >= 10000000) {
    return `?${(val / 10000000).toFixed(2)}Cr`
  }
  if (val >= 100000) {
    return `?${(val / 100000).toFixed(2)}L`
  }
  if (val >= 1000) {
    return `?${(val / 1000).toFixed(1)}K`
  }
  return `?${Math.round(val).toLocaleString('en-IN')}`
}

export function formatUSD(val: number): string {
  if (val >= 1000000) {
    return `$${(val / 1000000).toFixed(2)}M`
  }
  if (val >= 1000) {
    return `$${(val / 1000).toFixed(1)}K`
  }
  return `$${Math.round(val).toLocaleString('en-US')}`
}

export function formatDate(dateString: string): string {
  try {
    const d = new Date(dateString)
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return dateString
  }
}
