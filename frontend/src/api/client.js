import { tokenStorage } from './tokenStorage'

const API_URL = import.meta.env.VITE_API_URL ?? '/api'

// Демо-збірка для GitHub Pages: бекенду немає, API емулюється в браузері
const DEMO = import.meta.env.VITE_DEMO === 'true'
let demoServer = null

async function apiFetch(url, init) {
  if (!DEMO) return fetch(url, init)
  demoServer ??= import('./demo/server')
  return (await demoServer).demoFetch(url, init)
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

// Подія для AuthContext: сесія злетіла, треба показати логін
export const SESSION_EXPIRED_EVENT = 'auth:session-expired'

function buildUrl(path, params) {
  const url = API_URL + path
  if (!params) return url

  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.append(key, value)
  })
  const qs = query.toString()
  return qs ? `${url}?${qs}` : url
}

async function parseError(response) {
  const data = await response.json().catch(() => null)
  const detail = data?.detail

  if (Array.isArray(detail)) {
    // Помилки валідації FastAPI: [{loc, msg}, ...]
    return detail.map((item) => item.msg.replace(/^Value error, /, '')).join('; ')
  }
  return detail || `Помилка сервера (${response.status})`
}

// Кілька запитів одночасно отримали 401 — оновлюємо токени лише один раз
let refreshPromise = null

function refreshTokens() {
  if (!refreshPromise) {
    refreshPromise = apiFetch(buildUrl('/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: tokenStorage.refresh }),
    })
      .then(async (response) => {
        if (!response.ok) return false
        tokenStorage.save(await response.json())
        return true
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

/**
 * Запит до API.
 * body — JSON, form — x-www-form-urlencoded, raw — повернути Response як є
 */
export async function request(path, { method = 'GET', params, body, form, raw = false, retry = true } = {}) {
  const headers = {}
  if (tokenStorage.access) headers.Authorization = `Bearer ${tokenStorage.access}`

  let payload
  if (form) {
    payload = new URLSearchParams(form)
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  const response = await apiFetch(buildUrl(path, params), { method, headers, body: payload })

  if (response.status === 401 && retry && tokenStorage.refresh) {
    if (await refreshTokens()) {
      return request(path, { method, params, body, form, raw, retry: false })
    }
    tokenStorage.clear()
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
  }

  if (!response.ok) throw new ApiError(response.status, await parseError(response))
  if (raw) return response
  if (response.status === 204) return null
  return response.json()
}
