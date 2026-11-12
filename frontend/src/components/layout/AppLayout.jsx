import { Suspense } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Button, Spinner } from '../ui'
import styles from './AppLayout.module.css'

const NAV_ITEMS = [
  { to: '/', label: 'Огляд', icon: '◎', end: true },
  { to: '/transactions', label: 'Транзакції', icon: '⇅' },
  { to: '/budgets', label: 'Бюджети', icon: '◔' },
  { to: '/analytics', label: 'Аналітика', icon: '▤' },
  { to: '/categories', label: 'Категорії', icon: '☰' },
  { to: '/profile', label: 'Профіль', icon: '◉' },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  // ?month=... переносимо між сторінками, щоб не скидався обраний місяць
  const { search } = useLocation()

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <NavLink to={{ pathname: '/', search }} className={styles.brand}>
          <img src="/favicon.svg" alt="" className={styles.logo} />
          <span>Трекер</span>
        </NavLink>

        <nav className={styles.nav}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={{ pathname: item.to, search }}
              end={item.end}
              className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
            >
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className={styles.user}>
          <span className={styles.userName}>{user?.name}</span>
          <Button variant="ghost" size="small" onClick={logout}>Вийти</Button>
        </div>
      </aside>

      <main className={styles.main}>
        <Suspense fallback={<Spinner />}>
          <Outlet />
        </Suspense>
      </main>
    </div>
  )
}
