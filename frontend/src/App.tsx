import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import Articles from './pages/Articles'
import ArticleEdit from './pages/ArticleEdit'
import Materials from './pages/Materials'
import Schedule from './pages/Schedule'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="/admin/dashboard" element={<Dashboard />} />
        <Route path="/admin/accounts" element={<Accounts />} />
        <Route path="/admin/articles" element={<Articles />} />
        <Route path="/admin/articles/new" element={<ArticleEdit />} />
        <Route path="/admin/articles/:id" element={<ArticleEdit />} />
        <Route path="/admin/materials" element={<Materials />} />
        <Route path="/admin/schedule" element={<Schedule />} />
        <Route path="/admin/analytics" element={<Analytics />} />
      </Route>
      <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
    </Routes>
  )
}
