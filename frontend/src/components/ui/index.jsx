import { useEffect, useId } from 'react'
import styles from './ui.module.css'

const cx = (...classes) => classes.filter(Boolean).join(' ')

export function Button({ variant = 'primary', size, className, ...props }) {
  return <button className={cx(styles.button, styles[variant], size === 'small' && styles.small, className)} {...props} />
}

export function Card({ title, actions, children, className }) {
  return (
    <section className={cx(styles.card, className)}>
      {(title || actions) && (
        <header className={styles.cardHeader}>
          {title && <h2 className={styles.cardTitle}>{title}</h2>}
          {actions}
        </header>
      )}
      {children}
    </section>
  )
}

export function Field({ label, as = 'input', children, ...props }) {
  const id = useId()
  const Component = as
  return (
    <div className={styles.field}>
      {label && <label className={styles.label} htmlFor={id}>{label}</label>}
      <Component id={id} className={styles.input} {...props}>{children}</Component>
    </div>
  )
}

export function ErrorMessage({ error }) {
  if (!error) return null
  return <p className={styles.error} role="alert">{error.message ?? String(error)}</p>
}

export const Spinner = () => <div className={styles.spinner} aria-label="Завантаження" />

export const EmptyState = ({ children }) => <p className={styles.empty}>{children}</p>

export function ProgressBar({ percent }) {
  const tone = percent > 100 ? styles.progressOver : percent >= 80 ? styles.progressWarning : ''
  return (
    <div className={styles.progress}>
      <div className={cx(styles.progressBar, tone)} style={{ width: `${Math.min(percent, 100)}%` }} />
    </div>
  )
}

export function Segmented({ options, value, onChange }) {
  return (
    <div className={styles.segmented} role="tablist">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="tab"
          aria-selected={value === option.value}
          className={cx(styles.segment, value === option.value && styles.segmentActive)}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

export function Modal({ title, onClose, children }) {
  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className={styles.overlay} onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className={styles.modal} role="dialog" aria-modal="true" aria-label={title}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>{title}</h2>
          <Button variant="ghost" onClick={onClose} aria-label="Закрити">✕</Button>
        </div>
        {children}
      </div>
    </div>
  )
}

export const FormActions = ({ children }) => <div className={styles.actions}>{children}</div>
