import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { SESSION_EXPIRED_EVENT } from '../api/client'
import { authApi } from '../api/endpoints'
import { tokenStorage } from '../api/tokenStorage'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(tokenStorage.access))

  const reset = useCallback(() => {
    tokenStorage.clear()
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    if (!tokenStorage.access) return
    authApi.me()
      .then(setUser)
      .catch(reset)
      .finally(() => setLoading(false))
  }, [reset])

  useEffect(() => {
    window.addEventListener(SESSION_EXPIRED_EVENT, reset)
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, reset)
  }, [reset])

  const login = useCallback(async (email, password) => {
    tokenStorage.save(await authApi.login(email, password))
    setUser(await authApi.me())
  }, [])

  const register = useCallback(async ({ name, email, password }) => {
    await authApi.register({ name, email, password })
    await login(email, password)
  }, [login])

  const logout = useCallback(async () => {
    await authApi.logout().catch(() => {})
    reset()
  }, [reset])

  const value = useMemo(
    () => ({ user, setUser, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth має використовуватись всередині AuthProvider')
  return context
}
