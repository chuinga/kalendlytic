import { useState } from 'react'
import { useRouter } from 'next/router'
import { Calendar, Settings, Link, Activity, User, LogOut, Plus } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { ConnectionStatus } from '@/components/connections/ConnectionStatus'
import { ConnectionsPage } from '@/components/connections/ConnectionsPage'
import { AvailabilityTimeline, ConflictResolver, MeetingScheduler, AgentActionReview } from '@/components/calendar'
import { PreferencesPage } from '@/components/preferences'
import { CalendarViewMode, SchedulingConflict, MeetingRequest, AgentAction } from '@/types/calendar'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'

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
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
      {/* Glassmorphism Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-white/20 shadow-soft">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo with subtle animation */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg animate-float">
                <Calendar className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-neutral-800">Meeting Scheduler</h1>
                <p className="text-xs text-neutral-500">AI-Powered Assistant</p>
              </div>
            </div>

            {/* User Profile with Status Indicator */}
            <div className="flex items-center space-x-4">
              <ConnectionStatus />
              
              {/* User Info */}
              <div className="hidden md:flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-neutral-800">
                    {user?.attributes?.name || 'User'}
                  </p>
                  <p className="text-xs text-neutral-500">
                    {user?.email || user?.attributes?.email}
                  </p>
                </div>
                <Avatar
                  name={user?.attributes?.name || user?.email || 'User'}
                  size="md"
                  status="online"
                  showStatus={true}
                  className="cursor-pointer"
                  onClick={() => router.push('/profile')}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/profile')}
                  className="p-2 hover:bg-primary-50 hover:text-primary-600"
                >
                  <Settings className="h-5 w-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    try {
                      await logout()
                      router.push('/login')
                    } catch (error) {
                      console.error('Logout failed:', error)
                    }
                  }}
                  className="p-2 hover:bg-red-50 hover:text-error"
                >
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content with Sidebar Layout */}
      <div className="flex max-w-7xl mx-auto px-6 py-8 gap-8">
        {/* Floating Sidebar Navigation */}
        <aside className="w-64 flex-shrink-0">
          <nav className="bg-white/60 backdrop-blur-xl rounded-2xl shadow-soft border border-white/20 p-4 sticky top-24">
            <div className="space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 transform hover:scale-[1.02] ${
                      isActive
                        ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg'
                        : 'text-neutral-600 hover:text-primary-600 hover:bg-primary-50'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{tab.label}</span>
                    {isActive && (
                      <div className="ml-auto w-2 h-2 bg-white rounded-full animate-pulse"></div>
                    )}
                  </button>
                )
              })}
            </div>
            
            {/* Quick Stats in Sidebar */}
            <div className="mt-8 p-4 bg-gradient-to-br from-primary-50 to-accent-50 rounded-xl border border-primary-100">
              <h3 className="text-sm font-semibold text-neutral-700 mb-3">Today's Overview</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-neutral-600">Meetings</span>
                  <span className="text-sm font-bold text-primary-600">3</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-neutral-600">Conflicts</span>
                  <span className="text-sm font-bold text-accent-600">{conflicts.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-neutral-600">Free Time</span>
                  <span className="text-sm font-bold text-success">4h</span>
                </div>
              </div>
            </div>
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0">

          {/* Tab Content */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-large border border-white/20 animate-slideInUp">
            {activeTab === 'dashboard' && (
              <div className="p-8 space-y-8">
                {/* Dashboard Header with Actions */}
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-neutral-800 to-neutral-600 bg-clip-text text-transparent">
                      Calendar Dashboard
                    </h2>
                    <p className="text-neutral-600 mt-1">Manage your meetings with AI assistance</p>
                  </div>
                  <Button
                    onClick={() => setShowMeetingScheduler(true)}
                    variant="primary"
                    size="lg"
                    className="shadow-lg hover:shadow-xl"
                  >
                    <Plus className="h-5 w-5 mr-2" />
                    Schedule Meeting
                  </Button>
                </div>

                {/* Stats Cards Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl p-6 border border-primary-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-primary-600 text-sm font-medium">Today's Meetings</p>
                        <p className="text-2xl font-bold text-primary-800">3</p>
                      </div>
                      <div className="w-12 h-12 bg-primary-500 rounded-xl flex items-center justify-center">
                        <Calendar className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-accent-50 to-accent-100 rounded-2xl p-6 border border-accent-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-accent-600 text-sm font-medium">Active Conflicts</p>
                        <p className="text-2xl font-bold text-accent-800">{conflicts.length}</p>
                      </div>
                      <div className="w-12 h-12 bg-accent-500 rounded-xl flex items-center justify-center">
                        <Activity className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-6 border border-green-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-green-600 text-sm font-medium">Free Time</p>
                        <p className="text-2xl font-bold text-green-800">4h 30m</p>
                      </div>
                      <div className="w-12 h-12 bg-success rounded-xl flex items-center justify-center">
                        <User className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Conflicts Section */}
                {conflicts.length > 0 && (
                  <div className="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-error rounded-2xl p-6 shadow-soft animate-slideInUp">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-8 h-8 bg-error rounded-lg flex items-center justify-center">
                        <Activity className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-error">Scheduling Conflicts Detected</h3>
                        <p className="text-sm text-red-600">AI assistant found {conflicts.length} conflicts that need your attention</p>
                      </div>
                    </div>
                    <ConflictResolver
                      conflicts={conflicts}
                      onResolveConflict={handleResolveConflict}
                      onDismissConflict={handleDismissConflict}
                      onRefreshConflicts={handleRefreshConflicts}
                    />
                  </div>
                )}

                {/* Calendar Timeline */}
                <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-white/40 shadow-medium">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-semibold text-neutral-800">Your Schedule</h3>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setViewMode({ ...viewMode, type: 'day' })}
                        className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                          viewMode.type === 'day'
                            ? 'bg-primary-500 text-white shadow-md'
                            : 'text-neutral-600 hover:bg-primary-50 hover:text-primary-600'
                        }`}
                      >
                        Day
                      </button>
                      <button
                        onClick={() => setViewMode({ ...viewMode, type: 'week' })}
                        className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                          viewMode.type === 'week'
                            ? 'bg-primary-500 text-white shadow-md'
                            : 'text-neutral-600 hover:bg-primary-50 hover:text-primary-600'
                        }`}
                      >
                        Week
                      </button>
                      <button
                        onClick={() => setViewMode({ ...viewMode, type: 'month' })}
                        className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                          viewMode.type === 'month'
                            ? 'bg-primary-500 text-white shadow-md'
                            : 'text-neutral-600 hover:bg-primary-50 hover:text-primary-600'
                        }`}
                      >
                        Month
                      </button>
                    </div>
                  </div>
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
              <div className="p-8">
                <div className="mb-6">
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-neutral-800 to-neutral-600 bg-clip-text text-transparent">
                    Connect Your Calendars
                  </h2>
                  <p className="text-neutral-600 mt-1">Link your Google and Microsoft accounts for seamless scheduling</p>
                </div>
                <ConnectionsPage />
              </div>
            )}

            {activeTab === 'preferences' && (
              <div className="p-8">
                <div className="mb-6">
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-neutral-800 to-neutral-600 bg-clip-text text-transparent">
                    Preferences & Settings
                  </h2>
                  <p className="text-neutral-600 mt-1">Customize your AI assistant's behavior and scheduling rules</p>
                </div>
                <PreferencesPage />
              </div>
            )}

            {activeTab === 'logs' && (
              <div className="p-8">
                <div className="mb-6">
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-neutral-800 to-neutral-600 bg-clip-text text-transparent">
                    Agent Decision Logs
                  </h2>
                  <p className="text-neutral-600 mt-1">Review your AI assistant's decisions and reasoning</p>
                </div>
                <div className="bg-gradient-to-br from-primary-50 to-accent-50 rounded-2xl p-8 border border-primary-100 text-center">
                  <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Activity className="w-8 h-8 text-primary-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-neutral-800 mb-2">Coming Soon</h3>
                  <p className="text-neutral-600">
                    Agent logs interface will be implemented in the next phase
                  </p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Meeting Scheduler Modal */}
      {showMeetingScheduler && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-scaleIn">
            <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20">
              <MeetingScheduler
                onScheduleMeeting={handleScheduleMeeting}
                onClose={() => setShowMeetingScheduler(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}