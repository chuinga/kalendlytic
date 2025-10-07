import React, { useState } from 'react'
import { AlertTriangle, Clock, Users, CheckCircle, XCircle, RefreshCw, Calendar } from 'lucide-react'
import { SchedulingConflict, ConflictResolution, CalendarEvent } from '@/types/calendar'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface ConflictResolverProps {
  conflicts: SchedulingConflict[]
  onResolveConflict: (conflictId: string, resolutionId: string) => Promise<void>
  onDismissConflict: (conflictId: string) => void
  onRefreshConflicts: () => Promise<void>
}

export function ConflictResolver({ 
  conflicts, 
  onResolveConflict, 
  onDismissConflict,
  onRefreshConflicts 
}: ConflictResolverProps) {
  const [expandedConflict, setExpandedConflict] = useState<string | null>(null)
  const [resolvingConflict, setResolvingConflict] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const getSeverityColor = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'low':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'medium':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getConflictTypeIcon = (type: string) => {
    switch (type) {
      case 'overlap':
        return <AlertTriangle className="h-4 w-4" />
      case 'back_to_back':
        return <Clock className="h-4 w-4" />
      case 'focus_block':
        return <Calendar className="h-4 w-4" />
      case 'outside_hours':
        return <Clock className="h-4 w-4" />
      default:
        return <AlertTriangle className="h-4 w-4" />
    }
  }

  const handleResolveConflict = async (conflictId: string, resolutionId: string) => {
    try {
      setResolvingConflict(conflictId)
      await onResolveConflict(conflictId, resolutionId)
    } catch (error) {
      console.error('Failed to resolve conflict:', error)
    } finally {
      setResolvingConflict(null)
    }
  }

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      await onRefreshConflicts()
    } catch (error) {
      console.error('Failed to refresh conflicts:', error)
    } finally {
      setRefreshing(false)
    }
  }

  const renderEvent = (event: CalendarEvent) => (
    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
      <div className={`
        w-3 h-3 rounded-full
        ${event.provider === 'google' ? 'bg-yellow-400' : 'bg-purple-400'}
      `} />
      <div className="flex-1">
        <div className="font-medium text-gray-900">{event.title}</div>
        <div className="text-sm text-gray-600">
          {new Date(event.start).toLocaleString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
          })} - {new Date(event.end).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
          })}
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
      <div className="text-right">
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
          <div className="mt-1">
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              Agent
            </span>
          </div>
        )}
      </div>
    </div>
  )

  const renderResolution = (resolution: ConflictResolution, conflictId: string) => (
    <div key={resolution.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="font-medium text-gray-900">{resolution.description}</span>
            <span className={`
              px-2 py-1 text-xs rounded-full
              ${resolution.confidence >= 0.8 
                ? 'bg-green-100 text-green-800' 
                : resolution.confidence >= 0.6
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
              }
            `}>
              {Math.round(resolution.confidence * 100)}% confidence
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{resolution.reasoning}</p>
          
          {resolution.proposedTimes && resolution.proposedTimes.length > 0 && (
            <div className="mt-3">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Proposed Times:</h5>
              <div className="space-y-1">
                {resolution.proposedTimes.slice(0, 3).map((time, idx) => (
                  <div key={idx} className="text-sm text-gray-600 flex items-center space-x-2">
                    <Clock className="h-3 w-3" />
                    <span>
                      {new Date(time.start).toLocaleString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true
                      })} - {new Date(time.end).toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true
                      })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex space-x-2 ml-4">
          <button
            onClick={() => handleResolveConflict(conflictId, resolution.id)}
            disabled={resolvingConflict === conflictId}
            className="flex items-center space-x-1 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {resolvingConflict === conflictId ? (
              <LoadingSpinner />
            ) : (
              <CheckCircle className="h-4 w-4" />
            )}
            <span>Apply</span>
          </button>
        </div>
      </div>
    </div>
  )

  if (conflicts.length === 0) {
    return (
      <div className="text-center py-8">
        <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Conflicts Detected</h3>
        <p className="text-gray-600">Your calendar is looking good! All meetings are properly scheduled.</p>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="mt-4 flex items-center space-x-2 mx-auto px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {refreshing ? <LoadingSpinner /> : <RefreshCw className="h-4 w-4" />}
          <span>Refresh</span>
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="h-6 w-6 text-red-500" />
          <h2 className="text-xl font-semibold text-gray-900">
            Scheduling Conflicts ({conflicts.length})
          </h2>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {refreshing ? <LoadingSpinner /> : <RefreshCw className="h-4 w-4" />}
          <span>Refresh</span>
        </button>
      </div>

      <div className="space-y-4">
        {conflicts.map((conflict) => (
          <div key={conflict.id} className={`border rounded-lg ${getSeverityColor(conflict.severity)}`}>
            <div 
              className="p-4 cursor-pointer"
              onClick={() => setExpandedConflict(
                expandedConflict === conflict.id ? null : conflict.id
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getConflictTypeIcon(conflict.type)}
                  <div>
                    <h3 className="font-medium text-gray-900">{conflict.description}</h3>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className={`
                        px-2 py-1 text-xs rounded-full font-medium
                        ${getSeverityColor(conflict.severity)}
                      `}>
                        {conflict.severity.toUpperCase()} PRIORITY
                      </span>
                      <span className="text-sm text-gray-600">
                        {conflict.conflictingEvents.length} event{conflict.conflictingEvents.length !== 1 ? 's' : ''} affected
                      </span>
                      <span className="text-sm text-gray-600">
                        {conflict.suggestedResolutions.length} solution{conflict.suggestedResolutions.length !== 1 ? 's' : ''} available
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDismissConflict(conflict.id)
                    }}
                    className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <XCircle className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            {expandedConflict === conflict.id && (
              <div className="border-t bg-white p-4 space-y-6">
                {/* Conflicting Events */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Conflicting Events</h4>
                  <div className="space-y-3">
                    {conflict.conflictingEvents.map((event) => renderEvent(event))}
                  </div>
                </div>

                {/* Suggested Resolutions */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Suggested Resolutions</h4>
                  <div className="space-y-3">
                    {conflict.suggestedResolutions.map((resolution) => 
                      renderResolution(resolution, conflict.id)
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}