import axios from 'axios'

import { tokenStorage } from './tokenStorage.js'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000/api' : '/api'),
})

api.interceptors.request.use((config) => {
  const accessToken = tokenStorage.getAccessToken()
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const refreshToken = tokenStorage.getRefreshToken()

    if (error.response?.status !== 401 || originalRequest?._retry || !refreshToken) {
      return Promise.reject(error)
    }

    originalRequest._retry = true
    try {
      const response = await axios.post(
        `${api.defaults.baseURL}/auth/token/refresh/`,
        { refresh: refreshToken },
      )
      tokenStorage.updateTokens(response.data)
      originalRequest.headers.Authorization = `Bearer ${response.data.access}`
      return api(originalRequest)
    } catch (refreshError) {
      tokenStorage.clear()
      return Promise.reject(refreshError)
    }
  },
)

export default api
