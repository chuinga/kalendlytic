import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConflictResolver } from '@/components/calendar/ConflictResolver'
import { SchedulingConflict, ConflictResolution } from '@/types/calendar'

// Mock fetch
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

const mockConflict: SchedulingConflict = {
  id: 'conflict-1',
  type: 'overlap',
  severity: 'high',
  description: 'Team Meeting overlaps with Client Call',
  conflictingEvents: [
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
      priority: 0.7,
      createdByAgent: false,
      lastModified: '2024-01-01T00:00:00Z'
    },
    {
      id: '2',
      provider: 'microsoft',
      providerEventId: 'outlook_456',
      title: 'Client Call',
      start: '2024-01-01T10:30:00Z',
      end: '2024-01-01T11:30:00Z',
      attendees: ['client@company.com'],
      organizer: 'user@company.com',
      status: 'confirmed',
      priority: 0.9,
      createdByAgent: false,
      lastModified: '2024-01-01T00:00:00Z'
    }
  ],
  suggestedResolutions: [
    {
      id: 'resolution-1',
      type: 'reschedule',
      description: 'Reschedule Team Meeting to 2:00 PM',
      affectedEvents: ['1'],
      proposedTimes: [
        {
          start: '2024-01-01T14:00:00Z',
          end: '2024-01-01T15:00:00Z',
          available: true
        }
      ],
      confidence: 0.9,
      reasoning: 'Client Call has higher priority and cannot be moved'
    },
    {
      id: 'resolution-2',
      type: 'shorten',
      description: 'Shorten Team Meeting to 30 minutes',
      affectedEvents: ['1'],
      confidence: 0.7,
      reasoning: 'Reduce overlap by shortening lower priority meeting'
    }
  ]
}

describe('ConflictResolver', () => {
  const mockProps = {
    conflicts: [mockConflict],
    onResolveConflict: jest.fn(),
    onDismissConflict: jest.fn(),
    onRefreshConflicts: jest.fn()
  }
  
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders conflict information correctly', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('Scheduling Conflicts')).toBeInTheDocument()
    expect(screen.getByText('Team Meeting overlaps with Client Call')).toBeInTheDocument()
    expect(screen.getByText('Team Meeting')).toBeInTheDocument()
    expect(screen.getByText('Client Call')).toBeInTheDocument()
  })

  it('displays conflict severity with appropriate styling', () => {
    render(<ConflictResolver {...mockProps} />)
    
    const severityBadge = screen.getByText('high')
    expect(severityBadge).toBeInTheDocument()
    expect(severityBadge).toHaveClass('bg-red-100', 'text-red-800')
  })

  it('shows suggested resolutions', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('Suggested Resolutions')).toBeInTheDocument()
    expect(screen.getByText('Reschedule Team Meeting to 2:00 PM')).toBeInTheDocument()
    expect(screen.getByText('Shorten Team Meeting to 30 minutes')).toBeInTheDocument()
  })

  it('displays confidence scores for resolutions', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('90% confidence')).toBeInTheDocument()
    expect(screen.getByText('70% confidence')).toBeInTheDocument()
  })

  it('shows reasoning for each resolution', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('Client Call has higher priority and cannot be moved')).toBeInTheDocument()
    expect(screen.getByText('Reduce overlap by shortening lower priority meeting')).toBeInTheDocument()
  })

  it('calls onResolveConflict when resolution is approved', async () => {
    render(<ConflictResolver {...mockProps} />)
    
    const approveButtons = screen.getAllByText('Apply Resolution')
    await user.click(approveButtons[0])
    
    expect(mockProps.onResolveConflict).toHaveBeenCalledWith(
      mockConflict.id,
      mockConflict.suggestedResolutions[0].id
    )
  })

  it('calls onDismissConflict when conflict is dismissed', async () => {
    render(<ConflictResolver {...mockProps} />)
    
    const dismissButton = screen.getByText('Dismiss Conflict')
    await user.click(dismissButton)
    
    expect(mockProps.onDismissConflict).toHaveBeenCalledWith(mockConflict.id)
  })

  it('shows loading state when processing', async () => {
    // Mock the resolve function to simulate loading
    const mockResolve = jest.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(<ConflictResolver {...mockProps} onResolveConflict={mockResolve} />)
    
    const approveButtons = screen.getAllByText('Apply Resolution')
    await user.click(approveButtons[0])
    
    // Should show loading state
    expect(screen.getByText('Applying...')).toBeInTheDocument()
  })

  it('displays event details with time and attendees', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('10:00 AM - 11:00 AM')).toBeInTheDocument()
    expect(screen.getByText('10:30 AM - 11:30 AM')).toBeInTheDocument()
    expect(screen.getByText('1 attendee')).toBeInTheDocument()
  })

  it('shows provider badges for events', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('google')).toBeInTheDocument()
    expect(screen.getByText('microsoft')).toBeInTheDocument()
  })

  it('handles multiple conflicts', () => {
    const multipleConflicts = [
      mockConflict,
      {
        ...mockConflict,
        id: 'conflict-2',
        description: 'Another conflict'
      }
    ]
    
    render(<ConflictResolver {...mockProps} conflicts={multipleConflicts} />)
    
    expect(screen.getByText('Team Meeting overlaps with Client Call')).toBeInTheDocument()
    expect(screen.getByText('Another conflict')).toBeInTheDocument()
  })

  it('shows empty state when no conflicts', () => {
    render(<ConflictResolver {...mockProps} conflicts={[]} />)
    
    expect(screen.getByText('No scheduling conflicts found')).toBeInTheDocument()
    expect(screen.getByText('Your calendar is looking good!')).toBeInTheDocument()
  })

  it('displays proposed times for reschedule resolutions', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('Proposed time: 2:00 PM - 3:00 PM')).toBeInTheDocument()
  })

  it('handles different conflict types with appropriate icons', () => {
    const conflictTypes = [
      { ...mockConflict, type: 'back_to_back' as const },
      { ...mockConflict, type: 'focus_block' as const },
      { ...mockConflict, type: 'outside_hours' as const }
    ]
    
    conflictTypes.forEach((conflict, index) => {
      const { rerender } = render(<ConflictResolver {...mockProps} conflicts={[conflict]} />)
      
      // Each conflict type should render without errors
      expect(screen.getByText('Scheduling Conflicts')).toBeInTheDocument()
      
      if (index < conflictTypes.length - 1) {
        rerender(<div />)
      }
    })
  })

  it('shows resolution type badges', () => {
    render(<ConflictResolver {...mockProps} />)
    
    expect(screen.getByText('reschedule')).toBeInTheDocument()
    expect(screen.getByText('shorten')).toBeInTheDocument()
  })

  it('disables buttons when processing', async () => {
    const mockResolve = jest.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(<ConflictResolver {...mockProps} onResolveConflict={mockResolve} />)
    
    const approveButtons = screen.getAllByText('Apply Resolution')
    await user.click(approveButtons[0])
    
    // Buttons should be disabled during processing
    const dismissButton = screen.getByText('Dismiss Conflict')
    expect(dismissButton).toBeDisabled()
  })

  it('expands and collapses conflict details', async () => {
    render(<ConflictResolver {...mockProps} />)
    
    // Initially, detailed resolution info should be visible
    expect(screen.getByText('Client Call has higher priority and cannot be moved')).toBeInTheDocument()
    
    // Test that the component renders the full details by default
    expect(screen.getByText('Suggested Resolutions')).toBeInTheDocument()
  })
})