import { useState } from 'react'
import { useByCategory, useByPeriod, useSummary } from '../api/queries'
import PageHeader from '../components/layout/PageHeader'
import { Card, ErrorMessage, Segmented, Spinner } from '../components/ui'
import CashflowChart from '../features/analytics/CashflowChart'
import CategoryDonut from '../features/analytics/CategoryDonut'
import SummaryCards from '../features/analytics/SummaryCards'
import tableStyles from '../features/transactions/transactions.module.css'
import { formatMoney } from '../utils/format'
import { currentMonthKey, formatMonthTitle, monthBounds, shiftMonthKey } from '../utils/period'
import styles from './pages.module.css'

const RANGES = [
  { value: 3, label: '3 міс.' },
  { value: 6, label: '6 міс.' },
  { value: 12, label: '12 міс.' },
]

function CategoryTable({ items }) {
  if (!items?.length) return null
  return (
    <div className={tableStyles.tableWrap}>
      <table className={tableStyles.table}>
        <thead>
          <tr>
            <th>Категорія</th>
            <th className={tableStyles.right}>Операцій</th>
            <th className={tableStyles.right}>Сума</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.category_id}>
              <td>{item.category_name}</td>
              <td className={`${tableStyles.right} muted`}>{item.transactions_count}</td>
              <td className={`${tableStyles.right} ${tableStyles.amount}`}>{formatMoney(item.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function AnalyticsPage() {
  const [months, setMonths] = useState(6)

  const lastMonth = currentMonthKey()
  const firstMonth = shiftMonthKey(lastMonth, -(months - 1))
  const period = { date_from: monthBounds(firstMonth).from, date_to: monthBounds(lastMonth).to }

  const summary = useSummary(period)
  const trend = useByPeriod({ ...period, group_by: 'month' })
  const expenses = useByCategory({ ...period, type: 'expense' })
  const incomes = useByCategory({ ...period, type: 'income' })

  return (
    <>
      <PageHeader title="Аналітика" subtitle={`${formatMonthTitle(firstMonth)} — ${formatMonthTitle(lastMonth)}`}>
        <Segmented options={RANGES} value={months} onChange={setMonths} />
      </PageHeader>

      <div className={styles.stack}>
        <ErrorMessage error={summary.error || trend.error} />
        {summary.isLoading ? <Spinner /> : <SummaryCards summary={summary.data} />}

        <Card title="Динаміка по місяцях">
          {trend.isLoading ? <Spinner /> : <CashflowChart points={trend.data} />}
        </Card>

        <div className={styles.gridEqual}>
          <Card title="Витрати за категоріями">
            {expenses.isLoading ? <Spinner /> : (
              <div className={styles.stack}>
                <CategoryDonut items={expenses.data} />
                <CategoryTable items={expenses.data} />
              </div>
            )}
          </Card>
          <Card title="Джерела доходу">
            {incomes.isLoading ? <Spinner /> : (
              <div className={styles.stack}>
                <CategoryDonut items={incomes.data} />
                <CategoryTable items={incomes.data} />
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}
