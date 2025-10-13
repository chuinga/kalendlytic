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
        <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-800 flex items-center justify-center p-4 relative overflow-hidden">
          {/* Animated Gradient Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-pink-600/20 animate-pulse"></div>
          
          {/* Floating Orbs with Glassmorphism */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-cyan-400/30 to-blue-500/30 rounded-full filter blur-3xl animate-blob"></div>
            <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-purple-400/30 to-pink-500/30 rounded-full filter blur-3xl animate-blob" style={{ animationDelay: '2s' }}></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-gradient-to-br from-indigo-400/20 to-purple-500/20 rounded-full filter blur-3xl animate-blob" style={{ animationDelay: '4s' }}></div>
            <div className="absolute top-20 left-20 w-64 h-64 bg-gradient-to-br from-pink-400/25 to-rose-500/25 rounded-full filter blur-2xl animate-float"></div>
            <div className="absolute bottom-20 right-20 w-72 h-72 bg-gradient-to-br from-emerald-400/25 to-teal-500/25 rounded-full filter blur-2xl animate-float" style={{ animationDelay: '3s' }}></div>
          </div>

          {/* Particle Effect Overlay */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[length:50px_50px] animate-pulse opacity-30"></div>

          {/* Main Login Card - Glassmorphism */}
          <div className="relative z-10 w-full max-w-md animate-slideInUp">
            {/* Logo & Branding */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-white/10 backdrop-blur-md rounded-3xl shadow-2xl mb-6 animate-float border border-white/20">
                <Calendar className="w-10 h-10 text-white drop-shadow-lg" />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent mb-3 drop-shadow-lg">
                Meeting Scheduler
              </h1>
              <p className="text-white/80 text-lg font-medium drop-shadow-md">
                AI-powered meeting management
              </p>
              <p className="text-white/60 text-sm mt-1">
                Seamless scheduling across all your calendars
              </p>
            </div>

            {/* Glassmorphism Login Form Card */}
            <div className="bg-white/10 backdrop-blur-md rounded-3xl shadow-2xl border border-white/20 p-8 animate-scaleIn relative overflow-hidden">
              {/* Inner glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-3xl"></div>
              
              {/* Content */}
              <div className="relative z-10">
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

            {/* Footer */}
            <div className="text-center mt-8">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
                <p className="text-white/70 text-sm font-medium">
                  🔒 Secure authentication powered by AWS Cognito
                </p>
              </div>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    </>
  )
}