export interface TimeSlot {
  start: string // ISO 8601 datetime
  end: string // ISO 8601 datetime
  available: boolean
  conflicts?: ConflictInfo[]
}

export interface ConflictInfo {
  eventId: string
  title: string
  provider: 'google' | 'microsoft'
  priority: number
  attendees: string[]
  canReschedule: boolean
}

export interface CalendarEvent {
  id: string
  provider: 'google' | 'microsoft'
  providerEventId: string
  title: string
  description?: string
  start: string // ISO 8601 datetime
  end: string // ISO 8601 datetime
  attendees: string[]
  organizer: string
  location?: string
  conferenceLink?: string
  status: 'confirmed' | 'tentative' | 'cancelled'
  priority: number
  createdByAgent: boolean
  lastModified: string
}

export interface AvailabilityData {
  date: string // YYYY-MM-DD
  timeSlots: TimeSlot[]
  conflicts: ConflictInfo[]
  workingHours: {
    start: string // HH:MM
    end: string // HH:MM
  }
  focusBlocks: FocusBlock[]
}

export interface FocusBlock {
  id: string
  title: string
  start: string // HH:MM
  end: string // HH:MM
  protected: boolean
}

export interface MeetingRequest {
  title: string
  description?: string
  attendees: string[]
  duration: number // minutes
  preferredTimes?: TimeSlot[]
  location?: string
  requiresVideoConference: boolean
  priority: 'low' | 'medium' | 'high'
  meetingType?: string
}

export interface SchedulingConflict {
  id: string
  type: 'overlap' | 'back_to_back' | 'focus_block' | 'outside_hours'
  severity: 'low' | 'medium' | 'high'
  conflictingEvents: CalendarEvent[]
  suggestedResolutions: ConflictResolution[]
  description: string
}

export interface ConflictResolution {
  id: string
  type: 'reschedule' | 'shorten' | 'decline' | 'override'
  description: string
  affectedEvents: string[]
  proposedTimes?: TimeSlot[]
  confidence: number // 0-1
  reasoning: string
}

export interface AgentAction {
  id: string
  type: 'schedule' | 'reschedule' | 'cancel' | 'send_email' | 'detect_conflict'
  status: 'pending' | 'approved' | 'rejected' | 'executed'
  description: string
  reasoning: string
  proposedChanges: any
  requiresApproval: boolean
  createdAt: string
  executedAt?: string
  userFeedback?: string
}

export interface CalendarViewMode {
  type: 'day' | 'week' | 'month'
  date: string // Current date being viewed
}

export interface AvailabilityQuery {
  startDate: string // YYYY-MM-DD
  endDate: string // YYYY-MM-DD
  attendees?: string[]
  minDuration?: number // minutes
  workingHoursOnly?: boolean
}