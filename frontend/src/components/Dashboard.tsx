import { useState } from 'react'
import { useRouter } from 'next/router'
import { Calendar, Settings, Link, Activity, User, LogOut, Plus, Menu, X } from 'lucide-react'
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
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
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Mobile menu button */}
            <div className="flex items-center">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {isMobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
              
              {/* Logo */}
              <div className="flex items-center space-x-3 ml-2 md:ml-0">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-white" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-xl font-bold text-gray-900">Kalendlytic</h1>
                </div>
              </div>
            </div>

            {/* Right side - User info and actions */}
            <div className="flex items-center space-x-3">
              <ConnectionStatus />
              
              {/* User Info - Hidden on mobile */}
              <div className="hidden lg:flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.attributes?.name || 'User'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {user?.email || user?.attributes?.email}
                  </p>
                </div>
              </div>

              {/* User Avatar */}
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-gray-600" />
              </div>

              {/* Settings - Hidden on mobile */}
              <button
                onClick={() => router.push('/profile')}
                className="hidden md:flex p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
              >
                <Settings className="h-5 w-5" />
              </button>

              {/* Logout */}
              <button
                onClick={async () => {
                  try {
                    await logout()
                    router.push('/login')
                  } catch (error) {
                    console.error('Logout failed:', error)
                  }
                }}
                className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Navigation Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setIsMobileMenuOpen(false)} />
          <div className="fixed top-0 left-0 bottom-0 w-64 bg-white shadow-xl">
            <div className="p-4">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 text-gray-600 hover:text-gray-900"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              
              <nav className="space-y-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon
                  const isActive = activeTab === tab.id
                  return (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setActiveTab(tab.id)
                        setIsMobileMenuOpen(false)
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg font-medium text-sm transition-colors ${
                        isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{tab.label}</span>
                    </button>
                  )
                })}
              </nav>

              {/* Mobile User Info */}
              <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {user?.attributes?.name || 'User'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {user?.email || user?.attributes?.email}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    router.push('/profile')
                    setIsMobileMenuOpen(false)
                  }}
                  className="mt-3 w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
                >
                  <Settings className="h-4 w-4" />
                  <span>Settings</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex max-w-7xl mx-auto">
        {/* Desktop Sidebar */}
        <aside className="hidden md:flex w-64 flex-shrink-0">
          <nav className="w-full p-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="space-y-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon
                  const isActive = activeTab === tab.id
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg font-medium text-sm transition-colors ${
                        isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{tab.label}</span>
                    </button>
                  )
                })}
              </div>
              
              {/* Quick Stats */}
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Today's Overview</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">Meetings</span>
                    <span className="text-sm font-bold text-blue-600">3</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">Conflicts</span>
                    <span className="text-sm font-bold text-red-600">{conflicts.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">Free Time</span>
                    <span className="text-sm font-bold text-green-600">4h</span>
                  </div>
                </div>
              </div>
            </div>
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 p-4 md:p-6">

          {/* Tab Content */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {activeTab === 'dashboard' && (
              <div className="p-6 space-y-6">
                {/* Dashboard Header with Actions */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      Calendar Dashboard
                    </h2>
                    <p className="text-gray-600 mt-1">Manage your meetings with AI assistance</p>
                  </div>
                  <button
                    onClick={() => setShowMeetingScheduler(true)}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Plus className="h-5 w-5" />
                    <span>Schedule Meeting</span>
                  </button>
                </div>

                {/* Stats Cards Row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-blue-600 text-sm font-medium">Today's Meetings</p>
                        <p className="text-2xl font-bold text-blue-800">3</p>
                      </div>
                      <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                        <Calendar className="w-5 h-5 text-white" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-red-600 text-sm font-medium">Active Conflicts</p>
                        <p className="text-2xl font-bold text-red-800">{conflicts.length}</p>
                      </div>
                      <div className="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center">
                        <Activity className="w-5 h-5 text-white" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200 sm:col-span-2 lg:col-span-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-green-600 text-sm font-medium">Free Time</p>
                        <p className="text-2xl font-bold text-green-800">4h 30m</p>
                      </div>
                      <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                        <User className="w-5 h-5 text-white" />
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
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    Connect Your Calendars
                  </h2>
                  <p className="text-gray-600 mt-1">Link your Google and Microsoft accounts for seamless scheduling</p>
                </div>
                <ConnectionsPage />
              </div>
            )}

            {activeTab === 'preferences' && (
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    Preferences & Settings
                  </h2>
                  <p className="text-gray-600 mt-1">Customize your AI assistant's behavior and scheduling rules</p>
                </div>
                <PreferencesPage />
              </div>
            )}

            {activeTab === 'logs' && (
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    Agent Decision Logs
                  </h2>
                  <p className="text-gray-600 mt-1">Review your AI assistant's decisions and reasoning</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-8 border border-blue-200 text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <Activity className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Coming Soon</h3>
                  <p className="text-gray-600">
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