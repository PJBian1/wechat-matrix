import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Input, Button, Space, Select, message, Modal, Checkbox, DatePicker } from 'antd'
import { getArticle, createArticle, updateArticle, previewArticle, publishArticle, getAccounts } from '../api'

const { TextArea } = Input

interface Account {
  id: number
  nick_name: string
  is_active: boolean
}

export default function ArticleEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isNew = !id || id === 'new'

  const [form, setForm] = useState({
    title: '',
    content_md: '',
    author: '',
    digest: '',
    category: '',
    status: 'draft',
  })
  const [previewHtml, setPreviewHtml] = useState('')
  const [showPublish, setShowPublish] = useState(false)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedAccounts, setSelectedAccounts] = useState<number[]>([])
  const [publishType, setPublishType] = useState('freepublish')
  const [scheduledAt, setScheduledAt] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!isNew) {
      getArticle(Number(id)).then(res => {
        const d = res.data
        setForm({
          title: d.title || '',
          content_md: d.content_md || '',
          author: d.author || '',
          digest: d.digest || '',
          category: d.category || '',
          status: d.status || 'draft',
        })
      })
    }
  }, [id, isNew])

  const handleSave = async () => {
    setSaving(true)
    try {
      if (isNew) {
        const res = await createArticle(form)
        message.success('已创建')
        navigate(`/admin/articles/${res.data.id}`)
      } else {
        await updateArticle(Number(id), form)
        message.success('已保存')
      }
    } catch {
      message.error('保存失败')
    }
    setSaving(false)
  }

  const handlePreview = async () => {
    if (isNew) { message.warning('请先保存'); return }
    try {
      const res = await previewArticle(Number(id))
      setPreviewHtml(res.data.html)
    } catch {
      message.error('预览失败')
    }
  }

  const openPublish = async () => {
    if (isNew) { message.warning('请先保存'); return }
    try {
      const res = await getAccounts()
      setAccounts(res.data)
      setShowPublish(true)
    } catch {
      message.error('加载账号失败')
    }
  }

  const handlePublish = async () => {
    if (selectedAccounts.length === 0) { message.warning('请选择账号'); return }
    try {
      await publishArticle(Number(id), {
        account_ids: selectedAccounts,
        publish_type: publishType,
        scheduled_at: scheduledAt || undefined,
      })
      message.success(scheduledAt ? '已添加排期' : '已提交发布')
      setShowPublish(false)
    } catch {
      message.error('发布失败')
    }
  }

  return (
    <div>
      <Card
        title={isNew ? '新建文章' : '编辑文章'}
        extra={
          <Space>
            <Button onClick={() => navigate('/admin/articles')}>返回</Button>
            {!isNew && <Button onClick={handlePreview}>预览</Button>}
            {!isNew && <Button type="primary" onClick={openPublish}>发布</Button>}
          </Space>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <Input
            placeholder="文章标题"
            size="large"
            value={form.title}
            onChange={e => setForm({ ...form, title: e.target.value })}
          />
        </div>
        <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
          <Input
            placeholder="作者"
            style={{ width: 200 }}
            value={form.author}
            onChange={e => setForm({ ...form, author: e.target.value })}
          />
          <Input
            placeholder="分类"
            style={{ width: 200 }}
            value={form.category}
            onChange={e => setForm({ ...form, category: e.target.value })}
          />
        </div>
        <TextArea
          placeholder="Markdown 正文"
          rows={20}
          value={form.content_md}
          onChange={e => setForm({ ...form, content_md: e.target.value })}
          style={{ fontFamily: 'monospace' }}
        />
        <div style={{ marginTop: 16 }}>
          <TextArea
            placeholder="摘要（选填）"
            rows={2}
            value={form.digest}
            onChange={e => setForm({ ...form, digest: e.target.value })}
          />
        </div>
        <div style={{ marginTop: 16, textAlign: 'right' }}>
          <Button type="primary" onClick={handleSave} loading={saving}>保存</Button>
        </div>
      </Card>

      {previewHtml && (
        <Card title="预览" style={{ marginTop: 16 }}>
          <div dangerouslySetInnerHTML={{ __html: previewHtml }} style={{ maxWidth: 600, margin: '0 auto' }} />
        </Card>
      )}

      <Modal
        title="发布文章"
        open={showPublish}
        onOk={handlePublish}
        onCancel={() => setShowPublish(false)}
        width={500}
      >
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 500 }}>选择账号</label>
          <Checkbox.Group
            style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}
            value={selectedAccounts}
            onChange={v => setSelectedAccounts(v as number[])}
          >
            {accounts.map(a => (
              <Checkbox key={a.id} value={a.id}>{a.nick_name || `#${a.id}`}</Checkbox>
            ))}
          </Checkbox.Group>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 500 }}>发布方式</label>
          <Select
            value={publishType}
            onChange={setPublishType}
            style={{ width: '100%', marginTop: 8 }}
            options={[
              { value: 'freepublish', label: '发布（永久链接，不推粉丝）' },
              { value: 'mass_send', label: '群发（推送给粉丝）' },
            ]}
          />
        </div>
        <div>
          <label style={{ fontWeight: 500 }}>定时发布（可选）</label>
          <DatePicker
            showTime
            style={{ width: '100%', marginTop: 8 }}
            onChange={(_, dateStr) => setScheduledAt(dateStr as string || null)}
            placeholder="立即发布"
          />
        </div>
      </Modal>
    </div>
  )
}
