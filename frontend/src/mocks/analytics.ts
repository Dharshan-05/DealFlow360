export const mockMonthlyRevenue = [
  { month: 'Jan', revenue: 22, requests: 34, pipeline: 50 },
  { month: 'Feb', revenue: 28, requests: 40, pipeline: 58 },
  { month: 'Mar', revenue: 24, requests: 38, pipeline: 54 },
  { month: 'Apr', revenue: 34, requests: 48, pipeline: 68 },
  { month: 'May', revenue: 30, requests: 45, pipeline: 64 },
  { month: 'Jun', revenue: 38, requests: 52, pipeline: 74 },
  { month: 'Jul', revenue: 42, requests: 58, pipeline: 80 },
  { month: 'Aug', revenue: 48, requests: 64, pipeline: 92 },
  { month: 'Sep', revenue: 52, requests: 68, pipeline: 98 },
]

export const mockKpiMetrics = [
  { label: 'Total Revenue', value: 48.2, prefix: '?', suffix: 'M', change: '+14.2%', isPositive: true },
  { label: 'Active Requests', value: 38, prefix: '', suffix: '', change: '+8 this week', isPositive: true },
  { label: 'Pending Approvals', value: 7, prefix: '', suffix: '', change: '4 high risk', isPositive: false },
  { label: 'Avg Approval Time', value: 4.2, prefix: '', suffix: 'h', change: '-9% faster', isPositive: true },
  { label: 'AI Accuracy Rate', value: 94.6, prefix: '', suffix: '%', change: '+2.1%', isPositive: true },
  { label: 'Odoo Sync Rate', value: 99.8, prefix: '', suffix: '%', change: 'Real-time', isPositive: true },
]
