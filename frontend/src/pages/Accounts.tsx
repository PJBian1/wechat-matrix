import { useEffect, useState } from 'react'
import { Table, Button, Tag, Space, Avatar, message, Input, Modal } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import { getAccounts, getAuthorizeUrl, updateAccount, deactivateAccount, refreshAccountToken } from '../api'

interface Account {
  id: number
  authorizer_appid: string
  nick_name: string | null
  head_img: string | null
  service_type: number | null
  verify_type: number | null
  display_name: string | null
  group_tag: string | null
  is_active: boolean
  authorized_at: string
}

export default function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState({ display_name: '', group_tag: '' })

  const loadAccounts = () => {
    setLoading(true)
    getAccounts(false)
      .then(res => setAccounts(res.data))
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false))
  }

  useEffect(loadAccounts, [])

  const handleAuthorize = async () => {
    try {
      const res = await getAuthorizeUrl()
      window.open(res.data.authorize_url, '_blank')
    } catch {
      message.error('获取授权链接失败')
    }
  }

  const handleRefreshToken = async (id: number) => {
    try {
      await refreshAccountToken(id)
      message.success('Token 已刷新')
    } catch {
      message.error('刷新失败')
    }
  }

  const handleEdit = (account: Account) => {
    setEditingId(account.id)
    setEditForm({ display_name: account.display_name || '', group_tag: account.group_tag || '' })
  }

  const handleSaveEdit = async () => {
    if (editingId === null) return
    try {
      await updateAccount(editingId, editForm)
      message.success('已更新')
      setEditingId(null)
      loadAccounts()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDeactivate = async (id: number) => {
    try {
      await deactivateAccount(id)
      message.success('已停用')
      loadAccounts()
    } catch {
      message.error('操作失败')
    }
  }

  const columns = [
    {
      title: '头像',
      dataIndex: 'head_img',
      width: 60,
      render: (url: string) => <Avatar src={url} />,
    },
    {
      title: '公众号',
      dataIndex: 'nick_name',
      render: (name: string, record: Account) => (
        <div>
          <div>{name || record.authorizer_appid}</div>
          {record.display_name && <div style={{ color: '#999', fontSize: 12 }}>{record.display_name}</div>}
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'service_type',
      width: 100,
      render: (v: number) => v === 2 ? <Tag color="blue">服务号</Tag> : <Tag>订阅号</Tag>,
    },
    {
      title: '分组',
      dataIndex: 'group_tag',
      width: 100,
      render: (tag: string) => tag ? <Tag color="cyan">{tag}</Tag> : '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (v: boolean) => v ? <Tag color="green">活跃</Tag> : <Tag color="red">停用</Tag>,
    },
    {
      title: '操作',
      width: 200,
      render: (_: unknown, record: Account) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRefreshToken(record.id)}>刷新 Token</Button>
          {record.is_active && (
            <Button size="small" danger onClick={() => handleDeactivate(record.id)}>停用</Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAuthorize}>
          添加公众号授权
        </Button>
      </div>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={accounts}
        loading={loading}
        pagination={false}
      />
      <Modal
        title="编辑账号"
        open={editingId !== null}
        onOk={handleSaveEdit}
        onCancel={() => setEditingId(null)}
      >
        <div style={{ marginBottom: 12 }}>
          <label>显示名称</label>
          <Input
            value={editForm.display_name}
            onChange={e => setEditForm({ ...editForm, display_name: e.target.value })}
            placeholder="自定义名称"
          />
        </div>
        <div>
          <label>分组标签</label>
          <Input
            value={editForm.group_tag}
            onChange={e => setEditForm({ ...editForm, group_tag: e.target.value })}
            placeholder="如：教育、健康"
          />
        </div>
      </Modal>
    </div>
  )
}
