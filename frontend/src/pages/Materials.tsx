import { useEffect, useState } from 'react'
import { Card, Row, Col, Button, Upload, Select, message, Popconfirm, Empty } from 'antd'
import { UploadOutlined, DeleteOutlined } from '@ant-design/icons'
import { getMaterials, deleteMaterial, getAccounts } from '../api'

interface Material {
  id: number
  account_id: number
  media_type: string
  media_id: string
  wx_url: string | null
  title: string | null
  file_name: string | null
  file_size: number | null
  created_at: string
}

interface Account {
  id: number
  nick_name: string
}

export default function Materials() {
  const [materials, setMaterials] = useState<Material[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [filterAccountId, setFilterAccountId] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)
  const [uploadAccountId, setUploadAccountId] = useState<number | null>(null)

  const load = () => {
    setLoading(true)
    getMaterials({ account_id: filterAccountId })
      .then(res => setMaterials(res.data))
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    getAccounts().then(res => setAccounts(res.data)).catch(() => {})
    load()
  }, [filterAccountId])

  const handleDelete = async (id: number) => {
    try {
      await deleteMaterial(id)
      message.success('已删除')
      load()
    } catch {
      message.error('删除失败')
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center' }}>
        <Select
          style={{ width: 200 }}
          placeholder="上传到账号"
          value={uploadAccountId}
          onChange={setUploadAccountId}
          options={accounts.map(a => ({ value: a.id, label: a.nick_name }))}
        />
        <Upload
          action="/api/materials/upload"
          data={{ account_id: uploadAccountId || '', media_type: 'image' }}
          showUploadList={false}
          disabled={!uploadAccountId}
          onChange={info => {
            if (info.file.status === 'done') { message.success('上传成功'); load() }
            if (info.file.status === 'error') message.error('上传失败')
          }}
        >
          <Button icon={<UploadOutlined />} disabled={!uploadAccountId}>上传素材</Button>
        </Upload>
        <Select
          style={{ width: 200 }}
          placeholder="按账号筛选"
          allowClear
          value={filterAccountId}
          onChange={setFilterAccountId}
          options={accounts.map(a => ({ value: a.id, label: a.nick_name }))}
        />
      </div>

      {materials.length === 0 && !loading ? (
        <Empty description="暂无素材" />
      ) : (
        <Row gutter={[16, 16]}>
          {materials.map(m => (
            <Col key={m.id} xs={24} sm={12} md={8} lg={6}>
              <Card
                hoverable
                cover={
                  m.wx_url ? (
                    <img src={m.wx_url} alt={m.title || ''} style={{ height: 160, objectFit: 'cover' }} />
                  ) : (
                    <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
                      {m.media_type}
                    </div>
                  )
                }
                actions={[
                  <Popconfirm key="delete" title="确认删除？" onConfirm={() => handleDelete(m.id)}>
                    <DeleteOutlined />
                  </Popconfirm>,
                ]}
              >
                <Card.Meta
                  title={m.title || m.file_name || m.media_id}
                  description={`${m.media_type} | ${new Date(m.created_at).toLocaleDateString('zh-CN')}`}
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  )
}
