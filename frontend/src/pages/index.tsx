import { Authenticator } from '@aws-amplify/ui-react'
import Dashboard from '@/components/Dashboard'

export default function Home() {
  return (
    <Authenticator>
      {({ signOut, user }) => (
        <main className="min-h-screen bg-gray-50">
          <Dashboard user={user} signOut={signOut} />
        </main>
      )}
    </Authenticator>
  )
}