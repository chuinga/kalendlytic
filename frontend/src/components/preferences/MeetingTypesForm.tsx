import { useState } from 'react'
import { Plus, Trash2, Edit2, Save, X, AlertCircle, Clock, Video, MapPin } from 'lucide-react'
import { MeetingType } from '@/types/preferences'
import { PreferencesService } from '@/utils/preferences'

interface MeetingTypesFormProps {
  meetingTypes: MeetingType[]
  defaultMeetingDuration: number
  onUpdate: (updates: { meetingTypes?: MeetingType[]; defaultMeetingDuration?: number }) => void
}

export function MeetingTypesForm({ meetingTypes, defaultMeetingDuration, onUpdate }: MeetingTypesFormProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newMeetingType, setNewMeetingType] = useState<Partial<MeetingType>>({
    name: '',
    duration: 30,
    priority: 'medium',
    bufferBefore: 5,
    bufferAfter: 5,
    requiresVideoConference: false,
    defaultLocation: ''
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const priorityOptions = [
    { value: 'low', label: 'Low Priority', color: 'text-gray-600' },
    { value: 'medium', label: 'Medium Priority', color: 'text-blue-600' },
    { value: 'high', label: 'High Priority', color: 'text-red-600' }
  ] as const

  const durationOptions = [15, 30, 45, 60, 90, 120]

  const validateMeetingType = (meetingType: Partial<MeetingType>): Record<string, string> => {
    const errors: Record<string, string> = {}

    if (!meetingType.name?.trim()) {
      errors.name = 'Meeting type name is required'
    } else if (meetingTypes.some(mt => mt.name === meetingType.name && mt.id !== meetingType.id)) {
      errors.name = 'A meeting type with this name already exists'
    }

    if (!meetingType.duration || meetingType.duration < 5) {
      errors.duration = 'Duration must be at least 5 minutes'
    }

    if (meetingType.bufferBefore !== undefined && meetingType.bufferBefore < 0) {
      errors.bufferBefore = 'Buffer time cannot be negative'
    }

    if (meetingType.bufferAfter !== undefined && meetingType.bufferAfter < 0) {
      errors.bufferAfter = 'Buffer time cannot be negative'
    }

    return errors
  }

  const handleAddMeetingType = () => {
    const validationErrors = validateMeetingType(newMeetingType)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const meetingType: MeetingType = {
      id: PreferencesService.generateId(),
      name: newMeetingType.name!,
      duration: newMeetingType.duration!,
      priority: newMeetingType.priority as MeetingType['priority'],
      bufferBefore: newMeetingType.bufferBefore,
      bufferAfter: newMeetingType.bufferAfter,
      requiresVideoConference: newMeetingType.requiresVideoConference,
      defaultLocation: newMeetingType.defaultLocation || undefined
    }

    onUpdate({ meetingTypes: [...meetingTypes, meetingType] })
    setNewMeetingType({
      name: '',
      duration: 30,
      priority: 'medium',
      bufferBefore: 5,
      bufferAfter: 5,
      requiresVideoConference: false,
      defaultLocation: ''
    })
    setShowAddForm(false)
    setErrors({})
  }

  const handleUpdateMeetingType = (id: string, updates: Partial<MeetingType>) => {
    const meetingType = meetingTypes.find(mt => mt.id === id)
    if (!meetingType) return

    const updatedMeetingType = { ...meetingType, ...updates }
    const validationErrors = validateMeetingType(updatedMeetingType)
    
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const updatedMeetingTypes = meetingTypes.map(mt => 
      mt.id === id ? updatedMeetingType : mt
    )
    onUpdate({ meetingTypes: updatedMeetingTypes })
    setEditingId(null)
    setErrors({})
  }

  const handleDeleteMeetingType = (id: string) => {
    if (window.confirm('Are you sure you want to delete this meeting type?')) {
      const updatedMeetingTypes = meetingTypes.filter(mt => mt.id !== id)
      onUpdate({ meetingTypes: updatedMeetingTypes })
    }
  }

  return (
    <div className="space-y-6">
      {/* Default Duration Setting */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Default Meeting Duration
        </label>
        <select
          value={defaultMeetingDuration}
          onChange={(e) => onUpdate({ defaultMeetingDuration: parseInt(e.target.value) })}
          className="w-48 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          {durationOptions.map((duration) => (
            <option key={duration} value={duration}>
              {duration} minutes
            </option>
          ))}
        </select>
        <p className="mt-1 text-sm text-gray-500">
          This will be used when no specific meeting type is selected.
        </p>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Meeting Types</h3>
          <p className="text-sm text-gray-600">
            Define different types of meetings with specific durations, priorities, and buffer times.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add Meeting Type</span>
        </button>
      </div>

      {/* Add Meeting Type Form */}
      {showAddForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-4">Add New Meeting Type</h4>
          <MeetingTypeForm
            meetingType={newMeetingType}
            onChange={setNewMeetingType}
            errors={errors}
            priorityOptions={priorityOptions}
            durationOptions={durationOptions}
            onSave={handleAddMeetingType}
            onCancel={() => {
              setShowAddForm(false)
              setNewMeetingType({
                name: '',
                duration: 30,
                priority: 'medium',
                bufferBefore: 5,
                bufferAfter: 5,
                requiresVideoConference: false,
                defaultLocation: ''
              })
              setErrors({})
            }}
          />
        </div>
      )}

      {/* Meeting Types List */}
      {meetingTypes.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No meeting types configured yet.</p>
          <p className="text-sm">Add meeting types to help the AI agent better schedule your meetings.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {meetingTypes.map((meetingType) => (
            <div key={meetingType.id} className="bg-white border border-gray-200 rounded-lg p-4">
              {editingId === meetingType.id ? (
                <MeetingTypeForm
                  meetingType={meetingType}
                  onChange={(updates) => {
                    const updatedType = { ...meetingType, ...updates }
                    // This is just for local state, actual save happens on save button
                  }}
                  errors={errors}
                  priorityOptions={priorityOptions}
                  durationOptions={durationOptions}
                  onSave={(updates) => handleUpdateMeetingType(meetingType.id, updates)}
                  onCancel={() => {
                    setEditingId(null)
                    setErrors({})
                  }}
                  isEditing={true}
                  initialData={meetingType}
                />
              ) : (
                <MeetingTypeDisplay
                  meetingType={meetingType}
                  onEdit={() => setEditingId(meetingType.id)}
                  onDelete={() => handleDeleteMeetingType(meetingType.id)}
                  priorityOptions={priorityOptions}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">
          How Meeting Types Work
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• The AI agent will use these templates when scheduling meetings</li>
          <li>• Buffer times are added before and after meetings to prevent back-to-back scheduling</li>
          <li>• Higher priority meeting types will take precedence during conflict resolution</li>
          <li>• Video conference settings help the agent automatically add meeting links</li>
          <li>• Default locations can be automatically added to meeting invitations</li>
        </ul>
      </div>
    </div>
  )
}
in
terface MeetingTypeFormProps {
  meetingType: Partial<MeetingType>
  onChange: (updates: Partial<MeetingType>) => void
  errors: Record<string, string>
  priorityOptions: readonly { value: MeetingType['priority']; label: string; color: string }[]
  durationOptions: number[]
  onSave: (updates?: Partial<MeetingType>) => void
  onCancel: () => void
  isEditing?: boolean
  initialData?: MeetingType
}

function MeetingTypeForm({ 
  meetingType, 
  onChange, 
  errors, 
  priorityOptions, 
  durationOptions, 
  onSave, 
  onCancel,
  isEditing = false,
  initialData
}: MeetingTypeFormProps) {
  const [formData, setFormData] = useState(isEditing && initialData ? initialData : meetingType)

  const handleSave = () => {
    if (isEditing) {
      onSave(formData)
    } else {
      onSave()
    }
  }

  const updateFormData = (updates: Partial<MeetingType>) => {
    const newData = { ...formData, ...updates }
    setFormData(newData)
    if (!isEditing) {
      onChange(updates)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Meeting Type Name *
          </label>
          <input
            type="text"
            value={formData.name || ''}
            onChange={(e) => updateFormData({ name: e.target.value })}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.name ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="e.g., Daily Standup, One-on-One"
          />
          {errors.name && (
            <div className="flex items-center space-x-1 mt-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{errors.name}</span>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Duration *
          </label>
          <select
            value={formData.duration || 30}
            onChange={(e) => updateFormData({ duration: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {durationOptions.map((duration) => (
              <option key={duration} value={duration}>
                {duration} minutes
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Priority Level *
          </label>
          <select
            value={formData.priority || 'medium'}
            onChange={(e) => updateFormData({ priority: e.target.value as MeetingType['priority'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {priorityOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Buffer Before (minutes)
          </label>
          <input
            type="number"
            min="0"
            max="60"
            value={formData.bufferBefore || 0}
            onChange={(e) => updateFormData({ bufferBefore: parseInt(e.target.value) || 0 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Buffer After (minutes)
          </label>
          <input
            type="number"
            min="0"
            max="60"
            value={formData.bufferAfter || 0}
            onChange={(e) => updateFormData({ bufferAfter: parseInt(e.target.value) || 0 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Default Location (Optional)
          </label>
          <input
            type="text"
            value={formData.defaultLocation || ''}
            onChange={(e) => updateFormData({ defaultLocation: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Conference Room A, Online, etc."
          />
        </div>
      </div>

      <div>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={formData.requiresVideoConference || false}
            onChange={(e) => updateFormData({ requiresVideoConference: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">
            Requires Video Conference
          </span>
        </label>
        <p className="text-sm text-gray-500 ml-6">
          Automatically add video conference links to meetings of this type
        </p>
      </div>

      <div className="flex items-center justify-end space-x-3">
        <button
          onClick={onCancel}
          className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:text-gray-900 transition-colors"
        >
          <X className="h-4 w-4" />
          <span>Cancel</span>
        </button>
        <button
          onClick={handleSave}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Save className="h-4 w-4" />
          <span>{isEditing ? 'Save Changes' : 'Add Meeting Type'}</span>
        </button>
      </div>
    </div>
  )
}

interface MeetingTypeDisplayProps {
  meetingType: MeetingType
  onEdit: () => void
  onDelete: () => void
  priorityOptions: readonly { value: MeetingType['priority']; label: string; color: string }[]
}

function MeetingTypeDisplay({ meetingType, onEdit, onDelete, priorityOptions }: MeetingTypeDisplayProps) {
  const getPriorityLabel = (priority: MeetingType['priority']) => {
    return priorityOptions.find(opt => opt.value === priority)?.label || priority
  }

  const getPriorityColor = (priority: MeetingType['priority']) => {
    return priorityOptions.find(opt => opt.value === priority)?.color || 'text-gray-600'
  }

  return (
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <div className="flex items-center space-x-4 mb-2">
          <h4 className="font-medium text-gray-900">{meetingType.name}</h4>
          <span className={`text-sm font-medium ${getPriorityColor(meetingType.priority)}`}>
            {getPriorityLabel(meetingType.priority)}
          </span>
        </div>
        
        <div className="flex items-center space-x-6 text-sm text-gray-600">
          <div className="flex items-center space-x-1">
            <Clock className="h-4 w-4" />
            <span>{meetingType.duration} min</span>
          </div>
          
          {(meetingType.bufferBefore || meetingType.bufferAfter) && (
            <div className="flex items-center space-x-1">
              <span>Buffer:</span>
              <span>
                {meetingType.bufferBefore || 0}m before, {meetingType.bufferAfter || 0}m after
              </span>
            </div>
          )}
          
          {meetingType.requiresVideoConference && (
            <div className="flex items-center space-x-1">
              <Video className="h-4 w-4" />
              <span>Video required</span>
            </div>
          )}
          
          {meetingType.defaultLocation && (
            <div className="flex items-center space-x-1">
              <MapPin className="h-4 w-4" />
              <span>{meetingType.defaultLocation}</span>
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        <button
          onClick={onEdit}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <Edit2 className="h-4 w-4" />
        </button>
        <button
          onClick={onDelete}
          className="p-2 text-gray-400 hover:text-red-600 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}