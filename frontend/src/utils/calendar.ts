import { apiClient } from './api'
import { 
  AvailabilityData, 
  CalendarEvent, 
  AgentAction as AgentActionType,
  MeetingRequest as MeetingRequestType,
  ConflictData as ConflictDataType
} from '@/types/calendar'

// Re-export types for convenience
export type { AvailabilityData, CalendarEvent }

// Use types from the types file
export type MeetingRequest = MeetingRequestType
export type ConflictData = ConflictDataType  
export type AgentAction = AgentActionType

export class CalendarService {
  /**
   * Get availability data for a date range
   */
  static async getAvailability(startDate: string, endDate: string): Promise<AvailabilityData[]> {
    try {
      const response = await apiClient.get<{ availability: AvailabilityData[] }>(
        `/calendar/availability?start=${startDate}&end=${endDate}`
      )
      return response.data.availability
    } catch (error: any) {
      console.error('Error getting availability:', error)
      throw new Error(error.response?.data?.message || 'Failed to fetch availability data')
    }
  }

  /**
   * Get calendar events for a date range
   */
  static async getEvents(startDate: string, endDate: string): Promise<CalendarEvent[]> {
    try {
      const response = await apiClient.get<{ events: CalendarEvent[] }>(
        `/calendar/events?start=${startDate}&end=${endDate}`
      )
      return response.data.events
    } catch (error: any) {
      console.error('Error getting events:', error)
      throw new Error(error.response?.data?.message || 'Failed to fetch calendar events')
    }
  }

  /**
   * Schedule a new meeting
   */
  static async scheduleMeeting(request: MeetingRequest): Promise<CalendarEvent> {
    try {
      const response = await apiClient.post<{ event: CalendarEvent }>('/calendar/schedule', request)
      return response.data.event
    } catch (error: any) {
      console.error('Error scheduling meeting:', error)
      throw new Error(error.response?.data?.message || 'Failed to schedule meeting')
    }
  }

  /**
   * Get suggested meeting times
   */
  static async getSuggestedTimes(request: MeetingRequest): Promise<string[]> {
    try {
      const response = await apiClient.post<{ suggestedTimes: string[] }>('/calendar/suggest-times', request)
      return response.data.suggestedTimes
    } catch (error: any) {
      console.error('Error getting suggested times:', error)
      throw new Error(error.response?.data?.message || 'Failed to get suggested times')
    }
  }

  /**
   * Get calendar conflicts
   */
  static async getConflicts(): Promise<ConflictData[]> {
    try {
      const response = await apiClient.get<{ conflicts: ConflictData[] }>('/calendar/conflicts')
      return response.data.conflicts
    } catch (error: any) {
      console.error('Error getting conflicts:', error)
      throw new Error(error.response?.data?.message || 'Failed to fetch conflicts')
    }
  }

  /**
   * Resolve a calendar conflict
   */
  static async resolveConflict(conflictId: string, resolutionId: string): Promise<void> {
    try {
      await apiClient.post(`/calendar/conflicts/${conflictId}/resolve`, { resolutionId })
    } catch (error: any) {
      console.error('Error resolving conflict:', error)
      throw new Error(error.response?.data?.message || 'Failed to resolve conflict')
    }
  }
}

export class AgentService {
  /**
   * Get pending agent actions
   */
  static async getActions(): Promise<AgentAction[]> {
    try {
      const response = await apiClient.get<{ actions: AgentAction[] }>('/agent/actions')
      return response.data.actions
    } catch (error: any) {
      console.error('Error getting agent actions:', error)
      throw new Error(error.response?.data?.message || 'Failed to fetch agent actions')
    }
  }

  /**
   * Approve an agent action
   */
  static async approveAction(actionId: string): Promise<void> {
    try {
      await apiClient.post(`/agent/actions/${actionId}/approve`)
    } catch (error: any) {
      console.error('Error approving action:', error)
      throw new Error(error.response?.data?.message || 'Failed to approve action')
    }
  }

  /**
   * Reject an agent action
   */
  static async rejectAction(actionId: string, feedback?: string): Promise<void> {
    try {
      await apiClient.post(`/agent/actions/${actionId}/reject`, { feedback })
    } catch (error: any) {
      console.error('Error rejecting action:', error)
      throw new Error(error.response?.data?.message || 'Failed to reject action')
    }
  }
}