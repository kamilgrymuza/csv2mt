import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios, { isAxiosError } from '../lib/axios'
import { SignOutButton } from '@clerk/clerk-react'
import {
  Layout,
  Card,
  Button,
  Select,
  Upload,
  Typography,
  Space,
  Alert,
  Row,
  Col,
  Progress,
  notification,
  Spin
} from 'antd'
import {
  UploadOutlined,
  DownloadOutlined,
  ReloadOutlined,
  DeleteOutlined,
  FileTextOutlined,
  BankOutlined,
  LogoutOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd/es/upload/interface'

const { Header, Content } = Layout
const { Title, Text } = Typography
const { Option } = Select

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
  const [fileList, setFileList] = useState<UploadFile[]>([])

  // Fetch supported banks
  const { data: banks, isLoading: banksLoading } = useQuery({
    queryKey: ['supportedBanks'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/conversion/supported-banks`)
      return response.data as string[]
    }
  })

  const uploadProps: UploadProps = {
    accept: '.csv',
    beforeUpload: (file) => {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        notification.error({
          message: 'Invalid File Type',
          description: 'Please select a CSV file'
        })
        return false
      }
      setSelectedFile(file)
      setFileList([file])
      setConversionState({ status: 'idle' })
      return false // Prevent auto upload
    },
    onRemove: () => {
      setSelectedFile(null)
      setFileList([])
      setConversionState({ status: 'idle' })
    },
    fileList,
    maxCount: 1
  }

  const handleConvert = async () => {
    if (!selectedFile || !selectedBank) {
      notification.error({
        message: 'Missing Information',
        description: 'Please select both a file and a bank'
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

      notification.success({
        message: 'Conversion Complete',
        description: 'Your MT940 file is ready for download'
      })
    } catch (error) {
      console.error('Conversion error:', error)
      let errorMessage = 'Conversion failed. Please check your file format.'

      if (isAxiosError(error) && error.response?.data) {
        const reader = new FileReader()
        reader.onload = () => {
          try {
            const errorData = JSON.parse(reader.result as string)
            errorMessage = errorData.detail || errorMessage
          } catch {
            // Use default error message
          }
          setConversionState({
            status: 'error',
            message: errorMessage
          })
          notification.error({
            message: 'Conversion Failed',
            description: errorMessage
          })
        }
        reader.readAsText(error.response.data)
      } else {
        setConversionState({
          status: 'error',
          message: 'Network error. Please try again.'
        })
        notification.error({
          message: 'Network Error',
          description: 'Please check your connection and try again.'
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
    setFileList([])
  }

  const getProgress = () => {
    switch (conversionState.status) {
      case 'converting':
        return 50
      case 'success':
        return 100
      case 'error':
        return 0
      default:
        return 0
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Header */}
      <Header style={{
        background: '#fff',
        borderBottom: '1px solid #f0f0f0',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Title level={3} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileTextOutlined style={{ color: '#1890ff' }} />
            CSV to MT940 Converter
          </Title>
        </div>
        <SignOutButton>
          <Button icon={<LogoutOutlined />} type="primary" danger>
            Sign Out
          </Button>
        </SignOutButton>
      </Header>

      <Layout>
        {/* Main Content */}
        <Content style={{ padding: '24px', background: '#f5f5f5' }}>
          <Row gutter={24}>
            {/* Converter Section */}
            <Col xs={24} lg={16}>
              <Card
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <BankOutlined />
                    File Conversion
                  </div>
                }
                style={{ height: 'fit-content' }}
              >
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  {/* Bank Selection */}
                  <div>
                    <Text strong style={{ marginBottom: '8px', display: 'block' }}>
                      Select Your Bank <Text type="danger">*</Text>
                    </Text>
                    <Select
                      value={selectedBank}
                      onChange={setSelectedBank}
                      placeholder={banksLoading ? 'Loading banks...' : 'Choose your bank'}
                      style={{ width: '100%' }}
                      size="large"
                      loading={banksLoading}
                      disabled={banksLoading}
                    >
                      {banks?.map((bank) => (
                        <Option key={bank} value={bank}>
                          <Space>
                            <BankOutlined />
                            {bank.charAt(0).toUpperCase() + bank.slice(1)}
                          </Space>
                        </Option>
                      ))}
                    </Select>
                  </div>

                  {/* File Upload */}
                  <div>
                    <Text strong style={{ marginBottom: '8px', display: 'block' }}>
                      Upload CSV File <Text type="danger">*</Text>
                    </Text>
                    <Upload.Dragger {...uploadProps} style={{ background: '#fafafa' }}>
                      <p className="ant-upload-drag-icon">
                        <UploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
                      </p>
                      <p className="ant-upload-text">
                        Click or drag CSV file to this area to upload
                      </p>
                      <p className="ant-upload-hint">
                        Support for CSV files only. Single file upload.
                      </p>
                    </Upload.Dragger>
                  </div>

                  {/* Progress */}
                  {conversionState.status !== 'idle' && (
                    <div>
                      <Text strong style={{ marginBottom: '8px', display: 'block' }}>
                        Conversion Progress
                      </Text>
                      <Progress
                        percent={getProgress()}
                        status={conversionState.status === 'error' ? 'exception' :
                               conversionState.status === 'success' ? 'success' : 'active'}
                        format={() => conversionState.status.charAt(0).toUpperCase() + conversionState.status.slice(1)}
                      />
                    </div>
                  )}

                  {/* Status Messages */}
                  {conversionState.message && (
                    <Alert
                      message={conversionState.message}
                      type={conversionState.status === 'success' ? 'success' :
                           conversionState.status === 'error' ? 'error' : 'info'}
                      showIcon
                      icon={conversionState.status === 'converting' ? <Spin /> : undefined}
                    />
                  )}

                  {/* Action Buttons */}
                  <div>
                    <Space size="middle">
                      {conversionState.status === 'success' ? (
                        <>
                          <Button
                            type="primary"
                            icon={<DownloadOutlined />}
                            size="large"
                            onClick={handleDownload}
                          >
                            Download MT940 File
                          </Button>
                          <Button
                            icon={<ReloadOutlined />}
                            size="large"
                            onClick={resetForm}
                          >
                            Convert Another File
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            type="primary"
                            icon={conversionState.status === 'converting' ? <Spin /> : <ReloadOutlined />}
                            size="large"
                            loading={conversionState.status === 'converting'}
                            disabled={!selectedFile || !selectedBank}
                            onClick={handleConvert}
                          >
                            {conversionState.status === 'converting' ? 'Converting...' : 'Convert to MT940'}
                          </Button>
                          {(selectedFile || selectedBank) && (
                            <Button
                              icon={<DeleteOutlined />}
                              size="large"
                              onClick={resetForm}
                            >
                              Clear
                            </Button>
                          )}
                        </>
                      )}
                    </Space>
                  </div>
                </Space>
              </Card>
            </Col>

            {/* Sidebar */}
            <Col xs={24} lg={8}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {/* Supported Banks */}
                <Card title="Supported Banks" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {banksLoading ? (
                      <Spin />
                    ) : (
                      banks?.map((bank) => (
                        <Card
                          key={bank}
                          size="small"
                          style={{
                            background: selectedBank === bank ? '#e6f7ff' : '#fafafa',
                            border: selectedBank === bank ? '1px solid #1890ff' : '1px solid #d9d9d9'
                          }}
                        >
                          <Space>
                            <BankOutlined style={{ color: '#1890ff' }} />
                            <Text strong>
                              {bank.charAt(0).toUpperCase() + bank.slice(1)}
                            </Text>
                            {selectedBank === bank && (
                              <CheckCircleOutlined style={{ color: '#52c41a' }} />
                            )}
                          </Space>
                        </Card>
                      ))
                    )}
                  </Space>
                </Card>

                {/* About MT940 */}
                <Card title="About MT940 Format" size="small">
                  <Text>
                    MT940 is an international standard for electronic bank statements.
                    This converter transforms your bank's CSV export into the standardized
                    MT940 format for use with accounting software and financial systems.
                  </Text>
                </Card>
              </Space>
            </Col>
          </Row>
        </Content>
      </Layout>
    </Layout>
  )
}