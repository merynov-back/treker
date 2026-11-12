import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../api/endpoints'
import PageHeader from '../components/layout/PageHeader'
import { Button, Card, ErrorMessage, Field } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import styles from './pages.module.css'

const EMPTY_PASSWORDS = { current_password: '', new_password: '', confirm: '' }

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth()
  const [name, setName] = useState(user.name)
  const [passwords, setPasswords] = useState(EMPTY_PASSWORDS)
  const [passwordError, setPasswordError] = useState(null)

  const updateName = useMutation({ mutationFn: authApi.updateMe, onSuccess: setUser })
  const changePassword = useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => setPasswords(EMPTY_PASSWORDS),
  })

  const setPasswordField = (key) => (event) => setPasswords({ ...passwords, [key]: event.target.value })

  const handlePasswordSubmit = (event) => {
    event.preventDefault()
    setPasswordError(null)
    if (passwords.new_password !== passwords.confirm) {
      setPasswordError(new Error('Нові паролі не збігаються'))
      return
    }
    changePassword.mutate({ current_password: passwords.current_password, new_password: passwords.new_password })
  }

  return (
    <>
      <PageHeader title="Профіль">
        <Button variant="secondary" onClick={logout}>Вийти з акаунта</Button>
      </PageHeader>

      <div className={styles.gridEqual}>
        <div className={styles.stack}>
          <Card title="Акаунт">
            <dl className={styles.meta}>
              <dt>Email</dt>
              <dd>{user.email}</dd>
              <dt>З нами з</dt>
              <dd>{new Date(user.created_at).toLocaleDateString('uk-UA')}</dd>
            </dl>
          </Card>

          <Card title="Ім'я">
            <form
              className={styles.formStack}
              onSubmit={(event) => {
                event.preventDefault()
                updateName.mutate({ name })
              }}
            >
              <Field label="Як до вас звертатися" value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={100} required />
              <ErrorMessage error={updateName.error} />
              {updateName.isSuccess && <p className={styles.success}>Збережено</p>}
              <div>
                <Button type="submit" disabled={updateName.isPending || name === user.name}>Зберегти</Button>
              </div>
            </form>
          </Card>
        </div>

        <Card title="Зміна пароля">
          <form className={styles.formStack} onSubmit={handlePasswordSubmit}>
            <Field label="Поточний пароль" type="password" autoComplete="current-password" value={passwords.current_password} onChange={setPasswordField('current_password')} required />
            <Field label="Новий пароль" type="password" autoComplete="new-password" value={passwords.new_password} onChange={setPasswordField('new_password')} minLength={8} maxLength={72} required />
            <Field label="Повторіть новий пароль" type="password" autoComplete="new-password" value={passwords.confirm} onChange={setPasswordField('confirm')} required />
            <ErrorMessage error={passwordError || changePassword.error} />
            {changePassword.isSuccess && <p className={styles.success}>Пароль змінено. На інших пристроях потрібно буде увійти знову</p>}
            <div>
              <Button type="submit" disabled={changePassword.isPending}>Змінити пароль</Button>
            </div>
          </form>
        </Card>
      </div>
    </>
  )
}
