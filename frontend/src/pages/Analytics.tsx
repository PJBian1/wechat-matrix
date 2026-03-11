import { useEffect, useState } from 'react'
import { Card, Table, Select, DatePicker, Row, Col, Tabs, message } from 'antd'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'
import { getAccountStats, getAccountTrend, getTopArticles, getAccounts } from '../api'

const { RangePicker } = DatePicker

interface Account { id: number; nick_name: string }
interface AccountStat {
  account_id: number; nick_name: string; cumulate_user: number
  new_user: number; cancel_user: number; net_growth: number
  total_read_count: number; total_share_count: number
}
interface TrendPoint {
  date: string; cumulate_user: number; new_user: number
  net_growth: number; total_read_count: number
}
interface TopArticle {
  title: string; nick_name: string; reads: number; shares: number; favs: number
}

export default function Analytics() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [accountStats, setAccountStats] = useState<AccountStat[]>([])
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [topArticles, setTopArticles] = useState<TopArticle[]>([])

  useEffect(() => {
    getAccounts().then(res => setAccounts(res.data)).catch(() => {})
    getAccountStats().then(res => setAccountStats(res.data)).catch(() => {})
    getTopArticles({ days: 7, limit: 20 }).then(res => setTopArticles(res.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (selectedAccount) {
      getAccountTrend(selectedAccount)
        .then(res => setTrend(res.data))
        .catch(() => message.error('加载趋势数据失败'))
    }
  }, [selectedAccount])

  const trendOption = {
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['粉丝总数', '净增', '阅读量'] },
    xAxis: { type: 'category' as const, data: trend.map(t => t.date) },
    yAxis: [
      { type: 'value' as const, name: '粉丝' },
      { type: 'value' as const, name: '阅读' },
    ],
    series: [
      { name: '粉丝总数', type: 'line', data: trend.map(t => t.cumulate_user) },
      { name: '净增', type: 'bar', data: trend.map(t => t.net_growth) },
      { name: '阅读量', type: 'line', yAxisIndex: 1, data: trend.map(t => t.total_read_count) },
    ],
  }

  const statsColumns = [
    { title: '公众号', dataIndex: 'nick_name' },
    { title: '粉丝', dataIndex: 'cumulate_user', sorter: (a: AccountStat, b: AccountStat) => a.cumulate_user - b.cumulate_user },
    { title: '新增', dataIndex: 'new_user' },
    { title: '取关', dataIndex: 'cancel_user' },
    { title: '净增', dataIndex: 'net_growth', render: (v: number) => <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>{v}</span> },
    { title: '阅读', dataIndex: 'total_read_count', sorter: (a: AccountStat, b: AccountStat) => a.total_read_count - b.total_read_count },
    { title: '分享', dataIndex: 'total_share_count' },
  ]

  const topColumns = [
    { title: '标题', dataIndex: 'title', ellipsis: true },
    { title: '账号', dataIndex: 'nick_name', width: 120 },
    { title: '阅读', dataIndex: 'reads', width: 80, sorter: (a: TopArticle, b: TopArticle) => a.reads - b.reads },
    { title: '分享', dataIndex: 'shares', width: 80 },
    { title: '收藏', dataIndex: 'favs', width: 80 },
  ]

  return (
    <Tabs
      items={[
        {
          key: 'compare',
          label: '账号对比',
          children: (
            <Card>
              <Table rowKey="account_id" columns={statsColumns} dataSource={accountStats} pagination={false} />
            </Card>
          ),
        },
        {
          key: 'trend',
          label: '趋势分析',
          children: (
            <Card>
              <div style={{ marginBottom: 16 }}>
                <Select
                  style={{ width: 200 }}
                  placeholder="选择账号"
                  value={selectedAccount}
                  onChange={setSelectedAccount}
                  options={accounts.map(a => ({ value: a.id, label: a.nick_name }))}
                />
              </div>
              {trend.length > 0 ? (
                <ReactECharts option={trendOption} style={{ height: 400 }} />
              ) : (
                <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>选择账号查看趋势</div>
              )}
            </Card>
          ),
        },
        {
          key: 'top',
          label: '爆文排行',
          children: (
            <Card>
              <Table rowKey="title" columns={topColumns} dataSource={topArticles} pagination={{ pageSize: 20 }} />
            </Card>
          ),
        },
      ]}
    />
  )
}
