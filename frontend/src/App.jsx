import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import { GuestRoute, ProtectedRoute } from './components/layout/RouteGuards'
import { Spinner } from './components/ui'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import RegisterPage from './pages/RegisterPage'

// Сторінки за логіном вантажимо ліниво — екран входу не тягне графіки
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const TransactionsPage = lazy(() => import('./pages/TransactionsPage'))
const BudgetsPage = lazy(() => import('./pages/BudgetsPage'))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))
const CategoriesPage = lazy(() => import('./pages/CategoriesPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Spinner />}>
        <Routes>
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/budgets" element={<BudgetsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/categories" element={<CategoriesPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
