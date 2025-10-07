import React, { useState, useEffect } from 'react'
import { Calendar, Clock, Users, MapPin, Video, Send, Plus, X } from 'lucide-react'
import { MeetingRequest, TimeSlot, AvailabilityQuery } from '@/types/calendar'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface MeetingSchedulerProps {
  onScheduleMeeting: (request: MeetingRequest) => Promise<void>
  onClose?: () => void
  initialData?: Partial<MeetingRequest>
}

export function MeetingScheduler({ onScheduleMeeting, onClose, initialData }: MeetingSchedulerProps) {
  const [formData, setFormData] = useState<MeetingRequest>({
    title: '',
    description: '',
    attendees: [],
    duration: 30,
    location: '',
    requiresVideoConference: true,
    priority: 'medium',
    meetingType: '',
    ...initialData
  })
  
  const [newAttendee, setNewAttendee] = useState('')
  const [suggestedTimes, setSuggestedTimes] = useState<TimeSlot[]>([])
  const [selectedTimeSlots, setSelectedTimeSlots] = useState<TimeSlot[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (formData.attendees.length > 0 && formData.duration > 0) {
      fetchSuggestedTimes()
    }
  }, [formData.attendees, formData.duration])

  const fetchSuggestedTimes = async () => {
    try {
      setLoadingSuggestions(true)
      
      const query: AvailabilityQuery = {
        startDate: new Date().toISOString().split('T')[0],
        endDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Next 2 weeks
        attendees: formData.attendees,
        minDuration: formData.duration,
        workingHoursOnly: true
      }
      
      const response = await fetch('/api/calendar/suggest-times', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(query)
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch suggested times')
      }
      
      const suggestions = await response.json()
      setSuggestedTimes(suggestions.slice(0, 10)) // Show top 10 suggestions
    } catch (error) {
      console.error('Failed to fetch suggested times:', error)
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}
    
    if (!formData.title.trim()) {
      newErrors.title = 'Meeting title is required'
    }
    
    if (formData.attendees.length === 0) {
      newErrors.attendees = 'At least one attendee is required'
    }
    
    if (formData.duration < 15) {
      newErrors.duration = 'Meeting duration must be at least 15 minutes'
    }
    
    if (selectedTimeSlots.length === 0 && suggestedTimes.length > 0) {
      newErrors.timeSlots = 'Please select at least one preferred time slot'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    try {
      setSubmitting(true)
      
      const meetingRequest: MeetingRequest = {
        ...formData,
        preferredTimes: selectedTimeSlots.length > 0 ? selectedTimeSlots : suggestedTimes.slice(0, 3)
      }
      
      await onScheduleMeeting(meetingRequest)
      onClose?.()
    } catch (error) {
      console.error('Failed to schedule meeting:', error)
      setErrors({ submit: 'Failed to schedule meeting. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  const addAttendee = () => {
    if (newAttendee.trim() && !formData.attendees.includes(newAttendee.trim())) {
      setFormData(prev => ({
        ...prev,
        attendees: [...prev.attendees, newAttendee.trim()]
      }))
      setNewAttendee('')
    }
  }

  const removeAttendee = (email: string) => {
    setFormData(prev => ({
      ...prev,
      attendees: prev.attendees.filter(a => a !== email)
    }))
  }

  const toggleTimeSlot = (slot: TimeSlot) => {
    setSelectedTimeSlots(prev => {
      const exists = prev.some(s => s.start === slot.start && s.end === slot.end)
      if (exists) {
        return prev.filter(s => !(s.start === slot.start && s.end === slot.end))
      } else {
        return [...prev, slot]
      }
    })
  }

  const formatTimeSlot = (slot: TimeSlot) => {
    const start = new Date(slot.start)
    const end = new Date(slot.end)
    
    return {
      date: start.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
      }),
      time: `${start.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })} - ${end.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })}`
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg max-w-2xl mx-auto">
      <div className="flex items-center justify-between p-6 border-b">
        <h2 className="text-xl font-semibold text-gray-900">Schedule New Meeting</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* Meeting Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Meeting Title *
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.title ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter meeting title"
          />
          {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title}</p>}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Meeting agenda or description"
          />
        </div>

        {/* Attendees */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Attendees *
          </label>
          <div className="flex space-x-2 mb-2">
            <input
              type="email"
              value={newAttendee}
              onChange={(e) => setNewAttendee(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAttendee())}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter attendee email"
            />
            <button
              type="button"
              onClick={addAttendee}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
          
          {formData.attendees.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {formData.attendees.map((email) => (
                <span
                  key={email}
                  className="flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  <span>{email}</span>
                  <button
                    type="button"
                    onClick={() => removeAttendee(email)}
                    className="hover:text-blue-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
          {errors.attendees && <p className="mt-1 text-sm text-red-600">{errors.attendees}</p>}
        </div>

        {/* Duration and Priority */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Duration (minutes)
            </label>
            <select
              value={formData.duration}
              onChange={(e) => setFormData(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
              <option value={45}>45 minutes</option>
              <option value={60}>1 hour</option>
              <option value={90}>1.5 hours</option>
              <option value={120}>2 hours</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Priority
            </label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as 'low' | 'medium' | 'high' }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        {/* Location and Video Conference */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Meeting location or room"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Video Conference
            </label>
            <div className="flex items-center space-x-3 pt-2">
              <input
                type="checkbox"
                id="videoConference"
                checked={formData.requiresVideoConference}
                onChange={(e) => setFormData(prev => ({ ...prev, requiresVideoConference: e.target.checked }))}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="videoConference" className="text-sm text-gray-700">
                Include video conference link
              </label>
            </div>
          </div>
        </div>

        {/* Meeting Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Meeting Type
          </label>
          <input
            type="text"
            value={formData.meetingType}
            onChange={(e) => setFormData(prev => ({ ...prev, meetingType: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., standup, interview, client call"
          />
        </div>

        {/* Suggested Times */}
        {formData.attendees.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-gray-700">
                Suggested Times
              </label>
              {loadingSuggestions && <LoadingSpinner />}
            </div>
            
            {suggestedTimes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                {suggestedTimes.map((slot, index) => {
                  const formatted = formatTimeSlot(slot)
                  const isSelected = selectedTimeSlots.some(s => s.start === slot.start && s.end === slot.end)
                  
                  return (
                    <div
                      key={`${slot.start}-${slot.end}`}
                      onClick={() => toggleTimeSlot(slot)}
                      className={`
                        p-3 border rounded-lg cursor-pointer transition-all duration-200
                        ${isSelected 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }
                      `}
                    >
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4 text-gray-500" />
                        <span className="text-sm font-medium">{formatted.date}</span>
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <span className="text-sm text-gray-600">{formatted.time}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : !loadingSuggestions && formData.attendees.length > 0 && (
              <p className="text-sm text-gray-600">
                No available time slots found. Try adjusting the duration or attendees.
              </p>
            )}
            
            {errors.timeSlots && <p className="mt-1 text-sm text-red-600">{errors.timeSlots}</p>}
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={submitting}
            className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? (
              <LoadingSpinner />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span>Schedule Meeting</span>
          </button>
        </div>

        {errors.submit && (
          <p className="text-sm text-red-600 text-center">{errors.submit}</p>
        )}
      </form>
    </div>
  )
}