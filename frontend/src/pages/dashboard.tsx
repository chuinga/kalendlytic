import Head from 'next/head'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import Dashboard from '@/components/Dashboard'

export default function DashboardPage() {
  return (
    <>
      <Head>
        <title>Dashboard - Meeting Scheduler</title>
        <meta name="description" content="Manage your meetings and calendar integrations" />
      </Head>
      
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    </>
  )
}