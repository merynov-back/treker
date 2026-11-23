import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, ErrorMessage, Field } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import styles from './AuthPage.module.css'

export default function RegisterPage() {
  const { register } = useAuth()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value })

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (form.password !== form.confirm) {
      setError(new Error('Паролі не збігаються'))
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await register(form)
    } catch (err) {
      setError(err)
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.box}>
        <div className={styles.brand}>
          <img src={`${import.meta.env.BASE_URL}favicon.svg`} alt="" />
          Трекер фінансів
        </div>
        <Card>
          <h1 className={styles.title}>Реєстрація</h1>
          <p className="muted">Стандартні категорії створимо автоматично</p>
          <form className={styles.form} onSubmit={handleSubmit}>
            <Field label="Ім'я" autoComplete="name" value={form.name} onChange={update('name')} required minLength={2} maxLength={100} />
            <Field label="Email" type="email" autoComplete="email" value={form.email} onChange={update('email')} required />
            <Field label="Пароль" type="password" autoComplete="new-password" value={form.password} onChange={update('password')} required minLength={8} maxLength={72} />
            <Field label="Повторіть пароль" type="password" autoComplete="new-password" value={form.confirm} onChange={update('confirm')} required />
            <ErrorMessage error={error} />
            <Button type="submit" disabled={submitting}>{submitting ? 'Створюємо…' : 'Створити акаунт'}</Button>
          </form>
        </Card>
        <p className={styles.footer}>
          Вже є акаунт? <Link to="/login">Увійти</Link>
        </p>
      </div>
    </div>
  )
}
