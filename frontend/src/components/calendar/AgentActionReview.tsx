import React, { useState, useEffect } from 'react'
import { Bot, CheckCircle, XCircle, Clock, AlertTriangle, Eye, ThumbsUp, ThumbsDown, RefreshCw } from 'lucide-react'
import { AgentAction } from '@/types/calendar'
import { AgentService } from '@/utils/calendar'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface AgentActionReviewProps {
  onApproveAction: (actionId: string) => Promise<void>
  onRejectAction: (actionId: string, feedback?: string) => Promise<void>
  onRefreshActions: () => Promise<void>
}

export function AgentActionReview({ 
  onApproveAction, 
  onRejectAction, 
  onRefreshActions 
}: AgentActionReviewProps) {
  const [actions, setActions] = useState<AgentAction[]>([])
  const [loading, setLoading] = useState(true)
  const [processingAction, setProcessingAction] = useState<string | null>(null)
  const [expandedAction, setExpandedAction] = useState<string | null>(null)
  const [feedbackText, setFeedbackText] = useState<Record<string, string>>({})
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchActions()
  }, [])

  const fetchActions = async () => {
    try {
      setLoading(true)
      const actions = await AgentService.getActions()
      setActions(actions)
    } catch (error) {
      console.error('Failed to fetch actions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (actionId: string) => {
    try {
      setProcessingAction(actionId)
      await onApproveAction(actionId)
      await fetchActions() // Refresh the list
    } catch (error) {
      console.error('Failed to approve action:', error)
    } finally {
      setProcessingAction(null)
    }
  }

  const handleReject = async (actionId: string) => {
    try {
      setProcessingAction(actionId)
      const feedback = feedbackText[actionId] || undefined
      await onRejectAction(actionId, feedback)
      await fetchActions() // Refresh the list
      setFeedbackText(prev => ({ ...prev, [actionId]: '' }))
    } catch (error) {
      console.error('Failed to reject action:', error)
    } finally {
      setProcessingAction(null)
    }
  }

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      await onRefreshActions()
      await fetchActions()
    } catch (error) {
      console.error('Failed to refresh actions:', error)
    } finally {
      setRefreshing(false)
    }
  }

  const getStatusIcon = (status: AgentAction['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'executed':
        return <CheckCircle className="h-4 w-4 text-blue-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: AgentAction['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      case 'approved':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'rejected':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'executed':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getActionTypeIcon = (type: AgentAction['type']) => {
    switch (type) {
      case 'schedule':
        return '📅'
      case 'reschedule':
        return '🔄'
      case 'cancel':
        return '❌'
      case 'send_email':
        return '📧'
      case 'detect_conflict':
        return '⚠️'
      default:
        return '🤖'
    }
  }

  const formatProposedChanges = (changes: any) => {
    if (!changes) return null

    return (
      <div className="space-y-2">
        {changes.event && (
          <div>
            <h5 className="text-sm font-medium text-gray-700">Event Details:</h5>
            <div className="text-sm text-gray-600 ml-2">
              <div>Title: {changes.event.title}</div>
              {changes.event.start && (
                <div>
                  Time: {new Date(changes.event.start).toLocaleString()} - {new Date(changes.event.end).toLocaleString()}
                </div>
              )}
              {changes.event.attendees && (
                <div>Attendees: {changes.event.attendees.join(', ')}</div>
              )}
            </div>
          </div>
        )}
        
        {changes.email && (
          <div>
            <h5 className="text-sm font-medium text-gray-700">Email:</h5>
            <div className="text-sm text-gray-600 ml-2">
              <div>To: {changes.email.recipients?.join(', ')}</div>
              <div>Subject: {changes.email.subject}</div>
              {changes.email.preview && (
                <div className="mt-1 p-2 bg-gray-50 rounded text-xs">
                  {changes.email.preview}
                </div>
              )}
            </div>
          </div>
        )}
        
        {changes.reschedule && (
          <div>
            <h5 className="text-sm font-medium text-gray-700">Reschedule Options:</h5>
            <div className="text-sm text-gray-600 ml-2">
              {changes.reschedule.options?.map((option: any, idx: number) => (
                <div key={idx}>
                  Option {idx + 1}: {new Date(option.start).toLocaleString()} - {new Date(option.end).toLocaleString()}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const pendingActions = actions.filter(action => action.status === 'pending' && action.requiresApproval)
  const completedActions = actions.filter(action => action.status !== 'pending')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Bot className="h-6 w-6 text-blue-500" />
          <h2 className="text-xl font-semibold text-gray-900">Agent Actions</h2>
          {pendingActions.length > 0 && (
            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
              {pendingActions.length} pending
            </span>
          )}
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {refreshing ? <LoadingSpinner /> : <RefreshCw className="h-4 w-4" />}
          <span>Refresh</span>
        </button>
      </div>

      {/* Pending Actions */}
      {pendingActions.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Pending Approval</h3>
          {pendingActions.map((action) => (
            <div key={action.id} className="border border-yellow-200 rounded-lg bg-yellow-50">
              <div 
                className="p-4 cursor-pointer"
                onClick={() => setExpandedAction(
                  expandedAction === action.id ? null : action.id
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <span className="text-2xl">{getActionTypeIcon(action.type)}</span>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900">{action.description}</h4>
                        {getStatusIcon(action.status)}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{action.reasoning}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <span className="text-xs text-gray-500">
                          {new Date(action.createdAt).toLocaleString()}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setExpandedAction(expandedAction === action.id ? null : action.id)
                          }}
                          className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800"
                        >
                          <Eye className="h-3 w-3" />
                          <span>{expandedAction === action.id ? 'Hide' : 'View'} Details</span>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleApprove(action.id)
                      }}
                      disabled={processingAction === action.id}
                      className="flex items-center space-x-1 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
                    >
                      {processingAction === action.id ? (
                        <LoadingSpinner />
                      ) : (
                        <ThumbsUp className="h-4 w-4" />
                      )}
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleReject(action.id)
                      }}
                      disabled={processingAction === action.id}
                      className="flex items-center space-x-1 px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
                    >
                      {processingAction === action.id ? (
                        <LoadingSpinner />
                      ) : (
                        <ThumbsDown className="h-4 w-4" />
                      )}
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              </div>

              {expandedAction === action.id && (
                <div className="border-t bg-white p-4 space-y-4">
                  {/* Proposed Changes */}
                  {action.proposedChanges && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Proposed Changes:</h5>
                      {formatProposedChanges(action.proposedChanges)}
                    </div>
                  )}

                  {/* Feedback Input */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Feedback (optional):
                    </label>
                    <textarea
                      value={feedbackText[action.id] || ''}
                      onChange={(e) => setFeedbackText(prev => ({ 
                        ...prev, 
                        [action.id]: e.target.value 
                      }))}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Provide feedback for the agent to learn from..."
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Recent Actions */}
      {completedActions.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Recent Actions</h3>
          <div className="space-y-3">
            {completedActions.slice(0, 10).map((action) => (
              <div key={action.id} className={`border rounded-lg p-4 ${getStatusColor(action.status)}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <span className="text-lg">{getActionTypeIcon(action.type)}</span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium">{action.description}</h4>
                        {getStatusIcon(action.status)}
                      </div>
                      <p className="text-sm mt-1">{action.reasoning}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <span className="text-xs">
                          Created: {new Date(action.createdAt).toLocaleString()}
                        </span>
                        {action.executedAt && (
                          <span className="text-xs">
                            Executed: {new Date(action.executedAt).toLocaleString()}
                          </span>
                        )}
                      </div>
                      {action.userFeedback && (
                        <div className="mt-2 p-2 bg-white bg-opacity-50 rounded text-sm">
                          <strong>Feedback:</strong> {action.userFeedback}
                        </div>
                      )}
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(action.status)}`}>
                    {action.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {actions.length === 0 && (
        <div className="text-center py-8">
          <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Agent Actions</h3>
          <p className="text-gray-600">The agent hasn't performed any actions yet. Actions will appear here when the agent schedules meetings or detects conflicts.</p>
        </div>
      )}
    </div>
  )
}