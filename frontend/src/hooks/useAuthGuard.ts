import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '@/contexts/AuthContext'

interface UseAuthGuardOptions {
  requireAuth?: boolean
  redirectTo?: string
  onAuthRequired?: () => void
  onAuthNotRequired?: () => void
}

export function useAuthGuard({
  requireAuth = true,
  redirectTo,
  onAuthRequired,
  onAuthNotRequired
}: UseAuthGuardOptions = {}) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      if (requireAuth && !isAuthenticated) {
        if (redirectTo) {
          router.push(redirectTo)
        } else if (onAuthRequired) {
          onAuthRequired()
        }
      } else if (!requireAuth && isAuthenticated) {
        if (redirectTo) {
          router.push(redirectTo)
        } else if (onAuthNotRequired) {
          onAuthNotRequired()
        }
      }
    }
  }, [isAuthenticated, isLoading, requireAuth, redirectTo, onAuthRequired, onAuthNotRequired, router])

  return {
    isAuthenticated,
    isLoading,
    user,
    canAccess: requireAuth ? isAuthenticated : !isAuthenticated
  }
}