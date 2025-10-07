import { apiClient } from './api'
import { UserPreferences, PreferenceUpdateRequest, DEFAULT_PREFERENCES } from '@/types/preferences'

export class PreferencesService {
  /**
   * Get user preferences
   */
  static async getPreferences(): Promise<UserPreferences> {
    try {
      const response = await apiClient.get<UserPreferences>('/preferences')
      return response.data
    } catch (error) {
      console.error('Failed to fetch preferences:', error)
      // Return default preferences if API call fails
      return DEFAULT_PREFERENCES
    }
  }

  /**
   * Update user preferences
   */
  static async updatePreferences(updates: PreferenceUpdateRequest): Promise<UserPreferences> {
    try {
      const response = await apiClient.patch<UserPreferences>('/preferences', updates)
      return response.data
    } catch (error) {
      console.error('Failed to update preferences:', error)
      throw error
    }
  }

  /**
   * Reset preferences to defaults
   */
  static async resetPreferences(): Promise<UserPreferences> {
    try {
      const response = await apiClient.post<UserPreferences>('/preferences/reset')
      return response.data
    } catch (error) {
      console.error('Failed to reset preferences:', error)
      throw error
    }
  }

  /**
   * Validate working hours format
   */
  static validateWorkingHours(start: string, end: string): boolean {
    const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/
    if (!timeRegex.test(start) || !timeRegex.test(end)) {
      return false
    }

    const startMinutes = this.timeToMinutes(start)
    const endMinutes = this.timeToMinutes(end)
    
    return startMinutes < endMinutes
  }

  /**
   * Convert time string to minutes since midnight
   */
  static timeToMinutes(time: string): number {
    const [hours, minutes] = time.split(':').map(Number)
    return hours * 60 + minutes
  }

  /**
   * Convert minutes since midnight to time string
   */
  static minutesToTime(minutes: number): string {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
  }

  /**
   * Get available timezones
   */
  static getTimezones(): Array<{ value: string; label: string }> {
    return [
      { value: 'America/New_York', label: 'Eastern Time (ET)' },
      { value: 'America/Chicago', label: 'Central Time (CT)' },
      { value: 'America/Denver', label: 'Mountain Time (MT)' },
      { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
      { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
      { value: 'Pacific/Honolulu', label: 'Hawaii Time (HST)' },
      { value: 'Europe/London', label: 'Greenwich Mean Time (GMT)' },
      { value: 'Europe/Paris', label: 'Central European Time (CET)' },
      { value: 'Europe/Berlin', label: 'Central European Time (CET)' },
      { value: 'Asia/Tokyo', label: 'Japan Standard Time (JST)' },
      { value: 'Asia/Shanghai', label: 'China Standard Time (CST)' },
      { value: 'Asia/Kolkata', label: 'India Standard Time (IST)' },
      { value: 'Australia/Sydney', label: 'Australian Eastern Time (AET)' },
      { value: 'UTC', label: 'Coordinated Universal Time (UTC)' }
    ]
  }

  /**
   * Validate email format
   */
  static validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  /**
   * Generate unique ID for preferences items
   */
  static generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}