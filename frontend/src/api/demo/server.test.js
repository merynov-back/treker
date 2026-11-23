import { describe, expect, it } from 'vitest'
import { demoFetch } from './server'
import { DEMO_EMAIL, DEMO_PASSWORD } from './seed'

async function call(path, { method = 'GET', token, body, form } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  const init = { method, headers }
  if (form) init.body = new URLSearchParams(form)
  if (body) init.body = JSON.stringify(body)
  const response = await demoFetch(`/api${path}`, init)
  const text = await response.text()
  return { status: response.status, headers: response.headers, data: text && response.headers.get('Content-Type')?.includes('json') ? JSON.parse(text) : text }
}

async function login(email, password) {
  const { data } = await call('/auth/token', { method: 'POST', form: { username: email, password } })
  return data
}

describe('демо-API', () => {
  it('демо-акаунт має дані для графіків', async () => {
    const { access_token } = await login(DEMO_EMAIL, DEMO_PASSWORD)
    const list = await call('/transactions?limit=5', { token: access_token })
    expect(list.status).toBe(200)
    expect(Number(list.headers.get('X-Total-Count'))).toBeGreaterThan(5)

    const summary = await call('/analytics/summary', { token: access_token })
    expect(Number(summary.data.income)).toBeGreaterThan(0)
  })

  it('реєстрація створює стандартні категорії, дублікат email — 409', async () => {
    const user = { name: 'Іван', email: 'ivan@example.com', password: 'StrongPass1!' }
    expect((await call('/auth/register', { method: 'POST', body: user })).status).toBe(201)
    expect((await call('/auth/register', { method: 'POST', body: user })).status).toBe(409)

    const { access_token } = await login(user.email, user.password)
    const categories = await call('/categories', { token: access_token })
    expect(categories.data).toHaveLength(10)
  })

  it('транзакція впливає на підсумок і бюджет', async () => {
    const { access_token: token } = await login('ivan@example.com', 'StrongPass1!')
    const food = (await call('/categories?type=expense', { token })).data.find((c) => c.name === 'Продукти')
    const created = await call('/transactions', { method: 'POST', token, body: { category_id: food.id, amount: '150.50', description: 'Сільпо' } })
    expect(created.status).toBe(201)
    expect(created.data.amount).toBe('150.50')

    const [year, month] = created.data.date.split('-').map(Number)
    await call('/budgets', { method: 'POST', token, body: { category_id: food.id, amount: '100', year, month } })
    const status = await call(`/budgets/status?year=${year}&month=${month}`, { token })
    expect(status.data[0]).toMatchObject({ spent: '150.50', is_exceeded: true })

    const search = await call('/transactions?search=сіЛЬпо', { token })
    expect(search.data).toHaveLength(1)
  })

  it('категорії унікальні без урахування регістру', async () => {
    const { access_token: token } = await login('ivan@example.com', 'StrongPass1!')
    const res = await call('/categories', { method: 'POST', token, body: { name: 'продукти', type: 'expense' } })
    expect(res.status).toBe(409)
  })

  it('refresh-токен одноразовий, logout завершує сесію', async () => {
    const tokens = await login('ivan@example.com', 'StrongPass1!')
    const refreshed = await call('/auth/refresh', { method: 'POST', body: { refresh_token: tokens.refresh_token } })
    expect(refreshed.status).toBe(200)
    expect((await call('/auth/refresh', { method: 'POST', body: { refresh_token: tokens.refresh_token } })).status).toBe(401)

    await call('/auth/logout', { method: 'POST', token: refreshed.data.access_token })
    expect((await call('/auth/me', { token: refreshed.data.access_token })).status).toBe(401)
  })

  it('невалідна сума — 422', async () => {
    const { access_token: token } = await login('ivan@example.com', 'StrongPass1!')
    const [category] = (await call('/categories', { token })).data
    const res = await call('/transactions', { method: 'POST', token, body: { category_id: category.id, amount: '-5' } })
    expect(res.status).toBe(422)
  })
})
