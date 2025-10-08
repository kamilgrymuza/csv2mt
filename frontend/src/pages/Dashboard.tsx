import { SignedIn, SignOutButton, useAuth, useUser } from '@clerk/clerk-react'
import { useQuery } from '@tanstack/react-query'
import axios from '../lib/axios'
import {
  Layout,
  Card,
  Button,
  Typography,
  Space,
  Row,
  Col,
  Statistic,
  Alert,
  Spin,
  Tag,
  Steps,
  Descriptions
} from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ToolOutlined,
  GlobalOutlined
} from '@ant-design/icons'

const { Header, Content } = Layout
const { Title, Text, Paragraph } = Typography

const API_URL = import.meta.env.VITE_API_URL

export default function Dashboard() {
  const { getToken } = useAuth()
  const { user } = useUser()

  const { data: userData, isLoading, error } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const token = await getToken()
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return response.data
    },
    enabled: !!getToken
  })

  // Test public endpoint to verify backend connectivity
  const { data: publicTest } = useQuery({
    queryKey: ['publicTest'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/test/public`)
      return response.data
    }
  })

  // Get setup instructions
  const { data: authInfo } = useQuery({
    queryKey: ['authInfo'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/test/auth-info`)
      return response.data
    }
  })

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <SignedIn>
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
              <UserOutlined style={{ color: '#1890ff' }} />
              Dashboard
            </Title>
            <Tag color="blue">Welcome Back</Tag>
          </div>
          <SignOutButton>
            <Button
              type="primary"
              danger
              icon={<LogoutOutlined />}
            >
              Sign Out
            </Button>
          </SignOutButton>
        </Header>

        {/* Main Content */}
        <Content style={{ padding: '24px', background: '#f5f5f5' }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>

            {/* Welcome Section */}
            <Card>
              <Row gutter={24} align="middle">
                <Col>
                  <Space direction="vertical">
                    <Title level={2} style={{ margin: 0 }}>
                      Welcome back, {user?.firstName || 'User'}!
                    </Title>
                    <Text type="secondary">
                      You're successfully authenticated with Clerk
                    </Text>
                  </Space>
                </Col>
              </Row>
            </Card>

            <Row gutter={24}>
              {/* User Information */}
              <Col xs={24} lg={12}>
                <Card
                  title={
                    <Space>
                      <UserOutlined />
                      User Information
                    </Space>
                  }
                  style={{ height: '100%' }}
                >
                  <Descriptions column={1} bordered size="small">
                    <Descriptions.Item label="User ID">
                      <Text code>{user?.id}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="Email">
                      {user?.primaryEmailAddress?.emailAddress}
                    </Descriptions.Item>
                    <Descriptions.Item label="First Name">
                      {user?.firstName || <Text type="secondary">Not provided</Text>}
                    </Descriptions.Item>
                    <Descriptions.Item label="Last Name">
                      {user?.lastName || <Text type="secondary">Not provided</Text>}
                    </Descriptions.Item>
                    <Descriptions.Item label="Account Created">
                      {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Unknown'}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>

              {/* System Status */}
              <Col xs={24} lg={12}>
                <Card
                  title={
                    <Space>
                      <GlobalOutlined />
                      System Status
                    </Space>
                  }
                  style={{ height: '100%' }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Statistic
                          title="Frontend Status"
                          value="Online"
                          prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                          valueStyle={{ color: '#52c41a' }}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="Backend Status"
                          value={publicTest ? "Online" : "Checking..."}
                          prefix={publicTest ?
                            <CheckCircleOutlined style={{ color: '#52c41a' }} /> :
                            <Spin size="small" />
                          }
                          valueStyle={{ color: publicTest ? '#52c41a' : '#1890ff' }}
                        />
                      </Col>
                    </Row>

                    {publicTest && (
                      <Alert
                        message="Backend Connectivity"
                        description={publicTest.message}
                        type="success"
                        showIcon
                        icon={<CheckCircleOutlined />}
                      />
                    )}
                  </Space>
                </Card>
              </Col>
            </Row>

            {/* Backend Integration Status */}
            <Card
              title={
                <Space>
                  <DatabaseOutlined />
                  Backend API Integration
                </Space>
              }
            >
              {isLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <Spin size="large" />
                  <Paragraph style={{ marginTop: '1rem' }}>
                    Loading user data from backend...
                  </Paragraph>
                </div>
              ) : error ? (
                <Alert
                  message="Backend Connection Error"
                  description={
                    <div>
                      <Paragraph>Failed to connect to the backend API:</Paragraph>
                      <Text code style={{
                        display: 'block',
                        padding: '8px',
                        backgroundColor: '#f5f5f5',
                        borderRadius: '4px',
                        marginTop: '8px'
                      }}>
                        {error.message}
                      </Text>
                    </div>
                  }
                  type="error"
                  showIcon
                  icon={<ExclamationCircleOutlined />}
                />
              ) : userData ? (
                <Alert
                  message="Successfully Connected to Backend!"
                  description={
                    <Descriptions column={1} size="small" style={{ marginTop: '12px' }}>
                      <Descriptions.Item label="Backend User ID">
                        <Text code>{userData.id}</Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Backend Email">
                        {userData.email}
                      </Descriptions.Item>
                      <Descriptions.Item label="Backend Account Created">
                        {new Date(userData.created_at).toLocaleDateString()}
                      </Descriptions.Item>
                    </Descriptions>
                  }
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                />
              ) : (
                <Alert
                  message="No Data Received"
                  description="The backend connection is established but no user data was returned."
                  type="warning"
                  showIcon
                />
              )}
            </Card>

            {/* Setup Instructions (if needed) */}
            {error && authInfo && (
              <Card
                title={
                  <Space>
                    <ToolOutlined />
                    Setup Required
                  </Space>
                }
              >
                <Alert
                  message="Configuration Needed"
                  description={authInfo.message}
                  type="warning"
                  showIcon
                  style={{ marginBottom: '16px' }}
                />

                {authInfo.steps && (
                  <Steps
                    direction="vertical"
                    size="small"
                    items={authInfo.steps.map((step: string, index: number) => ({
                      title: `Step ${index + 1}`,
                      description: step,
                      status: 'wait'
                    }))}
                  />
                )}

                <Alert
                  message="Note"
                  description="The authentication system is fully configured and working. You just need to add your real Clerk credentials to test the protected endpoints."
                  type="info"
                  showIcon
                  style={{ marginTop: '16px' }}
                />
              </Card>
            )}

          </Space>
        </Content>
      </SignedIn>
    </Layout>
  )
}