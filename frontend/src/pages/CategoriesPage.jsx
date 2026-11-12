import { useState } from 'react'
import { useCategories, useCreateCategory, useDeleteCategory, useRenameCategory } from '../api/queries'
import PageHeader from '../components/layout/PageHeader'
import { Button, Card, EmptyState, ErrorMessage, Field, Spinner } from '../components/ui'
import styles from './pages.module.css'

function CategoryRow({ category, onError }) {
  const rename = useRenameCategory()
  const remove = useDeleteCategory()
  const [name, setName] = useState(null)

  const save = (event) => {
    event.preventDefault()
    rename.mutate({ id: category.id, name }, {
      onSuccess: () => setName(null),
      onError,
    })
  }

  const handleDelete = () => {
    if (window.confirm(`Видалити категорію «${category.name}»?`)) {
      remove.mutate(category.id, { onError })
    }
  }

  if (name !== null) {
    return (
      <li className={styles.categoryItem}>
        <form className={styles.inlineForm} style={{ margin: 0, flex: 1 }} onSubmit={save}>
          <Field aria-label="Нова назва" value={name} onChange={(event) => setName(event.target.value)} maxLength={50} required autoFocus />
          <Button type="submit" size="small" disabled={rename.isPending}>Зберегти</Button>
          <Button type="button" variant="ghost" size="small" onClick={() => setName(null)}>Скасувати</Button>
        </form>
      </li>
    )
  }

  return (
    <li className={styles.categoryItem}>
      <span className={styles.categoryName}>{category.name}</span>
      <Button variant="ghost" size="small" onClick={() => setName(category.name)} aria-label="Перейменувати">✎</Button>
      <Button variant="ghost" size="small" onClick={handleDelete} aria-label="Видалити">✕</Button>
    </li>
  )
}

function CategoryGroup({ title, type, categories }) {
  const create = useCreateCategory()
  const [name, setName] = useState('')
  const [error, setError] = useState(null)

  const handleSubmit = (event) => {
    event.preventDefault()
    setError(null)
    create.mutate({ name, type }, {
      onSuccess: () => setName(''),
      onError: setError,
    })
  }

  const items = categories.filter((category) => category.type === type)

  return (
    <Card title={`${title} · ${items.length}`}>
      <form className={styles.inlineForm} onSubmit={handleSubmit}>
        <Field aria-label="Назва категорії" placeholder="Нова категорія" value={name} onChange={(event) => setName(event.target.value)} maxLength={50} required />
        <Button type="submit" disabled={create.isPending}>Додати</Button>
      </form>
      <ErrorMessage error={error} />
      {items.length ? (
        <ul className={styles.categoryList}>
          {items.map((category) => <CategoryRow key={category.id} category={category} onError={setError} />)}
        </ul>
      ) : (
        <EmptyState>Категорій ще немає</EmptyState>
      )}
    </Card>
  )
}

export default function CategoriesPage() {
  const { data: categories = [], isLoading, error } = useCategories()

  return (
    <>
      <PageHeader title="Категорії" subtitle="Категорію з транзакціями видалити не можна — спершу перенесіть транзакції" />
      <ErrorMessage error={error} />
      {isLoading ? <Spinner /> : (
        <div className={styles.gridEqual}>
          <CategoryGroup title="Витрати" type="expense" categories={categories} />
          <CategoryGroup title="Доходи" type="income" categories={categories} />
        </div>
      )}
    </>
  )
}
