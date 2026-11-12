const moneyFormatter = new Intl.NumberFormat('uk-UA', {
  style: 'currency',
  currency: 'UAH',
  minimumFractionDigits: 2,
})

const compactFormatter = new Intl.NumberFormat('uk-UA', { notation: 'compact', maximumFractionDigits: 1 })

// API віддає суми рядками ("1250.50"), щоб не губити копійки
export const formatMoney = (value) => moneyFormatter.format(Number(value ?? 0))

export const formatCompact = (value) => compactFormatter.format(Number(value ?? 0))

export function formatDate(iso) {
  const [year, month, day] = iso.split('-')
  return `${day}.${month}.${year}`
}

export function formatPercentChange(current, previous) {
  const prev = Number(previous)
  if (!prev) return null
  const change = ((Number(current) - prev) / prev) * 100
  return Math.round(change)
}
