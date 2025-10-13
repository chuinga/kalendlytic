import React, { useState, useEffect } from 'react'
import { Calendar, Clock, AlertTriangle, Users, ChevronLeft, ChevronRight } from 'lucide-react'
import { AvailabilityData, CalendarEvent, TimeSlot, CalendarViewMode } from '@/types/calendar'
import { CalendarService } from '@/utils/calendar'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import OfflineIndicator from '@/components/ui/OfflineIndicator'

interface AvailabilityTimelineProps {
  viewMode: CalendarViewMode
  onViewModeChange: (mode: CalendarViewMode) => void
  onTimeSlotClick?: (slot: TimeSlot) => void
  onEventClick?: (event: CalendarEvent) => void
}

export function AvailabilityTimeline({ 
  viewMode, 
  onViewModeChange, 
  onTimeSlotClick,
  onEventClick 
}: AvailabilityTimelineProps) {
  const [availabilityData, setAvailabilityData] = useState<AvailabilityData[]>([])
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAvailabilityData()
  }, [viewMode])

  const fetchAvailabilityData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const startDate = getStartDate(viewMode)
      const endDate = getEndDate(viewMode)
      
      // Fetch availability data and calendar events
      const [availability, eventsData] = await Promise.all([
        CalendarService.getAvailability(startDate, endDate),
        CalendarService.getEvents(startDate, endDate)
      ])
      
      setAvailabilityData(availability)
      setEvents(eventsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load calendar data')
    } finally {
      setLoading(false)
    }
  }

  const getStartDate = (mode: CalendarViewMode): string => {
    const date = new Date(mode.date)
    switch (mode.type) {
      case 'day':
        return date.toISOString().split('T')[0]
      case 'week':
        const startOfWeek = new Date(date)
        startOfWeek.setDate(date.getDate() - date.getDay())
        return startOfWeek.toISOString().split('T')[0]
      case 'month':
        return new Date(date.getFullYear(), date.getMonth(), 1).toISOString().split('T')[0]
      default:
        return date.toISOString().split('T')[0]
    }
  }

  const getEndDate = (mode: CalendarViewMode): string => {
    const date = new Date(mode.date)
    switch (mode.type) {
      case 'day':
        return date.toISOString().split('T')[0]
      case 'week':
        const endOfWeek = new Date(date)
        endOfWeek.setDate(date.getDate() + (6 - date.getDay()))
        return endOfWeek.toISOString().split('T')[0]
      case 'month':
        return new Date(date.getFullYear(), date.getMonth() + 1, 0).toISOString().split('T')[0]
      default:
        return date.toISOString().split('T')[0]
    }
  }

  const navigateDate = (direction: 'prev' | 'next') => {
    const currentDate = new Date(viewMode.date)
    let newDate: Date

    switch (viewMode.type) {
      case 'day':
        newDate = new Date(currentDate)
        newDate.setDate(currentDate.getDate() + (direction === 'next' ? 1 : -1))
        break
      case 'week':
        newDate = new Date(currentDate)
        newDate.setDate(currentDate.getDate() + (direction === 'next' ? 7 : -7))
        break
      case 'month':
        newDate = new Date(currentDate)
        newDate.setMonth(currentDate.getMonth() + (direction === 'next' ? 1 : -1))
        break
      default:
        newDate = currentDate
    }

    onViewModeChange({
      ...viewMode,
      date: newDate.toISOString().split('T')[0]
    })
  }

  const formatDateRange = (): string => {
    const date = new Date(viewMode.date)
    switch (viewMode.type) {
      case 'day':
        return date.toLocaleDateString('en-US', { 
          weekday: 'long', 
          year: 'numeric', 
          month: 'long', 
          day: 'numeric' 
        })
      case 'week':
        const startOfWeek = new Date(date)
        startOfWeek.setDate(date.getDate() - date.getDay())
        const endOfWeek = new Date(startOfWeek)
        endOfWeek.setDate(startOfWeek.getDate() + 6)
        return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
      case 'month':
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
      default:
        return date.toLocaleDateString()
    }
  }

  const renderTimeSlot = (slot: TimeSlot, dayData: AvailabilityData) => {
    const startTime = new Date(slot.start)
    const endTime = new Date(slot.end)
    const duration = (endTime.getTime() - startTime.getTime()) / (1000 * 60) // minutes
    
    const conflictCount = slot.conflicts?.length || 0
    const hasConflicts = conflictCount > 0

    return (
      <div
        key={`${slot.start}-${slot.end}`}
        className={`
          relative p-2 border rounded-md cursor-pointer transition-all duration-200
          ${slot.available 
            ? 'bg-green-50 border-green-200 hover:bg-green-100' 
            : hasConflicts 
              ? 'bg-red-50 border-red-200 hover:bg-red-100'
              : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
          }
        `}
        onClick={() => onTimeSlotClick?.(slot)}
        style={{ minHeight: `${Math.max(duration / 15 * 20, 40)}px` }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium">
              {startTime.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
              })}
            </span>
          </div>
          {hasConflicts && (
            <div className="flex items-center space-x-1">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <span className="text-xs text-red-600">{conflictCount}</span>
            </div>
          )}
        </div>
        
        {slot.conflicts && slot.conflicts.length > 0 && (
          <div className="mt-1 space-y-1">
            {slot.conflicts.slice(0, 2).map((conflict, idx) => (
              <div key={idx} className="text-xs text-red-600 truncate">
                {conflict.title}
              </div>
            ))}
            {slot.conflicts.length > 2 && (
              <div className="text-xs text-red-500">
                +{slot.conflicts.length - 2} more conflicts
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderEvent = (event: CalendarEvent) => {
    const startTime = new Date(event.start)
    const endTime = new Date(event.end)
    
    return (
      <div
        key={event.id}
        className={`
          p-3 border rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md
          ${event.createdByAgent 
            ? 'bg-blue-50 border-blue-200' 
            : event.provider === 'google' 
              ? 'bg-yellow-50 border-yellow-200'
              : 'bg-purple-50 border-purple-200'
          }
        `}
        onClick={() => onEventClick?.(event)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 truncate">{event.title}</h4>
            <div className="flex items-center space-x-2 mt-1">
              <Clock className="h-3 w-3 text-gray-500" />
              <span className="text-sm text-gray-600">
                {startTime.toLocaleTimeString('en-US', { 
                  hour: 'numeric', 
                  minute: '2-digit',
                  hour12: true 
                })} - {endTime.toLocaleTimeString('en-US', { 
                  hour: 'numeric', 
                  minute: '2-digit',
                  hour12: true 
                })}
              </span>
            </div>
            {event.attendees.length > 0 && (
              <div className="flex items-center space-x-1 mt-1">
                <Users className="h-3 w-3 text-gray-500" />
                <span className="text-xs text-gray-600">
                  {event.attendees.length} attendee{event.attendees.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
          <div className="flex flex-col items-end space-y-1">
            <span className={`
              px-2 py-1 text-xs rounded-full
              ${event.provider === 'google' 
                ? 'bg-yellow-100 text-yellow-800' 
                : 'bg-purple-100 text-purple-800'
              }
            `}>
              {event.provider}
            </span>
            {event.createdByAgent && (
              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                Agent
              </span>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    // Check if it's a network error (API offline)
    if (error.includes('Network Error') || error.includes('ERR_NAME_NOT_RESOLVED') || error.includes('Failed to fetch')) {
      return (
        <OfflineIndicator
          title="Calendar Data Unavailable"
          message="Unable to connect to the backend API. Calendar features will be available once the backend is deployed."
        />
      )
    }

    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <span className="text-red-700">Error loading calendar data: {error}</span>
        </div>
        <button
          onClick={fetchAvailabilityData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-gray-900">Calendar Timeline</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => navigateDate('prev')}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm font-medium text-gray-700 min-w-[200px] text-center">
              {formatDateRange()}
            </span>
            <button
              onClick={() => navigateDate('next')}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {(['day', 'week', 'month'] as const).map((type) => (
            <button
              key={type}
              onClick={() => onViewModeChange({ ...viewMode, type })}
              className={`
                px-3 py-1 text-sm rounded-md transition-colors capitalize
                ${viewMode.type === type 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline content */}
      <div className="grid gap-6">
        {viewMode.type === 'day' && availabilityData.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Availability slots */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Available Time Slots</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {availabilityData[0]?.timeSlots
                  .filter(slot => slot.available)
                  .map(slot => renderTimeSlot(slot, availabilityData[0]))}
              </div>
            </div>
            
            {/* Scheduled events */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Scheduled Events</h3>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {events.map(event => renderEvent(event))}
              </div>
            </div>
          </div>
        )}

        {viewMode.type === 'week' && (
          <div className="grid grid-cols-7 gap-2">
            {availabilityData.map((dayData, index) => (
              <div key={dayData.date} className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700 text-center">
                  {new Date(dayData.date).toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' })}
                </h4>
                <div className="space-y-1">
                  {dayData.timeSlots.slice(0, 8).map(slot => (
                    <div
                      key={`${slot.start}-${slot.end}`}
                      className={`
                        h-8 rounded text-xs flex items-center justify-center cursor-pointer
                        ${slot.available 
                          ? 'bg-green-100 text-green-800' 
                          : slot.conflicts && slot.conflicts.length > 0
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-600'
                        }
                      `}
                      onClick={() => onTimeSlotClick?.(slot)}
                    >
                      {new Date(slot.start).toLocaleTimeString('en-US', { 
                        hour: 'numeric',
                        hour12: true 
                      })}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {viewMode.type === 'month' && (
          <div className="grid grid-cols-7 gap-1">
            {/* Month view would show a simplified calendar grid */}
            {availabilityData.map((dayData, index) => (
              <div
                key={dayData.date}
                className="aspect-square border rounded p-1 hover:bg-gray-50 cursor-pointer"
                onClick={() => onViewModeChange({ type: 'day', date: dayData.date })}
              >
                <div className="text-sm font-medium">
                  {new Date(dayData.date).getDate()}
                </div>
                <div className="flex space-x-1 mt-1">
                  {dayData.conflicts.length > 0 && (
                    <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                  )}
                  {dayData.timeSlots.some(slot => slot.available) && (
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}