import { Link } from 'react-router-dom'
import styles from './AuthPage.module.css'

export default function NotFoundPage() {
  return (
    <div className={styles.page}>
      <div className={styles.box} style={{ textAlign: 'center' }}>
        <h1 className={styles.title}>Сторінку не знайдено</h1>
        <p className="muted">Можливо, посилання застаріло.</p>
        <p style={{ marginTop: 16 }}><Link to="/">На головну</Link></p>
      </div>
    </div>
  )
}
