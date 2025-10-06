import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { SignOutButton, useAuth } from '@clerk/clerk-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'

const API_URL = import.meta.env.VITE_API_URL

interface SubscriptionStatus {
  has_active_subscription: boolean
  status: string | null
  conversions_used: number
  conversions_limit: number | null
  can_convert: boolean
}

interface ConversionState {
  status: 'idle' | 'uploading' | 'converting' | 'success' | 'error'
  message?: string
  downloadUrl?: string
  filename?: string
}

export default function SimpleConverter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedBank, setSelectedBank] = useState<string>('')
  const [conversionState, setConversionState] = useState<ConversionState>({ status: 'idle' })
  const [isDragOver, setIsDragOver] = useState(false)
  const { getToken } = useAuth()
  const navigate = useNavigate()

  // Fetch subscription status
  const { data: subscriptionStatus, refetch: refetchStatus } = useQuery<SubscriptionStatus>({
    queryKey: ['subscriptionStatus'],
    queryFn: async () => {
      const token = await getToken()
      const response = await axios.get(`${API_URL}/subscription/status`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return response.data
    },
    enabled: !!getToken
  })

  // Fetch supported banks
  const { data: banks, isLoading: banksLoading } = useQuery({
    queryKey: ['supportedBanks'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/conversion/supported-banks`)
      return response.data as string[]
    }
  })

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      processFile(file)
    }
  }

  const processFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setConversionState({
        status: 'error',
        message: 'Please select a CSV file'
      })
      return
    }
    setSelectedFile(file)
    setConversionState({ status: 'idle' })
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)

    const files = event.dataTransfer.files
    if (files.length > 0) {
      processFile(files[0])
    }
  }

  const handleConvert = async () => {
    if (!selectedFile || !selectedBank) {
      setConversionState({
        status: 'error',
        message: 'Please select both a file and a bank'
      })
      return
    }

    // Check if user can convert
    if (subscriptionStatus && !subscriptionStatus.can_convert) {
      setConversionState({
        status: 'error',
        message: 'You have reached your free conversion limit. Please upgrade to continue.'
      })
      return
    }

    setConversionState({ status: 'converting' })

    try {
      const token = await getToken()
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('bank_name', selectedBank)

      const response = await axios.post(`${API_URL}/conversion/csv-to-mt940`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob'
      })

      // Create download URL
      const blob = new Blob([response.data], { type: 'application/octet-stream' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const filename = selectedFile.name.replace('.csv', '.mt940')

      setConversionState({
        status: 'success',
        message: 'Conversion successful!',
        downloadUrl,
        filename
      })

      // Refetch subscription status to update usage count
      refetchStatus()
    } catch (error: any) {
      console.error('Conversion error:', error)

      // Handle 402 Payment Required error
      if (error.response?.status === 402) {
        setConversionState({
          status: 'error',
          message: 'You have reached your free conversion limit. Please upgrade to continue.'
        })
      } else {
        setConversionState({
          status: 'error',
          message: error.response?.data?.detail || 'Conversion failed. Please check your file format.'
        })
      }
    }
  }

  const handleDownload = () => {
    if (conversionState.downloadUrl && conversionState.filename) {
      const link = document.createElement('a')
      link.href = conversionState.downloadUrl
      link.download = conversionState.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(conversionState.downloadUrl)
    }
  }

  const resetForm = () => {
    setSelectedFile(null)
    setSelectedBank('')
    setConversionState({ status: 'idle' })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">CSV to MT940 Converter</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="secondary"
                onClick={() => navigate('/subscription')}
              >
                Subscription
              </Button>
              <SignOutButton>
                <Button variant="danger">
                  Sign Out
                </Button>
              </SignOutButton>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Converter Section */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>File Conversion</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Bank Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Your Bank <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedBank}
                    onChange={(e) => setSelectedBank(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    disabled={banksLoading}
                  >
                    <option value="">
                      {banksLoading ? 'Loading banks...' : 'Choose your bank'}
                    </option>
                    {banks?.map((bank) => (
                      <option key={bank} value={bank}>
                        {bank.charAt(0).toUpperCase() + bank.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* File Upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload CSV File <span className="text-red-500">*</span>
                  </label>
                  <div
                    className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md transition-colors ${
                      isDragOver
                        ? 'border-blue-400 bg-blue-50'
                        : 'border-gray-300'
                    }`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <div className="space-y-1 text-center">
                      <svg
                        className={`mx-auto h-12 w-12 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`}
                        stroke="currentColor"
                        fill="none"
                        viewBox="0 0 48 48"
                      >
                        <path
                          d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                          strokeWidth={2}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <div className={`flex text-sm ${isDragOver ? 'text-blue-600' : 'text-gray-600'}`}>
                        <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                          <span>Upload a file</span>
                          <input
                            type="file"
                            className="sr-only"
                            accept=".csv"
                            onChange={handleFileSelect}
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className={`text-xs ${isDragOver ? 'text-blue-500' : 'text-gray-500'}`}>
                        {isDragOver ? 'Drop your CSV file here' : 'CSV files only'}
                      </p>
                      {selectedFile && (
                        <div className="mt-2 p-2 bg-green-50 rounded-md">
                          <p className="text-sm text-green-700">{selectedFile.name}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Status Messages */}
                {conversionState.message && (
                  <div className={`rounded-md p-4 ${
                    conversionState.status === 'success' ? 'bg-green-50 text-green-800' :
                    conversionState.status === 'error' ? 'bg-red-50 text-red-800' :
                    'bg-blue-50 text-blue-800'
                  }`}>
                    <p className="text-sm">{conversionState.message}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex space-x-4">
                  {conversionState.status === 'success' ? (
                    <>
                      <Button
                        onClick={handleDownload}
                        variant="primary"
                      >
                        Download MT940 File
                      </Button>
                      <Button
                        onClick={resetForm}
                        variant="secondary"
                      >
                        Convert Another File
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        onClick={handleConvert}
                        disabled={!selectedFile || !selectedBank || conversionState.status === 'converting'}
                        loading={conversionState.status === 'converting'}
                        variant="primary"
                      >
                        {conversionState.status === 'converting' ? 'Converting...' : 'Convert to MT940'}
                      </Button>
                      {(selectedFile || selectedBank) && (
                        <Button
                          onClick={resetForm}
                          variant="secondary"
                        >
                          Clear
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Usage Display */}
            {subscriptionStatus && (
              <Card>
                <CardHeader>
                  <CardTitle>
                    {subscriptionStatus.has_active_subscription ? 'Premium Plan' : 'Free Plan'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {subscriptionStatus.has_active_subscription ? (
                      <div className="text-center py-4">
                        <div className="text-green-600 font-semibold mb-2">✓ Unlimited Conversions</div>
                        <p className="text-sm text-gray-600">
                          You have unlimited access to all features
                        </p>
                      </div>
                    ) : (
                      <>
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-600">Conversions used</span>
                            <span className="font-medium">
                              {subscriptionStatus.conversions_used} / {subscriptionStatus.conversions_limit}
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2.5">
                            <div
                              className={`h-2.5 rounded-full ${
                                subscriptionStatus.conversions_used >= (subscriptionStatus.conversions_limit || 0)
                                  ? 'bg-red-600'
                                  : subscriptionStatus.conversions_used >= (subscriptionStatus.conversions_limit || 0) * 0.8
                                  ? 'bg-yellow-500'
                                  : 'bg-blue-600'
                              }`}
                              style={{
                                width: `${Math.min(
                                  (subscriptionStatus.conversions_used / (subscriptionStatus.conversions_limit || 1)) * 100,
                                  100
                                )}%`
                              }}
                            />
                          </div>
                        </div>
                        {!subscriptionStatus.can_convert && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                            <p className="text-sm text-yellow-800 mb-2">
                              You've reached your monthly limit
                            </p>
                          </div>
                        )}
                        <Button
                          variant="primary"
                          onClick={() => navigate('/subscription')}
                          className="w-full"
                        >
                          Upgrade to Premium - $4.99/mo
                        </Button>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* About MT940 */}
            <Card>
              <CardHeader>
                <CardTitle>About MT940 Format</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  MT940 is an international standard for electronic bank statements.
                  This converter transforms your bank's CSV export into the standardized
                  MT940 format for use with accounting software and financial systems.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}