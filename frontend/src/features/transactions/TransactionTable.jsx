import { useCategories, useDeleteTransaction } from '../../api/queries'
import { Button, EmptyState } from '../../components/ui'
import { formatDate, formatMoney } from '../../utils/format'
import styles from './transactions.module.css'

export default function TransactionTable({ items, onEdit, compact = false, emptyText = 'Транзакцій немає' }) {
  const { data: categories = [] } = useCategories()
  const remove = useDeleteTransaction()
  const names = Object.fromEntries(categories.map((category) => [category.id, category.name]))

  if (!items?.length) return <EmptyState>{emptyText}</EmptyState>

  const handleDelete = (transaction) => {
    if (window.confirm(`Видалити транзакцію на ${formatMoney(transaction.amount)}?`)) {
      remove.mutate(transaction.id)
    }
  }

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Категорія</th>
            {!compact && <th>Опис</th>}
            <th className={styles.right}>Сума</th>
            {onEdit && <th aria-label="Дії" />}
          </tr>
        </thead>
        <tbody>
          {items.map((transaction) => (
            <tr key={transaction.id}>
              <td className="muted">{formatDate(transaction.date)}</td>
              <td>
                {names[transaction.category_id] ?? '—'}
                {compact && transaction.description && <div className={styles.note}>{transaction.description}</div>}
              </td>
              {!compact && <td className="muted">{transaction.description}</td>}
              <td className={`${styles.right} ${styles.amount} ${transaction.type}`}>
                {transaction.type === 'income' ? '+' : '−'}{formatMoney(transaction.amount)}
              </td>
              {onEdit && (
                <td className={styles.rowActions}>
                  <Button variant="ghost" size="small" onClick={() => onEdit(transaction)} aria-label="Редагувати">✎</Button>
                  <Button variant="ghost" size="small" onClick={() => handleDelete(transaction)} aria-label="Видалити">✕</Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
