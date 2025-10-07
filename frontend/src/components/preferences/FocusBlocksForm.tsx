import { useState } from 'react'
import { Plus, Trash2, Edit2, Save, X, AlertCircle, Shield, Calendar } from 'lucide-react'
import { FocusBlock } from '@/types/preferences'
import { PreferencesService } from '@/utils/preferences'

interface FocusBlocksFormProps {
  focusBlocks: FocusBlock[]
  onUpdate: (focusBlocks: FocusBlock[]) => void
}

export function FocusBlocksForm({ focusBlocks, onUpdate }: FocusBlocksFormProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newFocusBlock, setNewFocusBlock] = useState<Partial<FocusBlock>>({
    title: '',
    day: 'monday',
    start: '09:00',
    end: '10:00',
    protected: true,
    recurring: true
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const dayOptions = [
    { value: 'monday', label: 'Monday' },
    { value: 'tuesday', label: 'Tuesday' },
    { value: 'wednesday', label: 'Wednesday' },
    { value: 'thursday', label: 'Thursday' },
    { value: 'friday', label: 'Friday' },
    { value: 'saturday', label: 'Saturday' },
    { value: 'sunday', label: 'Sunday' }
  ] as const

  const validateFocusBlock = (focusBlock: Partial<FocusBlock>): Record<string, string> => {
    const errors: Record<string, string> = {}

    if (!focusBlock.title?.trim()) {
      errors.title = 'Focus block title is required'
    }

    if (!focusBlock.start || !focusBlock.end) {
      errors.time = 'Start and end times are required'
    } else if (!PreferencesService.validateWorkingHours(focusBlock.start, focusBlock.end)) {
      errors.time = 'End time must be after start time'
    }

    // Check for overlapping focus blocks on the same day
    if (focusBlock.day && focusBlock.start && focusBlock.end) {
      const overlapping = focusBlocks.find(fb => 
        fb.id !== focusBlock.id &&
        fb.day === focusBlock.day &&
        (
          (focusBlock.start >= fb.start && focusBlock.start < fb.end) ||
          (focusBlock.end > fb.start && focusBlock.end <= fb.end) ||
          (focusBlock.start <= fb.start && focusBlock.end >= fb.end)
        )
      )
      
      if (overlapping) {
        errors.time = `Overlaps with existing focus block "${overlapping.title}"`
      }
    }

    return errors
  }

  const handleAddFocusBlock = () => {
    const validationErrors = validateFocusBlock(newFocusBlock)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const focusBlock: FocusBlock = {
      id: PreferencesService.generateId(),
      title: newFocusBlock.title!,
      day: newFocusBlock.day as FocusBlock['day'],
      start: newFocusBlock.start!,
      end: newFocusBlock.end!,
      protected: newFocusBlock.protected ?? true,
      recurring: newFocusBlock.recurring ?? true
    }

    onUpdate([...focusBlocks, focusBlock])
    setNewFocusBlock({
      title: '',
      day: 'monday',
      start: '09:00',
      end: '10:00',
      protected: true,
      recurring: true
    })
    setShowAddForm(false)
    setErrors({})
  }

  const handleUpdateFocusBlock = (id: string, updates: Partial<FocusBlock>) => {
    const focusBlock = focusBlocks.find(fb => fb.id === id)
    if (!focusBlock) return

    const updatedFocusBlock = { ...focusBlock, ...updates }
    const validationErrors = validateFocusBlock(updatedFocusBlock)
    
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const updatedFocusBlocks = focusBlocks.map(fb => 
      fb.id === id ? updatedFocusBlock : fb
    )
    onUpdate(updatedFocusBlocks)
    setEditingId(null)
    setErrors({})
  }

  const handleDeleteFocusBlock = (id: string) => {
    if (window.confirm('Are you sure you want to delete this focus block?')) {
      const updatedFocusBlocks = focusBlocks.filter(fb => fb.id !== id)
      onUpdate(updatedFocusBlocks)
    }
  }

  const groupedFocusBlocks = dayOptions.reduce((acc, day) => {
    acc[day.value] = focusBlocks.filter(fb => fb.day === day.value)
    return acc
  }, {} as Record<string, FocusBlock[]>)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Focus Blocks</h3>
          <p className="text-sm text-gray-600">
            Block out time for focused work. Protected blocks cannot be overridden by meetings.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add Focus Block</span>
        </button>
      </div>

      {/* Add Focus Block Form */}
      {showAddForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-4">Add New Focus Block</h4>
          <FocusBlockForm
            focusBlock={newFocusBlock}
            onChange={setNewFocusBlock}
            errors={errors}
            dayOptions={dayOptions}
            onSave={handleAddFocusBlock}
            onCancel={() => {
              setShowAddForm(false)
              setNewFocusBlock({
                title: '',
                day: 'monday',
                start: '09:00',
                end: '10:00',
                protected: true,
                recurring: true
              })
              setErrors({})
            }}
          />
        </div>
      )}

      {/* Focus Blocks by Day */}
      {focusBlocks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No focus blocks configured yet.</p>
          <p className="text-sm">Add focus blocks to protect time for important work.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {dayOptions.map((day) => {
            const dayBlocks = groupedFocusBlocks[day.value]
            if (dayBlocks.length === 0) return null

            return (
              <div key={day.value}>
                <h4 className="text-sm font-medium text-gray-900 mb-3">{day.label}</h4>
                <div className="space-y-2">
                  {dayBlocks.map((focusBlock) => (
                    <div key={focusBlock.id} className="bg-white border border-gray-200 rounded-lg p-4">
                      {editingId === focusBlock.id ? (
                        <FocusBlockForm
                          focusBlock={focusBlock}
                          onChange={() => {}} // Not used in edit mode
                          errors={errors}
                          dayOptions={dayOptions}
                          onSave={(updates) => handleUpdateFocusBlock(focusBlock.id, updates)}
                          onCancel={() => {
                            setEditingId(null)
                            setErrors({})
                          }}
                          isEditing={true}
                          initialData={focusBlock}
                        />
                      ) : (
                        <FocusBlockDisplay
                          focusBlock={focusBlock}
                          onEdit={() => setEditingId(focusBlock.id)}
                          onDelete={() => handleDeleteFocusBlock(focusBlock.id)}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">
          About Focus Blocks
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• <strong>Protected blocks:</strong> Cannot be overridden by meetings, even high-priority ones</li>
          <li>• <strong>Unprotected blocks:</strong> Can be overridden by high-priority meetings if necessary</li>
          <li>• <strong>Recurring blocks:</strong> Apply every week on the specified day</li>
          <li>• Focus blocks help maintain work-life balance and ensure time for important tasks</li>
          <li>• The AI agent will avoid scheduling meetings during focus blocks</li>
        </ul>
      </div>
    </div>
  )
}inter
face FocusBlockFormProps {
  focusBlock: Partial<FocusBlock>
  onChange: (updates: Partial<FocusBlock>) => void
  errors: Record<string, string>
  dayOptions: readonly { value: FocusBlock['day']; label: string }[]
  onSave: (updates?: Partial<FocusBlock>) => void
  onCancel: () => void
  isEditing?: boolean
  initialData?: FocusBlock
}

function FocusBlockForm({ 
  focusBlock, 
  onChange, 
  errors, 
  dayOptions, 
  onSave, 
  onCancel,
  isEditing = false,
  initialData
}: FocusBlockFormProps) {
  const [formData, setFormData] = useState(isEditing && initialData ? initialData : focusBlock)

  const handleSave = () => {
    if (isEditing) {
      onSave(formData)
    } else {
      onSave()
    }
  }

  const updateFormData = (updates: Partial<FocusBlock>) => {
    const newData = { ...formData, ...updates }
    setFormData(newData)
    if (!isEditing) {
      onChange(updates)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Focus Block Title *
          </label>
          <input
            type="text"
            value={formData.title || ''}
            onChange={(e) => updateFormData({ title: e.target.value })}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.title ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="e.g., Deep Work, Planning Time, Code Review"
          />
          {errors.title && (
            <div className="flex items-center space-x-1 mt-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{errors.title}</span>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Day of Week *
          </label>
          <select
            value={formData.day || 'monday'}
            onChange={(e) => updateFormData({ day: e.target.value as FocusBlock['day'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {dayOptions.map((day) => (
              <option key={day.value} value={day.value}>
                {day.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Time Range *
          </label>
          <div className="flex items-center space-x-2">
            <input
              type="time"
              value={formData.start || '09:00'}
              onChange={(e) => updateFormData({ start: e.target.value })}
              className={`flex-1 px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                errors.time ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            <span className="text-gray-500">to</span>
            <input
              type="time"
              value={formData.end || '10:00'}
              onChange={(e) => updateFormData({ end: e.target.value })}
              className={`flex-1 px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                errors.time ? 'border-red-300' : 'border-gray-300'
              }`}
            />
          </div>
          {errors.time && (
            <div className="flex items-center space-x-1 mt-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{errors.time}</span>
            </div>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={formData.protected ?? true}
            onChange={(e) => updateFormData({ protected: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">
            Protected Focus Block
          </span>
        </label>
        <p className="text-sm text-gray-500 ml-6">
          Protected blocks cannot be overridden by meetings, even high-priority ones
        </p>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={formData.recurring ?? true}
            onChange={(e) => updateFormData({ recurring: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">
            Recurring Weekly
          </span>
        </label>
        <p className="text-sm text-gray-500 ml-6">
          This focus block will repeat every week on the selected day
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
          <span>{isEditing ? 'Save Changes' : 'Add Focus Block'}</span>
        </button>
      </div>
    </div>
  )
}

interface FocusBlockDisplayProps {
  focusBlock: FocusBlock
  onEdit: () => void
  onDelete: () => void
}

function FocusBlockDisplay({ focusBlock, onEdit, onDelete }: FocusBlockDisplayProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <div className="flex items-center space-x-3 mb-1">
          <h4 className="font-medium text-gray-900">{focusBlock.title}</h4>
          {focusBlock.protected && (
            <div className="flex items-center space-x-1 text-green-600">
              <Shield className="h-4 w-4" />
              <span className="text-xs font-medium">Protected</span>
            </div>
          )}
          {focusBlock.recurring && (
            <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded">
              Recurring
            </span>
          )}
        </div>
        
        <div className="text-sm text-gray-600">
          {focusBlock.start} - {focusBlock.end}
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