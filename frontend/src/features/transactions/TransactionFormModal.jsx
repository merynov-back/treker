import { useState } from 'react'
import { useCategories, useCreateTransaction, useUpdateTransaction } from '../../api/queries'
import { Button, ErrorMessage, Field, FormActions, Modal, Segmented } from '../../components/ui'
import { todayIso } from '../../utils/period'
import CategorySelect from '../categories/CategorySelect'
import styles from './transactions.module.css'

const TYPE_OPTIONS = [
  { value: 'expense', label: 'Витрата' },
  { value: 'income', label: 'Дохід' },
]

/** transaction — для редагування, без нього форма створює нову */
export default function TransactionFormModal({ transaction, onClose }) {
  const { data: categories = [] } = useCategories()
  const createMutation = useCreateTransaction()
  const updateMutation = useUpdateTransaction()
  const mutation = transaction ? updateMutation : createMutation

  const [type, setType] = useState(transaction?.type ?? 'expense')
  const [form, setForm] = useState({
    category_id: transaction ? String(transaction.category_id) : '',
    amount: transaction?.amount ?? '',
    date: transaction?.date ?? todayIso(),
    description: transaction?.description ?? '',
  })

  const setField = (key) => (event) => setForm({ ...form, [key]: event.target.value })

  const changeType = (value) => {
    setType(value)
    // Категорія іншого типу більше не підходить
    setForm((prev) => ({ ...prev, category_id: '' }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const data = {
      ...form,
      category_id: Number(form.category_id),
      description: form.description.trim() || null,
    }
    const payload = transaction ? { id: transaction.id, data } : data
    mutation.mutate(payload, { onSuccess: onClose })
  }

  return (
    <Modal title={transaction ? 'Редагувати транзакцію' : 'Нова транзакція'} onClose={onClose}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <Segmented options={TYPE_OPTIONS} value={type} onChange={changeType} />
        <div className={styles.formRow}>
          <Field label="Сума, ₴" type="number" inputMode="decimal" step="0.01" min="0.01" value={form.amount} onChange={setField('amount')} required autoFocus />
          <Field label="Дата" type="date" value={form.date} onChange={setField('date')} required />
        </div>
        <CategorySelect
          label="Категорія"
          categories={categories}
          onlyType={type}
          placeholder="Оберіть категорію"
          value={form.category_id}
          onChange={setField('category_id')}
          required
        />
        <Field label="Опис" placeholder="Наприклад, Сільпо" maxLength={255} value={form.description} onChange={setField('description')} />
        <ErrorMessage error={mutation.error} />
        <FormActions>
          <Button type="button" variant="secondary" onClick={onClose}>Скасувати</Button>
          <Button type="submit" disabled={mutation.isPending}>{transaction ? 'Зберегти' : 'Додати'}</Button>
        </FormActions>
      </form>
    </Modal>
  )
}
