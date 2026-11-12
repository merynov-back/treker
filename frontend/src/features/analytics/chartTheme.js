// SVG-атрибути не розуміють CSS-змінні, тому кольори графіків задаємо явно
export const CHART_COLORS = {
  income: '#10b981',
  expense: '#f43f5e',
  grid: 'rgba(128, 128, 128, 0.18)',
  axis: '#8a91a3',
}

export const CATEGORY_PALETTE = [
  '#6366f1', '#f43f5e', '#f59e0b', '#10b981', '#0ea5e9',
  '#a855f7', '#ec4899', '#84cc16', '#14b8a6', '#f97316',
]

export const tooltipStyle = {
  contentStyle: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text)',
  },
}
