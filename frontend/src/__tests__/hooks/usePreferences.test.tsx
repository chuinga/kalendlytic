import React from 'react'
import { renderHook, act } from '@testing-library/react'
import { usePreferences } from '@/hooks/usePreferences'
import { PreferencesService } from '@/utils/preferences'
import { UserPreferences } from '@/types/preferences'

// Mock PreferencesService
jest.mock('@/utils/preferences')
const mockPreferencesService = PreferencesService as jest.Mocked<typeof PreferencesService>

const mockPreferences: UserPreferences = {
  workingHours: {
    monday: { start: '09:00', end: '17:00' },
    tuesday: { start: '09:00', end: '17:00' },
    wednesday: { start: '09:00', end: '17:00' },
    thursday: { start: '09:00', end: '17:00' },
    friday: { start: '09:00', end: '17:00' },
    saturday: { start: '10:00', end: '14:00' },
    sunday: { start: '10:00', end: '14:00' }
  },
  bufferMinutes: 15,
  focusBlocks: [
    {
      id: '1',
      title: 'Deep Work',
      start: '09:00',
      end: '11:00',
      protected: true
    }
  ],
  vipContacts: ['boss@company.com', 'client@important.com'],
  meetingTypes: {
    standup: { duration: 15, priority: 'medium' },
    interview: { duration: 60, priority: 'high' }
  },
  defaultMeetingDuration: 30,
  autoBookEnabled: false
}

describe('usePreferences', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPreferencesService.getPreferences.mockResolvedValue(mockPreferences)
  })

  it('loads preferences on mount', async () => {
    const { result } = renderHook(() => usePreferences())

    expect(result.current.loading).toBe(true)

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.preferences).toEqual(mockPreferences)
    expect(mockPreferencesService.getPreferences).toHaveBeenCalledTimes(1)
  })

  it('handles loading errors', async () => {
    const errorMessage = 'Failed to load preferences'
    mockPreferencesService.getPreferences.mockRejectedValue(new Error(errorMessage))

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBe(errorMessage)
    expect(result.current.preferences).toBeNull()
  })

  it('updates working hours successfully', async () => {
    const updatedWorkingHours = {
      ...mockPreferences.workingHours,
      monday: { start: '08:00', end: '16:00' }
    }

    mockPreferencesService.updateWorkingHours.mockResolvedValue()

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.updateWorkingHours(updatedWorkingHours)
    })

    expect(mockPreferencesService.updateWorkingHours).toHaveBeenCalledWith(updatedWorkingHours)
    expect(result.current.preferences?.workingHours).toEqual(updatedWorkingHours)
  })

  it('handles working hours update errors', async () => {
    const errorMessage = 'Failed to update working hours'
    mockPreferencesService.updateWorkingHours.mockRejectedValue(new Error(errorMessage))

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      try {
        await result.current.updateWorkingHours(mockPreferences.workingHours)
      } catch (error) {
        // Expected to throw
      }
    })

    expect(result.current.error).toBe(errorMessage)
  })

  it('adds focus block successfully', async () => {
    const newFocusBlock = {
      id: '2',
      title: 'Planning Time',
      start: '14:00',
      end: '15:00',
      protected: true
    }

    mockPreferencesService.addFocusBlock.mockResolvedValue()

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.addFocusBlock(newFocusBlock)
    })

    expect(mockPreferencesService.addFocusBlock).toHaveBeenCalledWith(newFocusBlock)
    expect(result.current.preferences?.focusBlocks).toContainEqual(newFocusBlock)
  })

  it('removes focus block successfully', async () => {
    mockPreferencesService.removeFocusBlock.mockResolvedValue()

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.removeFocusBlock('1')
    })

    expect(mockPreferencesService.removeFocusBlock).toHaveBeenCalledWith('1')
    expect(result.current.preferences?.focusBlocks).toEqual([])
  })

  it('updates VIP contacts successfully', async () => {
    const updatedVipContacts = ['boss@company.com', 'client@important.com', 'new@vip.com']
    mockPreferencesService.updateVipContacts.mockResolvedValue()

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.updateVipContacts(updatedVipContacts)
    })

    expect(mockPreferencesService.updateVipContacts).toHaveBeenCalledWith(updatedVipContacts)
    expect(result.current.preferences?.vipContacts).toEqual(updatedVipContacts)
  })

  it('updates meeting types successfully', async () => {
    const updatedMeetingTypes = {
      ...mockPreferences.meetingTypes,
      'one-on-one': { duration: 45, priority: 'high' }
    }

    mockPreferencesService.updateMeetingTypes.mockResolvedValue()

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.updateMeetingTypes(updatedMeetingTypes)
    })

    expect(mockPreferencesService.updateMeetingTypes).toHaveBeenCalledWith(updatedMeetingTypes)
    expect(result.current.preferences?.meetingTypes).toEqual(updatedMeetingTypes)
  })

  it('updates general settings successfully', async () => {
    const updatedSettings = {
      bufferMinutes: 30,
      defaultMeetingDuration: 45,
      autoBookEnabled: true
    }

    mockPreferencesService.updateGeneralSettings.mockResolvedValue()

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.updateGeneralSettings(updatedSettings)
    })

    expect(mockPreferencesService.updateGeneralSettings).toHaveBeenCalledWith(updatedSettings)
    expect(result.current.preferences?.bufferMinutes).toBe(30)
    expect(result.current.preferences?.defaultMeetingDuration).toBe(45)
    expect(result.current.preferences?.autoBookEnabled).toBe(true)
  })

  it('clears error successfully', async () => {
    const errorMessage = 'Test error'
    mockPreferencesService.getPreferences.mockRejectedValue(new Error(errorMessage))

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.error).toBe(errorMessage)

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBe(null)
  })

  it('refreshes preferences successfully', async () => {
    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(mockPreferencesService.getPreferences).toHaveBeenCalledTimes(1)

    await act(async () => {
      await result.current.refreshPreferences()
    })

    expect(mockPreferencesService.getPreferences).toHaveBeenCalledTimes(2)
  })

  it('handles concurrent updates correctly', async () => {
    mockPreferencesService.updateWorkingHours.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    )
    mockPreferencesService.updateVipContacts.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 50))
    )

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    // Start both updates concurrently
    const workingHoursPromise = act(async () => {
      await result.current.updateWorkingHours(mockPreferences.workingHours)
    })

    const vipContactsPromise = act(async () => {
      await result.current.updateVipContacts(['new@contact.com'])
    })

    await Promise.all([workingHoursPromise, vipContactsPromise])

    expect(mockPreferencesService.updateWorkingHours).toHaveBeenCalled()
    expect(mockPreferencesService.updateVipContacts).toHaveBeenCalled()
  })

  it('provides default preferences when none exist', async () => {
    mockPreferencesService.getPreferences.mockResolvedValue(null)

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.preferences).toEqual({
      workingHours: {
        monday: { start: '09:00', end: '17:00' },
        tuesday: { start: '09:00', end: '17:00' },
        wednesday: { start: '09:00', end: '17:00' },
        thursday: { start: '09:00', end: '17:00' },
        friday: { start: '09:00', end: '17:00' },
        saturday: { start: '', end: '' },
        sunday: { start: '', end: '' }
      },
      bufferMinutes: 15,
      focusBlocks: [],
      vipContacts: [],
      meetingTypes: {},
      defaultMeetingDuration: 30,
      autoBookEnabled: false
    })
  })

  it('validates focus block times', async () => {
    const invalidFocusBlock = {
      id: '2',
      title: 'Invalid Block',
      start: '15:00',
      end: '14:00', // End before start
      protected: true
    }

    const { result } = renderHook(() => usePreferences())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      try {
        await result.current.addFocusBlock(invalidFocusBlock)
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
      }
    })

    expect(mockPreferencesService.addFocusBlock).not.toHaveBeenCalled()
  })
})