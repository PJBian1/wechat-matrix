import { useEffect, useState } from 'react'
import { Calendar, Badge, Card, List, Tag, Button, message, Popconfirm } from 'antd'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import { getCalendar, cancelSchedule } from '../api'

interface ScheduleItem {
  id: number
  article_id: number
  article_title: string
  account_id: number
  nick_name: string
  scheduled_at: string
  publish_type: string
  status: string
}

export default function Schedule() {
  const [items, setItems] = useState<ScheduleItem[]>([])
  const [currentMonth, setCurrentMonth] = useState(dayjs())

  const load = (d: Dayjs) => {
    getCalendar(d.year(), d.month() + 1)
      .then(res => setItems(res.data))
      .catch(() => {})
  }

  useEffect(() => { load(currentMonth) }, [currentMonth])

  const handleCancel = async (id: number) => {
    try {
      await cancelSchedule(id)
      message.success('已取消')
      load(currentMonth)
    } catch {
      message.error('取消失败')
    }
  }

  const dateCellRender = (date: Dayjs) => {
    const dateStr = date.format('YYYY-MM-DD')
    const dayItems = items.filter(i => i.scheduled_at?.startsWith(dateStr))
    return (
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {dayItems.map(item => (
          <li key={item.id}>
            <Badge
              status={item.status === 'pending' ? 'processing' : item.status === 'published' ? 'success' : 'default'}
              text={<span style={{ fontSize: 12 }}>{item.article_title?.slice(0, 8)}</span>}
            />
          </li>
        ))}
      </ul>
    )
  }

  const pendingItems = items.filter(i => i.status === 'pending')

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1 }}>
        <Calendar
          cellRender={(date) => dateCellRender(date as Dayjs)}
          onPanelChange={d => setCurrentMonth(d)}
        />
      </div>
      <Card title="待发布" style={{ width: 320 }}>
        <List
          size="small"
          dataSource={pendingItems}
          renderItem={item => (
            <List.Item
              actions={[
                <Popconfirm key="cancel" title="取消排期？" onConfirm={() => handleCancel(item.id)}>
                  <Button size="small" danger>取消</Button>
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={item.article_title}
                description={
                  <div>
                    <div>{item.nick_name}</div>
                    <div style={{ fontSize: 12 }}>
                      {dayjs(item.scheduled_at).format('MM-DD HH:mm')}
                      <Tag style={{ marginLeft: 4 }}>{item.publish_type === 'freepublish' ? '发布' : '群发'}</Tag>
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无排期' }}
        />
      </Card>
    </div>
  )
}
