import { useState, useEffect, useCallback } from 'react'
import { settingsService } from '../services/settingsService'
import type { SystemSettings } from '../types/settings'

export function useSettings() {
  const [settings, setSettings] = useState<SystemSettings>(() => settingsService.getSettings())
  const [isSaved, setIsSaved] = useState(false)

  const reload = useCallback(() => {
    setSettings(settingsService.getSettings())
  }, [])

  useEffect(() => {
    const unsubscribe = settingsService.subscribe(reload)
    return () => unsubscribe()
  }, [reload])

  const updateSettings = useCallback((partial: Partial<SystemSettings>) => {
    const updated = settingsService.updateSettings(partial)
    setSettings(updated)
    setIsSaved(true)
    setTimeout(() => setIsSaved(false), 2500)
    return updated
  }, [])

  const updateSection = useCallback(
    <K extends keyof SystemSettings>(section: K, partial: Partial<SystemSettings[K]>) => {
      const updated = settingsService.updateSection(section, partial)
      setSettings(updated)
      setIsSaved(true)
      setTimeout(() => setIsSaved(false), 2500)
      return updated
    },
    []
  )

  const resetSettings = useCallback(() => {
    const defaults = settingsService.resetSettings()
    setSettings(defaults)
    setIsSaved(true)
    setTimeout(() => setIsSaved(false), 2500)
    return defaults
  }, [])

  return {
    settings,
    isSaved,
    updateSettings,
    updateSection,
    resetSettings,
    reload,
  }
}
