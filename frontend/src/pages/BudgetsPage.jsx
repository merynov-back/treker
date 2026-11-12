import { useState } from 'react'
import { useBudgetStatus, useCopyBudgets } from '../api/queries'
import MonthPicker from '../components/MonthPicker'
import PageHeader from '../components/layout/PageHeader'
import { Button, Card, ErrorMessage, Spinner } from '../components/ui'
import BudgetFormModal from '../features/budgets/BudgetFormModal'
import BudgetList from '../features/budgets/BudgetList'
import { useMonthParam } from '../hooks/useMonthParam'
import { formatMoney } from '../utils/format'
import { parseMonthKey } from '../utils/period'
import styles from './pages.module.css'

export default function BudgetsPage() {
  const [month, setMonth] = useMonthParam()
  const { year, month: monthNumber } = parseMonthKey(month)
  const { data: statuses, isLoading, error } = useBudgetStatus(year, monthNumber)
  const copy = useCopyBudgets()

  const [editing, setEditing] = useState(null)
  const [notice, setNotice] = useState('')

  const changeMonth = (value) => {
    setMonth(value)
    setNotice('')
  }

  const handleCopy = () => {
    copy.mutate({ year, month: monthNumber }, {
      onSuccess: (created) => setNotice(
        created.length ? `Перенесено лімітів: ${created.length}` : 'Переносити нічого — у минулому місяці немає нових лімітів',
      ),
    })
  }

  const exceeded = statuses?.filter((status) => status.is_exceeded) ?? []

  return (
    <>
      <PageHeader title="Бюджети та ліміти" subtitle="Скільки можна витратити за місяць">
        <MonthPicker value={month} onChange={changeMonth} />
        <Button variant="secondary" onClick={handleCopy} disabled={copy.isPending}>З минулого місяця</Button>
        <Button onClick={() => setEditing({})}>+ Ліміт</Button>
      </PageHeader>

      <div className={styles.stack}>
        {notice && <p className={styles.notice}>{notice}</p>}
        <ErrorMessage error={error || copy.error} />
        {exceeded.length > 0 && (
          <p className={styles.notice}>
            ⚠️ Перевищено: {exceeded.map((s) => `${s.category_name} (на ${formatMoney(-Number(s.remaining))})`).join(', ')}
          </p>
        )}

        <Card>
          {isLoading ? <Spinner /> : <BudgetList statuses={statuses} onEdit={setEditing} />}
        </Card>
      </div>

      {editing && (
        <BudgetFormModal
          budget={editing.budget_id ? editing : null}
          month={month}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  )
}
