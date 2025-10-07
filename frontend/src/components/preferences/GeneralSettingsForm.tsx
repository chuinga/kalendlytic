import { Bell, Shield, Clock, Mail, AlertTriangle } from 'lucide-react'
import { UserPreferences } from '@/types/preferences'

interface GeneralSettingsFormProps {
  preferences: UserPreferences
  onUpdate: (updates: Partial<UserPreferences>) => void
}

export function GeneralSettingsForm({ preferences, onUpdate }: GeneralSettingsFormProps) {
  return (
    <div className="space-y-8">
      {/* Buffer Time Settings */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
          <Clock className="h-5 w-5" />
          <span>Buffer Time Settings</span>
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Buffer Time (minutes)
            </label>
            <input
              type="number"
              min="0"
              max="60"
              value={preferences.defaultBufferMinutes}
              onChange={(e) => onUpdate({ defaultBufferMinutes: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Default buffer time added to meetings when no specific buffer is set
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Buffer Between Meetings (minutes)
            </label>
            <input
              type="number"
              min="0"
              max="30"
              value={preferences.bufferBetweenMeetings}
              onChange={(e) => onUpdate({ bufferBetweenMeetings: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Minimum time between consecutive meetings to prevent back-to-back scheduling
            </p>
          </div>
        </div>
      </div>

      {/* Agent Behavior Settings */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
          <Shield className="h-5 w-5" />
          <span>Agent Behavior</span>
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="autoBookEnabled"
              checked={preferences.autoBookEnabled}
              onChange={(e) => onUpdate({ autoBookEnabled: e.target.checked })}
              className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div>
              <label htmlFor="autoBookEnabled" className="text-sm font-medium text-gray-700">
                Enable Automatic Booking
              </label>
              <p className="text-sm text-gray-500">
                Allow the AI agent to automatically book meetings without requiring approval for each one
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="autoSendEmails"
              checked={preferences.autoSendEmails}
              onChange={(e) => onUpdate({ autoSendEmails: e.target.checked })}
              className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div>
              <label htmlFor="autoSendEmails" className="text-sm font-medium text-gray-700">
                Auto-send Email Invitations
              </label>
              <p className="text-sm text-gray-500">
                Automatically send meeting invitations and updates without manual approval
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="requireApprovalForRescheduling"
              checked={preferences.requireApprovalForRescheduling}
              onChange={(e) => onUpdate({ requireApprovalForRescheduling: e.target.checked })}
              className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div>
              <label htmlFor="requireApprovalForRescheduling" className="text-sm font-medium text-gray-700">
                Require Approval for Rescheduling
              </label>
              <p className="text-sm text-gray-500">
                Always ask for approval before rescheduling existing meetings
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Meeting Limits */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5" />
          <span>Meeting Limits</span>
        </h3>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Maximum Meetings Per Day
          </label>
          <div className="flex items-center space-x-4">
            <input
              type="number"
              min="1"
              max="20"
              value={preferences.maxMeetingsPerDay || ''}
              onChange={(e) => onUpdate({ maxMeetingsPerDay: parseInt(e.target.value) || undefined })}
              className="w-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="No limit"
            />
            <span className="text-sm text-gray-500">
              Leave empty for no limit
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            The AI agent will avoid scheduling more than this number of meetings in a single day
          </p>
        </div>
      </div>

      {/* Notification Preferences */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
          <Bell className="h-5 w-5" />
          <span>Notifications</span>
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="emailNotifications"
              checked={preferences.emailNotifications}
              onChange={(e) => onUpdate({ emailNotifications: e.target.checked })}
              className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div>
              <label htmlFor="emailNotifications" className="text-sm font-medium text-gray-700">
                Email Notifications
              </label>
              <p className="text-sm text-gray-500">
                Receive email notifications about agent actions and meeting updates
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="conflictAlerts"
              checked={preferences.conflictAlerts}
              onChange={(e) => onUpdate({ conflictAlerts: e.target.checked })}
              className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div>
              <label htmlFor="conflictAlerts" className="text-sm font-medium text-gray-700">
                Conflict Alerts
              </label>
              <p className="text-sm text-gray-500">
                Get notified immediately when scheduling conflicts are detected
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="dailySummary"
              checked={preferences.dailySummary}
              onChange={(e) => onUpdate({ dailySummary: e.target.checked })}
              className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div>
              <label htmlFor="dailySummary" className="text-sm font-medium text-gray-700">
                Daily Summary
              </label>
              <p className="text-sm text-gray-500">
                Receive a daily summary of your schedule and any agent actions taken
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Security & Privacy */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
          <Shield className="h-5 w-5" />
          <span>Security & Privacy</span>
        </h3>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <h4 className="text-sm font-medium text-yellow-800">
                Important Security Information
              </h4>
              <div className="mt-2 text-sm text-yellow-700">
                <ul className="list-disc list-inside space-y-1">
                  <li>The AI agent only accesses calendar data you've explicitly connected</li>
                  <li>All meeting data is encrypted in transit and at rest</li>
                  <li>You can revoke calendar access at any time from the Connections page</li>
                  <li>The agent never shares your calendar data with third parties</li>
                  <li>All automated actions can be reviewed and reversed if needed</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">
          Tips for Optimal Agent Performance
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Start with conservative settings and gradually enable more automation as you build trust</li>
          <li>• Review agent actions regularly to ensure they align with your preferences</li>
          <li>• Use buffer times to prevent back-to-back meetings and allow for travel time</li>
          <li>• Set meeting limits to maintain work-life balance</li>
          <li>• Enable notifications to stay informed about agent decisions</li>
        </ul>
      </div>
    </div>
  )
}