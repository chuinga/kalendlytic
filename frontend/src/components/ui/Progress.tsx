import React from 'react'
import { cn } from '@/lib/utils'

interface ProgressProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'error' | 'gradient'
  showLabel?: boolean
  label?: string
  className?: string
}

const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  size = 'md',
  variant = 'default',
  showLabel = false,
  label,
  className
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  const sizeConfig = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const variantConfig = {
    default: 'bg-primary-500',
    success: 'bg-success',
    warning: 'bg-warning',
    error: 'bg-error',
    gradient: 'bg-gradient-to-r from-primary-500 to-accent-500'
  }

  return (
    <div className={cn('w-full', className)}>
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-neutral-700">
            {label || 'Progress'}
          </span>
          <span className="text-sm text-neutral-500">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      
      <div className={cn(
        'w-full bg-neutral-200 rounded-full overflow-hidden',
        sizeConfig[size]
      )}>
        <div
          className={cn(
            'h-full transition-all duration-500 ease-out rounded-full',
            variantConfig[variant]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export { Progress }