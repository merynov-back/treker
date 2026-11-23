// Емуляція REST API в браузері для демо на GitHub Pages.
// Правила ті самі, що в backend/src/services — коди помилок і формат відповідей збігаються
import { load, nextId, save } from './store'
import { seedDemoUser } from './seed'

const TIMEZONE = 'Europe/Kyiv'

export const DEFAULT_CATEGORIES = [
  ['Зарплата', 'income'],
  ['Подарунки', 'income'],
  ['Інше', 'income'],
  ['Продукти', 'expense'],
  ['Транспорт', 'expense'],
  ['Кафе та ресторани', 'expense'],
  ['Комунальні послуги', 'expense'],
  ["Здоров'я", 'expense'],
  ['Розваги', 'expense'],
  ['Інше', 'expense'],
]

class HttpError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : 'error')
    this.status = status
    this.detail = detail
  }
}

const badRequest = (msg) => new HttpError(400, msg)
const unauthorized = (msg) => new HttpError(401, msg)
const notFound = (msg) => new HttpError(404, msg)
const conflict = (msg) => new HttpError(409, msg)
const invalid = (msg) => new HttpError(422, [{ msg }])

function json(status, data, headers = {}) {
  return new Response(data === null ? null : JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
}

// --- дати ---

const pad = (n) => String(n).padStart(2, '0')

export function today() {
  // en-CA дає формат YYYY-MM-DD
  return new Intl.DateTimeFormat('en-CA', { timeZone: TIMEZONE }).format(new Date())
}

export function addDays(iso, days) {
  const d = new Date(`${iso}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

function monthBounds(year, month) {
  const last = new Date(Date.UTC(year, month, 0)).getUTCDate()
  return [`${year}-${pad(month)}-01`, `${year}-${pad(month)}-${pad(last)}`]
}

function parseDate(value, field) {
  if (value === undefined || value === null || value === '') return null
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || Number.isNaN(Date.parse(value))) {
    throw invalid(`Некоректна дата у полі ${field}`)
  }
  return value
}

function resolvePeriod(params) {
  const [y, m] = today().split('-').map(Number)
  const [defFrom, defTo] = monthBounds(y, m)
  const from = parseDate(params.get('date_from'), 'date_from') ?? defFrom
  const to = parseDate(params.get('date_to'), 'date_to') ?? defTo
  if (from > to) throw badRequest('date_from не може бути пізніше за date_to')
  return [from, to]
}

function parseYearMonth(params) {
  const year = Number(params.get('year'))
  const month = Number(params.get('month'))
  if (!Number.isInteger(year) || year < 2000 || year > 2100) throw invalid('Рік має бути від 2000 до 2100')
  if (!Number.isInteger(month) || month < 1 || month > 12) throw invalid('Місяць має бути від 1 до 12')
  return [year, month]
}

// --- гроші: зберігаємо в копійках, щоб не ловити похибки float ---

function toCents(value) {
  const text = String(value ?? '').trim().replace(',', '.')
  if (!/^\d{1,10}(\.\d{1,2})?$/.test(text)) throw invalid('Сума має бути додатним числом з не більш ніж двома знаками після коми')
  const [whole, fraction = ''] = text.split('.')
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, '0'))
  if (cents <= 0) throw invalid('Сума має бути більшою за 0')
  return cents
}

const money = (cents) => (cents / 100).toFixed(2)
const percent = (part, whole) => (whole ? Math.round((part / whole) * 10000) / 100 : 0)

// --- авторизація ---

async function hashPassword(password) {
  if (globalThis.crypto?.subtle) {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`treker:${password}`))
    return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('')
  }
  return `plain:${password}`
}

function randomToken() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID()
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

function issueTokens(db, userId) {
  const sid = randomToken()
  const refresh = randomToken()
  db.sessions[sid] = { userId, refresh }
  return { access_token: `demo.${sid}`, refresh_token: `demo.${sid}.${refresh}`, token_type: 'bearer' }
}

function currentUser(db, headers) {
  const token = (headers.get('Authorization') ?? '').replace(/^Bearer /, '')
  const sid = token.split('.')[1]
  const session = sid && db.sessions[sid]
  if (!session) throw unauthorized('Сесію завершено. Увійдіть знову')
  const user = db.users.find((u) => u.id === session.userId)
  if (!user) throw unauthorized('Користувача не знайдено або деактивовано')
  return { user, sid }
}

function validatePassword(password) {
  if (typeof password !== 'string' || password.length < 8) throw invalid('Пароль має містити щонайменше 8 символів')
  if (new TextEncoder().encode(password).length > 72) throw invalid('Пароль задовгий: максимум 72 байти (≈36 символів кирилицею)')
}

function validateName(name) {
  const value = typeof name === 'string' ? name.trim() : ''
  if (value.length < 2 || value.length > 100) throw invalid("Ім'я має містити від 2 до 100 символів")
  return value
}

const userRead = ({ id, name, email, role, is_active, created_at }) => ({ id, name, email, role, is_active, created_at })

export async function createUser(db, { name, email, password }) {
  const user = {
    id: nextId(db, 'users'),
    name,
    email,
    password: await hashPassword(password),
    role: 'user',
    is_active: true,
    created_at: new Date().toISOString(),
  }
  db.users.push(user)
  for (const [catName, type] of DEFAULT_CATEGORIES) {
    db.categories.push({ id: nextId(db, 'categories'), user_id: user.id, name: catName, type })
  }
  return user
}

// --- категорії ---

const normalizeName = (value) => (typeof value === 'string' ? value.split(/\s+/).filter(Boolean).join(' ') : '')

function validateCategoryName(value) {
  const name = normalizeName(value)
  if (name.length < 1 || name.length > 50) throw invalid('Назва має містити від 1 до 50 символів')
  return name
}

const sameName = (a, b) => a.toLocaleLowerCase('uk') === b.toLocaleLowerCase('uk')
const categoryRead = ({ id, name, type }) => ({ id, name, type })

function userCategory(db, userId, id) {
  const category = db.categories.find((c) => c.id === Number(id) && c.user_id === userId)
  if (!category) throw notFound('Категорію не знайдено')
  return category
}

// --- транзакції ---

function transactionRead(db, t) {
  const category = db.categories.find((c) => c.id === t.category_id)
  return {
    id: t.id,
    category_id: t.category_id,
    type: category.type,
    amount: money(t.amount),
    date: t.date,
    description: t.description,
    created_at: t.created_at,
  }
}

function filterTransactions(db, userId, params) {
  const from = parseDate(params.get('date_from'), 'date_from')
  const to = parseDate(params.get('date_to'), 'date_to')
  if (from && to && from > to) throw badRequest('date_from не може бути пізніше за date_to')
  const categoryId = Number(params.get('category_id')) || null
  const type = params.get('type') || null
  const search = (params.get('search') ?? '').trim().toLocaleLowerCase('uk')

  const categories = new Map(db.categories.filter((c) => c.user_id === userId).map((c) => [c.id, c]))

  return db.transactions
    .filter((t) => {
      if (t.user_id !== userId) return false
      const category = categories.get(t.category_id)
      if (from && t.date < from) return false
      if (to && t.date > to) return false
      if (categoryId && t.category_id !== categoryId) return false
      if (type && category.type !== type) return false
      if (search) {
        const inDescription = (t.description ?? '').toLocaleLowerCase('uk').includes(search)
        const inCategory = category.name.toLocaleLowerCase('uk').includes(search)
        if (!inDescription && !inCategory) return false
      }
      return true
    })
    .sort((a, b) => (a.date === b.date ? b.id - a.id : a.date < b.date ? 1 : -1))
}

function validateDescription(value) {
  if (value === undefined || value === null) return null
  if (typeof value !== 'string' || value.length > 255) throw invalid('Опис — до 255 символів')
  return value
}

function exportCsv(db, items) {
  const escape = (value) => (/[;"\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value)
  const rows = [['Дата', 'Тип', 'Категорія', 'Сума', 'Опис']]
  for (const t of items) {
    const category = db.categories.find((c) => c.id === t.category_id)
    const [y, m, d] = t.date.split('-')
    rows.push([
      `${d}.${m}.${y}`,
      category.type === 'income' ? 'Дохід' : 'Витрата',
      category.name,
      money(t.amount).replace('.', ','),
      t.description ?? '',
    ])
  }
  // BOM — щоб Excel правильно відкрив кирилицю
  return '﻿' + rows.map((row) => row.map(escape).join(';')).join('\r\n') + '\r\n'
}

// --- агрегати ---

function totalsByCategory(db, userId, from, to, type) {
  const totals = new Map()
  for (const t of db.transactions) {
    if (t.user_id !== userId || t.date < from || t.date > to) continue
    const category = db.categories.find((c) => c.id === t.category_id)
    if (type && category.type !== type) continue
    const row = totals.get(category.id) ?? { category, total: 0, count: 0 }
    row.total += t.amount
    row.count += 1
    totals.set(category.id, row)
  }
  return [...totals.values()].sort((a, b) => b.total - a.total)
}

function budgetsFor(db, userId, year, month) {
  return db.budgets
    .filter((b) => b.user_id === userId && b.year === year && b.month === month)
    .sort((a, b) => (a.category_id === null) === (b.category_id === null)
      ? a.id - b.id
      : a.category_id === null ? -1 : 1)
}

const budgetRead = ({ id, category_id, amount, year, month }) => ({ id, category_id, amount: money(amount), year, month })

function budgetStatus(db, userId, year, month) {
  const budgets = budgetsFor(db, userId, year, month)
  if (!budgets.length) return []

  const [from, to] = monthBounds(year, month)
  const spentByCategory = new Map(totalsByCategory(db, userId, from, to, 'expense').map((r) => [r.category.id, r.total]))
  const totalSpent = [...spentByCategory.values()].reduce((sum, v) => sum + v, 0)

  return budgets.map((b) => {
    const spent = b.category_id === null ? totalSpent : spentByCategory.get(b.category_id) ?? 0
    const name = b.category_id === null ? 'Усі витрати' : db.categories.find((c) => c.id === b.category_id).name
    return {
      budget_id: b.id,
      category_id: b.category_id,
      category_name: name,
      limit: money(b.amount),
      spent: money(spent),
      remaining: money(b.amount - spent),
      percent_used: percent(spent, b.amount),
      is_exceeded: spent > b.amount,
    }
  })
}

// --- маршрути ---

const routes = []
const route = (method, pattern, handler, { auth = true } = {}) => routes.push({ method, pattern, handler, auth })

route('POST', /^\/auth\/register$/, async ({ db, body }) => {
  const name = validateName(body.name)
  const email = String(body.email ?? '').trim().toLowerCase()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw invalid('Некоректний email')
  validatePassword(body.password)
  if (db.users.some((u) => u.email === email)) throw conflict('Користувач з таким email вже існує')
  return json(201, userRead(await createUser(db, { name, email, password: body.password })))
}, { auth: false })

route('POST', /^\/auth\/token$/, async ({ db, form }) => {
  const email = String(form.get('username') ?? '').trim().toLowerCase()
  const user = db.users.find((u) => u.email === email)
  if (!user || user.password !== await hashPassword(form.get('password') ?? '')) {
    throw unauthorized('Невірний email або пароль')
  }
  return json(200, issueTokens(db, user.id))
}, { auth: false })

route('POST', /^\/auth\/refresh$/, ({ db, body }) => {
  const [, sid, refresh] = String(body.refresh_token ?? '').split('.')
  const session = db.sessions[sid]
  if (!session || session.refresh !== refresh) throw unauthorized('Сесію завершено. Увійдіть знову')
  delete db.sessions[sid]
  return json(200, issueTokens(db, session.userId))
}, { auth: false })

route('POST', /^\/auth\/logout$/, ({ db, sid }) => {
  delete db.sessions[sid]
  return json(200, { message: 'Сесію завершено' })
})

route('GET', /^\/auth\/me$/, ({ user }) => json(200, userRead(user)))

route('PATCH', /^\/auth\/me$/, ({ user, body }) => {
  user.name = validateName(body.name)
  return json(200, userRead(user))
})

route('POST', /^\/auth\/change-password$/, async ({ db, user, sid, body }) => {
  validatePassword(body.new_password)
  if (user.password !== await hashPassword(body.current_password ?? '')) throw badRequest('Поточний пароль невірний')
  if (body.current_password === body.new_password) throw badRequest('Новий пароль збігається з поточним')
  user.password = await hashPassword(body.new_password)
  for (const [key, session] of Object.entries(db.sessions)) {
    if (session.userId === user.id && key !== sid) delete db.sessions[key]
  }
  return json(200, { message: 'Пароль змінено. Інші сесії завершено' })
})

route('GET', /^\/categories$/, ({ db, user, params }) => {
  const type = params.get('type')
  const items = db.categories
    .filter((c) => c.user_id === user.id && (!type || c.type === type))
    .sort((a, b) => (a.type === b.type ? a.name.localeCompare(b.name, 'uk') : a.type < b.type ? -1 : 1))
  return json(200, items.map(categoryRead))
})

route('POST', /^\/categories$/, ({ db, user, body }) => {
  const name = validateCategoryName(body.name)
  if (!['income', 'expense'].includes(body.type)) throw invalid('Тип має бути income або expense')
  if (db.categories.some((c) => c.user_id === user.id && c.type === body.type && sameName(c.name, name))) {
    throw conflict(`Категорія «${name}» вже існує`)
  }
  const category = { id: nextId(db, 'categories'), user_id: user.id, name, type: body.type }
  db.categories.push(category)
  return json(201, categoryRead(category))
})

route('PATCH', /^\/categories\/(\d+)$/, ({ db, user, body, match }) => {
  const category = userCategory(db, user.id, match[1])
  if (body.name !== undefined && body.name !== null) {
    const name = validateCategoryName(body.name)
    const taken = db.categories.some((c) => c.id !== category.id && c.user_id === user.id
      && c.type === category.type && sameName(c.name, name))
    if (taken) throw conflict(`Категорія «${name}» вже існує`)
    category.name = name
  }
  return json(200, categoryRead(category))
})

route('DELETE', /^\/categories\/(\d+)$/, ({ db, user, match }) => {
  const category = userCategory(db, user.id, match[1])
  if (db.transactions.some((t) => t.category_id === category.id)) {
    throw conflict('Категорія має транзакції. Спочатку видаліть або перенесіть їх')
  }
  db.categories = db.categories.filter((c) => c.id !== category.id)
  db.budgets = db.budgets.filter((b) => b.category_id !== category.id)
  return json(204, null)
})

route('GET', /^\/transactions$/, ({ db, user, params }) => {
  const items = filterTransactions(db, user.id, params)
  const skip = Math.max(Number(params.get('skip')) || 0, 0)
  const limit = Math.min(Math.max(Number(params.get('limit')) || 50, 1), 500)
  return json(200, items.slice(skip, skip + limit).map((t) => transactionRead(db, t)), {
    'X-Total-Count': String(items.length),
  })
})

route('GET', /^\/transactions\/export$/, ({ db, user, params }) => {
  const content = exportCsv(db, filterTransactions(db, user.id, params))
  return new Response(content, {
    status: 200,
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'attachment; filename="transactions.csv"' },
  })
})

route('POST', /^\/transactions$/, ({ db, user, body }) => {
  const category = userCategory(db, user.id, body.category_id)
  const transaction = {
    id: nextId(db, 'transactions'),
    user_id: user.id,
    category_id: category.id,
    amount: toCents(body.amount),
    date: parseDate(body.date, 'date') ?? today(),
    description: validateDescription(body.description),
    created_at: new Date().toISOString(),
  }
  db.transactions.push(transaction)
  return json(201, transactionRead(db, transaction))
})

function userTransaction(db, userId, id) {
  const transaction = db.transactions.find((t) => t.id === Number(id) && t.user_id === userId)
  if (!transaction) throw notFound('Транзакцію не знайдено')
  return transaction
}

route('GET', /^\/transactions\/(\d+)$/, ({ db, user, match }) => json(200, transactionRead(db, userTransaction(db, user.id, match[1]))))

route('PATCH', /^\/transactions\/(\d+)$/, ({ db, user, body, match }) => {
  const transaction = userTransaction(db, user.id, match[1])
  // валідуємо все до змін, щоб не зберегти половину
  const changes = {}
  if (body.category_id != null) changes.category_id = userCategory(db, user.id, body.category_id).id
  if (body.amount != null) changes.amount = toCents(body.amount)
  if (body.date != null) changes.date = parseDate(body.date, 'date')
  if ('description' in body) changes.description = validateDescription(body.description)
  Object.assign(transaction, changes)
  return json(200, transactionRead(db, transaction))
})

route('DELETE', /^\/transactions\/(\d+)$/, ({ db, user, match }) => {
  const transaction = userTransaction(db, user.id, match[1])
  db.transactions = db.transactions.filter((t) => t.id !== transaction.id)
  return json(204, null)
})

route('GET', /^\/budgets$/, ({ db, user, params }) => {
  const [year, month] = parseYearMonth(params)
  return json(200, budgetsFor(db, user.id, year, month).map(budgetRead))
})

route('GET', /^\/budgets\/status$/, ({ db, user, params }) => {
  const [year, month] = parseYearMonth(params)
  return json(200, budgetStatus(db, user.id, year, month))
})

route('POST', /^\/budgets$/, ({ db, user, body }) => {
  const [year, month] = parseYearMonth(new URLSearchParams({ year: body.year, month: body.month }))
  const categoryId = body.category_id ?? null
  if (categoryId !== null) {
    const category = userCategory(db, user.id, categoryId)
    if (category.type !== 'expense') throw badRequest('Ліміт можна встановити тільки на категорію витрат')
  }
  const amount = toCents(body.amount)
  if (budgetsFor(db, user.id, year, month).some((b) => b.category_id === categoryId)) {
    throw conflict('Бюджет на цей місяць для цієї категорії вже існує')
  }
  const budget = { id: nextId(db, 'budgets'), user_id: user.id, category_id: categoryId, amount, year, month }
  db.budgets.push(budget)
  return json(201, budgetRead(budget))
})

route('POST', /^\/budgets\/copy-previous$/, ({ db, user, params }) => {
  const [year, month] = parseYearMonth(params)
  const [prevYear, prevMonth] = month === 1 ? [year - 1, 12] : [year, month - 1]
  const existing = new Set(budgetsFor(db, user.id, year, month).map((b) => b.category_id))
  const created = budgetsFor(db, user.id, prevYear, prevMonth)
    .filter((b) => !existing.has(b.category_id))
    .map((b) => ({ id: nextId(db, 'budgets'), user_id: user.id, category_id: b.category_id, amount: b.amount, year, month }))
  db.budgets.push(...created)
  return json(200, created.map(budgetRead))
})

function userBudget(db, userId, id) {
  const budget = db.budgets.find((b) => b.id === Number(id) && b.user_id === userId)
  if (!budget) throw notFound('Бюджет не знайдено')
  return budget
}

route('PATCH', /^\/budgets\/(\d+)$/, ({ db, user, body, match }) => {
  const budget = userBudget(db, user.id, match[1])
  budget.amount = toCents(body.amount)
  return json(200, budgetRead(budget))
})

route('DELETE', /^\/budgets\/(\d+)$/, ({ db, user, match }) => {
  const budget = userBudget(db, user.id, match[1])
  db.budgets = db.budgets.filter((b) => b.id !== budget.id)
  return json(204, null)
})

route('GET', /^\/analytics\/summary$/, ({ db, user, params }) => {
  const [from, to] = resolvePeriod(params)
  const totals = { income: 0, expense: 0 }
  let count = 0
  for (const row of totalsByCategory(db, user.id, from, to)) {
    totals[row.category.type] += row.total
    count += row.count
  }
  return json(200, {
    date_from: from,
    date_to: to,
    income: money(totals.income),
    expense: money(totals.expense),
    balance: money(totals.income - totals.expense),
    transactions_count: count,
  })
})

route('GET', /^\/analytics\/by-category$/, ({ db, user, params }) => {
  const [from, to] = resolvePeriod(params)
  const rows = totalsByCategory(db, user.id, from, to, params.get('type') || null)
  // відсоток — у межах свого типу
  const typeTotals = { income: 0, expense: 0 }
  rows.forEach((r) => { typeTotals[r.category.type] += r.total })
  return json(200, rows.map((r) => ({
    category_id: r.category.id,
    category_name: r.category.name,
    type: r.category.type,
    total: money(r.total),
    percent: percent(r.total, typeTotals[r.category.type]),
    transactions_count: r.count,
  })))
})

route('GET', /^\/analytics\/by-period$/, ({ db, user, params }) => {
  const [from, to] = resolvePeriod(params)
  const groupBy = params.get('group_by') || 'day'
  const periodOf = groupBy === 'month' ? (iso) => iso.slice(0, 7) : (iso) => iso

  if (groupBy === 'day' && (Date.parse(to) - Date.parse(from)) / 86_400_000 >= 366) {
    throw badRequest('Для періоду довше року використовуйте group_by=month')
  }

  // заповнюємо нулями, щоб на графіку не було дірок
  const buckets = new Map()
  for (let day = from; day <= to; day = addDays(day, 1)) {
    if (!buckets.has(periodOf(day))) buckets.set(periodOf(day), { income: 0, expense: 0 })
  }
  for (const t of db.transactions) {
    if (t.user_id !== user.id || t.date < from || t.date > to) continue
    const type = db.categories.find((c) => c.id === t.category_id).type
    buckets.get(periodOf(t.date))[type] += t.amount
  }
  return json(200, [...buckets].map(([period, v]) => ({
    period,
    income: money(v.income),
    expense: money(v.expense),
    balance: money(v.income - v.expense),
  })))
})

route('GET', /^\/health$/, () => json(200, { status: 'ok', database: 'demo', redis: 'demo' }), { auth: false })

// --- вхідна точка: та сама сигнатура, що й у fetch ---

let ready = null

export async function demoFetch(url, init = {}) {
  const db = load()
  ready ??= seedDemoUser(db).then(save)
  await ready

  const { pathname, searchParams } = new URL(url, globalThis.location?.origin ?? 'http://localhost')
  const path = pathname.replace(/^.*?\/api(?=\/)/, '')
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)

  // невелика затримка — щоб спінери й стани завантаження виглядали як у житті
  await new Promise((resolve) => setTimeout(resolve, 120))

  try {
    for (const r of routes) {
      const match = r.method === method && path.match(r.pattern)
      if (!match) continue

      const ctx = {
        db,
        match,
        params: searchParams,
        body: typeof init.body === 'string' ? JSON.parse(init.body || '{}') : {},
        form: init.body instanceof URLSearchParams ? init.body : new URLSearchParams(),
      }
      if (r.auth) Object.assign(ctx, currentUser(db, headers))

      const response = await r.handler(ctx)
      if (method !== 'GET') save()
      return response
    }
    return json(404, { detail: 'Not Found' })
  } catch (error) {
    if (error instanceof HttpError) return json(error.status, { detail: error.detail })
    console.error(error)
    return json(500, { detail: 'Помилка демо-сервера' })
  }
}
