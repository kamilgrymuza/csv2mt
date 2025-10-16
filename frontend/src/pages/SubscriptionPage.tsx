import { useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { useQuery } from '@tanstack/react-query'
import axios from '../lib/axios'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
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
  const { t, i18n } = useTranslation()
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

      const priceId = i18n.language === 'pl'
        ? import.meta.env.VITE_STRIPE_PRICE_ID_PLN
        : import.meta.env.VITE_STRIPE_PRICE_ID_USD

      const response = await axios.post(
        `${API_URL}/subscription/create-checkout-session`,
        { price_id: priceId },
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

      const lang = i18n.language || 'en'
      const returnUrl = `${window.location.origin}/${lang}/subscription`

      const response = await axios.post(
        `${API_URL}/subscription/create-portal-session`,
        { return_url: returnUrl },
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
    message.success(t('subscription.subscriptionActivated'))
    // Clear query param
    const lang = i18n.language || 'en'
    navigate(`/${lang}/subscription`, { replace: true })
    refetch()
  }

  // Show canceled message
  if (canceled === 'true') {
    message.info(t('subscription.checkoutCanceled'))
    const lang = i18n.language || 'en'
    navigate(`/${lang}/subscription`, { replace: true })
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader />

      <Content style={{ padding: '48px 24px', background: '#f5f5f5' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: '8px' }}>
            {t('subscription.pageTitle')}
          </Title>
          <Paragraph style={{ textAlign: 'center', fontSize: '16px', color: '#666', marginBottom: '48px' }}>
            {t('subscription.pageSubtitle')}
          </Paragraph>

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '4rem' }}>
              <Spin size="large" />
            </div>
          ) : error ? (
            <Alert
              message={t('subscription.errorLoadingTitle')}
              description={error.message}
              type="error"
              showIcon
            />
          ) : (
            <Row gutter={[24, 24]} justify="center">
              {/* Current Plan */}
              <Col xs={24} lg={subscriptionStatus?.has_active_subscription ? 12 : 12}>
                <Card
                  title={t('subscription.currentPlan')}
                  style={{ height: '100%' }}
                  headStyle={{ fontSize: '20px', fontWeight: 600 }}
                >
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    {subscriptionStatus?.has_active_subscription ? (
                      <>
                        <Tag color={subscriptionStatus.cancel_at_period_end ? "orange" : "green"} style={{ fontSize: '16px', padding: '8px 16px' }}>
                          {subscriptionStatus.cancel_at_period_end ? t('subscription.premiumPlanCanceling') : t('subscription.premiumPlanTag')}
                        </Tag>

                        <div>
                          <Paragraph style={{ marginTop: '16px', marginBottom: '8px' }}>
                            <Text strong>
                              {t('subscription.conversionsUsedLabelPremium', {
                                used: subscriptionStatus?.conversions_used,
                                limit: subscriptionStatus?.conversions_limit
                              })}
                            </Text>
                          </Paragraph>
                          <Progress
                            percent={usagePercentage}
                            status={usagePercentage >= 100 ? 'exception' : 'active'}
                            strokeColor={usagePercentage >= 80 ? '#ff4d4f' : '#52c41a'}
                          />
                        </div>

                        {subscriptionStatus.cancel_at_period_end && subscriptionStatus.current_period_end ? (
                          <Alert
                            message={t('subscription.subscriptionCanceling')}
                            description={
                              <Space direction="vertical" size="small">
                                <Text>{t('subscription.cancelingOn', {
                                  date: new Date(subscriptionStatus.current_period_end).toLocaleDateString(i18n.language === 'pl' ? 'pl-PL' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                                })}</Text>
                                <Text>{t('subscription.retainAccess')}</Text>
                                <Text strong>{t('subscription.noRefunds')}</Text>
                                <Text type="secondary" style={{ fontSize: '12px' }}>{t('subscription.reactivateInfo')}</Text>
                              </Space>
                            }
                            type="warning"
                            showIcon
                          />
                        ) : !subscriptionStatus?.can_convert ? (
                          <Alert
                            message={t('subscription.limitReachedTitle')}
                            description={t('subscription.limitReachedDesc')}
                            type="warning"
                            showIcon
                          />
                        ) : null}
                      </>
                    ) : (
                      <>
                        <div>
                          <Tag color="blue" style={{ fontSize: '16px', padding: '8px 16px' }}>
                            {t('subscription.freePlanTag')}
                          </Tag>
                          <Paragraph style={{ marginTop: '16px', marginBottom: '8px' }}>
                            <Text strong>
                              {t('subscription.conversionsUsedLabel', {
                                used: subscriptionStatus?.conversions_used,
                                limit: subscriptionStatus?.conversions_limit
                              })}
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
                            message={t('subscription.limitReachedTitle')}
                            description={t('subscription.limitReachedDesc')}
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
                        title={t('subscription.paymentInformation')}
                        extra={
                          <Button
                            type="link"
                            icon={<SettingOutlined />}
                            onClick={handleManageSubscription}
                            loading={isCreatingPortal}
                          >
                            {t('subscription.manage')}
                          </Button>
                        }
                      >
                        <Space direction="vertical">
                          <Text>
                            <CreditCardOutlined /> Visa **** 4242
                          </Text>
                          <Text type="secondary">{t('subscription.expiresLabel', { date: '12/2025' })}</Text>
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
                        {t('subscription.manageSubscriptionButton')}
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
                        {t('subscription.upgradeToPremiumTitle')}
                      </Text>
                    }
                    style={{ height: '100%', borderColor: '#1890ff' }}
                    headStyle={{ borderBottomColor: '#1890ff' }}
                  >
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                      <Text style={{ fontSize: '16px', color: '#666' }}>
                        {t('subscription.upgradeToPremiumDesc')}
                      </Text>

                      <div>
                        <Title level={2} style={{ margin: 0, display: 'inline' }}>
                          {i18n.language === 'pl' ? t('landing.pricing.premium.price') : t('landing.pricing.premium.price')}
                        </Title>
                        <Text style={{ fontSize: '16px', color: '#666' }}> {t('subscription.perMonth')}</Text>
                      </div>

                      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>{t('subscription.feature1')}</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>{t('subscription.feature2')}</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>{t('subscription.feature3')}</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                          <Text>{t('subscription.feature4')}</Text>
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
                        {t('subscription.upgradeToPremiumButton')}
                      </Button>

                      <Text type="secondary" style={{ fontSize: '12px', textAlign: 'center', display: 'block' }}>
                        {t('subscription.cancelAnytime')}
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
