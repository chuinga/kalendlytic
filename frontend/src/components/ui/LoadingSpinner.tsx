import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  variant?: 'default' | 'primary' | 'accent'
  className?: string
}

export default function LoadingSpinner({ 
  size = 'md', 
  variant = 'default',
  className 
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  }

  const variantClasses = {
    default: 'border-neutral-200 border-t-neutral-600',
    primary: 'border-primary-200 border-t-primary-600',
    accent: 'border-accent-200 border-t-accent-600',
  }

  return (
    <div className={cn('flex items-center justify-center', className)}>
      <div
        className={cn(
          'animate-spin rounded-full border-2',
          sizeClasses[size],
          variantClasses[variant]
        )}
      />
    </div>
  )
}