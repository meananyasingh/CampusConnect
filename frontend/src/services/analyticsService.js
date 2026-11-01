import api from './api.js'

export const analyticsService = {
  studentDashboard: async () => {
    const response = await api.get('/analytics/student/dashboard/')
    return response.data
  },
  recruiterDashboard: async () => {
    const response = await api.get('/analytics/recruiter/dashboard/')
    return response.data
  },
  overview: async () => {
    const response = await api.get('/analytics/admin/overview/')
    return response.data
  },
  listStudents: async (params = {}) => {
    const response = await api.get('/students/', { params })
    return response.data
  },
  updateStudent: async (id, values) => {
    const response = await api.patch(`/students/${id}/`, values)
    return response.data
  },
  resendStudentActivation: async (id) => {
    const response = await api.post(`/students/${id}/resend-activation/`)
    return response.data
  },
  downloadReport: async (reportType) => {
    const response = await api.get(`/analytics/admin/reports/${reportType}/`, { responseType: 'blob' })
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `campusconnect-${reportType}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  },
}
