import { useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useNavigate, useSearchParams } from 'react-router-dom'
import AppHeader from '../components/AppHeader'
import {
  Layout,
  Card,
  Button,
  Typography,
  Space,
  Row,
  Col,
  Alert,
  Spin,
  Tag,
  Progress,
  message
} from 'antd'
import {
  CheckCircleOutlined,
  CreditCardOutlined,
  RocketOutlined,
  SettingOutlined
} from '@ant-design/icons'

const { Content } = Layout
const { Title, Text, Paragraph } = Typography

const API_URL = import.meta.env.VITE_API_URL

interface SubscriptionStatus {
  has_active_subscription: boolean
  status: string | null
  conversions_used: number
  conversions_limit: number | null
  can_convert: boolean
  cancel_at_period_end: boolean | null
  current_period_end: string | null
}

export default function SubscriptionPage() {
  const { getToken } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [isCreatingCheckout, setIsCreatingCheckout] = useState(false)
  const [isCreatingPortal, setIsCreatingPortal] = useState(false)

  // Show success/canceled messages from Stripe redirect
  const success = searchParams.get('success')
  const canceled = searchParams.get('canceled')

  // Fetch subscription status
  const { data: subscriptionStatus, isLoading, error, refetch } = useQuery<SubscriptionStatus>({
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
    enabled: !!getToken,
    refetchInterval: 5000 // Refetch every 5 seconds to catch webhook updates
  })

  // Handle creating checkout session
  const handleUpgrade = async () => {
    try {
      setIsCreatingCheckout(true)
      const token = await getToken()

      const response = await axios.post(
        `${API_URL}/subscription/create-checkout-session`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      // Redirect to Stripe Checkout
      window.location.href = response.data.url
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      message.error(axiosError.response?.data?.detail || 'Failed to create checkout session')
      setIsCreatingCheckout(false)
    }
  }

  // Handle managing subscription (portal)
  const handleManageSubscription = async () => {
    try {
      setIsCreatingPortal(true)
      const token = await getToken()

      const response = await axios.post(
        `${API_URL}/subscription/create-portal-session`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      // Redirect to Stripe Customer Portal
      window.location.href = response.data.url
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      message.error(axiosError.response?.data?.detail || 'Failed to open subscription management')
      setIsCreatingPortal(false)
    }
  }

  // Calculate usage percentage
  const usagePercentage = subscriptionStatus
    ? subscriptionStatus.conversions_limit
      ? Math.round((subscriptionStatus.conversions_used / subscriptionStatus.conversions_limit) * 100)
      : 0
    : 0

  // Show success message after successful subscription
  if (success === 'true') {
    message.success('Subscription activated successfully!')
    // Clear query param
    navigate('/subscription', { replace: true })
    refetch()
  }

  // Show canceled message
  if (canceled === 'true') {
    message.info('Subscription checkout was canceled')
    navigate('/subscription', { replace: true })
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader />

      <Content style={{ padding: '48px 24px', background: '#f5f5f5' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: '8px' }}>
            Manage Your Subscription
          </Title>
          <Paragraph style={{ textAlign: 'center', fontSize: '16px', color: '#666', marginBottom: '48px' }}>
            Your gateway to unlimited file conversions and premium features.
          </Paragraph>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '4rem' }}>
              <Spin size="large" />
            </div>
          ) : error ? (
            <Alert
              message="Error Loading Subscription Status"
              description={error.message}
              type="error"
              showIcon
            />
          ) : (
            <Row gutter={[24, 24]} justify="center">
              {/* Current Plan */}
              <Col xs={24} lg={subscriptionStatus?.has_active_subscription ? 12 : 12}>
                <Card
                  title="Current Plan"
                  style={{ height: '100%' }}
                  headStyle={{ fontSize: '20px', fontWeight: 600 }}
                >
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    {subscriptionStatus?.has_active_subscription ? (
                      <>
                        <Tag color={subscriptionStatus.cancel_at_period_end ? "orange" : "green"} style={{ fontSize: '16px', padding: '8px 16px' }}>
                          {subscriptionStatus.cancel_at_period_end ? "Premium Plan (Canceling)" : "Premium Plan"}
                        </Tag>

                        {subscriptionStatus.cancel_at_period_end && subscriptionStatus.current_period_end ? (
                          <Alert
                            message="Subscription Canceling"
                            description={
                              <Space direction="vertical" size="small">
                                <Text>Your subscription will cancel on {new Date(subscriptionStatus.current_period_end).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}.</Text>
                                <Text>You will retain Premium access until then.</Text>
                                <Text strong>No refunds for the current billing period.</Text>
                                <Text type="secondary" style={{ fontSize: '12px' }}>To reactivate, click "Manage Subscription" below.</Text>
                              </Space>
                            }
                            type="warning"
                            showIcon
                          />
                        ) : (
                          <Alert
                            message="Unlimited Conversions"
                            description="You have unlimited access to all conversion features"
                            type="success"
                            showIcon
                            icon={<CheckCircleOutlined />}
                          />
                        )}
                      </>
                    ) : (
                      <>
                        <div>
                          <Tag color="blue" style={{ fontSize: '16px', padding: '8px 16px' }}>
                            Free Plan
                          </Tag>
                          <Paragraph style={{ marginTop: '16px', marginBottom: '8px' }}>
                            <Text strong>
                              {subscriptionStatus?.conversions_used} / {subscriptionStatus?.conversions_limit} free conversions used
                            </Text>
                          </Paragraph>
                          <Progress
                            percent={usagePercentage}
                            status={usagePercentage >= 100 ? 'exception' : 'active'}
                            strokeColor={usagePercentage >= 80 ? '#ff4d4f' : '#1890ff'}
                          />
                        </div>

                        {!subscriptionStatus?.can_convert && (
                          <Alert
                            message="Limit Reached"
                            description="You've used all your free conversions for this month. Upgrade to Premium for unlimited access."
                            type="warning"
                            showIcon
                          />
                        )}
                      </>
                    )}

                    {/* Payment Information (if subscribed) */}
                    {subscriptionStatus?.has_active_subscription && (
                      <Card
                        type="inner"
                        title="Payment Information"
                        extra={
                          <Button
                            type="link"
                            icon={<SettingOutlined />}
                            onClick={handleManageSubscription}
                            loading={isCreatingPortal}
                          >
                            Manage
                          </Button>
                        }
                      >
                        <Space direction="vertical">
                          <Text>
                            <CreditCardOutlined /> Visa **** 4242
                          </Text>
                          <Text type="secondary">Expires 12/2025</Text>
                        </Space>
                      </Card>
                    )}

                    {subscriptionStatus?.has_active_subscription && (
                      <Button
                        size="large"
                        icon={<SettingOutlined />}
                        onClick={handleManageSubscription}
                        loading={isCreatingPortal}
                        block
                      >
                        Manage Subscription
                      </Button>
                    )}
                  </Space>
                </Card>
              </Col>

              {/* Upgrade to Premium */}
              {!subscriptionStatus?.has_active_subscription && (
                <Col xs={24} lg={12}>
                  <Card
                    title={
                      <Text style={{ fontSize: '20px', fontWeight: 600, color: '#1890ff' }}>
                        Upgrade to Premium
                      </Text>
                    }
                    style={{ height: '100%', borderColor: '#1890ff' }}
                    headStyle={{ borderBottomColor: '#1890ff' }}
                  >
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                      <Text style={{ fontSize: '16px', color: '#666' }}>
                        Unlock the full potential of our converter.
                      </Text>

                      <div>
                        <Title level={2} style={{ margin: 0, display: 'inline' }}>
                          $4.99
                        </Title>
                        <Text style={{ fontSize: '16px', color: '#666' }}> / month</Text>
                      </div>

                      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>Unlimited file conversions</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>Support for all major banks</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>Batch processing for multiple files</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>Priority customer support</Text>
                        </div>
                      </Space>

                      <Button
                        type="primary"
                        size="large"
                        icon={<RocketOutlined />}
                        onClick={handleUpgrade}
                        loading={isCreatingCheckout}
                        block
                        style={{ height: '50px', fontSize: '16px' }}
                      >
                        Upgrade to Premium
                      </Button>

                      <Text type="secondary" style={{ fontSize: '12px', textAlign: 'center', display: 'block' }}>
                        You can cancel your subscription at any time.
                      </Text>
                    </Space>
                  </Card>
                </Col>
              )}
            </Row>
          )}
        </div>
      </Content>
    </div>
  )
}
