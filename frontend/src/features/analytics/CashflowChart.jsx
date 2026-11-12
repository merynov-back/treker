import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatCompact, formatMoney } from '../../utils/format'
import { formatMonthShort } from '../../utils/period'
import styles from './analytics.module.css'
import { CHART_COLORS, tooltipStyle } from './chartTheme'

// period приходить як "2026-10-05" (день) або "2026-10" (місяць)
const formatPeriod = (period) => (period.length === 7 ? formatMonthShort(period) : period.slice(8))

export default function CashflowChart({ points }) {
  const data = (points ?? []).map((point) => ({
    period: point.period,
    income: Number(point.income),
    expense: Number(point.expense),
  }))

  return (
    <div className={styles.chart}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke={CHART_COLORS.grid} />
          <XAxis dataKey="period" tickFormatter={formatPeriod} tick={{ fill: CHART_COLORS.axis, fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={formatCompact} tick={{ fill: CHART_COLORS.axis, fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
          <Tooltip
            formatter={(value) => formatMoney(value)}
            labelFormatter={(period) => (period.length === 7 ? formatMonthShort(period) : period.split('-').reverse().join('.'))}
            cursor={{ fill: CHART_COLORS.grid }}
            {...tooltipStyle}
          />
          <Legend iconType="circle" />
          <Bar dataKey="income" name="Доходи" fill={CHART_COLORS.income} radius={[4, 4, 0, 0]} maxBarSize={28} />
          <Bar dataKey="expense" name="Витрати" fill={CHART_COLORS.expense} radius={[4, 4, 0, 0]} maxBarSize={28} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
