import { useState } from 'react'
import { useCategories, useTransactions } from '../api/queries'
import { transactionsApi } from '../api/endpoints'
import MonthPicker from '../components/MonthPicker'
import PageHeader from '../components/layout/PageHeader'
import { Button, Card, ErrorMessage, Field, Spinner } from '../components/ui'
import CategorySelect from '../features/categories/CategorySelect'
import TransactionFormModal from '../features/transactions/TransactionFormModal'
import TransactionTable from '../features/transactions/TransactionTable'
import tableStyles from '../features/transactions/transactions.module.css'
import { useDebounce } from '../hooks/useDebounce'
import { useMonthParam } from '../hooks/useMonthParam'
import { monthBounds } from '../utils/period'

const PAGE_SIZE = 20

export default function TransactionsPage() {
  const [month, setMonth] = useMonthParam()
  const { data: categories = [] } = useCategories()

  const [search, setSearch] = useState('')
  const [type, setType] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [page, setPage] = useState(0)
  // null — модалка закрита, {} — нова транзакція, об'єкт — редагування
  const [editing, setEditing] = useState(null)
  const [exportError, setExportError] = useState(null)

  const debouncedSearch = useDebounce(search.trim())
  const { from, to } = monthBounds(month)
  const filters = { date_from: from, date_to: to, search: debouncedSearch, type, category_id: categoryId }

  const { data, isLoading, isFetching, error } = useTransactions({ ...filters, skip: page * PAGE_SIZE, limit: PAGE_SIZE })
  const total = data?.total ?? 0
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  // Будь-яка зміна фільтра повертає на першу сторінку
  const withReset = (setter) => (value) => {
    setter(value)
    setPage(0)
  }

  const handleExport = async () => {
    setExportError(null)
    try {
      const blob = await transactionsApi.exportCsv(filters)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `transactions-${month}.csv`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setExportError(err)
    }
  }

  return (
    <>
      <PageHeader title="Транзакції" subtitle={`Знайдено: ${total}`}>
        <MonthPicker value={month} onChange={withReset(setMonth)} />
        <Button variant="secondary" onClick={handleExport} disabled={!total}>Експорт CSV</Button>
        <Button onClick={() => setEditing({})}>+ Транзакція</Button>
      </PageHeader>

      <Card>
        <div className={tableStyles.filters}>
          <Field
            type="search"
            placeholder="Пошук за описом або категорією…"
            aria-label="Пошук"
            value={search}
            onChange={(event) => withReset(setSearch)(event.target.value)}
          />
          <Field as="select" aria-label="Тип" value={type} onChange={(event) => withReset(setType)(event.target.value)}>
            <option value="">Усі типи</option>
            <option value="expense">Витрати</option>
            <option value="income">Доходи</option>
          </Field>
          <CategorySelect
            aria-label="Категорія"
            categories={categories}
            onlyType={type || undefined}
            placeholder="Усі категорії"
            value={categoryId}
            onChange={(event) => withReset(setCategoryId)(event.target.value)}
          />
        </div>

        <ErrorMessage error={error || exportError} />
        {isLoading ? (
          <Spinner />
        ) : (
          <TransactionTable
            items={data?.items}
            onEdit={setEditing}
            emptyText={debouncedSearch ? `Нічого не знайдено за «${debouncedSearch}»` : 'Транзакцій за цей місяць немає'}
          />
        )}

        {total > PAGE_SIZE && (
          <div className={tableStyles.pagination}>
            <Button variant="secondary" size="small" disabled={page === 0 || isFetching} onClick={() => setPage(page - 1)}>← Назад</Button>
            <span>Сторінка {page + 1} з {pages}</span>
            <Button variant="secondary" size="small" disabled={page + 1 >= pages || isFetching} onClick={() => setPage(page + 1)}>Далі →</Button>
          </div>
        )}
      </Card>

      {editing && <TransactionFormModal transaction={editing.id ? editing : null} onClose={() => setEditing(null)} />}
    </>
  )
}
