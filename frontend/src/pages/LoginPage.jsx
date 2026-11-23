import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, ErrorMessage, Field } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import styles from './AuthPage.module.css'

const DEMO = import.meta.env.VITE_DEMO === 'true'
const DEMO_ACCOUNT = { email: 'demo@treker.app', password: 'demo12345' }

export default function LoginPage() {
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value })

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await login(form.email, form.password)
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
        {DEMO && (
          <div className={styles.demo}>
            Демо-версія: дані зберігаються лише у вашому браузері.
            <br />
            Тестовий акаунт: <b>{DEMO_ACCOUNT.email}</b> / <b>{DEMO_ACCOUNT.password}</b>
            <br />
            <button type="button" onClick={() => setForm(DEMO_ACCOUNT)}>Підставити дані</button>
          </div>
        )}
        <Card>
          <h1 className={styles.title}>Вхід</h1>
          <p className="muted">Раді бачити знову</p>
          <form className={styles.form} onSubmit={handleSubmit}>
            <Field label="Email" type="email" autoComplete="email" value={form.email} onChange={update('email')} required />
            <Field label="Пароль" type="password" autoComplete="current-password" value={form.password} onChange={update('password')} required />
            <ErrorMessage error={error} />
            <Button type="submit" disabled={submitting}>{submitting ? 'Входимо…' : 'Увійти'}</Button>
          </form>
        </Card>
        <p className={styles.footer}>
          Немає акаунта? <Link to="/register">Зареєструватися</Link>
        </p>
      </div>
    </div>
  )
}
