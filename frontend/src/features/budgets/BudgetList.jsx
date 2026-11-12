import { useDeleteBudget } from '../../api/queries'
import { Button, EmptyState, ProgressBar } from '../../components/ui'
import { formatMoney } from '../../utils/format'
import styles from './budgets.module.css'

export default function BudgetList({ statuses, onEdit, emptyText = 'Лімітів на цей місяць немає' }) {
  const remove = useDeleteBudget()

  if (!statuses?.length) return <EmptyState>{emptyText}</EmptyState>

  const handleDelete = (status) => {
    if (window.confirm(`Видалити ліміт «${status.category_name}»?`)) remove.mutate(status.budget_id)
  }

  return (
    <ul className={styles.list}>
      {statuses.map((status) => (
        <li key={status.budget_id} className={styles.item}>
          <div className={styles.row}>
            <strong className={styles.name}>{status.category_name}</strong>
            <span className={status.is_exceeded ? 'expense' : 'muted'}>
              {formatMoney(status.spent)} з {formatMoney(status.limit)}
            </span>
            {onEdit && (
              <span className={styles.actions}>
                <Button variant="ghost" size="small" onClick={() => onEdit(status)} aria-label="Змінити ліміт">✎</Button>
                <Button variant="ghost" size="small" onClick={() => handleDelete(status)} aria-label="Видалити">✕</Button>
              </span>
            )}
          </div>
          <ProgressBar percent={status.percent_used} />
          <div className={styles.hint}>
            {status.is_exceeded
              ? <span className="expense">Перевищено на {formatMoney(-Number(status.remaining))}</span>
              : <span>Залишилось {formatMoney(status.remaining)}</span>}
            <span>{status.percent_used}%</span>
          </div>
        </li>
      ))}
    </ul>
  )
}
