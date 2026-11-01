import api from './api.js'

const unpack = (response) => response.data.results ?? response.data

export const notificationService = {
  list: async (params = {}) => {
    const response = await api.get('/notifications/', { params })
    return unpack(response)
  },
  unreadCount: async () => {
    const response = await api.get('/notifications/unread-count/')
    return response.data.unread_count
  },
  markRead: async (id) => {
    const response = await api.post(`/notifications/${id}/read/`)
    return response.data
  },
  markAllRead: async () => {
    const response = await api.post('/notifications/read-all/')
    return response.data
  },
  getPreferences: async () => {
    const response = await api.get('/notifications/preferences/')
    return response.data
  },
  updatePreferences: async (values) => {
    const response = await api.patch('/notifications/preferences/', values)
    return response.data
  },
}
