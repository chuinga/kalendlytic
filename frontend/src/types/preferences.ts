export interface WorkingHours {
  start: string // HH:MM format
  end: string // HH:MM format
}

export interface WeeklyWorkingHours {
  monday: WorkingHours
  tuesday: WorkingHours
  wednesday: WorkingHours
  thursday: WorkingHours
  friday: WorkingHours
  saturday: WorkingHours
  sunday: WorkingHours
}

export interface FocusBlock {
  id: string
  title: string
  day: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
  start: string // HH:MM format
  end: string // HH:MM format
  protected: boolean
  recurring: boolean
}

export interface MeetingType {
  id: string
  name: string
  duration: number // minutes
  priority: 'low' | 'medium' | 'high'
  bufferBefore?: number // minutes
  bufferAfter?: number // minutes
  requiresVideoConference?: boolean
  defaultLocation?: string
}

export interface VIPContact {
  id: string
  email: string
  name?: string
  priority: 'high' | 'vip' | 'critical'
  notes?: string
}

export interface PriorityRule {
  id: string
  name: string
  condition: {
    type: 'attendee' | 'subject' | 'organizer' | 'meeting_type' | 'time_of_day'
    operator: 'contains' | 'equals' | 'starts_with' | 'ends_with' | 'matches'
    value: string
  }
  priority: 'low' | 'medium' | 'high'
  enabled: boolean
}

export interface UserPreferences {
  // Working Hours Configuration
  workingHours: WeeklyWorkingHours
  timezone: string
  
  // Buffer Times
  defaultBufferMinutes: number
  bufferBetweenMeetings: number
  
  // Focus Blocks
  focusBlocks: FocusBlock[]
  
  // Meeting Types
  meetingTypes: MeetingType[]
  defaultMeetingDuration: number
  
  // VIP Contacts
  vipContacts: VIPContact[]
  
  // Priority Rules
  priorityRules: PriorityRule[]
  
  // General Settings
  autoBookEnabled: boolean
  autoSendEmails: boolean
  requireApprovalForRescheduling: boolean
  maxMeetingsPerDay?: number
  
  // Notification Preferences
  emailNotifications: boolean
  conflictAlerts: boolean
  dailySummary: boolean
  
  // Updated timestamp
  lastUpdated: string
}

export interface PreferenceUpdateRequest {
  workingHours?: Partial<WeeklyWorkingHours>
  timezone?: string
  defaultBufferMinutes?: number
  bufferBetweenMeetings?: number
  focusBlocks?: FocusBlock[]
  meetingTypes?: MeetingType[]
  defaultMeetingDuration?: number
  vipContacts?: VIPContact[]
  priorityRules?: PriorityRule[]
  autoBookEnabled?: boolean
  autoSendEmails?: boolean
  requireApprovalForRescheduling?: boolean
  maxMeetingsPerDay?: number
  emailNotifications?: boolean
  conflictAlerts?: boolean
  dailySummary?: boolean
}

// Default preferences for new users
export const DEFAULT_PREFERENCES: UserPreferences = {
  workingHours: {
    monday: { start: '09:00', end: '17:00' },
    tuesday: { start: '09:00', end: '17:00' },
    wednesday: { start: '09:00', end: '17:00' },
    thursday: { start: '09:00', end: '17:00' },
    friday: { start: '09:00', end: '17:00' },
    saturday: { start: '10:00', end: '14:00' },
    sunday: { start: '10:00', end: '14:00' }
  },
  timezone: 'America/New_York',
  defaultBufferMinutes: 15,
  bufferBetweenMeetings: 5,
  focusBlocks: [],
  meetingTypes: [
    {
      id: 'standup',
      name: 'Daily Standup',
      duration: 15,
      priority: 'medium',
      bufferBefore: 5,
      bufferAfter: 5,
      requiresVideoConference: true
    },
    {
      id: 'one-on-one',
      name: 'One-on-One',
      duration: 30,
      priority: 'high',
      bufferBefore: 10,
      bufferAfter: 10,
      requiresVideoConference: true
    },
    {
      id: 'interview',
      name: 'Interview',
      duration: 60,
      priority: 'high',
      bufferBefore: 15,
      bufferAfter: 15,
      requiresVideoConference: true
    },
    {
      id: 'team-meeting',
      name: 'Team Meeting',
      duration: 60,
      priority: 'medium',
      bufferBefore: 5,
      bufferAfter: 5,
      requiresVideoConference: true
    }
  ],
  defaultMeetingDuration: 30,
  vipContacts: [],
  priorityRules: [],
  autoBookEnabled: false,
  autoSendEmails: false,
  requireApprovalForRescheduling: true,
  maxMeetingsPerDay: 8,
  emailNotifications: true,
  conflictAlerts: true,
  dailySummary: true,
  lastUpdated: new Date().toISOString()
}