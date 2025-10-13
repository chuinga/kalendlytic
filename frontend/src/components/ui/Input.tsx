import React from 'react'
import { cn } from '@/lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, leftIcon, rightIcon, ...props }, ref) => {
    const inputId = React.useId()

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-outfit font-semibold text-white/90 mb-3 tracking-wide"
          >
            {label}
          </label>
        )}
        
        <div className="relative group">
          {leftIcon && (
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/60 group-focus-within:text-cyan-400 transition-all duration-200">
              {leftIcon}
            </div>
          )}
          
          <input
            id={inputId}
            className={cn(
              'input-premium',
              leftIcon && 'pl-12',
              rightIcon && 'pr-12',
              error && 'border-red-400/50 focus:border-red-400/70 focus:ring-red-400/20 focus:shadow-red-500/20',
              className
            )}
            ref={ref}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white/60 group-focus-within:text-cyan-400 transition-all duration-200">
              {rightIcon}
            </div>
          )}
        </div>
        
        {(error || helperText) && (
          <p className={cn(
            'mt-3 text-sm font-medium',
            error ? 'text-red-300 flex items-center space-x-2' : 'text-white/60'
          )}>
            {error && <span className="w-1.5 h-1.5 bg-red-400 rounded-full animate-pulse"></span>}
            <span>{error || helperText}</span>
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export { Input }