/**
 * Application environment configuration
 * Provides centralized, safe access to Vite environment variables
 * with fallback defaults so the app runs smoothly without a .env file.
 */

export interface AppConfig {
  apiBaseUrl: string
  appEnv: 'development' | 'staging' | 'production' | 'test'
  isDevelopment: boolean
  isProduction: boolean
}

export const env: AppConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '',
  appEnv: (import.meta.env.VITE_APP_ENV as AppConfig['appEnv']) || 'development',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
}

export default env
