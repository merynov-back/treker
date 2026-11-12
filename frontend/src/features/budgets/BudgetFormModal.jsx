import { useState } from 'react'
import { useCategories, useCreateBudget, useUpdateBudget } from '../../api/queries'
import { Button, ErrorMessage, Field, FormActions, Modal } from '../../components/ui'
import { formatMonthTitle, parseMonthKey } from '../../utils/period'
import CategorySelect from '../categories/CategorySelect'
import styles from '../transactions/transactions.module.css'

/** budget — статус бюджету для редагування суми, без нього створюємо новий ліміт */
export default function BudgetFormModal({ budget, month, onClose }) {
  const { data: categories = [] } = useCategories()
  const createMutation = useCreateBudget()
  const updateMutation = useUpdateBudget()
  const mutation = budget ? updateMutation : createMutation

  const [categoryId, setCategoryId] = useState('')
  const [amount, setAmount] = useState(budget?.limit ?? '')

  const handleSubmit = (event) => {
    event.preventDefault()
    if (budget) {
      mutation.mutate({ id: budget.budget_id, amount }, { onSuccess: onClose })
      return
    }
    const { year, month: monthNumber } = parseMonthKey(month)
    mutation.mutate(
      { category_id: categoryId ? Number(categoryId) : null, amount, year, month: monthNumber },
      { onSuccess: onClose },
    )
  }

  return (
    <Modal title={budget ? `Ліміт: ${budget.category_name}` : `Новий ліміт · ${formatMonthTitle(month)}`} onClose={onClose}>
      <form className={styles.form} onSubmit={handleSubmit}>
        {!budget && (
          <CategorySelect
            label="На що"
            categories={categories}
            onlyType="expense"
            placeholder="Усі витрати за місяць"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
          />
        )}
        <Field
          label="Ліміт, ₴"
          type="number"
          inputMode="decimal"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          required
          autoFocus
        />
        <ErrorMessage error={mutation.error} />
        <FormActions>
          <Button type="button" variant="secondary" onClick={onClose}>Скасувати</Button>
          <Button type="submit" disabled={mutation.isPending}>Зберегти</Button>
        </FormActions>
      </form>
    </Modal>
  )
}
