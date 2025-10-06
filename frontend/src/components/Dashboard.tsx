import { useState } from 'react'
import { Calendar, Settings, Link, Activity } from 'lucide-react'

interface DashboardProps {
  user: any
  signOut: () => void
}

export default function Dashboard({ user, signOut }: DashboardProps) {
  const [activeTab, setActiveTab] = useState('dashboard')

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Calendar },
    { id: 'connect', label: 'Connect', icon: Link },
    { id: 'preferences', label: 'Preferences', icon: Settings },
    { id: 'logs', label: 'Agent Logs', icon: Activity },
  ]

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
              <span className="text-sm text-gray-700">
                Welcome, {user?.attributes?.email}
              </span>
              <button
                onClick={signOut}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Sign Out
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
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === 'dashboard' && (
            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Calendar Dashboard
              </h2>
              <p className="text-gray-600">
                Dashboard functionality will be implemented in task 8.3
              </p>
            </div>
          )}

          {activeTab === 'connect' && (
            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Connect Accounts
              </h2>
              <p className="text-gray-600">
                OAuth connection interface will be implemented in task 8.2
              </p>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Preferences & Settings
              </h2>
              <p className="text-gray-600">
                Preferences interface will be implemented in task 8.4
              </p>
            </div>
          )}

          {activeTab === 'logs' && (
            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Agent Decision Logs
              </h2>
              <p className="text-gray-600">
                Agent logs interface will be implemented in task 9.2
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}