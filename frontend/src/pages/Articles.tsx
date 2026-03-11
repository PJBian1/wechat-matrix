import { useEffect, useState } from 'react'
import { Table, Button, Tag, Space, message, Popconfirm } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getArticles, deleteArticle } from '../api'

interface Article {
  id: number
  title: string
  status: string
  category: string | null
  author: string | null
  created_at: string
  updated_at: string
}

const statusColors: Record<string, string> = {
  draft: 'default',
  ready: 'blue',
  publishing: 'orange',
  published: 'green',
  failed: 'red',
}

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = () => {
    setLoading(true)
    getArticles()
      .then(res => setArticles(res.data))
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleDelete = async (id: number) => {
    try {
      await deleteArticle(id)
      message.success('已删除')
      load()
    } catch {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      render: (title: string, record: Article) => (
        <a onClick={() => navigate(`/admin/articles/${record.id}`)}>{title || '无标题'}</a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (s: string) => <Tag color={statusColors[s] || 'default'}>{s}</Tag>,
    },
    {
      title: '分类',
      dataIndex: 'category',
      width: 100,
      render: (c: string) => c || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      width: 150,
      render: (_: unknown, record: Article) => (
        <Space>
          <Button size="small" onClick={() => navigate(`/admin/articles/${record.id}`)}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/admin/articles/new')}>
          新建文章
        </Button>
      </div>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={articles}
        loading={loading}
        pagination={{ pageSize: 20 }}
      />
    </div>
  )
}
