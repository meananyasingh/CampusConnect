import api from './api.js'

const loginEndpoints = {
  STUDENT: '/auth/student/login/',
  RECRUITER: '/auth/recruiter/login/',
  ADMIN: '/auth/admin/login/',
}

const registrationEndpoints = {
  STUDENT: '/auth/student/register/',
  RECRUITER: '/auth/recruiter/register/',
}

export const authService = {
  login: async (role, credentials) => {
    const response = await api.post(loginEndpoints[role], credentials)
    return response.data
  },
  register: async (role, details) => {
    const response = await api.post(registrationEndpoints[role], details)
    return response.data
  },
  currentUser: async () => {
    const response = await api.get('/auth/me/')
    return response.data
  },
  logout: async (refresh) => api.post('/auth/logout/', { refresh }),
  requestPasswordReset: async (email) => {
    const response = await api.post('/auth/password-reset/', { email })
    return response.data
  },
  confirmPasswordReset: async (details) => {
    const response = await api.post('/auth/password-reset/confirm/', details)
    return response.data
  },
}
