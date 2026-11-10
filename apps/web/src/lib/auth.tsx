import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api, type Me } from './api'
import { Spinner } from '../components/ui'

interface AuthState {
  user: Me | null
  loading: boolean
  setUser: (u: Me | null) => void
  logout: () => Promise<void>
}
const Ctx = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let live = true
    api.me().then(u => live && setUser(u)).catch(() => live && setUser(null)).finally(() => live && setLoading(false))
    return () => { live = false }
  }, [])

  const logout = useCallback(async () => {
    try { await api.logout() } finally { setUser(null) }
  }, [])

  const value = useMemo(() => ({ user, loading, setUser, logout }), [user, loading, logout])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth(): AuthState {
  const c = useContext(Ctx)
  if (!c) throw new Error('useAuth must be used inside AuthProvider')
  return c
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <Spinner label="Checking your session" />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return <>{children}</>
}

export function RequireAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (user?.role !== 'admin') return <Navigate to="/app" replace />
  return <>{children}</>
}
