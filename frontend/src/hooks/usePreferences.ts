import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { UserPreferences, PreferenceUpdateRequest } from '@/types/preferences'
import { PreferencesService } from '@/utils/preferences'

export function usePreferences() {
  const queryClient = useQueryClient()

  // Query for fetching preferences
  const {
    data: preferences,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['preferences'],
    queryFn: PreferencesService.getPreferences,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1
  })

  // Mutation for updating preferences
  const updateMutation = useMutation({
    mutationFn: (updates: PreferenceUpdateRequest) => 
      PreferencesService.updatePreferences(updates),
    onSuccess: (updatedPreferences) => {
      // Update the cache with new preferences
      queryClient.setQueryData(['preferences'], updatedPreferences)
    },
    onError: (error) => {
      console.error('Failed to update preferences:', error)
    }
  })

  // Mutation for resetting preferences
  const resetMutation = useMutation({
    mutationFn: PreferencesService.resetPreferences,
    onSuccess: (resetPreferences) => {
      // Update the cache with reset preferences
      queryClient.setQueryData(['preferences'], resetPreferences)
    },
    onError: (error) => {
      console.error('Failed to reset preferences:', error)
    }
  })

  const updatePreferences = async (updates: PreferenceUpdateRequest) => {
    try {
      await updateMutation.mutateAsync(updates)
      return true
    } catch (error) {
      return false
    }
  }

  const resetPreferences = async () => {
    try {
      await resetMutation.mutateAsync()
      return true
    } catch (error) {
      return false
    }
  }

  return {
    preferences,
    isLoading,
    error,
    isUpdating: updateMutation.isPending,
    isResetting: resetMutation.isPending,
    updateError: updateMutation.error,
    resetError: resetMutation.error,
    updatePreferences,
    resetPreferences,
    refetch
  }
}

export function usePreferencesForm(initialPreferences?: UserPreferences) {
  const [formData, setFormData] = useState<UserPreferences | null>(null)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    if (initialPreferences && !formData) {
      setFormData(initialPreferences)
    }
  }, [initialPreferences, formData])

  const updateFormData = (updates: Partial<UserPreferences>) => {
    if (!formData) return

    const newFormData = { ...formData, ...updates }
    setFormData(newFormData)
    
    // Check if there are changes compared to initial preferences
    if (initialPreferences) {
      const hasChanges = JSON.stringify(newFormData) !== JSON.stringify(initialPreferences)
      setHasChanges(hasChanges)
    }
  }

  const resetForm = () => {
    if (initialPreferences) {
      setFormData(initialPreferences)
      setHasChanges(false)
    }
  }

  const getChanges = (): PreferenceUpdateRequest | null => {
    if (!formData || !initialPreferences || !hasChanges) {
      return null
    }

    const changes: PreferenceUpdateRequest = {}

    // Compare each field and include only changed ones
    if (JSON.stringify(formData.workingHours) !== JSON.stringify(initialPreferences.workingHours)) {
      changes.workingHours = formData.workingHours
    }

    if (formData.timezone !== initialPreferences.timezone) {
      changes.timezone = formData.timezone
    }

    if (formData.defaultBufferMinutes !== initialPreferences.defaultBufferMinutes) {
      changes.defaultBufferMinutes = formData.defaultBufferMinutes
    }

    if (formData.bufferBetweenMeetings !== initialPreferences.bufferBetweenMeetings) {
      changes.bufferBetweenMeetings = formData.bufferBetweenMeetings
    }

    if (JSON.stringify(formData.focusBlocks) !== JSON.stringify(initialPreferences.focusBlocks)) {
      changes.focusBlocks = formData.focusBlocks
    }

    if (JSON.stringify(formData.meetingTypes) !== JSON.stringify(initialPreferences.meetingTypes)) {
      changes.meetingTypes = formData.meetingTypes
    }

    if (formData.defaultMeetingDuration !== initialPreferences.defaultMeetingDuration) {
      changes.defaultMeetingDuration = formData.defaultMeetingDuration
    }

    if (JSON.stringify(formData.vipContacts) !== JSON.stringify(initialPreferences.vipContacts)) {
      changes.vipContacts = formData.vipContacts
    }

    if (JSON.stringify(formData.priorityRules) !== JSON.stringify(initialPreferences.priorityRules)) {
      changes.priorityRules = formData.priorityRules
    }

    if (formData.autoBookEnabled !== initialPreferences.autoBookEnabled) {
      changes.autoBookEnabled = formData.autoBookEnabled
    }

    if (formData.autoSendEmails !== initialPreferences.autoSendEmails) {
      changes.autoSendEmails = formData.autoSendEmails
    }

    if (formData.requireApprovalForRescheduling !== initialPreferences.requireApprovalForRescheduling) {
      changes.requireApprovalForRescheduling = formData.requireApprovalForRescheduling
    }

    if (formData.maxMeetingsPerDay !== initialPreferences.maxMeetingsPerDay) {
      changes.maxMeetingsPerDay = formData.maxMeetingsPerDay
    }

    if (formData.emailNotifications !== initialPreferences.emailNotifications) {
      changes.emailNotifications = formData.emailNotifications
    }

    if (formData.conflictAlerts !== initialPreferences.conflictAlerts) {
      changes.conflictAlerts = formData.conflictAlerts
    }

    if (formData.dailySummary !== initialPreferences.dailySummary) {
      changes.dailySummary = formData.dailySummary
    }

    return Object.keys(changes).length > 0 ? changes : null
  }

  return {
    formData,
    hasChanges,
    updateFormData,
    resetForm,
    getChanges
  }
}