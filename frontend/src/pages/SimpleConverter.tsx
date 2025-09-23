import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { SignOutButton } from '@clerk/clerk-react'
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'

const API_URL = import.meta.env.VITE_API_URL

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

    setConversionState({ status: 'converting' })

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('bank_name', selectedBank)

      const response = await axios.post(`${API_URL}/conversion/csv-to-mt940`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
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
    } catch (error) {
      console.error('Conversion error:', error)
      setConversionState({
        status: 'error',
        message: 'Conversion failed. Please check your file format.'
      })
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
            <SignOutButton>
              <Button variant="danger">
                Sign Out
              </Button>
            </SignOutButton>
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
            {/* Supported Banks */}
            <Card>
              <CardHeader>
                <CardTitle>Supported Banks</CardTitle>
              </CardHeader>
              <CardContent>
                {banksLoading ? (
                  <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {banks?.map((bank) => (
                      <div
                        key={bank}
                        className={`flex items-center p-3 rounded-lg border ${
                          selectedBank === bank
                            ? 'border-blue-200 bg-blue-50'
                            : 'border-gray-200'
                        }`}
                      >
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <span className="text-blue-600 font-medium text-sm">
                              {bank.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">
                            {bank.charAt(0).toUpperCase() + bank.slice(1)}
                          </p>
                        </div>
                        {selectedBank === bank && (
                          <div className="ml-auto">
                            <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

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