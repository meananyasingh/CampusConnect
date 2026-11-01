import api from './api.js'

const unpack = (response) => response.data.results ?? response.data

export const placementService = {
  getAdminDashboard: async () => {
    const response = await api.get('/placements/admin/dashboard/')
    return response.data
  },
  getAdminPolicy: async () => {
    const response = await api.get('/placements/admin/policy/')
    return response.data
  },
  updateAdminPolicy: async (values) => {
    const response = await api.patch('/placements/admin/policy/', values)
    return response.data
  },
  listDriveOpportunities: async () => {
    const response = await api.get('/placements/admin/drive-opportunities/')
    return unpack(response)
  },
  listAdminDrives: async () => {
    const response = await api.get('/placements/admin/drives/')
    return unpack(response)
  },
  createDrive: async (values) => {
    const response = await api.post('/placements/admin/drives/', values)
    return response.data
  },
  updateDrive: async (id, values) => {
    const response = await api.patch(`/placements/admin/drives/${id}/`, values)
    return response.data
  },
  deleteDrive: async (id) => api.delete(`/placements/admin/drives/${id}/`),
  listStudentDrives: async () => {
    const response = await api.get('/placements/student/drives/')
    return unpack(response)
  },
  listRecruiterDrives: async () => {
    const response = await api.get('/placements/recruiter/drives/')
    return unpack(response)
  },
  listAdminApplications: async (params = {}) => {
    const response = await api.get('/placements/admin/applications/', { params })
    return unpack(response)
  },
  listAdminInterviews: async (params = {}) => {
    const response = await api.get('/placements/admin/interviews/', { params })
    return unpack(response)
  },
  listAdminRecords: async (params = {}) => {
    const response = await api.get('/placements/admin/records/', { params })
    return unpack(response)
  },
  createRecord: async (values) => {
    const response = await api.post('/placements/admin/records/', values)
    return response.data
  },
  updateRecord: async (id, values) => {
    const response = await api.patch(`/placements/admin/records/${id}/`, values)
    return response.data
  },
  listStudent: async () => {
    const response = await api.get('/placements/student/')
    return unpack(response)
  },
  getStudentReadiness: async () => {
    const response = await api.get('/placements/student/readiness/')
    return response.data
  },
  decideOffer: async (id, status) => {
    const response = await api.patch(`/placements/student/${id}/decision/`, { status })
    return response.data
  },
}
