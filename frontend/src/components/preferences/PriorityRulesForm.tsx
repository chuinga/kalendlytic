import { useState } from 'react'
import { Plus, Trash2, Edit2, Save, X, AlertCircle, Settings, ToggleLeft, ToggleRight } from 'lucide-react'
import { PriorityRule } from '@/types/preferences'
import { PreferencesService } from '@/utils/preferences'

interface PriorityRulesFormProps {
  priorityRules: PriorityRule[]
  onUpdate: (priorityRules: PriorityRule[]) => void
}

export function PriorityRulesForm({ priorityRules, onUpdate }: PriorityRulesFormProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newRule, setNewRule] = useState<Partial<PriorityRule>>({
    name: '',
    condition: {
      type: 'attendee',
      operator: 'contains',
      value: ''
    },
    priority: 'medium',
    enabled: true
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const conditionTypes = [
    { value: 'attendee', label: 'Attendee Email' },
    { value: 'subject', label: 'Meeting Subject' },
    { value: 'organizer', label: 'Meeting Organizer' },
    { value: 'meeting_type', label: 'Meeting Type' },
    { value: 'time_of_day', label: 'Time of Day' }
  ] as const

  const operators = [
    { value: 'contains', label: 'Contains' },
    { value: 'equals', label: 'Equals' },
    { value: 'starts_with', label: 'Starts With' },
    { value: 'ends_with', label: 'Ends With' },
    { value: 'matches', label: 'Matches (Regex)' }
  ] as const

  const priorityOptions = [
    { value: 'low', label: 'Low Priority', color: 'text-gray-600' },
    { value: 'medium', label: 'Medium Priority', color: 'text-blue-600' },
    { value: 'high', label: 'High Priority', color: 'text-red-600' }
  ] as const

  const validateRule = (rule: Partial<PriorityRule>): Record<string, string> => {
    const errors: Record<string, string> = {}

    if (!rule.name?.trim()) {
      errors.name = 'Rule name is required'
    } else if (priorityRules.some(r => r.name === rule.name && r.id !== rule.id)) {
      errors.name = 'A rule with this name already exists'
    }

    if (!rule.condition?.value?.trim()) {
      errors.value = 'Condition value is required'
    }

    return errors
  }

  const handleAddRule = () => {
    const validationErrors = validateRule(newRule)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const rule: PriorityRule = {
      id: PreferencesService.generateId(),
      name: newRule.name!,
      condition: newRule.condition!,
      priority: newRule.priority as PriorityRule['priority'],
      enabled: newRule.enabled ?? true
    }

    onUpdate([...priorityRules, rule])
    setNewRule({
      name: '',
      condition: {
        type: 'attendee',
        operator: 'contains',
        value: ''
      },
      priority: 'medium',
      enabled: true
    })
    setShowAddForm(false)
    setErrors({})
  }

  const handleUpdateRule = (id: string, updates: Partial<PriorityRule>) => {
    const rule = priorityRules.find(r => r.id === id)
    if (!rule) return

    const updatedRule = { ...rule, ...updates }
    const validationErrors = validateRule(updatedRule)
    
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const updatedRules = priorityRules.map(r => 
      r.id === id ? updatedRule : r
    )
    onUpdate(updatedRules)
    setEditingId(null)
    setErrors({})
  }

  const handleDeleteRule = (id: string) => {
    if (window.confirm('Are you sure you want to delete this priority rule?')) {
      const updatedRules = priorityRules.filter(r => r.id !== id)
      onUpdate(updatedRules)
    }
  }

  const handleToggleRule = (id: string) => {
    const rule = priorityRules.find(r => r.id === id)
    if (!rule) return

    const updatedRules = priorityRules.map(r => 
      r.id === id ? { ...r, enabled: !r.enabled } : r
    )
    onUpdate(updatedRules)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Priority Rules</h3>
          <p className="text-sm text-gray-600">
            Automatically assign priority levels to meetings based on specific conditions.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add Priority Rule</span>
        </button>
      </div>

      {/* Add Rule Form */}
      {showAddForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-4">Add New Priority Rule</h4>
          <PriorityRuleForm
            rule={newRule}
            onChange={setNewRule}
            errors={errors}
            conditionTypes={conditionTypes}
            operators={operators}
            priorityOptions={priorityOptions}
            onSave={handleAddRule}
            onCancel={() => {
              setShowAddForm(false)
              setNewRule({
                name: '',
                condition: {
                  type: 'attendee',
                  operator: 'contains',
                  value: ''
                },
                priority: 'medium',
                enabled: true
              })
              setErrors({})
            }}
          />
        </div>
      )}

      {/* Priority Rules List */}
      {priorityRules.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Settings className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No priority rules configured yet.</p>
          <p className="text-sm">Add rules to automatically prioritize meetings based on specific criteria.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {priorityRules.map((rule) => (
            <div key={rule.id} className={`bg-white border rounded-lg p-4 ${
              rule.enabled ? 'border-gray-200' : 'border-gray-100 bg-gray-50'
            }`}>
              {editingId === rule.id ? (
                <PriorityRuleForm
                  rule={rule}
                  onChange={() => {}} // Not used in edit mode
                  errors={errors}
                  conditionTypes={conditionTypes}
                  operators={operators}
                  priorityOptions={priorityOptions}
                  onSave={(updates) => updates && handleUpdateRule(rule.id, updates)}
                  onCancel={() => {
                    setEditingId(null)
                    setErrors({})
                  }}
                  isEditing={true}
                  initialData={rule}
                />
              ) : (
                <PriorityRuleDisplay
                  rule={rule}
                  onEdit={() => setEditingId(rule.id)}
                  onDelete={() => handleDeleteRule(rule.id)}
                  onToggle={() => handleToggleRule(rule.id)}
                  conditionTypes={conditionTypes}
                  operators={operators}
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
          How Priority Rules Work
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Rules are evaluated in the order they appear when scheduling meetings</li>
          <li>• The first matching rule determines the meeting priority</li>
          <li>• Higher priority meetings take precedence during conflict resolution</li>
          <li>• You can temporarily disable rules without deleting them</li>
          <li>• Use regex patterns for advanced matching (e.g., ".*@company\.com" for company emails)</li>
        </ul>
      </div>
    </div>
  )
}

interface PriorityRuleFormProps {
  rule: Partial<PriorityRule>
  onChange: (updates: Partial<PriorityRule>) => void
  errors: Record<string, string>
  conditionTypes: readonly { value: PriorityRule['condition']['type']; label: string }[]
  operators: readonly { value: PriorityRule['condition']['operator']; label: string }[]
  priorityOptions: readonly { value: PriorityRule['priority']; label: string; color: string }[]
  onSave: (updates?: Partial<PriorityRule>) => void
  onCancel: () => void
  isEditing?: boolean
  initialData?: PriorityRule
}

function PriorityRuleForm({ 
  rule, 
  onChange, 
  errors, 
  conditionTypes,
  operators,
  priorityOptions,
  onSave, 
  onCancel,
  isEditing = false,
  initialData
}: PriorityRuleFormProps) {
  const [formData, setFormData] = useState(isEditing && initialData ? initialData : rule)

  const handleSave = () => {
    if (isEditing) {
      onSave(formData)
    } else {
      onSave()
    }
  }

  const updateFormData = (updates: Partial<PriorityRule>) => {
    const newData = { ...formData, ...updates }
    setFormData(newData)
    if (!isEditing) {
      onChange(updates)
    }
  }

  const updateCondition = (conditionUpdates: Partial<PriorityRule['condition']>) => {
    const newCondition = { ...formData.condition, ...conditionUpdates }
    // Only update if all required fields are present
    if (newCondition.type && newCondition.operator && newCondition.value !== undefined) {
      updateFormData({ condition: newCondition as PriorityRule['condition'] })
    }
  }

  const getPlaceholderText = (type: string) => {
    switch (type) {
      case 'attendee':
        return 'e.g., john@company.com or @company.com'
      case 'subject':
        return 'e.g., "urgent" or "standup"'
      case 'organizer':
        return 'e.g., manager@company.com'
      case 'meeting_type':
        return 'e.g., "interview" or "one-on-one"'
      case 'time_of_day':
        return 'e.g., "morning" or "09:00-12:00"'
      default:
        return 'Enter condition value'
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Rule Name *
          </label>
          <input
            type="text"
            value={formData.name || ''}
            onChange={(e) => updateFormData({ name: e.target.value })}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.name ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="e.g., VIP Client Meetings, Executive Meetings"
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
            Condition Type *
          </label>
          <select
            value={formData.condition?.type || 'attendee'}
            onChange={(e) => updateCondition({ type: e.target.value as PriorityRule['condition']['type'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {conditionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Operator *
          </label>
          <select
            value={formData.condition?.operator || 'contains'}
            onChange={(e) => updateCondition({ operator: e.target.value as PriorityRule['condition']['operator'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {operators.map((operator) => (
              <option key={operator.value} value={operator.value}>
                {operator.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Value *
          </label>
          <input
            type="text"
            value={formData.condition?.value || ''}
            onChange={(e) => updateCondition({ value: e.target.value })}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.value ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder={getPlaceholderText(formData.condition?.type || 'attendee')}
          />
          {errors.value && (
            <div className="flex items-center space-x-1 mt-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{errors.value}</span>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Priority Level *
          </label>
          <select
            value={formData.priority || 'medium'}
            onChange={(e) => updateFormData({ priority: e.target.value as PriorityRule['priority'] })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {priorityOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={formData.enabled ?? true}
            onChange={(e) => updateFormData({ enabled: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">
            Enable this rule
          </span>
        </label>
        <p className="text-sm text-gray-500 ml-6">
          Disabled rules are ignored when determining meeting priorities
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
          <span>{isEditing ? 'Save Changes' : 'Add Rule'}</span>
        </button>
      </div>
    </div>
  )
}

interface PriorityRuleDisplayProps {
  rule: PriorityRule
  onEdit: () => void
  onDelete: () => void
  onToggle: () => void
  conditionTypes: readonly { value: PriorityRule['condition']['type']; label: string }[]
  operators: readonly { value: PriorityRule['condition']['operator']; label: string }[]
  priorityOptions: readonly { value: PriorityRule['priority']; label: string; color: string }[]
}

function PriorityRuleDisplay({ 
  rule, 
  onEdit, 
  onDelete, 
  onToggle,
  conditionTypes,
  operators,
  priorityOptions
}: PriorityRuleDisplayProps) {
  const getConditionTypeLabel = (type: string) => {
    return conditionTypes.find(ct => ct.value === type)?.label || type
  }

  const getOperatorLabel = (operator: string) => {
    return operators.find(op => op.value === operator)?.label || operator
  }

  const getPriorityLabel = (priority: string) => {
    return priorityOptions.find(opt => opt.value === priority)?.label || priority
  }

  const getPriorityColor = (priority: string) => {
    return priorityOptions.find(opt => opt.value === priority)?.color || 'text-gray-600'
  }

  return (
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <div className="flex items-center space-x-3 mb-2">
          <h4 className={`font-medium ${rule.enabled ? 'text-gray-900' : 'text-gray-500'}`}>
            {rule.name}
          </h4>
          <span className={`text-sm font-medium ${getPriorityColor(rule.priority)}`}>
            {getPriorityLabel(rule.priority)}
          </span>
          {!rule.enabled && (
            <span className="text-xs font-medium text-gray-500 bg-gray-200 px-2 py-1 rounded">
              Disabled
            </span>
          )}
        </div>
        
        <div className={`text-sm ${rule.enabled ? 'text-gray-600' : 'text-gray-400'}`}>
          When <strong>{getConditionTypeLabel(rule.condition.type)}</strong>{' '}
          <strong>{getOperatorLabel(rule.condition.operator)}</strong>{' '}
          "<strong>{rule.condition.value}</strong>"
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        <button
          onClick={onToggle}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          title={rule.enabled ? 'Disable rule' : 'Enable rule'}
        >
          {rule.enabled ? (
            <ToggleRight className="h-5 w-5 text-green-600" />
          ) : (
            <ToggleLeft className="h-5 w-5" />
          )}
        </button>
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