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
            className="block text-sm font-medium text-white/90 mb-2 drop-shadow-sm"
          >
            {label}
          </label>
        )}
        
        <div className="relative group">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60 group-focus-within:text-white/90 transition-colors duration-200">
              {leftIcon}
            </div>
          )}
          
          <input
            id={inputId}
            className={cn(
              `w-full px-4 py-3 rounded-xl
               border border-white/20 
               focus:border-white/40 focus:ring-4 focus:ring-white/10
               bg-white/10 backdrop-blur-md placeholder-white/50
               text-white font-medium
               transition-all duration-200 ease-out
               disabled:opacity-50 disabled:cursor-not-allowed
               disabled:bg-white/5`,
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              error && 'border-red-400/50 focus:border-red-400/70 focus:ring-red-400/20',
              className
            )}
            ref={ref}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/60 group-focus-within:text-white/90 transition-colors duration-200">
              {rightIcon}
            </div>
          )}
        </div>
        
        {(error || helperText) && (
          <p className={cn(
            'mt-2 text-sm',
            error ? 'text-red-300' : 'text-white/60'
          )}>
            {error || helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export { Input }