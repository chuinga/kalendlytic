import React from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'glass'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  children: React.ReactNode
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', padding = 'md', children, ...props }, ref) => {
    const baseStyles = `
      relative overflow-hidden
      transition-all duration-300 ease-out
      transform hover:scale-[1.01]
    `

    const variants = {
      default: `
        bg-white rounded-2xl shadow-soft hover:shadow-medium
        border border-neutral-100 hover:border-primary-200
        before:absolute before:inset-0 
        before:bg-gradient-to-br before:from-primary-50/50 before:to-transparent
        before:opacity-0 hover:before:opacity-100
        before:transition-opacity before:duration-300
      `,
      elevated: `
        bg-white rounded-2xl shadow-medium hover:shadow-large
        border border-neutral-100
      `,
      outlined: `
        bg-white rounded-2xl border-2 border-neutral-200
        hover:border-primary-300 hover:shadow-soft
      `,
      glass: `
        bg-white/80 backdrop-blur-xl rounded-2xl
        shadow-soft hover:shadow-medium
        border border-white/20
      `,
    }

    const paddings = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
      xl: 'p-10',
    }

    return (
      <div
        className={cn(
          baseStyles,
          variants[variant],
          paddings[padding],
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="relative z-10">
          {children}
        </div>
      </div>
    )
  }
)

Card.displayName = 'Card'

export { Card }