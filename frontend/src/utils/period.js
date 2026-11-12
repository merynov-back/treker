const MONTH_NAMES = [
  'Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
  'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень',
]

const pad = (n) => String(n).padStart(2, '0')

// Не toISOString(): він переводить у UTC і вночі дає вчорашню дату
export const toIsoDate = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`

export const todayIso = () => toIsoDate(new Date())

export const toMonthKey = (year, month) => `${year}-${pad(month)}`

export const currentMonthKey = () => {
  const now = new Date()
  return toMonthKey(now.getFullYear(), now.getMonth() + 1)
}

export function parseMonthKey(key) {
  const match = /^(\d{4})-(\d{2})$/.exec(key ?? '')
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  return month >= 1 && month <= 12 ? { year, month } : null
}

export function shiftMonthKey(key, delta) {
  const { year, month } = parseMonthKey(key)
  const date = new Date(year, month - 1 + delta, 1)
  return toMonthKey(date.getFullYear(), date.getMonth() + 1)
}

export function monthBounds(key) {
  const { year, month } = parseMonthKey(key)
  const lastDay = new Date(year, month, 0).getDate()
  return { from: `${key}-01`, to: `${key}-${pad(lastDay)}` }
}

export function formatMonthTitle(key) {
  const { year, month } = parseMonthKey(key)
  return `${MONTH_NAMES[month - 1]} ${year}`
}

export function formatMonthShort(key) {
  const { year, month } = parseMonthKey(key)
  return `${MONTH_NAMES[month - 1].slice(0, 3)} ${String(year).slice(2)}`
}
