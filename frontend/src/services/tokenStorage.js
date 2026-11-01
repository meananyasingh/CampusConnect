const ACCESS_TOKEN_KEY = 'campusconnect_access_token'
const REFRESH_TOKEN_KEY = 'campusconnect_refresh_token'
const USER_KEY = 'campusconnect_user'

export const tokenStorage = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  getUser: () => {
    const value = localStorage.getItem(USER_KEY)
    if (!value) return null

    try {
      return JSON.parse(value)
    } catch {
      localStorage.removeItem(USER_KEY)
      return null
    }
  },
  saveSession: ({ access, refresh, user }) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  updateTokens: ({ access, refresh }) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  },
  saveUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
}
