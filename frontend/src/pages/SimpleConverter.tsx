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

interface FileConversionStatus {
  file: File
  status: 'pending' | 'converting' | 'success' | 'error'
  progress: number
  message?: string
  downloadUrl?: string
  filename?: string
}

export default function SimpleConverter() {
  const [selectedFiles, setSelectedFiles] = useState<FileConversionStatus[]>([])
  const [selectedBank, setSelectedBank] = useState<string>('')
  const [isConverting, setIsConverting] = useState(false)
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
    const files = event.target.files
    if (files && files.length > 0) {
      processFiles(Array.from(files))
    }
  }

  const processFiles = (files: File[]) => {
    // Filter only CSV files
    const csvFiles = files.filter(file => file.name.toLowerCase().endsWith('.csv'))

    if (csvFiles.length === 0) {
      alert('Please select CSV file(s)')
      return
    }

    // Check if trying to upload more than remaining limit (free tier only)
    if (subscriptionStatus && !subscriptionStatus.has_active_subscription) {
      const remaining = (subscriptionStatus.conversions_limit || 0) - subscriptionStatus.conversions_used
      if (csvFiles.length > remaining) {
        alert(`You can only convert ${remaining} more file(s) this month. Please select fewer files or upgrade to Premium.`)
        return
      }
    }

    // Add files to list with pending status
    const fileStatuses: FileConversionStatus[] = csvFiles.map(file => ({
      file,
      status: 'pending',
      progress: 0
    }))

    setSelectedFiles(fileStatuses)
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
      processFiles(Array.from(files))
    }
  }

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const convertSingleFile = async (fileStatus: FileConversionStatus, index: number): Promise<void> => {
    try {
      // Update status to converting
      setSelectedFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'converting', progress: 50 } : f
      ))

      const token = await getToken()
      const formData = new FormData()
      formData.append('file', fileStatus.file)
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
      const filename = fileStatus.file.name.replace('.csv', '.mt940')

      // Update status to success
      setSelectedFiles(prev => prev.map((f, i) =>
        i === index ? {
          ...f,
          status: 'success',
          progress: 100,
          downloadUrl,
          filename,
          message: 'Converted successfully'
        } : f
      ))

    } catch (error: any) {
      console.error('Conversion error:', error)

      let errorMessage = 'Conversion failed'
      if (error.response?.status === 402) {
        errorMessage = 'Limit reached'
      } else if (error.response?.data?.detail) {
        errorMessage = typeof error.response.data.detail === 'string'
          ? error.response.data.detail
          : 'Conversion failed'
      }

      // Update status to error
      setSelectedFiles(prev => prev.map((f, i) =>
        i === index ? {
          ...f,
          status: 'error',
          progress: 0,
          message: errorMessage
        } : f
      ))
    }
  }

  const handleConvertAll = async () => {
    if (selectedFiles.length === 0 || !selectedBank) {
      alert('Please select file(s) and a bank')
      return
    }

    // Check if user can convert
    if (subscriptionStatus && !subscriptionStatus.can_convert) {
      alert('You have reached your free conversion limit. Please upgrade to continue.')
      return
    }

    setIsConverting(true)

    // Convert files one by one
    for (let i = 0; i < selectedFiles.length; i++) {
      await convertSingleFile(selectedFiles[i], i)
      // Refetch subscription status after each conversion
      await refetchStatus()
    }

    setIsConverting(false)
  }

  const handleDownload = (fileStatus: FileConversionStatus) => {
    if (fileStatus.downloadUrl && fileStatus.filename) {
      const link = document.createElement('a')
      link.href = fileStatus.downloadUrl
      link.download = fileStatus.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const handleDownloadAll = () => {
    selectedFiles.forEach(fileStatus => {
      if (fileStatus.status === 'success') {
        handleDownload(fileStatus)
      }
    })
  }

  const resetForm = () => {
    setSelectedFiles([])
    setSelectedBank('')
  }

  const remainingConversions = subscriptionStatus && !subscriptionStatus.has_active_subscription
    ? (subscriptionStatus.conversions_limit || 0) - subscriptionStatus.conversions_used
    : null

  const successCount = selectedFiles.filter(f => f.status === 'success').length
  const errorCount = selectedFiles.filter(f => f.status === 'error').length
  const allComplete = selectedFiles.length > 0 && selectedFiles.every(f => f.status === 'success' || f.status === 'error')

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
                    Select your bank
                  </label>
                  <select
                    value={selectedBank}
                    onChange={(e) => setSelectedBank(e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
                    disabled={banksLoading || isConverting}
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
                    Drag and drop your files here
                  </label>
                  <div
                    className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md transition-colors ${
                      isDragOver
                        ? 'border-blue-400 bg-blue-50'
                        : 'border-gray-300'
                    } ${isConverting ? 'opacity-50 pointer-events-none' : ''}`}
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
                      <div className={`flex text-sm justify-center ${isDragOver ? 'text-blue-600' : 'text-gray-600'}`}>
                        <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                          <span>browse from disk</span>
                          <input
                            type="file"
                            className="sr-only"
                            accept=".csv"
                            multiple
                            onChange={handleFileSelect}
                            disabled={isConverting}
                          />
                        </label>
                      </div>
                      <p className={`text-xs ${isDragOver ? 'text-blue-500' : 'text-gray-500'}`}>
                        or {isDragOver ? 'Drop your CSV files here' : 'CSV files only'}
                      </p>
                      {remainingConversions !== null && (
                        <p className="text-xs text-gray-500 mt-2">
                          Free conversion for up to {remainingConversions} files. <button className="text-blue-600 underline" onClick={() => navigate('/subscription')}>Register</button> and make a micro-payment for unlimited conversions.
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* File List */}
                {selectedFiles.length > 0 && (
                  <div className="space-y-2">
                    {selectedFiles.map((fileStatus, index) => (
                      <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-md">
                        {/* File icon */}
                        <div className="flex-shrink-0">
                          {fileStatus.file.type === 'application/pdf' ? (
                            <svg className="h-8 w-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                            </svg>
                          ) : (
                            <svg className="h-8 w-8 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                            </svg>
                          )}
                        </div>

                        {/* File info and progress */}
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start">
                            <p className="text-sm font-medium text-gray-900 truncate">{fileStatus.file.name}</p>
                            {!isConverting && fileStatus.status === 'pending' && (
                              <button
                                onClick={() => removeFile(index)}
                                className="ml-2 text-gray-400 hover:text-gray-600"
                              >
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            )}
                          </div>

                          {/* Progress bar */}
                          {(fileStatus.status === 'converting' || fileStatus.status === 'success') && (
                            <div className="mt-1">
                              <div className="w-full bg-gray-200 rounded-full h-1.5">
                                <div
                                  className={`h-1.5 rounded-full transition-all ${
                                    fileStatus.status === 'success' ? 'bg-blue-600' : 'bg-blue-500'
                                  }`}
                                  style={{ width: `${fileStatus.progress}%` }}
                                />
                              </div>
                            </div>
                          )}

                          {/* Status message */}
                          {fileStatus.message && (
                            <p className={`text-xs mt-1 ${
                              fileStatus.status === 'success' ? 'text-green-600' :
                              fileStatus.status === 'error' ? 'text-red-600' :
                              'text-gray-500'
                            }`}>
                              {fileStatus.message}
                            </p>
                          )}
                        </div>

                        {/* Download button */}
                        {fileStatus.status === 'success' && (
                          <button
                            onClick={() => handleDownload(fileStatus)}
                            className="flex-shrink-0 text-blue-600 hover:text-blue-700"
                          >
                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-600">
                    {allComplete && (
                      <span>
                        {successCount} successful, {errorCount} failed
                      </span>
                    )}
                  </div>
                  <div className="flex space-x-4">
                    {allComplete ? (
                      <>
                        {successCount > 0 && (
                          <Button
                            onClick={handleDownloadAll}
                            variant="primary"
                          >
                            Download All
                          </Button>
                        )}
                        <Button
                          onClick={resetForm}
                          variant="secondary"
                        >
                          Convert More Files
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          onClick={handleConvertAll}
                          disabled={selectedFiles.length === 0 || !selectedBank || isConverting}
                          loading={isConverting}
                          variant="primary"
                        >
                          {isConverting ? 'Converting...' : 'Convert Files'}
                        </Button>
                        {selectedFiles.length > 0 && (
                          <Button
                            onClick={resetForm}
                            variant="secondary"
                            disabled={isConverting}
                          >
                            Clear
                          </Button>
                        )}
                      </>
                    )}
                  </div>
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
