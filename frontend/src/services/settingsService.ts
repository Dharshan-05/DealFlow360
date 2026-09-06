import type { SystemSettings, SystemConfiguration } from '../types/settings'
import { defaultSystemSettings } from '../mocks/settings'
import { auditService } from './auditService'
import { notificationService } from './notificationService'

export const SETTINGS_STORAGE_KEY = 'dealflow360_settings'
export const SETTINGS_UPDATED_EVENT = 'dealflow_settings_updated'

class SettingsService {
  private listeners: (() => void)[] = []

  public subscribe(callback: () => void): () => void {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback)
    }
  }

  private notify(): void {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(SETTINGS_UPDATED_EVENT))
      this.listeners.forEach((cb) => cb())
    }
  }

  public getSettings(): SystemSettings {
    try {
      const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
      if (!raw) {
        this.saveSettings(defaultSystemSettings, false)
        return defaultSystemSettings
      }
      return JSON.parse(raw)
    } catch {
      return defaultSystemSettings
    }
  }

  private saveSettings(settings: SystemSettings, triggerAudit = true): void {
    try {
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
      this.notify()

      if (triggerAudit) {
        auditService.logEvent({
          category: 'SETTINGS',
          eventType: 'SETTINGS_UPDATED',
          actor: 'Current Session User',
          actorRole: 'Sales Director',
          action: 'Updated System Settings',
          resource: 'Settings',
          severity: 'LOW',
          result: 'SUCCESS',
          description: 'Updated system settings in browser storage.',
        })

        notificationService.addNotification({
          type: 'SYSTEM',
          title: 'Settings Saved',
          message: 'Workspace configurations updated successfully.',
          priority: 'LOW',
          linkTarget: 'settings',
          dotColor: '#10B981',
        })
      }
    } catch (e) {
      console.error('Failed to save settings to localStorage', e)
    }
  }

  public updateSettings(partial: Partial<SystemSettings>): SystemSettings {
    const current = this.getSettings()
    const updated: SystemSettings = {
      ...current,
      ...partial,
      general: { ...current.general, ...(partial.general || {}) },
      workflow: { ...current.workflow, ...(partial.workflow || {}) },
      ai: { ...current.ai, ...(partial.ai || {}) },
      notifications: { ...current.notifications, ...(partial.notifications || {}) },
      integrations: { ...current.integrations, ...(partial.integrations || {}) },
      security: { ...current.security, ...(partial.security || {}) },
      system: { ...current.system, ...(partial.system || {}) },
    }

    this.saveSettings(updated)
    return updated
  }

  public updateSection<K extends keyof SystemSettings>(
    section: K,
    partial: Partial<SystemSettings[K]>
  ): SystemSettings {
    const current = this.getSettings()
    const updated: SystemSettings = {
      ...current,
      [section]: {
        ...(current[section] as any),
        ...partial,
      },
    }

    this.saveSettings(updated)
    return updated
  }

  public resetSettings(): SystemSettings {
    this.saveSettings(defaultSystemSettings, true)
    return defaultSystemSettings
  }

  public getSystemInfo(): SystemConfiguration {
    return this.getSettings().system
  }
}

export const settingsService = new SettingsService()
