import { useState } from 'react'
import Head from 'next/head'
import { Calendar } from 'lucide-react'
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
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md">
            {/* Logo & Branding */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
                <Calendar className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Meeting Scheduler
              </h1>
              <p className="text-gray-600">
                AI-powered meeting management across Gmail and Outlook
              </p>
            </div>

            {/* Login Form Card */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
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

            {/* Footer */}
            <div className="text-center mt-6">
              <p className="text-gray-500 text-sm">
                Secure authentication powered by AWS Cognito
              </p>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    </>
  )
}