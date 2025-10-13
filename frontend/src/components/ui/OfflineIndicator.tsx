import React from 'react'
import { WifiOff, AlertCircle } from 'lucide-react'

interface OfflineIndicatorProps {
  title?: string
  message?: string
  className?: string
}

export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({
  title = "Backend API Offline",
  message = "The backend services are currently unavailable. Please check back later.",
  className = ""
}) => {
  return (
    <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center ${className}`}>
      <div className="flex flex-col items-center space-y-4">
        <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center">
          <WifiOff className="w-8 h-8 text-yellow-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">{title}</h3>
          <p className="text-yellow-700 max-w-md">{message}</p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-yellow-600">
          <AlertCircle className="w-4 h-4" />
          <span>This is expected during development when the backend isn't deployed</span>
        </div>
      </div>
    </div>
  )
}

export default OfflineIndicator