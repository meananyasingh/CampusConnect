import api from './api.js'

export const auditService = {
  list: async (params = {}) => {
    const response = await api.get('/audit/admin/', { params })
    return response.data
  },
  download: async (params = {}) => {
    const response = await api.get('/audit/admin/export/', { params, responseType: 'blob' })
    const objectUrl = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = 'campusconnect-audit-log.csv'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(objectUrl)
  },
}
