import { useState } from 'react'
import { Save, RotateCcw, AlertCircle, CheckCircle, Clock, Users, Calendar, Settings, Bell } from 'lucide-react'
import { usePreferences, usePreferencesForm } from '@/hooks/usePreferences'
import { WorkingHoursForm } from './WorkingHoursForm'
import { VIPContactsForm } from './VIPContactsForm'
import { MeetingTypesForm } from './MeetingTypesForm'
import { FocusBlocksForm } from './FocusBlocksForm'
import { PriorityRulesForm } from './PriorityRulesForm'
import { GeneralSettingsForm } from './GeneralSettingsForm'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export function PreferencesPage() {
  const {
    preferences,
    isLoading,
    error,
    isUpdating,
    updateError,
    updatePreferences,
    resetPreferences
  } = usePreferences()

  const {
    formData,
    hasChanges,
    updateFormData,
    resetForm,
    getChanges
  } = usePreferencesForm(preferences)

  const [activeSection, setActiveSection] = useState('working-hours')
  const [saveSuccess, setSaveSuccess] = useState(false)

  const sections = [
    { id: 'working-hours', label: 'Working Hours', icon: Clock },
    { id: 'vip-contacts', label: 'VIP Contacts', icon: Users },
    { id: 'meeting-types', label: 'Meeting Types', icon: Calendar },
    { id: 'focus-blocks', label: 'Focus Blocks', icon: Calendar },
    { id: 'priority-rules', label: 'Priority Rules', icon: Settings },
    { id: 'general', label: 'General Settings', icon: Bell }
  ]

  const handleSave = async () => {
    const changes = getChanges()
    if (!changes) return

    const success = await updatePreferences(changes)
    if (success) {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  }

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset all preferences to defaults? This action cannot be undone.')) {
      const success = await resetPreferences()
      if (success) {
        resetForm()
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Failed to load preferences
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {error instanceof Error ? error.message : 'An unexpected error occurred'}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!formData) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="flex h-full">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Preferences & Settings
        </h2>
        <nav className="space-y-2">
          {sections.map((section) => {
            const Icon = section.icon
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeSection === section.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{section.label}</span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header with Save Actions */}
        <div className="border-b border-gray-200 bg-white px-6 py-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              {sections.find(s => s.id === activeSection)?.label}
            </h3>
            <div className="flex items-center space-x-3">
              {saveSuccess && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm">Saved successfully</span>
                </div>
              )}
              {updateError && (
                <div className="flex items-center space-x-2 text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm">Save failed</span>
                </div>
              )}
              <button
                onClick={handleReset}
                disabled={isUpdating}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Reset to Defaults</span>
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || isUpdating}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUpdating ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                <span>{isUpdating ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeSection === 'working-hours' && (
            <WorkingHoursForm
              workingHours={formData.workingHours}
              timezone={formData.timezone}
              onUpdate={(updates) => updateFormData(updates)}
            />
          )}

          {activeSection === 'vip-contacts' && (
            <VIPContactsForm
              vipContacts={formData.vipContacts}
              onUpdate={(vipContacts) => updateFormData({ vipContacts })}
            />
          )}

          {activeSection === 'meeting-types' && (
            <MeetingTypesForm
              meetingTypes={formData.meetingTypes}
              defaultMeetingDuration={formData.defaultMeetingDuration}
              onUpdate={(updates) => updateFormData(updates)}
            />
          )}

          {activeSection === 'focus-blocks' && (
            <FocusBlocksForm
              focusBlocks={formData.focusBlocks}
              onUpdate={(focusBlocks) => updateFormData({ focusBlocks })}
            />
          )}

          {activeSection === 'priority-rules' && (
            <PriorityRulesForm
              priorityRules={formData.priorityRules}
              onUpdate={(priorityRules) => updateFormData({ priorityRules })}
            />
          )}

          {activeSection === 'general' && (
            <GeneralSettingsForm
              preferences={formData}
              onUpdate={(updates) => updateFormData(updates)}
            />
          )}
        </div>
      </div>
    </div>
  )
}