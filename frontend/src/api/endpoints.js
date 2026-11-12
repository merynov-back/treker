import { request } from './client'

export const authApi = {
  register: (data) => request('/auth/register', { method: 'POST', body: data }),
  login: (email, password) => request('/auth/token', { method: 'POST', form: { username: email, password } }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  updateMe: (data) => request('/auth/me', { method: 'PATCH', body: data }),
  changePassword: (data) => request('/auth/change-password', { method: 'POST', body: data }),
}

export const categoriesApi = {
  list: (type) => request('/categories', { params: { type } }),
  create: (data) => request('/categories', { method: 'POST', body: data }),
  rename: (id, name) => request(`/categories/${id}`, { method: 'PATCH', body: { name } }),
  remove: (id) => request(`/categories/${id}`, { method: 'DELETE' }),
}

export const transactionsApi = {
  async list(params) {
    const response = await request('/transactions', { params, raw: true })
    return {
      items: await response.json(),
      total: Number(response.headers.get('X-Total-Count') ?? 0),
    }
  },
  create: (data) => request('/transactions', { method: 'POST', body: data }),
  update: (id, data) => request(`/transactions/${id}`, { method: 'PATCH', body: data }),
  remove: (id) => request(`/transactions/${id}`, { method: 'DELETE' }),
  async exportCsv(params) {
    const response = await request('/transactions/export', { params, raw: true })
    return response.blob()
  },
}

export const budgetsApi = {
  list: (year, month) => request('/budgets', { params: { year, month } }),
  status: (year, month) => request('/budgets/status', { params: { year, month } }),
  create: (data) => request('/budgets', { method: 'POST', body: data }),
  update: (id, amount) => request(`/budgets/${id}`, { method: 'PATCH', body: { amount } }),
  remove: (id) => request(`/budgets/${id}`, { method: 'DELETE' }),
  copyPrevious: (year, month) => request('/budgets/copy-previous', { method: 'POST', params: { year, month } }),
}

export const analyticsApi = {
  summary: (params) => request('/analytics/summary', { params }),
  byCategory: (params) => request('/analytics/by-category', { params }),
  byPeriod: (params) => request('/analytics/by-period', { params }),
}
