import { useState } from 'react'
import Head from 'next/head'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import LoginForm from '@/components/auth/LoginForm'
import RegisterForm from '@/components/auth/RegisterForm'
import ConfirmationMessage from '@/components/auth/ConfirmationMessage'

type AuthView = 'login' | 'register' | 'confirmation'

export default function LoginPage() {
  const [currentView, setCurrentView] = useState<AuthView>('login')

  return (
    <>
      <Head>
        <title>Sign In - Meeting Scheduler</title>
        <meta name="description" content="Sign in to your Meeting Scheduler account" />
      </Head>
      
      <ProtectedRoute requireAuth={false}>
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Meeting Scheduler
              </h1>
              <p className="text-gray-600">
                AI-powered meeting management across Gmail and Outlook
              </p>
            </div>
          </div>

          <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
            {currentView === 'login' && (
              <LoginForm onSwitchToRegister={() => setCurrentView('register')} />
            )}
            
            {currentView === 'register' && (
              <RegisterForm
                onSwitchToLogin={() => setCurrentView('login')}
                onRegistrationSuccess={() => setCurrentView('confirmation')}
              />
            )}
            
            {currentView === 'confirmation' && (
              <ConfirmationMessage onBackToLogin={() => setCurrentView('login')} />
            )}
          </div>
        </div>
      </ProtectedRoute>
    </>
  )
}