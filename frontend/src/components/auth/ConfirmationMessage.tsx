import { CheckCircle, Mail } from 'lucide-react'

interface ConfirmationMessageProps {
  onBackToLogin: () => void
}

export default function ConfirmationMessage({ onBackToLogin }: ConfirmationMessageProps) {
  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white shadow-lg rounded-lg px-8 py-6 text-center">
        <div className="mb-6">
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Check Your Email</h2>
          <p className="text-gray-600 mt-2">We've sent you a confirmation link</p>
        </div>

        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <Mail className="h-6 w-6 text-blue-600 mx-auto mb-2" />
          <p className="text-sm text-blue-800">
            Please check your email and click the confirmation link to activate your account.
            You may need to check your spam folder.
          </p>
        </div>

        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            After confirming your email, you can sign in to your account.
          </p>
          
          <button
            onClick={onBackToLogin}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition duration-200"
          >
            Back to Sign In
          </button>
        </div>
      </div>
    </div>
  )
}