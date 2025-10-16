import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from '../lib/axios'
import { useAuth } from '@clerk/clerk-react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import AppHeader from '../components/AppHeader'

const API_URL = import.meta.env.VITE_API_URL

interface SubscriptionStatus {
  has_active_subscription: boolean
  status: string | null
  conversions_used: number
  conversions_limit: number | null
  can_convert: boolean
  limit_reset_date: string | null
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
  const [isConverting, setIsConverting] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const { getToken } = useAuth()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()

  // Helper to get current language and construct language-aware paths
  const getLangPath = (path: string) => {
    const lang = i18n.language || 'en'
    return `/${lang}${path}`
  }

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

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length > 0) {
      processFiles(Array.from(files))
    }
  }

  const processFiles = (files: File[]) => {
    // Filter only supported files (CSV, PDF, XLS, XLSX)
    const supportedFiles = files.filter(file => {
      const name = file.name.toLowerCase()
      return name.endsWith('.csv') || name.endsWith('.pdf') || name.endsWith('.xls') || name.endsWith('.xlsx')
    })

    if (supportedFiles.length === 0) {
      alert(t('converter.alerts.unsupportedFiles'))
      return
    }

    // Check if user is on free plan - only allow single file
    if (subscriptionStatus && !subscriptionStatus.has_active_subscription) {
      if (supportedFiles.length > 1) {
        alert(t('converter.alerts.freePlanSingleFile'))
        return
      }

      const remaining = (subscriptionStatus.conversions_limit || 0) - subscriptionStatus.conversions_used
      if (remaining <= 0) {
        alert(t('converter.alerts.freeLimitReached'))
        return
      }
    }

    // Add files to list with pending status
    const fileStatuses: FileConversionStatus[] = supportedFiles.map(file => ({
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

      // Use auto-convert endpoint for AI-powered parsing
      const response = await axios.post(`${API_URL}/conversion/auto-convert`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        responseType: 'blob'
      })

      // Create download URL
      const blob = new Blob([response.data], { type: 'application/octet-stream' })
      const downloadUrl = window.URL.createObjectURL(blob)

      // Get the original extension and replace with .mt940
      const originalName = fileStatus.file.name
      const extensionIndex = originalName.lastIndexOf('.')
      const filename = extensionIndex > 0
        ? originalName.substring(0, extensionIndex) + '.mt940'
        : originalName + '.mt940'

      // Update status to success
      setSelectedFiles(prev => prev.map((f, i) =>
        i === index ? {
          ...f,
          status: 'success',
          progress: 100,
          downloadUrl,
          filename,
          message: t('converter.convertedSuccessfully')
        } : f
      ))

    } catch (error: unknown) {
      console.error('Conversion error:', error)

      let errorMessage = t('converter.conversionFailed')
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number; data?: { detail?: string } } }
        if (axiosError.response?.status === 402) {
          errorMessage = t('converter.limitReached')
        } else if (axiosError.response?.data?.detail) {
          errorMessage = typeof axiosError.response.data.detail === 'string'
            ? axiosError.response.data.detail
            : t('converter.conversionFailed')
        }
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
    if (selectedFiles.length === 0) {
      alert(t('converter.alerts.selectFiles'))
      return
    }

    // Check if user can convert
    if (subscriptionStatus && !subscriptionStatus.can_convert) {
      alert(t('converter.alerts.limitReachedUpgrade'))
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
  }

  const remainingConversions = subscriptionStatus && !subscriptionStatus.has_active_subscription
    ? (subscriptionStatus.conversions_limit || 0) - subscriptionStatus.conversions_used
    : null

  const successCount = selectedFiles.filter(f => f.status === 'success').length
  const errorCount = selectedFiles.filter(f => f.status === 'error').length
  const allComplete = selectedFiles.length > 0 && selectedFiles.every(f => f.status === 'success' || f.status === 'error')

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />

      {/* Main Content */}
      <main className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Converter Section */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>{t('converter.title')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* AI-powered conversion notice */}
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <p className="text-sm text-blue-800">
                    {t('converter.aiNotice')}
                  </p>
                </div>

                {/* File Upload */}
                <div>
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
                      {/* Image icon with + */}
                      <div className="relative mx-auto w-16 h-16 mb-4">
                        <svg
                          className={`w-16 h-16 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" strokeWidth="1.5"/>
                          <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                          <polyline points="21 15 16 10 5 21" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                        <div className="absolute -top-1 -right-1 bg-white rounded-full">
                          <svg className={`w-6 h-6 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" strokeWidth="1.5"/>
                            <line x1="12" y1="8" x2="12" y2="16" strokeWidth="1.5" strokeLinecap="round"/>
                            <line x1="8" y1="12" x2="16" y2="12" strokeWidth="1.5" strokeLinecap="round"/>
                          </svg>
                        </div>
                      </div>
                      <p className={`text-base font-medium mb-1 ${isDragOver ? 'text-blue-600' : 'text-gray-900'}`}>
                        {t('converter.dragDropTitle')}
                      </p>
                      <div className={`text-sm ${isDragOver ? 'text-blue-600' : 'text-gray-600'}`}>
                        <span>or </span>
                        <label className="relative cursor-pointer font-medium text-blue-600 hover:text-blue-500">
                          <span>{t('converter.browseFromDisk')}</span>
                          <input
                            type="file"
                            className="sr-only"
                            accept=".csv,.pdf,.xls,.xlsx"
                            multiple={subscriptionStatus?.has_active_subscription || false}
                            onChange={handleFileSelect}
                            disabled={isConverting}
                          />
                        </label>
                      </div>
                      <p className={`text-xs mt-1 ${isDragOver ? 'text-blue-500' : 'text-gray-500'}`}>
                        {isDragOver ? t('converter.dropHere') : ''}
                      </p>
                      {remainingConversions !== null && (
                        <p className="text-xs text-gray-500 mt-2">
                          {t('converter.freePlanNotice', { remaining: remainingConversions, s: remainingConversions !== 1 ? 's' : '' })} <button className="text-blue-600 underline" onClick={() => navigate(getLangPath('/subscription'))}>{t('converter.upgradeToPremium')}</button> {t('converter.unlimitedBatchConversions')}
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
                          {fileStatus.file.type === 'application/pdf' || fileStatus.file.name.toLowerCase().endsWith('.pdf') ? (
                            <svg className="h-8 w-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                            </svg>
                          ) : (fileStatus.file.name.toLowerCase().endsWith('.xls') || fileStatus.file.name.toLowerCase().endsWith('.xlsx')) ? (
                            <svg className="h-8 w-8 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
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
                <div className="space-y-3">
                  {allComplete && (
                    <div className="text-sm text-gray-600 text-center">
                      <span>
                        {successCount} {t('converter.successful')}, {errorCount} {t('converter.failed')}
                      </span>
                    </div>
                  )}
                  {allComplete ? (
                    <div className="flex flex-col space-y-2">
                      {successCount > 0 && (
                        <Button
                          onClick={handleDownloadAll}
                          variant="primary"
                          className="w-full"
                        >
                          {t('converter.downloadAll')}
                        </Button>
                      )}
                      <Button
                        onClick={resetForm}
                        variant="secondary"
                        className="w-full"
                      >
                        {t('converter.convertMoreFiles')}
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-col space-y-2">
                      <Button
                        onClick={handleConvertAll}
                        disabled={selectedFiles.length === 0 || isConverting}
                        loading={isConverting}
                        variant="primary"
                        className="w-full"
                      >
                        {isConverting ? t('converter.converting') : t('converter.convertFiles')}
                      </Button>
                      {selectedFiles.length > 0 && (
                        <Button
                          onClick={resetForm}
                          variant="secondary"
                          disabled={isConverting}
                          className="w-full"
                        >
                          {t('converter.clear')}
                        </Button>
                      )}
                    </div>
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
                    {subscriptionStatus.has_active_subscription ? t('converter.premiumPlan') : t('converter.freePlan')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {subscriptionStatus.has_active_subscription ? (
                      <>
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-600">{t('converter.conversionsUsed')}</span>
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
                                  : 'bg-green-600'
                              }`}
                              style={{
                                width: `${Math.min(
                                  (subscriptionStatus.conversions_used / (subscriptionStatus.conversions_limit || 1)) * 100,
                                  100
                                )}%`
                              }}
                            />
                          </div>
                          {subscriptionStatus.limit_reset_date && (
                            <p className="text-xs text-gray-500 mt-2">
                              {t('subscription.limitResetsOn', {
                                date: new Date(subscriptionStatus.limit_reset_date).toLocaleDateString(
                                  i18n.language === 'pl' ? 'pl-PL' : 'en-US',
                                  { year: 'numeric', month: 'long', day: 'numeric' }
                                )
                              })}
                            </p>
                          )}
                        </div>
                        {!subscriptionStatus.can_convert && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                            <p className="text-sm text-yellow-800 mb-2">
                              {t('converter.monthlyLimitReached')}
                            </p>
                          </div>
                        )}
                      </>
                    ) : (
                      <>
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-600">{t('converter.conversionsUsed')}</span>
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
                          {subscriptionStatus.limit_reset_date && (
                            <p className="text-xs text-gray-500 mt-2">
                              {t('subscription.limitResetsOn', {
                                date: new Date(subscriptionStatus.limit_reset_date).toLocaleDateString(
                                  i18n.language === 'pl' ? 'pl-PL' : 'en-US',
                                  { year: 'numeric', month: 'long', day: 'numeric' }
                                )
                              })}
                            </p>
                          )}
                        </div>
                        {!subscriptionStatus.can_convert && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                            <p className="text-sm text-yellow-800 mb-2">
                              {t('converter.monthlyLimitReached')}
                            </p>
                          </div>
                        )}
                        <Button
                          variant="primary"
                          onClick={() => navigate(getLangPath('/subscription'))}
                          className="w-full"
                        >
                          {t('converter.upgradeToPremiumPrice')}
                        </Button>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
