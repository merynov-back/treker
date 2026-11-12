import { formatMonthTitle, shiftMonthKey } from '../utils/period'
import { Button } from './ui'
import styles from './ui/ui.module.css'

export default function MonthPicker({ value, onChange }) {
  return (
    <div className={styles.monthPicker}>
      <Button variant="ghost" onClick={() => onChange(shiftMonthKey(value, -1))} aria-label="Попередній місяць">←</Button>
      <span className={styles.monthTitle}>{formatMonthTitle(value)}</span>
      <Button variant="ghost" onClick={() => onChange(shiftMonthKey(value, 1))} aria-label="Наступний місяць">→</Button>
    </div>
  )
}
