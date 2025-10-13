import { useState } from 'react'
import { Plus, Trash2, Edit2, Save, X, AlertCircle, Star, Crown, Zap, Users } from 'lucide-react'
import { VIPContact } from '@/types/preferences'
import { PreferencesService } from '@/utils/preferences'

interface VIPContactsFormProps {
  vipContacts: VIPContact[]
  onUpdate: (vipContacts: VIPContact[]) => void
}

export function VIPContactsForm({ vipContacts, onUpdate }: VIPContactsFormProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [newContact, setNewContact] = useState<Partial<VIPContact>>({
    email: '',
    name: '',
    priority: 'high',
    notes: ''
  })
  const [showAddForm, setShowAddForm] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const priorityOptions = [
    { value: 'high', label: 'High Priority', icon: Star, color: 'text-yellow-600' },
    { value: 'vip', label: 'VIP', icon: Crown, color: 'text-purple-600' },
    { value: 'critical', label: 'Critical', icon: Zap, color: 'text-red-600' }
  ] as const

  const validateContact = (contact: Partial<VIPContact>): Record<string, string> => {
    const errors: Record<string, string> = {}

    if (!contact.email) {
      errors.email = 'Email is required'
    } else if (!PreferencesService.validateEmail(contact.email)) {
      errors.email = 'Please enter a valid email address'
    } else if (vipContacts.some(c => c.email === contact.email && c.id !== contact.id)) {
      errors.email = 'This email is already in your VIP contacts'
    }

    if (!contact.priority) {
      errors.priority = 'Priority is required'
    }

    return errors
  }

  const handleAddContact = () => {
    const validationErrors = validateContact(newContact)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const contact: VIPContact = {
      id: PreferencesService.generateId(),
      email: newContact.email!,
      name: newContact.name || undefined,
      priority: newContact.priority as VIPContact['priority'],
      notes: newContact.notes || undefined
    }

    onUpdate([...vipContacts, contact])
    setNewContact({ email: '', name: '', priority: 'high', notes: '' })
    setShowAddForm(false)
    setErrors({})
  }

  const handleUpdateContact = (id: string, updates: Partial<VIPContact>) => {
    const contact = vipContacts.find(c => c.id === id)
    if (!contact) return

    const updatedContact = { ...contact, ...updates }
    const validationErrors = validateContact(updatedContact)
    
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const updatedContacts = vipContacts.map(c => 
      c.id === id ? updatedContact : c
    )
    onUpdate(updatedContacts)
    setEditingId(null)
    setErrors({})
  }

  const handleDeleteContact = (id: string) => {
    if (window.confirm('Are you sure you want to remove this VIP contact?')) {
      const updatedContacts = vipContacts.filter(c => c.id !== id)
      onUpdate(updatedContacts)
    }
  }

  const getPriorityIcon = (priority: VIPContact['priority']) => {
    const option = priorityOptions.find(opt => opt.value === priority)
    if (!option) return null
    
    const Icon = option.icon
    return <Icon className={`h-4 w-4 ${option.color}`} />
  }

  const getPriorityLabel = (priority: VIPContact['priority']) => {
    return priorityOptions.find(opt => opt.value === priority)?.label || priority
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">VIP Contacts</h3>
          <p className="text-sm text-gray-600">
            Meetings with VIP contacts will be automatically prioritized by the AI agent.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add VIP Contact</span>
        </button>
      </div>

      {/* Add Contact Form */}
      {showAddForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-4">Add New VIP Contact</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Address *
              </label>
              <input
                type="email"
                value={newContact.email}
                onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="contact@example.com"
              />
              {errors.email && (
                <div className="flex items-center space-x-1 mt-1 text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm">{errors.email}</span>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name (Optional)
              </label>
              <input
                type="text"
                value={newContact.name}
                onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority Level *
              </label>
              <select
                value={newContact.priority}
                onChange={(e) => setNewContact({ ...newContact, priority: e.target.value as VIPContact['priority'] })}
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
                Notes (Optional)
              </label>
              <input
                type="text"
                value={newContact.notes}
                onChange={(e) => setNewContact({ ...newContact, notes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="CEO, Important client, etc."
              />
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3 mt-4">
            <button
              onClick={() => {
                setShowAddForm(false)
                setNewContact({ email: '', name: '', priority: 'high', notes: '' })
                setErrors({})
              }}
              className="px-3 py-2 text-sm text-gray-700 hover:text-gray-900 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAddContact}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Save className="h-4 w-4" />
              <span>Add Contact</span>
            </button>
          </div>
        </div>
      )}

      {/* VIP Contacts List */}
      {vipContacts.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Users className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No VIP contacts added yet.</p>
          <p className="text-sm">Add contacts to automatically prioritize meetings with them.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {vipContacts.map((contact) => (
            <div key={contact.id} className="bg-white border border-gray-200 rounded-lg p-4">
              {editingId === contact.id ? (
                <EditContactForm
                  contact={contact}
                  onSave={(updates) => handleUpdateContact(contact.id, updates)}
                  onCancel={() => {
                    setEditingId(null)
                    setErrors({})
                  }}
                  errors={errors}
                  priorityOptions={priorityOptions}
                />
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {getPriorityIcon(contact.priority)}
                      <span className="text-sm font-medium text-gray-500">
                        {getPriorityLabel(contact.priority)}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">
                        {contact.name || contact.email}
                      </div>
                      {contact.name && (
                        <div className="text-sm text-gray-600">{contact.email}</div>
                      )}
                      {contact.notes && (
                        <div className="text-sm text-gray-500 italic">{contact.notes}</div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setEditingId(contact.id)}
                      className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteContact(contact.id)}
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">
          How VIP Contacts Work
        </h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• <strong>High Priority:</strong> Meetings with these contacts get preference over regular meetings</li>
          <li>• <strong>VIP:</strong> Higher priority than "High" - these meetings are very important</li>
          <li>• <strong>Critical:</strong> Highest priority - these meetings take precedence over all others</li>
          <li>• The AI agent will automatically protect VIP meetings from being rescheduled</li>
          <li>• When conflicts occur, lower priority meetings will be moved to accommodate VIP contacts</li>
        </ul>
      </div>
    </div>
  )
}

interface EditContactFormProps {
  contact: VIPContact
  onSave: (updates: Partial<VIPContact>) => void
  onCancel: () => void
  errors: Record<string, string>
  priorityOptions: readonly { value: VIPContact['priority']; label: string; icon: any; color: string }[]
}

function EditContactForm({ contact, onSave, onCancel, errors, priorityOptions }: EditContactFormProps) {
  const [formData, setFormData] = useState({
    email: contact.email,
    name: contact.name || '',
    priority: contact.priority,
    notes: contact.notes || ''
  })

  const handleSave = () => {
    onSave({
      email: formData.email,
      name: formData.name || undefined,
      priority: formData.priority,
      notes: formData.notes || undefined
    })
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email Address *
          </label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
              errors.email ? 'border-red-300' : 'border-gray-300'
            }`}
          />
          {errors.email && (
            <div className="flex items-center space-x-1 mt-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{errors.email}</span>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name (Optional)
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Priority Level *
          </label>
          <select
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: e.target.value as VIPContact['priority'] })}
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
            Notes (Optional)
          </label>
          <input
            type="text"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
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
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  )
}