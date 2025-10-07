import { useState } from 'react'
import { useRouter } from 'next/router'
import { Calendar, Settings, Link, Activity, User, LogOut } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { ConnectionStatus } from '@/components/connections/ConnectionStatus'
import { ConnectionsPage } from '@/components/connections/ConnectionsPage'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
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
            <div className="-m-6">
              <ConnectionsPage />
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