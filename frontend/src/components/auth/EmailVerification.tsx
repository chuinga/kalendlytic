import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/router'

interface EmailVerificationProps {
  email: string
  onBackToLogin: () => void
  onVerificationSuccess: () => void
}

interface VerificationForm {
  email?: string
  code: string
}

export default function EmailVerification({ 
  email, 
  onBackToLogin, 
  onVerificationSuccess 
}: EmailVerificationProps) {
  const [isResending, setIsResending] = useState(false)
  const [isVerified, setIsVerified] = useState(false)
  const [currentEmail, setCurrentEmail] = useState(email)
  const { confirmSignUp, resendConfirmationCode, login, isLoading, error, clearError } = useAuth()
  const router = useRouter()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    watch
  } = useForm<VerificationForm>({
    defaultValues: {
      email: email || ''
    }
  })

  const watchedEmail = watch('email')

  const onSubmit = async (data: VerificationForm) => {
    try {
      clearError()
      const emailToUse = email || data.email || watchedEmail
      if (!emailToUse) {
        setError('email', { message: 'Email is required' })
        return
      }
      await confirmSignUp(emailToUse, data.code)
      setIsVerified(true)
      
      // Show success message briefly, then redirect and auto-sign in
      setTimeout(async () => {
        try {
          // Get password from localStorage if available (from registration)
          const savedPassword = localStorage.getItem('tempPassword')
          if (savedPassword) {
            await login({ email: emailToUse, password: savedPassword })
            localStorage.removeItem('tempPassword')
            router.push('/dashboard')
          } else {
            onVerificationSuccess()
          }
        } catch (loginError) {
          // If auto-login fails, just redirect to login
          onVerificationSuccess()
        }
      }, 2000)
    } catch (error: any) {
      if (error.message.includes('CodeMismatchException')) {
        setError('code', { 
          message: 'Invalid verification code. Please check and try again.' 
        })
      } else if (error.message.includes('ExpiredCodeException')) {
        setError('code', { 
          message: 'Verification code has expired. Please request a new one.' 
        })
      }
    }
  }

  const handleResendCode = async () => {
    try {
      setIsResending(true)
      clearError()
      const emailToUse = email || watchedEmail
      if (!emailToUse) return
      await resendConfirmationCode(emailToUse)
      // Show success message or toast
    } catch (error) {
      console.error('Failed to resend code:', error)
    } finally {
      setIsResending(false)
    }
  }

  // Show success state if verified
  if (isVerified) {
    return (
      <div className="w-full text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h2>
        <p className="text-gray-600 mb-4">
          Your email has been successfully verified. You're being signed in automatically...
        </p>
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
          <Mail className="w-8 h-8 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Verify Your Email</h2>
        <p className="text-gray-600">
          {email ? (
            <>We've sent a verification code to <strong>{email}</strong></>
          ) : (
            'Enter your email and verification code to complete registration'
          )}
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600 font-medium">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {!email && (
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address'
                }
              })}
              type="email"
              id="email"
              className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your email address"
              disabled={isLoading}
            />
            {errors.email && (
              <p className="mt-2 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>
        )}
        <div>
          <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-2">
            Verification Code
          </label>
          <input
            {...register('code', {
              required: 'Verification code is required',
              pattern: {
                value: /^\d{6}$/,
                message: 'Please enter a 6-digit code'
              }
            })}
            type="text"
            id="code"
            maxLength={6}
            className="w-full px-3 py-3 text-center text-2xl font-mono border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent tracking-widest"
            placeholder="000000"
            disabled={isLoading}
          />
          {errors.code && (
            <p className="mt-2 text-sm text-red-600">{errors.code.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-3 px-4 rounded-lg transition duration-200 flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Verifying...
            </>
          ) : (
            'Verify Email'
          )}
        </button>
      </form>

      <div className="mt-6 space-y-4">
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-2">
            Didn't receive the code?
          </p>
          <button
            onClick={handleResendCode}
            disabled={isResending || isLoading}
            className="text-blue-600 hover:text-blue-700 font-medium text-sm disabled:text-gray-400"
          >
            {isResending ? 'Sending...' : 'Resend verification code'}
          </button>
        </div>

        <div className="text-center">
          <button
            onClick={onBackToLogin}
            disabled={isLoading}
            className="inline-flex items-center text-gray-600 hover:text-gray-700 text-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to sign in
          </button>
        </div>
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-600 text-center">
          Check your email (including spam folder) for a 6-digit verification code from AWS Meeting Scheduler.
        </p>
      </div>
    </div>
  )
}