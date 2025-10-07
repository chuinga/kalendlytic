import { useState } from 'react'
import { Clock, AlertCircle } from 'lucide-react'
import { WeeklyWorkingHours, WorkingHours } from '@/types/preferences'
import { PreferencesService } from '@/utils/preferences'

interface WorkingHoursFormProps {
  workingHours: WeeklyWorkingHours
  timezone: string
  onUpdate: (updates: { workingHours?: WeeklyWorkingHours; timezone?: string }) => void
}

export function WorkingHoursForm({ workingHours, timezone, onUpdate }: WorkingHoursFormProps) {
  const [errors, setErrors] = useState<Record<string, string>>({})

  const days = [
    { key: 'monday', label: 'Monday' },
    { key: 'tuesday', label: 'Tuesday' },
    { key: 'wednesday', label: 'Wednesday' },
    { key: 'thursday', label: 'Thursday' },
    { key: 'friday', label: 'Friday' },
    { key: 'saturday', label: 'Saturday' },
    { key: 'sunday', label: 'Sunday' }
  ] as const

  const timezones = PreferencesService.getTimezones()

  const validateTime = (day: string, start: string, end: string) => {
    const newErrors = { ...errors }
    const errorKey = `${day}-time`

    if (!PreferencesService.validateWorkingHours(start, end)) {
      newErrors[errorKey] = 'End time must be after start time'
    } else {
      delete newErrors[errorKey]
    }

    setErrors(newErrors)
  }

  const updateDayHours = (day: keyof WeeklyWorkingHours, hours: WorkingHours) => {
    validateTime(day, hours.start, hours.end)
    
    const newWorkingHours = {
      ...workingHours,
      [day]: hours
    }
    onUpdate({ workingHours: newWorkingHours })
  }

  const updateTimezone = (newTimezone: string) => {
    onUpdate({ timezone: newTimezone })
  }

  const applyToAllDays = (hours: WorkingHours) => {
    const newWorkingHours = { ...workingHours }
    days.forEach(day => {
      newWorkingHours[day.key] = { ...hours }
    })
    onUpdate({ workingHours: newWorkingHours })
  }

  const applyToWeekdays = (hours: WorkingHours) => {
    const weekdays: (keyof WeeklyWorkingHours)[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    const newWorkingHours = { ...workingHours }
    weekdays.forEach(day => {
      newWorkingHours[day] = { ...hours }
    })
    onUpdate({ workingHours: newWorkingHours })
  }

  const applyToWeekends = (hours: WorkingHours) => {
    const weekends: (keyof WeeklyWorkingHours)[] = ['saturday', 'sunday']
    const newWorkingHours = { ...workingHours }
    weekends.forEach(day => {
      newWorkingHours[day] = { ...hours }
    })
    onUpdate({ workingHours: newWorkingHours })
  }

  return (
    <div className="space-y-8">
      {/* Timezone Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Timezone
        </label>
        <select
          value={timezone}
          onChange={(e) => updateTimezone(e.target.value)}
          className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          {timezones.map((tz) => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
        <p className="mt-1 text-sm text-gray-500">
          Your timezone affects when meetings can be scheduled and how times are displayed.
        </p>
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => applyToAllDays({ start: '09:00', end: '17:00' })}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
          >
            Set All Days: 9 AM - 5 PM
          </button>
          <button
            onClick={() => applyToWeekdays({ start: '09:00', end: '17:00' })}
            className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
          >
            Set Weekdays: 9 AM - 5 PM
          </button>
          <button
            onClick={() => applyToWeekends({ start: '10:00', end: '14:00' })}
            className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors"
          >
            Set Weekends: 10 AM - 2 PM
          </button>
        </div>
      </div>

      {/* Daily Working Hours */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-4">Daily Working Hours</h3>
        <div className="space-y-4">
          {days.map((day) => {
            const dayHours = workingHours[day.key]
            const errorKey = `${day.key}-time`
            const hasError = errors[errorKey]

            return (
              <div key={day.key} className="flex items-center space-x-4">
                <div className="w-24 text-sm font-medium text-gray-700">
                  {day.label}
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <input
                    type="time"
                    value={dayHours.start}
                    onChange={(e) => updateDayHours(day.key, { ...dayHours, start: e.target.value })}
                    className={`px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                      hasError ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="time"
                    value={dayHours.end}
                    onChange={(e) => updateDayHours(day.key, { ...dayHours, end: e.target.value })}
                    className={`px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                      hasError ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                </div>
                {hasError && (
                  <div className="flex items-center space-x-1 text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">{errors[errorKey]}</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">
          About Working Hours
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Meetings will only be scheduled during your working hours unless you override this setting</li>
          <li>• The AI agent will respect these hours when proposing meeting times</li>
          <li>• You can set different hours for each day of the week</li>
          <li>• Times are displayed in your selected timezone</li>
        </ul>
      </div>
    </div>
  )
}