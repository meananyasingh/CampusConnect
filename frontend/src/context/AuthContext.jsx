import { useEffect, useMemo, useState } from 'react'

import { authService } from '../services/authService.js'
import { tokenStorage } from '../services/tokenStorage.js'
import { AuthContext } from './auth-context.js'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => tokenStorage.getUser())
  const [initializing, setInitializing] = useState(true)

  useEffect(() => {
    const restoreSession = async () => {
      if (!tokenStorage.getAccessToken() && !tokenStorage.getRefreshToken()) {
        tokenStorage.clear()
        setUser(null)
        setInitializing(false)
        return
      }

      try {
        const currentUser = await authService.currentUser()
        tokenStorage.saveUser(currentUser)
        setUser(currentUser)
      } catch {
        tokenStorage.clear()
        setUser(null)
      } finally {
        setInitializing(false)
      }
    }

    restoreSession()
  }, [])

  const login = async (role, credentials) => {
    const session = await authService.login(role, credentials)
    tokenStorage.saveSession(session)
    setUser(session.user)
    return session.user
  }

  const logout = async () => {
    const refresh = tokenStorage.getRefreshToken()
    try {
      if (refresh) await authService.logout(refresh)
    } finally {
      tokenStorage.clear()
      setUser(null)
    }
  }

  const updateCurrentUser = (updatedUser) => {
    tokenStorage.saveUser(updatedUser)
    setUser(updatedUser)
  }

  const value = useMemo(
    () => ({
      user,
      initializing,
      isAuthenticated: Boolean(user),
      login,
      logout,
      updateCurrentUser,
    }),
    [initializing, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
