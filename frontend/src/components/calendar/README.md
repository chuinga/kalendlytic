# Calendar Components

This directory contains the calendar and scheduling components for the AWS Meeting Scheduling Agent dashboard.

## Components

### AvailabilityTimeline
Displays a unified calendar view showing availability across all connected calendar providers (Google Calendar and Microsoft Outlook).

**Features:**
- Day, week, and month view modes
- Unified availability display across multiple calendar providers
- Conflict indicators and time slot highlighting
- Interactive time slot and event selection
- Real-time data fetching with loading states

**Props:**
- `viewMode`: Current calendar view configuration
- `onViewModeChange`: Callback for view mode changes
- `onTimeSlotClick`: Optional callback for time slot interactions
- `onEventClick`: Optional callback for event interactions

### ConflictResolver
Provides an interface for detecting, reviewing, and resolving scheduling conflicts.

**Features:**
- Automatic conflict detection across all calendars
- Severity-based conflict prioritization
- Multiple resolution options with confidence scores
- Agent-generated reasoning for each resolution
- One-click conflict resolution with user approval

**Props:**
- `conflicts`: Array of detected scheduling conflicts
- `onResolveConflict`: Callback for applying conflict resolutions
- `onDismissConflict`: Callback for dismissing conflicts
- `onRefreshConflicts`: Callback for refreshing conflict data

### MeetingScheduler
A comprehensive form for creating new meeting requests with intelligent time suggestions.

**Features:**
- Meeting details form with validation
- Attendee management with email validation
- Duration and priority selection
- Automatic time slot suggestions based on attendee availability
- Video conference integration options
- Meeting type classification

**Props:**
- `onScheduleMeeting`: Callback for submitting meeting requests
- `onClose`: Optional callback for closing the scheduler
- `initialData`: Optional pre-filled meeting data

### AgentActionReview
Interface for reviewing and approving AI agent actions before execution.

**Features:**
- Pending action approval workflow
- Detailed action reasoning and proposed changes
- User feedback collection for agent learning
- Action history with execution status
- Real-time action status updates

**Props:**
- `onApproveAction`: Callback for approving agent actions
- `onRejectAction`: Callback for rejecting actions with feedback
- `onRefreshActions`: Callback for refreshing action data

## Usage

```tsx
import { 
  AvailabilityTimeline, 
  ConflictResolver, 
  MeetingScheduler, 
  AgentActionReview 
} from '@/components/calendar'

// Example usage in Dashboard component
<AvailabilityTimeline
  viewMode={viewMode}
  onViewModeChange={setViewMode}
  onTimeSlotClick={handleTimeSlotClick}
  onEventClick={handleEventClick}
/>
```

## API Integration

These components expect the following API endpoints to be available:

- `GET /api/calendar/availability` - Fetch availability data
- `GET /api/calendar/events` - Fetch calendar events
- `POST /api/calendar/suggest-times` - Get suggested meeting times
- `POST /api/calendar/schedule` - Schedule new meetings
- `GET /api/calendar/conflicts` - Fetch scheduling conflicts
- `POST /api/calendar/conflicts/:id/resolve` - Resolve conflicts
- `GET /api/agent/actions` - Fetch agent actions
- `POST /api/agent/actions/:id/approve` - Approve agent actions
- `POST /api/agent/actions/:id/reject` - Reject agent actions

## Types

All components use TypeScript interfaces defined in `@/types/calendar.ts`:

- `CalendarViewMode` - Calendar view configuration
- `TimeSlot` - Available time slot data
- `CalendarEvent` - Calendar event data
- `SchedulingConflict` - Conflict detection data
- `MeetingRequest` - Meeting scheduling request
- `AgentAction` - AI agent action data

## Styling

Components use Tailwind CSS classes and follow the design system established in the main Dashboard component. All components are responsive and include proper loading states, error handling, and accessibility features.