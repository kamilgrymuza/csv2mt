import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import './CsvConverter.css'

const API_URL = import.meta.env.VITE_API_URL

interface ConversionState {
  status: 'idle' | 'uploading' | 'converting' | 'success' | 'error'
  message?: string
  downloadUrl?: string
  filename?: string
}

export default function CsvConverter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedBank, setSelectedBank] = useState<string>('')
  const [conversionState, setConversionState] = useState<ConversionState>({ status: 'idle' })
  const fileInputRef = useRef<HTMLInputElement>(null)

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
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file) {
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
      if (axios.isAxiosError(error) && error.response?.data) {
        const reader = new FileReader()
        reader.onload = () => {
          try {
            const errorData = JSON.parse(reader.result as string)
            setConversionState({
              status: 'error',
              message: errorData.detail || 'Conversion failed'
            })
          } catch {
            setConversionState({
              status: 'error',
              message: 'Conversion failed. Please check your file format.'
            })
          }
        }
        reader.readAsText(error.response.data)
      } else {
        setConversionState({
          status: 'error',
          message: 'Network error. Please try again.'
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
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="csv-converter">
      <div className="container">
        <header className="header">
          <h1 className="title">CSV to MT940 Converter</h1>
          <p className="subtitle">
            Convert your bank statements from CSV format to MT940 standard
          </p>
        </header>

        <div className="converter-card">
          {/* Bank Selection */}
          <div className="form-section">
            <label className="form-label">
              Select Your Bank
              <span className="required">*</span>
            </label>
            <select
              value={selectedBank}
              onChange={(e) => setSelectedBank(e.target.value)}
              className="bank-select"
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
          <div className="form-section">
            <label className="form-label">
              Upload CSV File
              <span className="required">*</span>
            </label>
            <div
              className={`file-upload-area ${selectedFile ? 'has-file' : ''}`}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".csv"
                className="file-input"
                hidden
              />
              <div className="file-upload-content">
                {selectedFile ? (
                  <>
                    <div className="file-icon">📄</div>
                    <div className="file-info">
                      <p className="file-name">{selectedFile.name}</p>
                      <p className="file-size">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="upload-icon">⬆️</div>
                    <p className="upload-text">
                      <strong>Click to upload</strong> or drag and drop
                    </p>
                    <p className="upload-hint">CSV files only</p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Status Messages */}
          {conversionState.status !== 'idle' && (
            <div className={`status-message ${conversionState.status}`}>
              {conversionState.status === 'converting' && (
                <div className="loading-spinner">⏳</div>
              )}
              {conversionState.status === 'success' && (
                <div className="success-icon">✅</div>
              )}
              {conversionState.status === 'error' && (
                <div className="error-icon">❌</div>
              )}
              <p>{conversionState.message}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="button-group">
            {conversionState.status === 'success' ? (
              <>
                <button
                  onClick={handleDownload}
                  className="btn btn-primary"
                >
                  📥 Download MT940 File
                </button>
                <button
                  onClick={resetForm}
                  className="btn btn-secondary"
                >
                  🔄 Convert Another File
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleConvert}
                  disabled={!selectedFile || !selectedBank || conversionState.status === 'converting'}
                  className="btn btn-primary"
                >
                  {conversionState.status === 'converting' ? '⏳ Converting...' : '🔄 Convert to MT940'}
                </button>
                {(selectedFile || selectedBank) && (
                  <button
                    onClick={resetForm}
                    className="btn btn-secondary"
                  >
                    🗑️ Clear
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="info-section">
          <h3>About MT940 Format</h3>
          <p>
            MT940 is an international standard for electronic bank statements.
            This converter transforms your bank's CSV export into the standardized
            MT940 format for use with accounting software and financial systems.
          </p>
          <div className="supported-banks">
            <h4>Currently Supported Banks:</h4>
            <div className="bank-list">
              {banks?.map((bank) => (
                <span key={bank} className="bank-badge">
                  {bank.charAt(0).toUpperCase() + bank.slice(1)}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}