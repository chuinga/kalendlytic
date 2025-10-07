import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { ConnectionsService } from '@/utils/connections'
import { OAuthProvider } from '@/types/connections'

interface OAuthCallbackProps {
  provider: OAuthProvider
}

export function OAuthCallback({ provider }: OAuthCallbackProps) {
  const router = useRouter()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const callback = ConnectionsService.parseOAuthCallback()
        
        if (!callback) {
          throw new Error('Invalid OAuth callback parameters')
        }

        if (callback.provider !== provider) {
          throw new Error(`Provider mismatch: expected ${provider}, got ${callback.provider}`)
        }

        await ConnectionsService.completeOAuthFlow(callback)
        ConnectionsService.clearOAuthCallback()
        
        setStatus('success')
        
        // Redirect to connections page after success
        setTimeout(() => {
          router.push('/connections')
        }, 2000)
        
      } catch (err: any) {
        console.error('OAuth callback error:', err)
        setError(err.message)
        setStatus('error')
        
        // Clear callback params even on error
        ConnectionsService.clearOAuthCallback()
        
        // Redirect to connections page after error
        setTimeout(() => {
          router.push('/connections')
        }, 5000)
      }
    }

    handleCallback()
  }, [provider, router])

  const getProviderName = () => {
    return provider === 'google' ? 'Google' : 'Microsoft'
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        {status === 'processing' && (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Connecting {getProviderName()}...
            </h2>
            <p className="text-gray-600">
              Please wait while we complete your {getProviderName()} connection.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {getProviderName()} Connected!
            </h2>
            <p className="text-gray-600 mb-4">
              Your {getProviderName()} account has been successfully connected.
            </p>
            <p className="text-sm text-gray-500">
              Redirecting to connections page...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Connection Failed
            </h2>
            <p className="text-gray-600 mb-4">
              We couldn't connect your {getProviderName()} account.
            </p>
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
            <p className="text-sm text-gray-500">
              Redirecting to connections page...
            </p>
          </>
        )}
      </div>
    </div>
  )
}