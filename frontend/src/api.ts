import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// 账号
export const getAccounts = (activeOnly = true) =>
  api.get('/accounts', { params: { active_only: activeOnly } })

export const getAuthorizeUrl = () => api.get('/accounts/authorize')

export const updateAccount = (id: number, data: Record<string, string>) =>
  api.put(`/accounts/${id}`, data)

export const deactivateAccount = (id: number) => api.delete(`/accounts/${id}`)

export const refreshAccountToken = (id: number) =>
  api.post(`/accounts/${id}/refresh-token`)

// 文章
export const getArticles = (params?: Record<string, unknown>) =>
  api.get('/articles', { params })

export const getArticle = (id: number) => api.get(`/articles/${id}`)

export const createArticle = (data: Record<string, unknown>) =>
  api.post('/articles', data)

export const updateArticle = (id: number, data: Record<string, unknown>) =>
  api.put(`/articles/${id}`, data)

export const deleteArticle = (id: number) => api.delete(`/articles/${id}`)

export const previewArticle = (id: number) => api.post(`/articles/${id}/preview`)

export const publishArticle = (id: number, data: Record<string, unknown>) =>
  api.post(`/articles/${id}/publish`, data)

// 素材
export const getMaterials = (params?: Record<string, unknown>) =>
  api.get('/materials', { params })

export const uploadMaterial = (formData: FormData) =>
  api.post('/materials/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const deleteMaterial = (id: number) => api.delete(`/materials/${id}`)

export const distributeMaterial = (id: number, accountIds: number[]) =>
  api.post(`/materials/${id}/distribute`, accountIds)

// 数据分析
export const getOverview = () => api.get('/analytics/overview')

export const getAccountStats = (params?: Record<string, string>) =>
  api.get('/analytics/accounts', { params })

export const getAccountTrend = (accountId: number, params?: Record<string, string>) =>
  api.get(`/analytics/account/${accountId}/trend`, { params })

export const getTopArticles = (params?: Record<string, unknown>) =>
  api.get('/analytics/articles/top', { params })

// 排期
export const getSchedule = (params?: Record<string, unknown>) =>
  api.get('/schedule', { params })

export const getCalendar = (year: number, month: number) =>
  api.get('/schedule/calendar', { params: { year, month } })

export const updateSchedule = (id: number, scheduledAt: string) =>
  api.put(`/schedule/${id}`, null, { params: { scheduled_at: scheduledAt } })

export const cancelSchedule = (id: number) => api.delete(`/schedule/${id}`)

// 系统
export const healthCheck = () => api.get('/system/health')

export default api
