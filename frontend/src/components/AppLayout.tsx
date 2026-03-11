import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  PictureOutlined,
  CalendarOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const { Sider, Content, Header } = Layout

const menuItems = [
  { key: '/admin/dashboard', icon: <DashboardOutlined />, label: '概览' },
  { key: '/admin/accounts', icon: <TeamOutlined />, label: '账号管理' },
  { key: '/admin/articles', icon: <FileTextOutlined />, label: '内容管理' },
  { key: '/admin/materials', icon: <PictureOutlined />, label: '素材库' },
  { key: '/admin/schedule', icon: <CalendarOutlined />, label: '发布排期' },
  { key: '/admin/analytics', icon: <BarChartOutlined />, label: '数据分析' },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ height: 48, margin: 16, textAlign: 'center', color: '#fff', fontSize: collapsed ? 14 : 16, fontWeight: 600, lineHeight: '48px' }}>
          {collapsed ? 'GZH' : '公众号矩阵'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: '#fff', fontSize: 16, fontWeight: 500 }}>
          {menuItems.find(i => location.pathname.startsWith(i.key))?.label || '公众号矩阵管理系统'}
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
