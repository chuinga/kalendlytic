import { useState } from 'react'
import { useRouter } from 'next/router'
import { Calendar, Settings, Link, Activity, User, LogOut, Plus } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { ConnectionStatus } from '@/components/connections/ConnectionStatus'
import { ConnectionsPage } from '@/components/connections/ConnectionsPage'
import { AvailabilityTimeline, ConflictResolver, MeetingScheduler, AgentActionReview } from '@/components/calendar'
import { CalendarViewMode, SchedulingConflict, MeetingRequest, AgentAction } from '@/types/calendar'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState('dashboard')
  const [showMeetingScheduler, setShowMeetingScheduler] = useState(false)
  const [viewMode, setViewMode] = useState<CalendarViewMode>({
    type: 'week',
    date: new Date().toISOString().split('T')[0]
  })
  const [conflicts, setConflicts] = useState<SchedulingConflict[]>([])
  const [refreshingConflicts, setRefreshingConflicts] = useState(false)

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Calendar },
    { id: 'connect', label: 'Connect', icon: Link },
    { id: 'preferences', label: 'Preferences', icon: Settings },
    { id: 'logs', label: 'Agent Logs', icon: Activity },
  ]

  // Handler functions for calendar operations
  const handleScheduleMeeting = async (request: MeetingRequest) => {
    try {
      const response = await fetch('/api/calendar/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      })
      
      if (!response.ok) {
        throw new Error('Failed to schedule meeting')
      }
      
      // Refresh conflicts after scheduling
      await handleRefreshConflicts()
    } catch (error) {
      console.error('Failed to schedule meeting:', error)
      throw error
    }
  }

  const handleResolveConflict = async (conflictId: string, resolutionId: string) => {
    try {
      const response = await fetch(`/api/calendar/conflicts/${conflictId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolutionId })
      })
      
      if (!response.ok) {
        throw new Error('Failed to resolve conflict')
      }
      
      // Remove resolved conflict from state
      setConflicts(prev => prev.filter(c => c.id !== conflictId))
    } catch (error) {
      console.error('Failed to resolve conflict:', error)
      throw error
    }
  }

  const handleDismissConflict = (conflictId: string) => {
    setConflicts(prev => prev.filter(c => c.id !== conflictId))
  }

  const handleRefreshConflicts = async () => {
    try {
      setRefreshingConflicts(true)
      const response = await fetch('/api/calendar/conflicts')
      if (response.ok) {
        const conflictsData = await response.json()
        setConflicts(conflictsData)
      }
    } catch (error) {
      console.error('Failed to refresh conflicts:', error)
    } finally {
      setRefreshingConflicts(false)
    }
  }

  const handleApproveAction = async (actionId: string) => {
    try {
      const response = await fetch(`/api/agent/actions/${actionId}/approve`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to approve action')
      }
    } catch (error) {
      console.error('Failed to approve action:', error)
      throw error
    }
  }

  const handleRejectAction = async (actionId: string, feedback?: string) => {
    try {
      const response = await fetch(`/api/agent/actions/${actionId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback })
      })
      
      if (!response.ok) {
        throw new Error('Failed to reject action')
      }
    } catch (error) {
      console.error('Failed to reject action:', error)
      throw error
    }
  }

  const handleRefreshActions = async () => {
    // This will be handled by the AgentActionReview component
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Meeting Scheduling Agent
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <ConnectionStatus />
              <span className="text-sm text-gray-700">
                Welcome, {user?.email || user?.attributes?.email}
              </span>
              <button
                onClick={() => router.push('/profile')}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition duration-200"
              >
                <User className="h-4 w-4" />
                <span>Profile</span>
              </button>
              <button
                onClick={async () => {
                  try {
                    await logout()
                    router.push('/login')
                  } catch (error) {
                    console.error('Logout failed:', error)
                  }
                }}
                className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-200"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow">
          {activeTab === 'dashboard' && (
            <div className="p-6 space-y-8">
              {/* Dashboard Header with Actions */}
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-semibold text-gray-900">
                  Calendar Dashboard
                </h2>
                <button
                  onClick={() => setShowMeetingScheduler(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  <span>Schedule Meeting</span>
                </button>
              </div>

              {/* Conflicts Section */}
              {conflicts.length > 0 && (
                <div className="border-l-4 border-red-400 bg-red-50 p-4 rounded-r-lg">
                  <ConflictResolver
                    conflicts={conflicts}
                    onResolveConflict={handleResolveConflict}
                    onDismissConflict={handleDismissConflict}
                    onRefreshConflicts={handleRefreshConflicts}
                  />
                </div>
              )}

              {/* Calendar Timeline */}
              <div>
                <AvailabilityTimeline
                  viewMode={viewMode}
                  onViewModeChange={setViewMode}
                  onTimeSlotClick={(slot) => {
                    // Could open meeting scheduler with pre-selected time
                    console.log('Time slot clicked:', slot)
                  }}
                  onEventClick={(event) => {
                    // Could open event details modal
                    console.log('Event clicked:', event)
                  }}
                />
              </div>

              {/* Agent Actions Review */}
              <div className="border-t pt-8">
                <AgentActionReview
                  onApproveAction={handleApproveAction}
                  onRejectAction={handleRejectAction}
                  onRefreshActions={handleRefreshActions}
                />
              </div>
            </div>
          )}

          {activeTab === 'connect' && (
            <div className="-m-6">
              <ConnectionsPage />
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Preferences & Settings
              </h2>
              <p className="text-gray-600">
                Preferences interface will be implemented in task 8.4
              </p>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Agent Decision Logs
              </h2>
              <p className="text-gray-600">
                Agent logs interface will be implemented in task 9.2
              </p>
            </div>
          )}
        </div>

        {/* Meeting Scheduler Modal */}
        {showMeetingScheduler && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <MeetingScheduler
                onScheduleMeeting={handleScheduleMeeting}
                onClose={() => setShowMeetingScheduler(false)}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}