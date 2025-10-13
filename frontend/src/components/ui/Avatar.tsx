import React from 'react'
import { cn, getInitials, generateGradient } from '@/lib/utils'
import { User } from 'lucide-react'

interface AvatarProps {
  src?: string
  name?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  status?: 'online' | 'offline' | 'away' | 'busy'
  showStatus?: boolean
  className?: string
  onClick?: () => void
}

const Avatar: React.FC<AvatarProps> = ({
  src,
  name = '',
  size = 'md',
  status,
  showStatus = false,
  className,
  onClick
}) => {
  const sizeConfig = {
    xs: { avatar: 'w-6 h-6', text: 'text-xs', status: 'w-2 h-2' },
    sm: { avatar: 'w-8 h-8', text: 'text-sm', status: 'w-2.5 h-2.5' },
    md: { avatar: 'w-10 h-10', text: 'text-base', status: 'w-3 h-3' },
    lg: { avatar: 'w-12 h-12', text: 'text-lg', status: 'w-3.5 h-3.5' },
    xl: { avatar: 'w-16 h-16', text: 'text-xl', status: 'w-4 h-4' },
    '2xl': { avatar: 'w-20 h-20', text: 'text-2xl', status: 'w-5 h-5' },
  }

  const statusConfig = {
    online: 'bg-success border-white',
    offline: 'bg-neutral-400 border-white',
    away: 'bg-warning border-white',
    busy: 'bg-error border-white',
  }

  const config = sizeConfig[size]
  const gradient = generateGradient(name)

  return (
    <div className={cn('relative inline-block', className)}>
      <div
        className={cn(
          'rounded-xl flex items-center justify-center font-semibold shadow-sm transition-all duration-200',
          config.avatar,
          config.text,
          onClick && 'cursor-pointer hover:shadow-md transform hover:scale-105',
          src ? 'bg-neutral-100' : `bg-gradient-to-br ${gradient}`
        )}
        onClick={onClick}
      >
        {src ? (
          <img
            src={src}
            alt={name}
            className="w-full h-full object-cover rounded-xl"
          />
        ) : name ? (
          <span className="text-white font-bold">
            {getInitials(name)}
          </span>
        ) : (
          <User className={cn(
            'text-neutral-500',
            size === 'xs' ? 'w-3 h-3' :
            size === 'sm' ? 'w-4 h-4' :
            size === 'md' ? 'w-5 h-5' :
            size === 'lg' ? 'w-6 h-6' :
            size === 'xl' ? 'w-8 h-8' : 'w-10 h-10'
          )} />
        )}
      </div>

      {showStatus && status && (
        <div
          className={cn(
            'absolute -bottom-0.5 -right-0.5 rounded-full border-2 shadow-sm',
            config.status,
            statusConfig[status]
          )}
        />
      )}
    </div>
  )
}

export { Avatar }