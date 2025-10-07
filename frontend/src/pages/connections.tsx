import React from 'react'
import { GetServerSideProps } from 'next'
import { ConnectionsPage } from '@/components/connections/ConnectionsPage'
import { useAuthGuard } from '@/hooks/useAuthGuard'

export default function Connections() {
  const { loading } = useAuthGuard()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return <ConnectionsPage />
}

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    props: {}
  }
}