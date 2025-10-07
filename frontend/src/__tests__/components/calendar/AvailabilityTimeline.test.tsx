import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AvailabilityTimeline } from '@/components/calendar/AvailabilityTimeline'
import { CalendarViewMode, AvailabilityData, CalendarEvent, TimeSlot } from '@/types/calendar'

// Mock fetch
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

// Mock LoadingSpinner
jest.mock('@/components/ui/LoadingSpinner', () => {
  return function LoadingSpinner() {
    return <div data-testid="loading-spinner">Loading...</div>
  }
})

const mockAvailabilityData: AvailabilityData[] = [
  {
    date: '2024-01-01',
    timeSlots: [
      {
        start: '2024-01-01T09:00:00Z',
        end: '2024-01-01T10:00:00Z',
        available: true
      },
      {
        start: '2024-01-01T10:00:00Z',
        end: '2024-01-01T11:00:00Z',
        available: false,
        conflicts: [
          {
            eventId: '1',
            title: 'Team Meeting',
            provider: 'google',
            priority: 0.8,
            attendees: ['team@company.com'],
            canReschedule: true
          }
        ]
      }
    ],
    conflicts: [],
    workingHours: { start: '09:00', end: '17:00' },
    focusBlocks: []
  }
]

const mockEvents: CalendarEvent[] = [
  {
    id: '1',
    provider: 'google',
    providerEventId: 'google_123',
    title: 'Team Meeting',
    start: '2024-01-01T10:00:00Z',
    end: '2024-01-01T11:00:00Z',
    attendees: ['team@company.com'],
    organizer: 'user@company.com',
    status: 'confirmed',
    priority: 0.8,
    createdByAgent: false,
    lastModified: '2024-01-01T00:00:00Z'
  }
]

describe('AvailabilityTimeline', () => {
  const mockViewMode: CalendarViewMode = {
    type: 'day',
    date: '2024-01-01'
  }
  
  const mockProps = {
    viewMode: mockViewMode,
    onViewModeChange: jest.fn(),
    onTimeSlotClick: jest.fn(),
    onEventClick: jest.fn()
  }
  
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API responses
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockAvailabilityData)
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockEvents)
      } as Response)
  })

  it('renders loading state initially', () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('renders calendar timeline after loading', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Available Time Slots')).toBeInTheDocument()
    expect(screen.getByText('Scheduled Events')).toBeInTheDocument()
  })

  it('displays view mode buttons', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('day')).toBeInTheDocument()
      expect(screen.getByText('week')).toBeInTheDocument()
      expect(screen.getByText('month')).toBeInTheDocument()
    })
  })

  it('calls onViewModeChange when view mode button is clicked', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('week')).toBeInTheDocument()
    })
    
    const weekButton = screen.getByText('week')
    await user.click(weekButton)
    
    expect(mockProps.onViewModeChange).toHaveBeenCalledWith({
      ...mockViewMode,
      type: 'week'
    })
  })

  it('displays navigation buttons and date range', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
    })
    
    // Check for navigation buttons (ChevronLeft and ChevronRight icons)
    const navButtons = screen.getAllByRole('button')
    const prevButton = navButtons.find(button => button.querySelector('svg'))
    const nextButton = navButtons.find(button => button.querySelector('svg'))
    
    expect(prevButton).toBeInTheDocument()
    expect(nextButton).toBeInTheDocument()
  })

  it('navigates to previous/next date when navigation buttons are clicked', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
    })
    
    // Find and click the next button (second navigation button)
    const navButtons = screen.getAllByRole('button')
    const nextButton = navButtons[1] // Assuming second button is next
    
    await user.click(nextButton)
    
    expect(mockProps.onViewModeChange).toHaveBeenCalledWith({
      ...mockViewMode,
      date: '2024-01-02' // Next day
    })
  })

  it('displays available time slots in day view', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Available Time Slots')).toBeInTheDocument()
    })
    
    // Check for time slot display
    expect(screen.getByText('9:00 AM')).toBeInTheDocument()
  })

  it('displays scheduled events in day view', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Scheduled Events')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Team Meeting')).toBeInTheDocument()
    expect(screen.getByText('google')).toBeInTheDocument()
  })

  it('calls onTimeSlotClick when time slot is clicked', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('9:00 AM')).toBeInTheDocument()
    })
    
    const timeSlot = screen.getByText('9:00 AM').closest('div')
    if (timeSlot) {
      await user.click(timeSlot)
      
      expect(mockProps.onTimeSlotClick).toHaveBeenCalledWith(
        expect.objectContaining({
          start: '2024-01-01T09:00:00Z',
          end: '2024-01-01T10:00:00Z',
          available: true
        })
      )
    }
  })

  it('calls onEventClick when event is clicked', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Team Meeting')).toBeInTheDocument()
    })
    
    const event = screen.getByText('Team Meeting').closest('div')
    if (event) {
      await user.click(event)
      
      expect(mockProps.onEventClick).toHaveBeenCalledWith(
        expect.objectContaining({
          id: '1',
          title: 'Team Meeting',
          provider: 'google'
        })
      )
    }
  })

  it('displays conflicts in time slots', async () => {
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Available Time Slots')).toBeInTheDocument()
    })
    
    // Check for conflict indicator (should show "1" for one conflict)
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))
    
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Error loading calendar data: API Error')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('retries loading data when retry button is clicked', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))
    
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })
    
    // Reset mock to return successful response
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockAvailabilityData)
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockEvents)
      } as Response)
    
    const retryButton = screen.getByText('Retry')
    await user.click(retryButton)
    
    await waitFor(() => {
      expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
    })
  })

  it('formats date range correctly for different view modes', async () => {
    const { rerender } = render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
    })
    
    // Test week view
    rerender(
      <AvailabilityTimeline 
        {...mockProps} 
        viewMode={{ type: 'week', date: '2024-01-01' }} 
      />
    )
    
    // Test month view
    rerender(
      <AvailabilityTimeline 
        {...mockProps} 
        viewMode={{ type: 'month', date: '2024-01-01' }} 
      />
    )
    
    // The component should handle different view modes without crashing
    expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
  })

  it('shows agent-created events with special styling', async () => {
    const agentEvent = {
      ...mockEvents[0],
      createdByAgent: true
    }
    
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockAvailabilityData)
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([agentEvent])
      } as Response)
    
    render(<AvailabilityTimeline {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Agent')).toBeInTheDocument()
    })
  })
})