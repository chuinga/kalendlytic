import Head from 'next/head'
import { useRouter } from 'next/router'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import UserProfile from '@/components/user/UserProfile'

export default function ProfilePage() {
  const router = useRouter()

  const handleClose = () => {
    router.push('/dashboard')
  }

  return (
    <>
      <Head>
        <title>Profile - Meeting Scheduler</title>
        <meta name="description" content="Manage your profile and account settings" />
      </Head>
      
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 py-8">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <UserProfile onClose={handleClose} />
          </div>
        </div>
      </ProtectedRoute>
    </>
  )
}