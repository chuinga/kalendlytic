import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'
import { CheckCircle, AlertCircle, XCircle, Info, X } from 'lucide-react'

export interface ToastProps {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  description?: string
  duration?: number
  onClose: (id: string) => void
}

const Toast: React.FC<ToastProps> = ({
  id,
  type,
  title,
  description,
  duration = 5000,
  onClose
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    setIsVisible(true)
    
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose()
      }, duration)
      
      return () => clearTimeout(timer)
    }
  }, [duration])

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(() => {
      onClose(id)
    }, 300)
  }

  const typeConfig = {
    success: {
      icon: CheckCircle,
      bgColor: 'bg-gradient-to-r from-green-50 to-emerald-50',
      borderColor: 'border-success/20',
      iconColor: 'text-success',
      titleColor: 'text-green-800'
    },
    error: {
      icon: XCircle,
      bgColor: 'bg-gradient-to-r from-red-50 to-rose-50',
      borderColor: 'border-error/20',
      iconColor: 'text-error',
      titleColor: 'text-red-800'
    },
    warning: {
      icon: AlertCircle,
      bgColor: 'bg-gradient-to-r from-yellow-50 to-orange-50',
      borderColor: 'border-warning/20',
      iconColor: 'text-warning',
      titleColor: 'text-yellow-800'
    },
    info: {
      icon: Info,
      bgColor: 'bg-gradient-to-r from-blue-50 to-indigo-50',
      borderColor: 'border-info/20',
      iconColor: 'text-info',
      titleColor: 'text-blue-800'
    }
  }

  const config = typeConfig[type]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'flex items-start space-x-3 p-4 rounded-2xl shadow-lg border backdrop-blur-sm transition-all duration-300 transform',
        config.bgColor,
        config.borderColor,
        isVisible && !isExiting ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      )}
    >
      <Icon className={cn('w-5 h-5 mt-0.5 flex-shrink-0', config.iconColor)} />
      
      <div className="flex-1 min-w-0">
        <p className={cn('text-sm font-medium', config.titleColor)}>
          {title}
        </p>
        {description && (
          <p className="text-sm text-neutral-600 mt-1">
            {description}
          </p>
        )}
      </div>
      
      <button
        onClick={handleClose}
        className="flex-shrink-0 p-1 hover:bg-white/50 rounded-lg transition-colors duration-200"
      >
        <X className="w-4 h-4 text-neutral-500" />
      </button>
    </div>
  )
}

interface ToastContainerProps {
  toasts: ToastProps[]
  onClose: (id: string) => void
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onClose }) => {
  if (toasts.length === 0) return null

  const containerContent = (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-sm w-full">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onClose={onClose} />
      ))}
    </div>
  )

  return createPortal(containerContent, document.body)
}

// Hook for managing toasts
export const useToast = () => {
  const [toasts, setToasts] = useState<ToastProps[]>([])

  const addToast = (toast: Omit<ToastProps, 'id' | 'onClose'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    setToasts(prev => [...prev, { ...toast, id, onClose: removeToast }])
  }

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }

  const ToastProvider = () => (
    <ToastContainer toasts={toasts} onClose={removeToast} />
  )

  return {
    addToast,
    removeToast,
    ToastProvider,
    toasts
  }
}

export { Toast, ToastContainer }