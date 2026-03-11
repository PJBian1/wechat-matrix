import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Spin } from 'antd'
import { TeamOutlined, RiseOutlined, ReadOutlined, UserSwitchOutlined } from '@ant-design/icons'
import { getOverview } from '../api'

interface Overview {
  total_accounts: number
  active_accounts: number
  total_fans: number
  daily_net_growth: number
  daily_reads: number
}

export default function Dashboard() {
  const [data, setData] = useState<Overview | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOverview()
      .then(res => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃账号"
              value={data?.active_accounts || 0}
              suffix={`/ ${data?.total_accounts || 0}`}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总粉丝"
              value={data?.total_fans || 0}
              prefix={<UserSwitchOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="日净增粉丝"
              value={data?.daily_net_growth || 0}
              prefix={<RiseOutlined />}
              valueStyle={{ color: (data?.daily_net_growth || 0) >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="日阅读量"
              value={data?.daily_reads || 0}
              prefix={<ReadOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
