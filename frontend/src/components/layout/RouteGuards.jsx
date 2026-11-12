import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Spinner } from '../ui'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Spinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}

export function GuestRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Spinner />
  // Після входу повертаємо туди, куди користувач ішов
  if (user) return <Navigate to={location.state?.from ?? '/'} replace />
  return <Outlet />
}
