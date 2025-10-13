import React from 'react'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  children: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading = false, disabled, children, ...props }, ref) => {
    const baseStyles = `
      relative inline-flex items-center justify-center font-medium
      transition-all duration-200 ease-out
      focus:outline-none focus:ring-4 focus:ring-primary-100
      disabled:opacity-50 disabled:cursor-not-allowed
      transform hover:scale-[1.02] active:scale-[0.98]
      disabled:hover:scale-100 disabled:active:scale-100
    `

    const variants = {
      primary: `
        bg-gradient-to-r from-blue-500/80 to-purple-600/80 backdrop-blur-md
        hover:from-blue-400/90 hover:to-purple-500/90
        text-white shadow-2xl hover:shadow-blue-500/25
        border border-white/20 hover:border-white/30
        before:absolute before:inset-0 
        before:bg-gradient-to-r before:from-white/20 before:to-transparent
        before:opacity-0 hover:before:opacity-100
        before:transition-opacity before:duration-300
        before:rounded-xl
      `,
      secondary: `
        bg-gradient-to-r from-accent-500 to-accent-600
        hover:from-accent-600 hover:to-accent-700
        text-white shadow-lg hover:shadow-xl
        before:absolute before:inset-0 
        before:bg-gradient-to-r before:from-white/20 before:to-transparent
        before:opacity-0 hover:before:opacity-100
        before:transition-opacity before:duration-300
        before:rounded-xl
      `,
      outline: `
        border border-white/30 hover:border-white/50
        text-white/90 hover:text-white
        bg-white/10 hover:bg-white/20 backdrop-blur-md
        shadow-lg hover:shadow-xl
      `,
      ghost: `
        text-neutral-600 hover:text-primary-600
        hover:bg-primary-50
      `,
      danger: `
        bg-gradient-to-r from-error to-red-600
        hover:from-red-600 hover:to-red-700
        text-white shadow-lg hover:shadow-xl
      `,
    }

    const sizes = {
      sm: 'px-4 py-2 text-sm rounded-lg',
      md: 'px-6 py-3 text-base rounded-xl',
      lg: 'px-8 py-4 text-lg rounded-xl',
      xl: 'px-10 py-5 text-xl rounded-2xl',
    }

    return (
      <button
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          className
        )}
        disabled={disabled || loading}
        ref={ref}
        {...props}
      >
        <span className="relative z-10 flex items-center space-x-2">
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          <span>{children}</span>
        </span>
      </button>
    )
  }
)

Button.displayName = 'Button'

export { Button }