import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Mail, Lock, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { LoginCredentials } from '@/types/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

interface LoginFormProps {
  onSwitchToRegister: () => void
}

export default function LoginForm({ onSwitchToRegister }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false)
  const { login, isLoading, error, clearError } = useAuth()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError
  } = useForm<LoginCredentials>()

  const onSubmit = async (data: LoginCredentials) => {
    try {
      clearError()
      await login(data)
    } catch (error: any) {
      if (error.message.includes('UserNotConfirmedException')) {
        setError('email', { 
          message: 'Please check your email and confirm your account before signing in.' 
        })
      } else if (error.message.includes('NotAuthorizedException')) {
        setError('password', { 
          message: 'Invalid email or password.' 
        })
      }
    }
  }

  return (
    <div className="w-full">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white mb-2 drop-shadow-lg">Welcome Back</h2>
        <p className="text-white/70">Sign in to your account to continue</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/20 backdrop-blur-sm border border-red-300/30 rounded-xl animate-slideInUp">
          <p className="text-sm text-red-100 font-medium">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Input
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address'
            }
          })}
          type="email"
          label="Email Address"
          placeholder="Enter your email"
          leftIcon={<Mail className="h-5 w-5" />}
          error={errors.email?.message}
          disabled={isLoading}
        />

        <Input
          {...register('password', {
            required: 'Password is required',
            minLength: {
              value: 8,
              message: 'Password must be at least 8 characters'
            }
          })}
          type={showPassword ? 'text' : 'password'}
          label="Password"
          placeholder="Enter your password"
          leftIcon={<Lock className="h-5 w-5" />}
          rightIcon={
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-white/60 hover:text-white/90 transition-colors duration-200"
              disabled={isLoading}
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          }
          error={errors.password?.message}
          disabled={isLoading}
        />

        <div className="flex items-center justify-between">
          <label className="flex items-center">
            <input
              type="checkbox"
              className="w-4 h-4 text-blue-400 bg-white/20 border-white/30 rounded focus:ring-blue-400/50 focus:ring-2 backdrop-blur-sm"
            />
            <span className="ml-2 text-sm text-white/80">Remember me</span>
          </label>
          <button
            type="button"
            className="text-sm text-blue-300 hover:text-blue-200 font-medium transition-colors duration-200"
          >
            Forgot password?
          </button>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={isLoading}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Signing In...' : 'Sign In'}
        </Button>
      </form>

      <div className="mt-8 text-center">
        <p className="text-white/70">
          Don't have an account?{' '}
          <button
            onClick={onSwitchToRegister}
            className="text-blue-300 hover:text-blue-200 font-semibold transition-colors duration-200"
            disabled={isLoading}
          >
            Create account
          </button>
        </p>
      </div>

      {/* Social Login Divider */}
      <div className="mt-8">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/20"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-white/10 backdrop-blur-sm text-white/70 rounded-full">Or continue with</span>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          <Button
            type="button"
            variant="outline"
            className="w-full"
            disabled={isLoading}
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Google
          </Button>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            disabled={isLoading}
          >
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
              <path d="M23.5 12.2c0-1.4-.1-2.7-.3-4H12.2v7.5h6.4c-.3 1.6-1.2 2.9-2.5 3.8v3.1h4.1c2.4-2.2 3.8-5.4 3.8-9.4z"/>
              <path d="M12.2 24c3.2 0 5.9-1.1 7.9-2.9l-4.1-3.1c-1.1.7-2.5 1.2-3.8 1.2-2.9 0-5.4-2-6.3-4.6H1.7v3.1C3.8 21.9 7.7 24 12.2 24z"/>
              <path d="M5.9 14.6c-.2-.7-.4-1.4-.4-2.2s.1-1.5.4-2.2V7.1H1.7C.6 9.2 0 10.5 0 12.4s.6 3.2 1.7 5.3l4.2-3.1z"/>
              <path d="M12.2 4.8c1.6 0 3.1.6 4.2 1.7l3.2-3.2C17.1 1.2 14.9 0 12.2 0 7.7 0 3.8 2.1 1.7 5.3l4.2 3.1c.9-2.6 3.4-4.6 6.3-4.6z"/>
            </svg>
            Microsoft
          </Button>
        </div>
      </div>
    </div>
  )
}