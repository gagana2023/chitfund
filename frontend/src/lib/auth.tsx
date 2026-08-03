import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, clearStoredUserId, getStoredUserId, setStoredUserId } from './api'
import type { User } from './types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (name: string, pin: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedId = getStoredUserId()
    if (storedId === null) {
      setLoading(false)
      return
    }
    api
      .get<User>('/auth/me')
      .then(setUser)
      .catch(() => clearStoredUserId())
      .finally(() => setLoading(false))
  }, [])

  async function login(name: string, pin: string) {
    const loggedInUser = await api.post<User>('/auth/login', { name, pin })
    setStoredUserId(loggedInUser.id)
    setUser(loggedInUser)
  }

  function logout() {
    clearStoredUserId()
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
