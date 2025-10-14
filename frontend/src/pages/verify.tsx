import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { Calendar } from 'lucide-react'
import EmailVerification from '@/components/auth/EmailVerification'

export default function VerifyPage() {
  const router = useRouter()
  const [email, setEmail] = useState<string>('')

  useEffect(() => {
    // Get email from URL query parameter
    if (router.query.email && typeof router.query.email === 'string') {
      setEmail(router.query.email)
    }
  }, [router.query.email])

  const handleVerificationSuccess = () => {
    router.push('/login')
  }

  const handleBackToLogin = () => {
    router.push('/login')
  }

  return (
    <>
      <Head>
        <title>Verify Email - Meeting Scheduler</title>
        <meta name="description" content="Verify your email address to complete registration" />
      </Head>
      
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

          {/* Verification Form Card */}
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <EmailVerification
              email={email}
              onBackToLogin={handleBackToLogin}
              onVerificationSuccess={handleVerificationSuccess}
            />
          </div>

          {/* Footer */}
          <div className="text-center mt-6">
            <p className="text-gray-500 text-sm">
              Secure authentication powered by AWS Cognito
            </p>
          </div>
        </div>
      </div>
    </>
  )
}