export interface GeneralSettings {
  organizationName: string
  workspaceName: string
  defaultCurrency: 'USD' | 'EUR' | 'GBP' | 'INR'
  defaultTimeZone: string
  dateFormat: 'YYYY-MM-DD' | 'MM/DD/YYYY' | 'DD/MM/YYYY'
  language: 'English' | 'Spanish' | 'German' | 'French'
  defaultDashboardView: 'Command Center' | 'Analytics' | 'Requests'
}

export interface WorkflowSettings {
  requireApproval: boolean
  autoSubmitDrafts: boolean
  aiPreAnalysis: boolean
  approvalSlaHours: number
  enableRequestValidation: boolean
  allowRequestChanges: boolean
  autoCreateTransactionAfterExecution: boolean
  enableExecutionSimulation: boolean
  simulateErpFailureAtStep3: boolean
}

export interface AISettings {
  aiAnalysisEnabled: boolean
  recommendationEnabled: boolean
  riskScoringEnabled: boolean
  confidenceThreshold: number // 0-100
  highRiskThreshold: number // 0-100
  analysisDetailLevel: 'Standard' | 'High' | 'Comprehensive'
  recommendationMode: 'Conservative' | 'Balanced' | 'Aggressive'
}

export interface NotificationSettings {
  approvalNotifications: boolean
  aiAlerts: boolean
  processingNotifications: boolean
  securityAlerts: boolean
  systemMessages: boolean
  desktopNotificationSimulation: boolean
  notificationRetentionDays: number
}

export interface IntegrationStatus {
  name: string
  status: 'Simulated' | 'Local' | 'Connected'
  environment: string
  lastSync: string
  description: string
  details?: string
}

export interface IntegrationSettings {
  odooErp: IntegrationStatus
  aiEngine: IntegrationStatus
  analytics: IntegrationStatus
  reporting: IntegrationStatus
}

export interface SecuritySettings {
  sessionDurationMinutes: number
  rememberMeEnabled: boolean
  securityAlertsOnFailedLogin: boolean
  autoLogoutOnInactivity: boolean
  inactivityTimeoutMinutes: number
  requirePasswordChangeDays: number
  permissionVisibility: 'Visible to All' | 'Role-Restricted'
}

export interface SystemConfiguration {
  applicationName: string
  version: string
  environment: 'Demo' | 'Staging' | 'Production'
  buildStatus: 'Passing (Local)'
  dataStorage: 'Browser LocalStorage'
  backendStatus: 'Not Connected (Frontend Only)'
  odooStatus: 'Simulated / Demo Environment'
  aiStatus: 'Frontend AI Simulation'
  apiStatus: 'Not Connected'
  lastDeployment: string
}

export interface SystemSettings {
  general: GeneralSettings
  workflow: WorkflowSettings
  ai: AISettings
  notifications: NotificationSettings
  integrations: IntegrationSettings
  security: SecuritySettings
  system: SystemConfiguration
}
