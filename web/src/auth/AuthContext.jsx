import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { api, hasSession, setSession, setSessionExpiredHandler } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(hasSession())

  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null))
    if (!hasSession()) return
    api
      .profile()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const open = useCallback((data) => {
    setSession(data)
    setUser(data.user)
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      setUser,
      login: async (credentials) => open(await api.login(credentials)),
      register: async (payload) => open(await api.register(payload)),
      logout: () => {
        setSession(null)
        setUser(null)
      },
    }),
    [user, loading, open],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
