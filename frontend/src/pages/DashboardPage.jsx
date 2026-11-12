import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useBudgetStatus, useByCategory, useByPeriod, useSummary, useTransactions } from '../api/queries'
import MonthPicker from '../components/MonthPicker'
import PageHeader from '../components/layout/PageHeader'
import { Button, Card, ErrorMessage, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import BudgetList from '../features/budgets/BudgetList'
import CashflowChart from '../features/analytics/CashflowChart'
import CategoryDonut from '../features/analytics/CategoryDonut'
import SummaryCards from '../features/analytics/SummaryCards'
import TransactionFormModal from '../features/transactions/TransactionFormModal'
import TransactionTable from '../features/transactions/TransactionTable'
import { useMonthParam } from '../hooks/useMonthParam'
import { monthBounds, parseMonthKey, shiftMonthKey } from '../utils/period'
import styles from './pages.module.css'

export default function DashboardPage() {
  const { user } = useAuth()
  const [month, setMonth] = useMonthParam()
  const [creating, setCreating] = useState(false)

  const { from, to } = monthBounds(month)
  const prev = monthBounds(shiftMonthKey(month, -1))
  const { year, month: monthNumber } = parseMonthKey(month)
  const period = { date_from: from, date_to: to }

  const summary = useSummary(period)
  const previousSummary = useSummary({ date_from: prev.from, date_to: prev.to })
  const daily = useByPeriod({ ...period, group_by: 'day' })
  const expenses = useByCategory({ ...period, type: 'expense' })
  const budgets = useBudgetStatus(year, monthNumber)
  const recent = useTransactions({ ...period, limit: 6 })

  return (
    <>
      <PageHeader title={`Привіт, ${user.name.split(' ')[0]}!`} subtitle="Ось як справи з грошима цього місяця">
        <MonthPicker value={month} onChange={setMonth} />
        <Button onClick={() => setCreating(true)}>+ Транзакція</Button>
      </PageHeader>

      <div className={styles.stack}>
        <ErrorMessage error={summary.error} />
        {summary.isLoading ? <Spinner /> : <SummaryCards summary={summary.data} previous={previousSummary.data} />}

        <div className={styles.grid2}>
          <Card title="Доходи і витрати по днях">
            {daily.isLoading ? <Spinner /> : <CashflowChart points={daily.data} />}
          </Card>
          <Card title="Куди йдуть гроші">
            {expenses.isLoading ? <Spinner /> : <CategoryDonut items={expenses.data} emptyText="Витрат цього місяця ще немає" />}
          </Card>
        </div>

        <div className={styles.gridEqual}>
          <Card title="Останні транзакції" actions={<Link className={styles.linkMore} to={`/transactions?month=${month}`}>Усі →</Link>}>
            {recent.isLoading ? <Spinner /> : <TransactionTable items={recent.data?.items} compact emptyText="Цього місяця транзакцій немає" />}
          </Card>
          <Card title="Бюджети" actions={<Link className={styles.linkMore} to={`/budgets?month=${month}`}>Керувати →</Link>}>
            {budgets.isLoading ? <Spinner /> : <BudgetList statuses={budgets.data} emptyText="Лімітів немає — встановіть їх у розділі «Бюджети»" />}
          </Card>
        </div>
      </div>

      {creating && <TransactionFormModal onClose={() => setCreating(false)} />}
    </>
  )
}
