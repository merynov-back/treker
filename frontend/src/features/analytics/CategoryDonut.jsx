import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { EmptyState } from '../../components/ui'
import { formatMoney } from '../../utils/format'
import styles from './analytics.module.css'
import { CATEGORY_PALETTE, tooltipStyle } from './chartTheme'

// Решту дрібних категорій зводимо в «Інше», щоб діаграма лишалась читабельною
const MAX_SLICES = 6

function groupSmall(items) {
  if (items.length <= MAX_SLICES) return items

  const top = items.slice(0, MAX_SLICES - 1)
  const rest = items.slice(MAX_SLICES - 1)
  return [
    ...top,
    {
      category_id: 'rest',
      category_name: `Інше (${rest.length})`,
      total: rest.reduce((sum, item) => sum + Number(item.total), 0),
      percent: Math.round(rest.reduce((sum, item) => sum + item.percent, 0) * 100) / 100,
    },
  ]
}

export default function CategoryDonut({ items, emptyText = 'Даних за період немає' }) {
  if (!items?.length) return <EmptyState>{emptyText}</EmptyState>

  const data = groupSmall(items).map((item) => ({ ...item, value: Number(item.total) }))

  return (
    <div className={styles.donutWrap}>
      <div style={{ height: 200 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="category_name" innerRadius="60%" outerRadius="100%" paddingAngle={2} stroke="none">
              {data.map((item, index) => (
                <Cell key={item.category_id} fill={CATEGORY_PALETTE[index % CATEGORY_PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => formatMoney(value)} {...tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <ul className={styles.legend}>
        {data.map((item, index) => (
          <li key={item.category_id} className={styles.legendItem}>
            <span className={styles.dot} style={{ background: CATEGORY_PALETTE[index % CATEGORY_PALETTE.length] }} />
            <span className={styles.legendName}>{item.category_name}</span>
            <span className={styles.legendValue}>{item.percent}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
