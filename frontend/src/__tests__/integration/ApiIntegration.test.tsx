import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider } from '@/contexts/AuthContext'
import { AvailabilityTimeline } from '@/components/calendar/AvailabilityTimeline'
import { ConnectionsPage } from '@/components/connections/ConnectionsPage'
import { CalendarViewMode } from '@/types/calendar'

// Mock fetch globally
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

// Mock AuthService
jest.mock('@/utils/auth', () => ({
  AuthService: {
    isSessionValid: jest.fn().mockResolvedValue(true),
    getCurrentUser: jest.fn().mockResolvedValue({
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    })
  }
}))

// Mock ConnectionsService
jest.mock('@/utils/connections', () => ({
  ConnectionsService: {
    getConnections: jest.fn(),
    parseOAuthCallback: jest.fn().mockReturnValue(null)
  }
}))

const ApiTestApp = ({ children }: { children: React.ReactNode }) => {
  return <AuthProvider>{children}</AuthProvider>
}

describe('API Integration Tests', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockClear()
  })

  describe('Calendar API Integration', () => {
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

    it('fetches availability data from correct API endpoint', async () => {
      const mockAvailabilityData = [
        {
          date: '2024-01-01',
          timeSlots: [
            {
              start: '2024-01-01T09:00:00Z',
              end: '2024-01-01T10:00:00Z',
              available: true
            }
          ],
          conflicts: [],
          workingHours: { start: '09:00', end: '17:00' },
          focusBlocks: []
        }
      ]

      const mockEvents = [
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

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockAvailabilityData)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockEvents)
        } as Response)

      render(
        <ApiTestApp>
          <AvailabilityTimeline {...mockProps} />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/calendar/availability?start=2024-01-01&end=2024-01-01')
        expect(mockFetch).toHaveBeenCalledWith('/api/calendar/events?start=2024-01-01&end=2024-01-01')
      })

      expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
    })

    it('handles API errors with proper error messages', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      render(
        <ApiTestApp>
          <AvailabilityTimeline {...mockProps} />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(screen.getByText('Error loading calendar data: Network error')).toBeInTheDocument()
      })
    })

    it('handles HTTP error responses', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      } as Response)

      render(
        <ApiTestApp>
          <AvailabilityTimeline {...mockProps} />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(screen.getByText(/Error loading calendar data/)).toBeInTheDocument()
      })
    })

    it('retries failed requests when retry button is clicked', async () => {
      // First call fails
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      render(
        <ApiTestApp>
          <AvailabilityTimeline {...mockProps} />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument()
      })

      // Setup successful response for retry
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([])
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([])
        } as Response)

      const retryButton = screen.getByText('Retry')
      await user.click(retryButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(4) // 2 initial + 2 retry
      })
    })

    it('sends correct date ranges for different view modes', async () => {
      mockFetch
        .mockResolvedValue({
          ok: true,
          json: () => Promise.resolve([])
        } as Response)

      const { rerender } = render(
        <ApiTestApp>
          <AvailabilityTimeline {...mockProps} />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/calendar/availability?start=2024-01-01&end=2024-01-01')
      })

      // Test week view
      mockFetch.mockClear()
      rerender(
        <ApiTestApp>
          <AvailabilityTimeline 
            {...mockProps} 
            viewMode={{ type: 'week', date: '2024-01-01' }} 
          />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/calendar/availability?start=2023-12-31&end=2024-01-06')
      })

      // Test month view
      mockFetch.mockClear()
      rerender(
        <ApiTestApp>
          <AvailabilityTimeline 
            {...mockProps} 
            viewMode={{ type: 'month', date: '2024-01-01' }} 
          />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/calendar/availability?start=2024-01-01&end=2024-01-31')
      })
    })
  })

  describe('Authentication API Integration', () => {
    it('includes authentication headers in API requests', async () => {
      // Mock localStorage to simulate stored auth token
      const mockToken = 'mock-jwt-token'
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: jest.fn(() => mockToken),
          setItem: jest.fn(),
          removeItem: jest.fn()
        },
        writable: true
      })

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([])
      } as Response)

      const mockViewMode: CalendarViewMode = {
        type: 'day',
        date: '2024-01-01'
      }

      render(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={mockViewMode}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/calendar/availability?start=2024-01-01&end=2024-01-01',
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': `Bearer ${mockToken}`
            })
          })
        )
      })
    })

    it('handles 401 unauthorized responses', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized'
      } as Response)

      const mockViewMode: CalendarViewMode = {
        type: 'day',
        date: '2024-01-01'
      }

      render(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={mockViewMode}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(screen.getByText(/Error loading calendar data/)).toBeInTheDocument()
      })
    })
  })

  describe('Real-time Data Updates', () => {
    it('refreshes data when view mode changes', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([])
      } as Response)

      const mockViewMode: CalendarViewMode = {
        type: 'day',
        date: '2024-01-01'
      }

      const { rerender } = render(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={mockViewMode}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2) // availability + events
      })

      mockFetch.mockClear()

      // Change date
      rerender(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={{ ...mockViewMode, date: '2024-01-02' }}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2) // New requests for new date
      })
    })
  })

  describe('Error Recovery', () => {
    it('recovers from temporary network failures', async () => {
      // First request fails
      mockFetch.mockRejectedValueOnce(new Error('Network error'))
      
      // Second request succeeds
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([])
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([])
        } as Response)

      const mockViewMode: CalendarViewMode = {
        type: 'day',
        date: '2024-01-01'
      }

      render(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={mockViewMode}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      // Should show error initially
      await waitFor(() => {
        expect(screen.getByText(/Error loading calendar data/)).toBeInTheDocument()
      })

      // Click retry
      const retryButton = screen.getByText('Retry')
      await user.click(retryButton)

      // Should recover and show content
      await waitFor(() => {
        expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
      })
    })
  })

  describe('Data Validation', () => {
    it('handles malformed API responses gracefully', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(null) // Invalid response
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([])
        } as Response)

      const mockViewMode: CalendarViewMode = {
        type: 'day',
        date: '2024-01-01'
      }

      render(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={mockViewMode}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      // Should handle the malformed response without crashing
      await waitFor(() => {
        expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
      })
    })

    it('validates required fields in API responses', async () => {
      const invalidAvailabilityData = [
        {
          // Missing required fields
          timeSlots: []
        }
      ]

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(invalidAvailabilityData)
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([])
        } as Response)

      const mockViewMode: CalendarViewMode = {
        type: 'day',
        date: '2024-01-01'
      }

      render(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={mockViewMode}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      // Should handle invalid data gracefully
      await waitFor(() => {
        expect(screen.getByText('Calendar Timeline')).toBeInTheDocument()
      })
    })
  })

  describe('Performance Optimization', () => {
    it('debounces rapid API calls', async () => {
      jest.useFakeTimers()
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([])
      } as Response)

      const mockViewMode: CalendarViewMode = {
        type: 'day',
        date: '2024-01-01'
      }

      const { rerender } = render(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={mockViewMode}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      // Rapidly change dates
      rerender(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={{ ...mockViewMode, date: '2024-01-02' }}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      rerender(
        <ApiTestApp>
          <AvailabilityTimeline 
            viewMode={{ ...mockViewMode, date: '2024-01-03' }}
            onViewModeChange={jest.fn()}
          />
        </ApiTestApp>
      )

      // Fast-forward timers
      jest.runAllTimers()

      await waitFor(() => {
        // Should have made requests for initial load and final date only
        expect(mockFetch).toHaveBeenCalledTimes(4) // 2 for initial + 2 for final
      })

      jest.useRealTimers()
    })
  })
})