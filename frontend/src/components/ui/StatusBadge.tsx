import React from 'react'
import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  status: 'online' | 'offline' | 'connecting' | 'error'
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  className?: string
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  size = 'md', 
  showText = false,
  className 
}) => {
  const statusConfig = {
    online: {
      color: 'bg-success',
      text: 'Connected',
      textColor: 'text-success',
      animation: 'animate-pulse'
    },
    offline: {
      color: 'bg-neutral-400',
      text: 'Offline',
      textColor: 'text-neutral-600',
      animation: ''
    },
    connecting: {
      color: 'bg-warning',
      text: 'Connecting',
      textColor: 'text-warning',
      animation: 'animate-pulse'
    },
    error: {
      color: 'bg-error',
      text: 'Error',
      textColor: 'text-error',
      animation: 'animate-pulse'
    }
  }

  const sizeConfig = {
    sm: {
      dot: 'w-2 h-2',
      text: 'text-xs'
    },
    md: {
      dot: 'w-3 h-3',
      text: 'text-sm'
    },
    lg: {
      dot: 'w-4 h-4',
      text: 'text-base'
    }
  }

  const config = statusConfig[status]
  const sizeStyles = sizeConfig[size]

  if (showText) {
    return (
      <div className={cn('flex items-center space-x-2', className)}>
        <div className={cn(
          'rounded-full border-2 border-white shadow-sm',
          config.color,
          config.animation,
          sizeStyles.dot
        )} />
        <span className={cn(
          'font-medium',
          config.textColor,
          sizeStyles.text
        )}>
          {config.text}
        </span>
      </div>
    )
  }

  return (
    <div className={cn(
      'rounded-full border-2 border-white shadow-sm',
      config.color,
      config.animation,
      sizeStyles.dot,
      className
    )} />
  )
}

export { StatusBadge }