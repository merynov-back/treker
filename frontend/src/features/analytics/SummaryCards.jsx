import { Card } from '../../components/ui'
import { formatMoney, formatPercentChange } from '../../utils/format'
import styles from './analytics.module.css'

function Delta({ current, previous, inverse = false }) {
  const change = formatPercentChange(current, previous)
  if (change === null) return <span className={styles.delta}>немає даних за минулий період</span>

  // Для витрат зростання — погано, тому колір інвертуємо
  const good = inverse ? change <= 0 : change >= 0
  return (
    <span className={styles.delta}>
      <span className={good ? 'income' : 'expense'}>{change > 0 ? '+' : ''}{change}%</span> до минулого періоду
    </span>
  )
}

export default function SummaryCards({ summary, previous }) {
  const balance = Number(summary?.balance ?? 0)

  return (
    <div className={styles.stats}>
      <Card className={styles.stat}>
        <span className={styles.statLabel}>Доходи</span>
        <span className={`${styles.statValue} income`}>{formatMoney(summary?.income)}</span>
        {previous && <Delta current={summary?.income} previous={previous.income} />}
      </Card>
      <Card className={styles.stat}>
        <span className={styles.statLabel}>Витрати</span>
        <span className={`${styles.statValue} expense`}>{formatMoney(summary?.expense)}</span>
        {previous && <Delta current={summary?.expense} previous={previous.expense} inverse />}
      </Card>
      <Card className={styles.stat}>
        <span className={styles.statLabel}>Баланс</span>
        <span className={`${styles.statValue} ${balance >= 0 ? 'income' : 'expense'}`}>{formatMoney(balance)}</span>
        <span className={styles.delta}>доходи мінус витрати</span>
      </Card>
      <Card className={styles.stat}>
        <span className={styles.statLabel}>Транзакцій</span>
        <span className={styles.statValue}>{summary?.transactions_count ?? 0}</span>
        <span className={styles.delta}>за обраний період</span>
      </Card>
    </div>
  )
}
